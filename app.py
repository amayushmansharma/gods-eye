import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.intelligence_engine import analyze_domain, query_memory_drilldown
from services.hindsight_service import HindsightService

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
    Memory drilldown endpoint querying Hindsight Cloud reflect API.
    """
    try:
        answer_data = query_memory_drilldown(req.bank_id, req.brand_name, req.question)
        return JSONResponse(content=answer_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hindsight/status")
def get_hindsight_status():
    return {
        "status": "connected" if hindsight.is_configured() else "local_disk_fallback",
        "hindsight_configured": hindsight.is_configured(),
        "provider": "Vectorize Hindsight Cloud"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.py:app", host="0.0.0.0", port=8000, reload=True)
