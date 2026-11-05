import os
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from services.intelligence_engine import analyze_domain
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

# Serve static assets
public_dir = os.path.join(os.path.dirname(__file__), "public")
app.mount("/static", StaticFiles(directory=public_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(public_dir, "index.html"))

@app.get("/api/analyze")
def run_analysis(url: str = Query(..., description="Target brand URL to analyze")):
    result = analyze_domain(url)
    return JSONResponse(content=result)

@app.get("/api/hindsight/status")
def get_hindsight_status():
    return {
        "status": "connected" if hindsight.is_configured() else "local_agent_bank",
        "hindsight_configured": hindsight.is_configured(),
        "provider": "Vectorize Hindsight Memory"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.py:app", host="0.0.0.0", port=8000, reload=True)
