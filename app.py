import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.intelligence_engine import analyze_domain, query_memory_drilldown
from services.hindsight_service import HindsightService
from services.snapshot_service import SnapshotService, DEFAULT_WATCHLIST
from scan_watchlist import run_watchlist_scan

app = FastAPI(title="God's Eye - Competitive Intelligence Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

hindsight = HindsightService()
snapshot_svc = SnapshotService()

public_dir = os.path.join(os.path.dirname(__file__), "public")
app.mount("/static", StaticFiles(directory=public_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(public_dir, "index.html"))

@app.get("/api/watchlist")
def get_watchlist():
    """
    Returns compact watchlist list of tracked competitors, their scan counts,
    latest scan timestamps, and cached last scan results.
    """
    manifest = snapshot_svc._load_manifest()
    urls_manifest = manifest.get("urls", {})
    competitors_manifest = manifest.get("competitors", {})

    watchlist_data = []

    # Combine DEFAULT_WATCHLIST with any dynamically added competitors in manifest without duplicates
    seen_domains = set()
    competitors_pool = []
    
    # 1. Add defaults
    for comp in DEFAULT_WATCHLIST:
        d = comp.get("domain", "").lower()
        if d not in seen_domains:
            seen_domains.add(d)
            competitors_pool.append(comp)

    # 2. Add dynamically scanned competitors
    for c_id, c_data in competitors_manifest.items():
        d = c_data.get("domain", "").lower()
        if d and d not in seen_domains:
            seen_domains.add(d)
            competitors_pool.append({
                "id": c_id,
                "name": c_data.get("name", c_id.capitalize()),
                "domain": d,
                "pages": c_data.get("pages", [])
            })

    for comp in competitors_pool:
        c_id = comp["id"]
        c_name = comp["name"]
        domain = comp.get("domain", "")

        pages = comp.get("pages", [])
        pricing_page = next((p for p in pages if p.get("type") == "pricing"), None)
        changelog_page = next((p for p in pages if p.get("type") == "changelog"), None)

        p_info = urls_manifest.get(pricing_page["url"], {}) if pricing_page else {}
        c_info = urls_manifest.get(changelog_page["url"], {}) if changelog_page else {}

        scan_count = max(p_info.get("scan_count", 0), c_info.get("scan_count", 0))
        last_scanned = p_info.get("last_scanned_at") or c_info.get("last_scanned_at")

        # Determine status
        status = "Not Scanned"
        if scan_count == 1:
            status = "Baseline Active"
        elif scan_count > 1:
            p_hist = p_info.get("history", [])
            c_hist = c_info.get("history", [])
            recent_p = p_hist[-1].get("status") if p_hist else ""
            recent_c = c_hist[-1].get("status") if c_hist else ""
            if "page_diff_detected" in [recent_p, recent_c]:
                status = "Changes Detected"
            else:
                status = "Monitored (Stable)"

        # Find cached result by competitor id or domain
        cached_result = None
        for cid, cdata in competitors_manifest.items():
            if cdata.get("domain", "").lower() == domain.lower() or cid == c_id:
                cached_result = cdata.get("last_result")
                if cached_result:
                    cached_result["decisions"] = snapshot_svc.get_decisions(cid)
                break

        watchlist_data.append({
            "id": c_id,
            "name": c_name,
            "domain": domain,
            "pricing_url": pricing_page["url"] if pricing_page else None,
            "changelog_url": changelog_page["url"] if changelog_page else None,
            "scan_count": scan_count,
            "last_scanned_at": last_scanned,
            "status": status,
            "last_result": cached_result
        })

    history = snapshot_svc.get_scan_history()
    return JSONResponse(content={
        "watchlist": watchlist_data,
        "recent_runs": history[-20:],
        "total_tracked_pages": len(urls_manifest)
    })

class ScanSiteRequest(BaseModel):
    url: str

@app.post("/api/scan_url")
def scan_site_endpoint(req: ScanSiteRequest):
    """
    Automatic discovery, snapshotting, diffing, and Hindsight memory integration
    for any user-provided website URL.
    - First scan: saves baseline with real extracted summary (prices, plan limits, changelog).
    - Second/subsequent scan: computes real diff, recalls memories, reflects, and synthesizes recommendation.
    """
    raw_input = req.url.strip()
    if not raw_input:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    # 1. Automatic discovery of pricing & changelog
    discovery = snapshot_svc.discover_pages(raw_input)
    name = discovery["name"]
    domain = discovery["domain"]
    c_id = domain.replace(".", "-").lower()
    bank_id = f"godseye-watchlist-{c_id}"

    pricing_url = discovery["pricing_url"]
    changelog_url = discovery["changelog_url"]

    now_iso = datetime.now(timezone.utc).isoformat()

    # If neither page could be found, return honest diagnostic
    if not pricing_url and not changelog_url:
        return JSONResponse(content={
            "success": False,
            "competitor_id": c_id,
            "name": name,
            "domain": domain,
            "error": "Neither pricing nor changelog page was found. Tested candidate paths: /pricing, /price, /plans, /changelog, /releases, /release-notes, /updates, /blog.",
            "discovery": discovery
        })

    # 2. Process found pages through deterministic snapshot engine
    pricing_res = snapshot_svc.process_url(name, "pricing", pricing_url) if pricing_url else None
    changelog_res = snapshot_svc.process_url(name, "changelog", changelog_url) if changelog_url else None

    # Check scan counts
    p_scans = pricing_res.get("scan_count", 0) if pricing_res else 0
    c_scans = changelog_res.get("scan_count", 0) if changelog_res else 0
    max_scans = max(p_scans, c_scans)
    is_baseline = (max_scans <= 1)

    manifest = snapshot_svc._load_manifest()

    if is_baseline:
        # First-time scan: Extract real baseline summary using Groq
        raw_p_text = pricing_res.get("normalized_full", "") if pricing_res else ""
        raw_c_text = changelog_res.get("normalized_full", "") if changelog_res else ""

        baseline_summary = snapshot_svc.summarize_baseline(raw_p_text, raw_c_text, name)

        # Retain baseline markers into Hindsight
        h_retain_res = hindsight.retain_page_diff(
            bank_id=bank_id,
            competitor=name,
            page_type="baseline",
            url=pricing_url or changelog_url,
            diff_text=f"Baseline established for {name}. Content cataloged.",
            timestamp_iso=now_iso,
            status="baseline_established",
            lines_changed=0
        )
        storage_backend = h_retain_res.get("storage_backend", "hindsight")
        h_error = h_retain_res.get("error") if not h_retain_res.get("success", True) else None

        result_payload = {
            "success": True,
            "competitor_id": c_id,
            "name": name,
            "domain": domain,
            "bank_id": bank_id,
            "is_baseline": True,
            "status": "baseline_saved",
            "scan_number": 1,
            "pricing_url": pricing_url,
            "changelog_url": changelog_url,
            "pricing_status": pricing_res.get("status") if pricing_res else "not_found",
            "changelog_status": changelog_res.get("status") if changelog_res else "not_found",
            "baseline_summary": baseline_summary,
            "recalled_memories": [],
            "recall_error": h_error,
            "storage_backend": storage_backend,
            "timestamp": now_iso,
            "decisions": snapshot_svc.get_decisions(c_id)
        }
    else:
        # Second or subsequent scan: evaluate real diffs
        p_diff = pricing_res.get("diff") if pricing_res else None
        c_diff = changelog_res.get("diff") if changelog_res else None

        has_p_change = p_diff.get("is_change", False) if p_diff else False
        has_c_change = c_diff.get("is_change", False) if c_diff else False
        any_change = has_p_change or has_c_change

        diff_text_accum = []
        if has_p_change and p_diff:
            diff_text_accum.append(f"--- PRICING DIFF ({pricing_url}) ---\n" + p_diff.get("raw_diff", ""))
            hindsight.retain_page_diff(
                bank_id=bank_id,
                competitor=name,
                page_type="pricing",
                url=pricing_url,
                diff_text=p_diff.get("raw_diff", ""),
                timestamp_iso=now_iso,
                status=p_diff.get("status", "diff_detected"),
                lines_changed=p_diff.get("changed_lines_count", 0)
            )

        if has_c_change and c_diff:
            diff_text_accum.append(f"--- CHANGELOG DIFF ({changelog_url}) ---\n" + c_diff.get("raw_diff", ""))
            hindsight.retain_page_diff(
                bank_id=bank_id,
                competitor=name,
                page_type="changelog",
                url=changelog_url,
                diff_text=c_diff.get("raw_diff", ""),
                timestamp_iso=now_iso,
                status=c_diff.get("status", "diff_detected"),
                lines_changed=c_diff.get("changed_lines_count", 0)
            )

        full_diff_str = "\n\n".join(diff_text_accum)

        # Recall memories from Hindsight
        memories = hindsight.recall(bank_id, f"{name} pricing changes releases feature launches")
        recalled_nodes = memories.get("results", [])
        recall_error = memories.get("error")
        storage_backend = memories.get("storage_backend", "hindsight")

        # Native reflect across Hindsight memories
        reflect_res = hindsight.reflect(
            bank_id=bank_id,
            query=f"Synthesize the competitive trajectory, pricing changes, and feature launches for {name} across stored observations."
        )
        reflection_text = reflect_res.get("text", "")
        reflection_error = reflect_res.get("error")

        # Synthesize tactical recommendation grounded in diff and memories
        memory_summary_str = "\n".join([f"- ({m.get('timestamp')}) {m.get('text')}" for m in recalled_nodes[:4]])
        recommendation = snapshot_svc.synthesize_recommendation(
            competitor_name=name,
            diff_text=full_diff_str,
            is_change=any_change,
            memory_context=memory_summary_str
        )

        result_payload = {
            "success": True,
            "competitor_id": c_id,
            "name": name,
            "domain": domain,
            "bank_id": bank_id,
            "is_baseline": False,
            "status": "diff_detected" if any_change else "unchanged",
            "scan_number": max_scans,
            "pricing_url": pricing_url,
            "changelog_url": changelog_url,
            "pricing_diff": p_diff,
            "changelog_diff": c_diff,
            "pricing_status": pricing_res.get("status") if pricing_res else "not_found",
            "changelog_status": changelog_res.get("status") if changelog_res else "not_found",
            "is_change": any_change,
            "raw_diff": full_diff_str,
            "recalled_memories": recalled_nodes,
            "recall_error": recall_error,
            "storage_backend": storage_backend,
            "reflection": reflection_text,
            "reflection_error": reflection_error,
            "recommendation": recommendation,
            "timestamp": now_iso,
            "decisions": snapshot_svc.get_decisions(c_id)
        }

    # Cache competitor result in manifest
    if "competitors" not in manifest:
        manifest["competitors"] = {}
    manifest["competitors"][c_id] = {
        "name": name,
        "domain": domain,
        "pages": [
            {"type": "pricing", "url": pricing_url} if pricing_url else {},
            {"type": "changelog", "url": changelog_url} if changelog_url else {}
        ],
        "last_result": result_payload
    }
    snapshot_svc._save_manifest(manifest)

    return JSONResponse(content=result_payload)

class LogDecisionRequest(BaseModel):
    competitor_id: str
    competitor_name: str
    action: str
    note: Optional[str] = ""
    is_sample: Optional[bool] = True

@app.post("/api/decisions")
def log_decision_endpoint(req: LogDecisionRequest):
    """
    Logs a founder strategic decision (Held price, Matched, Launched campaign, Ignored)
    and retains it into Hindsight memory.
    """
    entry = snapshot_svc.save_decision(
        competitor_id=req.competitor_id,
        competitor_name=req.competitor_name,
        action=req.action,
        note=req.note or "",
        is_sample=req.is_sample if req.is_sample is not None else True
    )

    # Retain decision into Hindsight bank
    bank_id = f"godseye-watchlist-{req.competitor_id}"
    now_iso = entry["timestamp"]
    decision_label = "Sample Founder Decision" if entry["is_sample"] else "Real Founder Decision"
    hindsight.retain_page_diff(
        bank_id=bank_id,
        competitor=req.competitor_name,
        page_type="founder_decision",
        url=f"internal://decisions/{entry['id']}",
        diff_text=f"Decision Logged: {req.action}\nRationale: {entry['note']}\nType: {decision_label}",
        timestamp_iso=now_iso,
        status="founder_decision_logged",
        lines_changed=1
    )

    all_decisions = snapshot_svc.get_decisions(req.competitor_id)
    return JSONResponse(content={"success": True, "entry": entry, "decisions": all_decisions})

@app.get("/api/decisions")
def get_decisions_endpoint(competitor_id: str):
    decisions = snapshot_svc.get_decisions(competitor_id)
    return JSONResponse(content={"competitor_id": competitor_id, "decisions": decisions})

@app.get("/api/hindsight/status")
def get_hindsight_status(force: bool = False):
    """
    Live healthcheck hitting Hindsight API (cached for 60s).
    """
    health = hindsight.check_health(force=force)
    return JSONResponse(content=health)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.py:app", host="0.0.0.0", port=8000, reload=True)
