"""
LLM agent that can decide and act: query with tools (run investigation, get metrics, logs, deployments).
Supports OpenAI and Azure OpenAI via env.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from engine import IncidentState, run_incident_pipeline
from rca import generate_rca_report
from agents.metrics_agent import get_metrics_delta
from agents.logs_agent import search_logs
from agents.deploy_agent import get_recent_deployments


def _minus_30_min(iso_time: Optional[str]) -> Optional[str]:
    if not iso_time:
        return None
    try:
        from datetime import datetime, timedelta
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        earlier = dt - timedelta(minutes=30)
        return earlier.isoformat().replace("+00:00", "Z")
    except (ValueError, TypeError):
        return None


# In-memory so tools can see current trigger time when LLM asks for investigation
_current_trigger_time: Optional[str] = None
_last_investigation_state: Optional[IncidentState] = None


def set_trigger_time_for_llm(trigger_time: Optional[str] = None) -> None:
    global _current_trigger_time
    _current_trigger_time = trigger_time


def get_last_investigation_state() -> Optional[IncidentState]:
    """Return state from last run_full_investigation tool call (e.g. by LLM)."""
    return _last_investigation_state


@tool
def run_full_investigation(trigger_time_iso: Optional[str] = None) -> str:
    """
    Run the full incident investigation pipeline: gather metrics, logs, and deployments,
    then run causal reasoning to get root cause and recommendation.
    Use this when the user asks to investigate, find root cause, or recommend an action.
    Pass trigger_time_iso as ISO timestamp (e.g. 2026-02-06T10:15:00Z) or leave empty to use last known incident time.
    """
    t = trigger_time_iso or _current_trigger_time or "2026-02-06T10:15:00Z"
    state = IncidentState(triggered=True, trigger_time=t, latency_threshold=2000)
    state = run_incident_pipeline(state)
    state.rca_report = generate_rca_report(state)
    set_trigger_time_for_llm(t)
    global _last_investigation_state
    _last_investigation_state = state
    return (
        f"Investigation complete. Root cause: {state.root_cause or 'Not identified'}. "
        f"Recommendation: {state.recommendation or 'Investigate further'}. "
        f"Confidence: {(state.confidence_score or 0) * 100:.0f}%. "
        f"Agent messages: " + "; ".join(state.agent_messages[-4:])
    )


@tool
def get_metrics(trigger_time_iso: Optional[str] = None) -> str:
    """Get current vs normal latency metrics. Pass trigger_time_iso as ISO string or leave empty for default."""
    t = trigger_time_iso or _current_trigger_time
    out = get_metrics_delta(incident_time=t)
    return str(out)


@tool
def search_logs_tool(since_iso: Optional[str] = None, until_iso: Optional[str] = None) -> str:
    """Search logs for errors (Timeout, Refused, 500). Pass since_iso and until_iso as ISO timestamps or leave empty for last incident window."""
    since = since_iso or (_minus_30_min(_current_trigger_time) if _current_trigger_time else None)
    until = until_iso or _current_trigger_time
    results = search_logs(since_time=since, until_time=until)
    return str(results[:15]) if results else "No matching log entries."


@tool
def get_recent_deployments_tool(before_iso: Optional[str] = None, n: int = 3) -> str:
    """Get the last n deployments before a time. Pass before_iso as ISO timestamp or leave empty for last incident time."""
    before = before_iso or _current_trigger_time
    results = get_recent_deployments(before_time=before, n=n)
    return str(results)


def _get_llm():
    """ChatOpenAI; model from OPENAI_MODEL (default gpt-4o-mini)."""
    api_key =  os.getenv("OPENAI_API_KEY")
    model = (os.getenv("OPENAI_MODEL"))
    return ChatOpenAI(model=model, api_key=api_key, temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")))


def _run_tool(name: str, args: dict) -> str:
    if name == "run_full_investigation":
        return run_full_investigation.invoke(args or {})
    if name == "get_metrics":
        return get_metrics.invoke(args or {})
    if name == "search_logs_tool":
        return search_logs_tool.invoke(args or {})
    if name == "get_recent_deployments_tool":
        return get_recent_deployments_tool.invoke(args or {})
    return f"Unknown tool: {name}"


def query_llm(message: str, context_summary: str = "") -> str:
    """
    Send user message to the LLM. LLM can request tool calls (run investigation, get metrics, etc.);
    we execute them and return the final response.
    """
    from langchain_core.messages import ToolMessage

    global _last_investigation_state
    _last_investigation_state = None  # only set again if run_full_investigation is called this request

    llm = _get_llm()
    tools = [run_full_investigation, get_metrics, search_logs_tool, get_recent_deployments_tool]
    llm_with_tools = llm.bind_tools(tools)
    system = (
        "You are the Autonomous Incident Commander. You help investigate incidents (latency spikes, errors). "
        "When the user asks to investigate, find root cause, or recommend an action, use run_full_investigation. "
        "Use get_metrics, search_logs_tool, or get_recent_deployments_tool for targeted queries. "
        "Always state your reasoning and recommendation clearly."
    )
    if context_summary:
        system += f"\n\nCurrent context from the last investigation:\n{context_summary}"

    messages: list = [SystemMessage(content=system), HumanMessage(content=message)]
    max_rounds = int(os.getenv("MAX_ROUNDS", "5"))
    for _ in range(max_rounds):
        response = llm_with_tools.invoke(messages)
        if not getattr(response, "tool_calls", None):
            return response.content or "No response from the commander."
        messages.append(response)
        for tc in response.tool_calls:
            name = getattr(tc, "name", None) or (tc.get("name", "") if isinstance(tc, dict) else "")
            args = getattr(tc, "args", None) or (tc.get("args") if isinstance(tc, dict) else None) or {}
            tc_id = getattr(tc, "id", None) or (tc.get("id", "") if isinstance(tc, dict) else "")
            result = _run_tool(name, args)
            messages.append(ToolMessage(content=result, tool_call_id=tc_id))
    return messages[-1].content if messages else "No response from the commander."
