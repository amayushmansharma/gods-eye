import os
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

public_dir = os.path.join(os.path.dirname(__file__), "public")
app.mount("/static", StaticFiles(directory=public_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(public_dir, "index.html"))

@app.get("/api/watchlist")
def get_watchlist():
    """
    Returns watchlist competitors, their monitored pricing/changelog pages,
    real scan counts, last scan timestamps, and Hindsight memory nodes.
    """
    snapshot_svc = SnapshotService()
    manifest = snapshot_svc._load_manifest().get("urls", {})
    watchlist_data = []

    for comp in DEFAULT_WATCHLIST:
        c_id = comp["id"]
        c_name = comp["name"]
        bank_id = f"godseye-watchlist-{c_id}"
        
        pages_status = []
        for p in comp.get("pages", []):
            u = p["url"]
            manifest_info = manifest.get(u, {})
            pages_status.append({
                "type": p["type"],
                "url": u,
                "scan_count": manifest_info.get("scan_count", 0),
                "baseline_at": manifest_info.get("baseline_at"),
                "last_scanned_at": manifest_info.get("last_scanned_at"),
                "history": manifest_info.get("history", [])[-5:]
            })
        
        # Recall memories from Hindsight
        memories = hindsight.recall(bank_id, f"{c_name} pricing changelog competitor move")
        
        watchlist_data.append({
            "id": c_id,
            "name": c_name,
            "domain": comp["domain"],
            "bank_id": bank_id,
            "pages": pages_status,
            "memories": memories.get("results", []),
            "storage_backend": memories.get("storage_backend", "hindsight"),
            "recall_error": memories.get("error")
        })

    history = snapshot_svc.get_scan_history()
    return JSONResponse(content={
        "watchlist": watchlist_data,
        "recent_runs": history[-20:],
        "total_tracked_pages": len(manifest)
    })

@app.post("/api/watchlist/scan")
def trigger_watchlist_scan():
    """
    Triggers live watchlist scan across pricing and changelog pages,
    diffing against previous snapshots and updating Hindsight.
    """
    try:
        results = run_watchlist_scan()
        return JSONResponse(content={"success": True, "results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AddCompetitorRequest(BaseModel):
    name: str
    domain: str
    pricing_url: str
    changelog_url: str

@app.post("/api/watchlist/add")
def add_competitor_to_watchlist(req: AddCompetitorRequest):
    new_comp = {
        "id": req.name.lower().replace(" ", "-"),
        "name": req.name,
        "domain": req.domain,
        "pages": [
            {"type": "pricing", "url": req.pricing_url},
            {"type": "changelog", "url": req.changelog_url}
        ]
    }
    DEFAULT_WATCHLIST.append(new_comp)
    return JSONResponse(content={"success": True, "competitor": new_comp})

@app.get("/api/analyze")
def run_analysis(url: str = Query(..., description="Target brand URL to analyze")):
    result = analyze_domain(url)
    return JSONResponse(content=result)

class AskRequest(BaseModel):
    bank_id: str
    question: str
    brand_name: str

@app.post("/api/ask")
def ask_gods_eye(req: AskRequest):
    """
    Memory drilldown endpoint querying Hindsight reflect API.
    """
    try:
        answer_data = query_memory_drilldown(req.bank_id, req.brand_name, req.question)
        return JSONResponse(content=answer_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
