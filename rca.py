"""
RCA report generator from final IncidentState (template-based; optional LLM via Azure OpenAI).
"""
from __future__ import annotations

import os
from typing import Any, Optional

from engine import IncidentState


def generate_rca_report(state: IncidentState) -> str:
    """
    Produce a Markdown RCA report from the final IncidentState.
    Uses template; if Azure OpenAI env vars are set, can optionally use LLM for summary.
    """
    return _template_report(state)


def _template_report(state: IncidentState) -> str:
    """Template-based Markdown report."""
    lines = [
        "# Root Cause Analysis Report",
        "",
        "## Summary",
        f"- **Trigger time:** {state.trigger_time or 'N/A'}",
        f"- **Root cause:** {state.root_cause or 'Not identified'}",
        f"- **Confidence:** {(state.confidence_score or 0) * 100:.0f}%",
        f"- **Recommendation:** {state.recommendation or 'Investigate further'}",
        "",
        "## Timeline",
    ]
    if state.trigger_time:
        lines.append(f"- Incident detected at {state.trigger_time} (latency > {state.latency_threshold}ms).")
    if state.deploy_result:
        lines.append("- Recent deployments before incident:")
        for d in state.deploy_result:
            lines.append(f"  - **{d.get('id', '')}** at {d.get('timestamp', '')}: {d.get('description', '')}")
    if state.logs_result:
        lines.append("- Relevant log entries:")
        for log in (state.logs_result or [])[:5]:
            lines.append(f"  - [{log.get('timestamp')}] {log.get('level')}: {log.get('message', '')[:100]}")
    lines.extend([
        "",
        "## Evidence",
    ])
    if state.metrics_result:
        m = state.metrics_result
        lines.append(f"- Metrics: Normal latency {m.get('normal_ms')}ms → Current {m.get('current_ms')}ms (delta {m.get('delta_ms')}ms).")
    if state.logs_result:
        lines.append(f"- Logs: {len(state.logs_result)} entries matched error keywords (e.g. ConnectionTimeout, 500).")
    if state.deploy_result and state.root_cause:
        dep = next((d for d in state.deploy_result if d.get("id") == state.root_cause), None)
        if dep:
            lines.append(f"- Deployment **{state.root_cause}** at {dep.get('timestamp')}: {dep.get('description')}.")
    lines.extend([
        "",
        "## Recommendation",
        state.recommendation or "Investigate further.",
        "",
    ])
    return "\n".join(lines)
