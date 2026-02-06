"""
FastAPI server: HTML/CSS/JS UI and API for incident pipeline and LLM query.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine import (
    IncidentState,
    check_metrics_trigger,
    run_incident_pipeline,
)
from rca import generate_rca_report
from llm_agent import get_last_investigation_state, query_llm, set_trigger_time_for_llm

app = FastAPI(title="Autonomous Incident Commander")

# In-memory incident state (single latest run)
_current_state: IncidentState | None = None
STATIC_DIR = Path(__file__).resolve().parent / "static"


def _state_to_dict(s: IncidentState | None) -> dict | None:
    if s is None:
        return None
    return {
        "triggered": s.triggered,
        "trigger_time": s.trigger_time,
        "phase": s.phase,
        "metrics_result": s.metrics_result,
        "logs_result": s.logs_result,
        "deploy_result": s.deploy_result,
        "confidence_score": s.confidence_score,
        "root_cause": s.root_cause,
        "recommendation": s.recommendation,
        "agent_messages": s.agent_messages,
        "rca_report": s.rca_report,
    }


@app.get("/")
def index():
    """Serve the main UI."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="static/index.html not found")
    return FileResponse(index_path)


@app.get("/api/status")
def api_status():
    """Current trigger check and whether we have investigation state."""
    triggered, trigger_time = check_metrics_trigger()
    return {
        "triggered": triggered,
        "trigger_time": trigger_time,
        "has_state": _current_state is not None,
    }


@app.post("/api/simulate-incident")
def api_simulate_incident():
    """Run the full pipeline with mock incident time and store state."""
    global _current_state
    trigger_time = "2026-02-06T10:15:00Z"
    state = IncidentState(triggered=True, trigger_time=trigger_time, latency_threshold=2000)
    state = run_incident_pipeline(state)
    state.rca_report = generate_rca_report(state)
    _current_state = state
    set_trigger_time_for_llm(trigger_time)
    return _state_to_dict(state)


@app.get("/api/state")
def api_state():
    """Return current incident state for the dashboard."""
    return _state_to_dict(_current_state)


class QueryBody(BaseModel):
    message: str


@app.post("/api/query")
def api_query(body: QueryBody):
    """Query the LLM; it can decide and act (e.g. run investigation via tools)."""
    global _current_state
    context = ""
    if _current_state:
        context = (
            f"Last investigation: root_cause={_current_state.root_cause}, "
            f"recommendation={_current_state.recommendation}, "
            f"confidence={( _current_state.confidence_score or 0) * 100:.0f}%. "
            f"Trigger time: {_current_state.trigger_time}. "
        )
    try:
        response = query_llm(body.message.strip(), context_summary=context)
        # If the LLM ran an investigation via tool, persist state for the dashboard
        last_state = get_last_investigation_state()
        if last_state is not None:
            _current_state = last_state
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static assets (CSS, JS) if present
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
