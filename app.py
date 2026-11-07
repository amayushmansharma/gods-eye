import os
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.intelligence_engine import (
    run_intelligence_scan,
    get_scan_progress,
    query_memory_drilldown,
    clean_domain_string,
    extract_brand_display,
    SCAN_CACHE_DIR
)
from services.hindsight_service import HindsightService
from services.snapshot_service import SnapshotService

app = FastAPI(title="God's Eye — Autonomous Competitive Intelligence Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

hindsight = HindsightService()
snapshot_svc = SnapshotService()

public_dir = os.path.join(os.path.dirname(__file__), "public")
app.mount("/static", StaticFiles(directory=public_dir), name="static")

ALERTS_FILE = os.path.join(os.path.dirname(__file__), ".snapshots", "alerts.json")


def _load_alerts() -> List[Dict[str, Any]]:
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Default initial alert templates
    return [
        {
            "id": "alert-1",
            "title": "Competitor Price Increase > 2%",
            "company": "All Tracked",
            "condition": "Price change exceeds +2.0%",
            "channel": "In-App Banner + Slack Webhook",
            "status": "Active",
            "created_at": "2026-11-01"
        },
        {
            "id": "alert-2",
            "title": "Flagship EV / AI Feature Launch",
            "company": "BMW India & Rivals",
            "condition": "New model launch or major feature release announced",
            "channel": "Email Digest",
            "status": "Active",
            "created_at": "2026-11-03"
        }
    ]


def _save_alerts(alerts: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)


@app.get("/")
def read_root():
    return FileResponse(
        os.path.join(public_dir, "index.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


class ScanRequest(BaseModel):
    url: str
    deep_mode: Optional[bool] = True
    simulate_rescan: Optional[bool] = False
    scan_id: Optional[str] = None
    use_memory: Optional[bool] = True


@app.post("/api/scan")
def start_scan_endpoint(req: ScanRequest):
    """
    Main Competitive Intelligence scan endpoint.
    Executes the 6-stage research engine:
    1. Understand company positioning & products
    2. Discover 2–4 direct competitors
    3. Research competitor products, pricing and features
    4. Find news and articles published in last 7 days
    5. Analyse trends, launches and recall Hindsight memory
    6. Verify findings against original sources and synthesize recommendations
    """
    raw_url = req.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    from services.intelligence_engine import is_safe_url
    if not is_safe_url(raw_url):
        raise HTTPException(
            status_code=400,
            detail=f"Unsafe target URL '{raw_url}': Localhost, loopback, private networks, and cloud metadata endpoints are strictly restricted."
        )

    scan_id = req.scan_id or f"scan_{uuid.uuid4().hex[:10]}"

    try:
        result = run_intelligence_scan(
            raw_url=raw_url,
            deep_mode=req.deep_mode if req.deep_mode is not None else True,
            simulate_rescan=req.simulate_rescan or False,
            scan_id=scan_id,
            use_memory=req.use_memory if req.use_memory is not None else True
        )
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "scan_id": scan_id}
        )


@app.get("/api/scan_progress/{scan_id}")
def check_scan_progress_endpoint(scan_id: str):
    """
    Provides real-time step streaming of the 6 engine phases,
    elapsed timer, and execution log lines.
    """
    prog = get_scan_progress(scan_id)
    return JSONResponse(content=prog)


@app.get("/api/watchlist")
def get_watchlist():
    """
    Returns watchlist of tracked competitors with latest scans,
    statistics, and cached payloads.
    """
    cached_scans = []
    seen_domains = set()

    # Load all cached scans from .snapshots/scans
    if os.path.exists(SCAN_CACHE_DIR):
        all_files = sorted(
            [os.path.join(SCAN_CACHE_DIR, f) for f in os.listdir(SCAN_CACHE_DIR) if f.endswith(".json")],
            key=lambda p: (1 if "_scan_" not in os.path.basename(p) else 0, os.path.getmtime(p)),
            reverse=True
        )
        for fpath in all_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    domain = data.get("domain", "")
                    if domain and domain not in seen_domains:
                        seen_domains.add(domain)
                        scan_count = data.get("scan_iteration", 1)
                        changes_count = data.get("stats", {}).get("detected_changes_count", 0)
                        if scan_count > 1:
                            status_text = f"{changes_count} changes" if changes_count > 0 else "Compounded Active"
                        else:
                            status_text = "Baseline Active"
                        cached_scans.append({
                            "id": domain.replace(".", "-"),
                            "name": data.get("brand_name", domain),
                            "domain": domain,
                            "target_url": data.get("target_url", f"https://{domain}"),
                            "scan_count": scan_count,
                            "last_scanned_at": data.get("scanned_at"),
                            "last_scanned_iso": data.get("scanned_at_iso", ""),
                            "status": status_text,
                            "changes_count": changes_count,
                            "stats": data.get("stats", {}),
                            "last_result": data
                        })
            except Exception:
                pass

    # Ensure default showcase presets are represented if not yet scanned
    default_presets = [
        {"domain": "linear.app", "name": "Linear", "target_url": "https://linear.app"},
        {"domain": "posthog.com", "name": "PostHog", "target_url": "https://posthog.com"},
        {"domain": "resend.com", "name": "Resend", "target_url": "https://resend.com"},
        {"domain": "school.bosscoderacademy.com", "name": "Bosscoder Academy", "target_url": "https://school.bosscoderacademy.com"},
        {"domain": "bmw.in", "name": "BMW India", "target_url": "https://www.bmw.in/"}
    ]

    for preset in default_presets:
        d = preset["domain"]
        if d not in seen_domains:
            cached_scans.append({
                "id": d.replace(".", "-"),
                "name": preset["name"],
                "domain": d,
                "target_url": preset["target_url"],
                "scan_count": 0,
                "last_scanned_at": None,
                "last_scanned_iso": "",
                "status": "Ready to analyse",
                "changes_count": 0,
                "stats": {"competitors_count": 4, "news_coverage_days": 7},
                "last_result": None
            })

    # Sort watchlist: scanned companies first (ordered by last_scanned_iso descending), then ready presets
    cached_scans.sort(key=lambda x: (x.get("scan_count", 0) > 0, x.get("last_scanned_iso") or ""), reverse=True)

    return JSONResponse(content={
        "watchlist": cached_scans,
        "total_tracked": len(cached_scans)
    })


@app.delete("/api/watchlist/{domain}")
def delete_watchlist_domain(domain: str):
    """
    Clears cached test scan data for a given domain from the watchlist.
    """
    clean_d = clean_domain_string(domain)
    fpath = os.path.join(SCAN_CACHE_DIR, f"{clean_d}.json")
    if os.path.exists(fpath):
        try:
            os.remove(fpath)
            return JSONResponse(content={"success": True, "message": f"Cleared test data for {clean_d}", "domain": clean_d})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(content={"success": True, "message": f"Domain {clean_d} not found in scan cache", "domain": clean_d})


class LogDecisionRequest(BaseModel):
    competitor_id: str
    competitor_name: str
    action: str
    note: Optional[str] = ""
    is_sample: Optional[bool] = False


@app.post("/api/decisions")
def log_decision_endpoint(req: LogDecisionRequest):
    """
    Logs a founder strategic decision (Held price, Matched, Launched campaign, Ignored)
    and retains it permanently into the company's Hindsight memory bank.
    """
    entry = snapshot_svc.save_decision(
        competitor_id=req.competitor_id,
        competitor_name=req.competitor_name,
        action=req.action,
        note=req.note or "",
        is_sample=req.is_sample if req.is_sample is not None else False
    )

    bank_id = f"godseye-intel-{req.competitor_id}"
    decision_type = "Sample Founder Move" if entry.get("is_sample") else "Real Founder Decision"
    
    hindsight.retain_fact(
        bank_id=bank_id,
        brand_name=req.competitor_name,
        content=f"Founder Decision Logged: {req.action}\nRationale: {entry.get('note')}\nStatus: {decision_type}",
        fact_type="founder_decision",
        metadata={
            "action": req.action,
            "decision_id": entry.get("id"),
            "is_sample": entry.get("is_sample")
        },
        timestamp_iso=entry.get("timestamp")
    )

    all_decisions = snapshot_svc.get_decisions(req.competitor_id)
    return JSONResponse(content={"success": True, "entry": entry, "decisions": all_decisions})


@app.get("/api/decisions")
def get_decisions_endpoint(competitor_id: str):
    decisions = snapshot_svc.get_decisions(competitor_id)
    return JSONResponse(content={"competitor_id": competitor_id, "decisions": decisions})


class MemoryQueryRequest(BaseModel):
    bank_id: str
    brand_name: str
    question: str


class FormNodeRequest(BaseModel):
    bank_id: str
    brand_name: str
    label: str
    node_type: str = "Pricing Model"
    content: str


@app.post("/api/hindsight/form_node")
def form_node_endpoint(req: FormNodeRequest):
    """
    Forms a new memory node into the company's Hindsight Persistent Memory Neural Network.
    """
    bank_id = req.bank_id or f"godseye-intel-{req.brand_name.lower().replace(' ', '-')}"
    node_id = f"node_{uuid.uuid4().hex[:16]}"
    chip_id = f"#node_{node_id[5:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Retain into Hindsight persistent memory bank
    hindsight.retain_fact(
        bank_id=bank_id,
        brand_name=req.brand_name,
        content=f"Founder Memory Node [{req.node_type}]: {req.label}\n{req.content}",
        fact_type="user_memory_node",
        metadata={
            "node_id": node_id,
            "chip_id": chip_id,
            "label": req.label,
            "type": req.node_type
        },
        timestamp_iso=now_iso
    )
    
    new_node = {
        "id": node_id,
        "chip_id": chip_id,
        "label": req.label if len(req.label) <= 18 else req.label[:16] + "...",
        "full_title": req.label,
        "subtitle": req.node_type,
        "type": req.node_type,
        "color": "#10b981" if req.node_type == "Pricing Model" else "#38bdf8",
        "content": req.content,
        "timestamp": now_iso
    }
    
    return JSONResponse(content={"success": True, "node": new_node})


@app.post("/api/hindsight/ask")
def ask_hindsight_endpoint(req: MemoryQueryRequest):
    """
    Direct Interrogation into Hindsight Memory.
    Asks a question grounded exclusively in the company's persistent memory nodes.
    """
    result = query_memory_drilldown(
        bank_id=req.bank_id,
        brand_name=req.brand_name,
        question=req.question
    )
    return JSONResponse(content=result)


@app.get("/api/hindsight/status")
def get_hindsight_status(force: bool = False):
    """
    Live health check hitting Hindsight API and reporting engine status.
    """
    health = hindsight.check_health(force=force)
    return JSONResponse(content=health)


@app.get("/api/hindsight/memories/{bank_id}")
def get_bank_memories_endpoint(bank_id: str):
    """
    Inspects all raw memory nodes in a specific Hindsight memory bank.
    """
    memories = hindsight.get_all_memories(bank_id)
    return JSONResponse(content={"bank_id": bank_id, "count": len(memories), "memories": memories})


# Custom Alerts
@app.get("/api/alerts")
def get_alerts():
    return JSONResponse(content={"alerts": _load_alerts()})


class CreateAlertRequest(BaseModel):
    title: str
    company: str
    condition: str
    channel: Optional[str] = "In-App Notification"


@app.post("/api/alerts")
def create_alert(req: CreateAlertRequest):
    alerts = _load_alerts()
    new_alert = {
        "id": f"alert-{int(time.time()*1000)}",
        "title": req.title,
        "company": req.company,
        "condition": req.condition,
        "channel": req.channel or "In-App Notification",
        "status": "Active",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }
    alerts.insert(0, new_alert)
    _save_alerts(alerts)
    return JSONResponse(content={"success": True, "alert": new_alert, "alerts": alerts})


@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: str):
    alerts = _load_alerts()
    alerts = [a for a in alerts if a.get("id") != alert_id]
    _save_alerts(alerts)
    return JSONResponse(content={"success": True, "alerts": alerts})


# Executive PDF / Printable Export
@app.get("/api/export_report/{domain}")
def export_report_endpoint(domain: str):
    """
    Generates a clean, print-ready, professional executive intelligence report
    ready for PDF generation via browser print (Ctrl/Cmd + P).
    """
    clean_d = clean_domain_string(domain)
    meta_path = os.path.join(SCAN_CACHE_DIR, f"{clean_d}.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"No scan report found for {clean_d}. Please run a scan first.")

    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    brand = data.get("brand_name", clean_d)
    tagline = data.get("tagline", "")
    scanned_at = data.get("scanned_at", "")
    summary = data.get("executive_summary", "")
    stats = data.get("stats", {})
    what_happened = data.get("what_happened", {})
    why_it_matters = data.get("why_does_it_matter", {})
    what_to_do = data.get("what_should_we_do", {})
    competitors = what_happened.get("competitors", [])
    matrix = what_happened.get("pricing_feature_matrix", [])
    trends = why_it_matters.get("market_trends", [])
    opps = why_it_matters.get("opportunities", [])
    threats = why_it_matters.get("threats", [])
    recs = what_to_do.get("strategic_recommendations", [])
    news = what_happened.get("news_pulse_7_days", [])
    reflection = why_it_matters.get("hindsight_reflection", "")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>God's Eye Intelligence Report — {brand}</title>
  <style>
    @page {{ size: A4; margin: 18mm; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #111827;
      background: #ffffff;
      line-height: 1.5;
      margin: 0;
      padding: 24px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #000;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }}
    .title {{ font-size: 26px; font-weight: 800; margin: 0; text-transform: uppercase; letter-spacing: -0.5px; }}
    .subtitle {{ font-size: 13px; color: #4b5563; margin-top: 4px; }}
    .meta-badge {{ font-size: 11px; font-family: monospace; background: #f3f4f6; border: 1px solid #d1d5db; padding: 4px 8px; border-radius: 4px; }}
    .stats-row {{ display: flex; gap: 16px; margin-bottom: 24px; }}
    .stat-card {{ flex: 1; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; background: #fafafa; }}
    .stat-val {{ font-size: 24px; font-weight: bold; color: #111827; }}
    .stat-lbl {{ font-size: 11px; text-transform: uppercase; color: #6b7280; font-weight: 600; }}
    .section {{ margin-bottom: 28px; page-break-inside: avoid; }}
    .sec-title {{ font-size: 14px; font-weight: 800; text-transform: uppercase; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 12px; color: #1f2937; display: flex; align-items: center; justify-content: space-between; }}
    .sec-badge {{ font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }}
    .badge-fact {{ background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }}
    .badge-infer {{ background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }}
    .badge-rec {{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px 10px; text-align: left; }}
    th {{ background: #f9fafb; font-weight: 600; text-transform: uppercase; font-size: 11px; }}
    .rec-card {{ border: 1px solid #e5e7eb; border-left: 4px solid #111827; padding: 12px; margin-bottom: 10px; border-radius: 4px; }}
    .rec-act {{ font-weight: 700; font-size: 13px; }}
    .rec-rat {{ font-size: 12px; color: #4b5563; margin-top: 4px; }}
    .print-btn {{
      position: fixed; top: 16px; right: 16px; background: #000; color: #fff;
      padding: 8px 16px; border-radius: 6px; border: none; font-weight: 600; cursor: pointer;
    }}
    @media print {{
      .print-btn {{ display: none; }}
      body {{ padding: 0; }}
    }}
  </style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">Print / Save PDF</button>

  <div class="header">
    <div>
      <h1 class="title">{brand}</h1>
      <div class="subtitle">{tagline} • Domain: {clean_d}</div>
    </div>
    <div style="text-align: right;">
      <span class="meta-badge">GOD'S EYE INTELLIGENCE REPORT</span>
      <div style="font-size: 11px; color: #6b7280; margin-top: 6px;">Generated: {scanned_at}</div>
    </div>
  </div>

  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-val">{stats.get('competitors_count', 4)}</div>
      <div class="stat-lbl">Direct Competitors</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{stats.get('news_coverage_days', 7)} Days</div>
      <div class="stat-lbl">Verified News Coverage</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{stats.get('verified_sources_count', len(news))}</div>
      <div class="stat-lbl">Primary Sources</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">#{data.get('scan_iteration', 1)}</div>
      <div class="stat-lbl">Scan Iteration</div>
    </div>
  </div>

  <div class="section">
    <div class="sec-title">Executive Summary</div>
    <p style="font-size: 13px; color: #374151; margin: 0; line-height: 1.6;">{summary}</p>
  </div>

  <div class="section">
    <div class="sec-title">
      <span>1. What Happened? — Competitor Landscape</span>
      <span class="sec-badge badge-fact">VERIFIED FACT</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Competitor</th>
          <th>Market Share</th>
          <th>Core Focus</th>
          <th>Recent Move / Announcement</th>
          <th>Price Action</th>
          <th>Threat</th>
        </tr>
      </thead>
      <tbody>
        {"".join([f"<tr><td><b>{c.get('name')}</b><br><small style='color:#6b7280;'>{c.get('domain')}</small></td><td>{c.get('market_share')}</td><td>{c.get('focus')}</td><td>{c.get('recent_move')}</td><td>{c.get('price_trend')}</td><td><b>{c.get('threat_level')}</b></td></tr>" for c in competitors])}
      </tbody>
    </table>
  </div>

  {f'''
  <div class="section">
    <div class="sec-title">
      <span>Pricing & Feature Benchmark Matrix</span>
      <span class="sec-badge badge-fact">VERIFIED FACT</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Segment / Tier</th>
          <th>{brand} Offering</th>
          <th>Competitor A</th>
          <th>Competitor B</th>
          <th>Competitor C</th>
        </tr>
      </thead>
      <tbody>
        {"".join([f"<tr><td><b>{m.get('segment')}</b></td><td>{m.get('target_offering')}</td><td>{m.get('comp1_offering')}</td><td>{m.get('comp2_offering')}</td><td>{m.get('comp3_offering')}</td></tr>" for m in matrix])}
      </tbody>
    </table>
  </div>
  ''' if matrix else ''}

  <div class="section">
    <div class="sec-title">
      <span>2. Why Does It Matter? — Macro Trends & Memory Compounding</span>
      <span class="sec-badge badge-infer">INFERRED STRATEGY</span>
    </div>
    <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 12px; border-radius: 6px; font-size: 12px; margin-bottom: 14px;">
      <b>Hindsight Temporal Reflection:</b><br>
      <span style="color: #374151;">{reflection}</span>
    </div>

    <div style="display: flex; gap: 16px;">
      <div style="flex: 1;">
        <h4 style="margin: 0 0 8px 0; font-size: 12px; text-transform: uppercase;">Opportunities (Market Gaps)</h4>
        {"".join([f"<div style='border: 1px solid #e5e7eb; padding: 8px; margin-bottom: 6px; border-radius: 4px; font-size: 11px;'><b>{o.get('title')}</b><br><span style='color:#4b5563;'>Gap: {o.get('gap')}</span><br><b>Action:</b> {o.get('actionable_counter')}</div>" for o in opps])}
      </div>
      <div style="flex: 1;">
        <h4 style="margin: 0 0 8px 0; font-size: 12px; text-transform: uppercase;">Threats (Competitor Moves)</h4>
        {"".join([f"<div style='border: 1px solid #e5e7eb; padding: 8px; margin-bottom: 6px; border-radius: 4px; font-size: 11px;'><b>{t.get('title')} [{t.get('severity')}]</b><br><span style='color:#4b5563;'>Initiated by: {t.get('competitor')}</span><br>{t.get('move_detail')}</div>" for t in threats])}
      </div>
    </div>
  </div>

  <div class="section">
    <div class="sec-title">
      <span>3. What Should We Do? — Strategic Recommendations</span>
      <span class="sec-badge badge-rec">STRATEGIC RECOMMENDATION</span>
    </div>
    {"".join([f"<div class='rec-card'><div class='rec-act'>[{r.get('priority')}] {r.get('action')}</div><div class='rec-rat'><b>Rationale:</b> {r.get('rationale')}</div><div style='font-size:11px; color:#10b981; margin-top:2px;'><b>Expected Outcome:</b> {r.get('expected_outcome')}</div></div>" for r in recs])}
  </div>

  <div class="section" style="border-top: 1px solid #e5e7eb; padding-top: 14px; margin-top: 30px;">
    <div style="font-size: 10px; color: #9ca3af; text-transform: uppercase; font-family: monospace;">
      God's Eye Autonomous Market Intelligence Agent • Grounded in Vectorize Hindsight Persistent Memory
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
