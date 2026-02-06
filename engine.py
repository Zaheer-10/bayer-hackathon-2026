"""
LangGraph state machine and incident trigger (poller) for Autonomous Incident Commander.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable, Optional, TypedDict

from pydantic import BaseModel, Field

from agents.commander import evaluate_causal_rules
from agents.deploy_agent import get_recent_deployments
from agents.logs_agent import search_logs
from agents.metrics_agent import get_metrics_delta

# Default paths relative to project root
DATA_DIR = Path(__file__).resolve().parent / "data"
METRICS_PATH = DATA_DIR / "metrics.json"
LATENCY_THRESHOLD_MS = 2000
POLL_INTERVAL_SEC = 5


class IncidentState(BaseModel):
    """State for the incident investigation pipeline."""

    triggered: bool = False
    trigger_time: Optional[str] = None
    latency_threshold: int = LATENCY_THRESHOLD_MS
    phase: str = "detect"  # detect | investigate | decide | act
    metrics_result: Optional[dict[str, Any]] = None
    logs_result: Optional[list[dict[str, Any]]] = None
    deploy_result: Optional[list[dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    root_cause: Optional[str] = None
    recommendation: Optional[str] = None
    agent_messages: list[str] = Field(default_factory=list)
    rca_report: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


def _read_last_metric(metrics_path: Path = METRICS_PATH) -> Optional[dict[str, Any]]:
    """Read the last entry from metrics.json."""
    try:
        with open(metrics_path) as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return data[-1]
        return None
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def check_metrics_trigger(metrics_path: Path = METRICS_PATH) -> tuple[bool, Optional[str]]:
    """
    Check if the last metric exceeds the latency threshold.
    Returns (triggered, trigger_time_iso).
    """
    entry = _read_last_metric(metrics_path)
    if not entry:
        return False, None
    latency = entry.get("latency_ms")
    ts = entry.get("timestamp")
    if latency is not None and ts and latency > LATENCY_THRESHOLD_MS:
        return True, ts
    return False, None


def run_poller(
    on_trigger: Callable[[IncidentState], None],
    metrics_path: Path = METRICS_PATH,
    interval_sec: float = POLL_INTERVAL_SEC,
    stop_event: Optional[threading.Event] = None,
) -> None:
    """
    Poll metrics every interval_sec. When last latency > threshold, call on_trigger once
    with a new IncidentState and return (or keep running if on_trigger doesn't set stop).
    """
    stop = stop_event or threading.Event()
    triggered_once = False

    while not stop.is_set():
        ok, trigger_time = check_metrics_trigger(metrics_path)
        if ok and not triggered_once:
            triggered_once = True
            state = IncidentState(
                triggered=True,
                trigger_time=trigger_time,
                latency_threshold=LATENCY_THRESHOLD_MS,
            )
            on_trigger(state)
        stop.wait(timeout=interval_sec)


# --- State machine (Gather -> Reason) ---
class GraphState(TypedDict, total=False):
    triggered: bool
    trigger_time: Optional[str]
    latency_threshold: int
    phase: str
    metrics_result: Optional[dict[str, Any]]
    logs_result: Optional[list[dict[str, Any]]]
    deploy_result: Optional[list[dict[str, Any]]]
    confidence_score: Optional[float]
    root_cause: Optional[str]
    recommendation: Optional[str]
    agent_messages: list[str]
    rca_report: Optional[str]


def _gather_node(state: GraphState) -> dict[str, Any]:
    """Fetch metrics, logs, and deployments; append agent messages."""
    trigger_time = state.get("trigger_time")
    messages: list[str] = []

    messages.append("Commander: Fetching metrics, logs, and recent deployments.")
    metrics_result = get_metrics_delta(incident_time=trigger_time)
    messages.append(f"Metrics Agent: Normal={metrics_result.get('normal_ms')}ms, Current={metrics_result.get('current_ms')}ms, Delta={metrics_result.get('delta_ms')}ms.")

    logs_result = search_logs(since_time=_minus_30_min(trigger_time), until_time=trigger_time)
    if logs_result:
        first_log = logs_result[0]
        messages.append(f"Logs Agent: Found {len(logs_result)} matching entries. First: {first_log.get('message', '')[:80]}...")
    else:
        messages.append("Logs Agent: No matching error keywords in window.")

    deploy_result = get_recent_deployments(before_time=trigger_time, n=3)
    if deploy_result:
        for d in deploy_result:
            messages.append(f"Deploy Agent: {d.get('id')} at {d.get('timestamp')} - {d.get('description', '')[:60]}.")
    else:
        messages.append("Deploy Agent: No deployments in window.")

    return {
        "phase": "investigate",
        "metrics_result": metrics_result,
        "logs_result": logs_result,
        "deploy_result": deploy_result,
        "agent_messages": messages,
    }


def _minus_30_min(iso_time: Optional[str]) -> Optional[str]:
    if not iso_time:
        return None
    try:
        from datetime import datetime, timezone, timedelta
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        earlier = dt - timedelta(minutes=30)
        return earlier.isoformat().replace("+00:00", "Z")
    except (ValueError, TypeError):
        return None


def _reason_node(state: GraphState) -> dict[str, Any]:
    """Commander evaluates causal rules and sets confidence, root_cause, recommendation."""
    messages: list[str] = []
    messages.append("Commander: Evaluating causal rules (deployment within 30 min of first error + DB/timeout correlation).")

    confidence, root_cause, recommendation = evaluate_causal_rules(
        state.get("metrics_result"),
        state.get("logs_result"),
        state.get("deploy_result"),
        state.get("trigger_time"),
    )
    if root_cause:
        messages.append(f"Commander: Root cause identified: {root_cause}. Confidence={confidence:.0%}. {recommendation}")
    else:
        messages.append(f"Commander: {recommendation} (confidence={confidence:.0%})")

    return {
        "phase": "decide",
        "confidence_score": confidence,
        "root_cause": root_cause,
        "recommendation": recommendation,
        "agent_messages": messages,
    }


def run_incident_pipeline(state: IncidentState) -> IncidentState:
    """
    Run the full pipeline: Gather -> Reason. Updates and returns the given state (and agent_messages).
    """
    current: GraphState = {
        "triggered": state.triggered,
        "trigger_time": state.trigger_time,
        "latency_threshold": state.latency_threshold,
        "phase": state.phase,
        "agent_messages": list(state.agent_messages),
    }
    # Gather
    gather_out = _gather_node(current)
    current["phase"] = gather_out.get("phase", current["phase"])
    current["metrics_result"] = gather_out.get("metrics_result")
    current["logs_result"] = gather_out.get("logs_result")
    current["deploy_result"] = gather_out.get("deploy_result")
    current["agent_messages"] = (current.get("agent_messages") or []) + (gather_out.get("agent_messages") or [])
    # Reason
    reason_out = _reason_node(current)
    current["phase"] = reason_out.get("phase", current["phase"])
    current["confidence_score"] = reason_out.get("confidence_score")
    current["root_cause"] = reason_out.get("root_cause")
    current["recommendation"] = reason_out.get("recommendation")
    current["agent_messages"] = (current.get("agent_messages") or []) + (reason_out.get("agent_messages") or [])
    # Map back to IncidentState
    state.phase = current.get("phase") or state.phase
    state.metrics_result = current.get("metrics_result")
    state.logs_result = current.get("logs_result")
    state.deploy_result = current.get("deploy_result")
    state.confidence_score = current.get("confidence_score")
    state.root_cause = current.get("root_cause")
    state.recommendation = current.get("recommendation")
    state.agent_messages = current.get("agent_messages") or []
    return state
