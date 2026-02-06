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
    
    # Advanced Log Analysis Section
    if state.log_analysis:
        lines.extend([
            "",
            "## Advanced Log Analysis",
        ])
        
        analysis = state.log_analysis
        summary = analysis.get("summary", {})
        
        # Overall stats
        lines.append(f"- **Total logs analyzed:** {summary.get('total_logs', 0)}")
        
        # Severity breakdown
        severities = summary.get("severities", {})
        if severities:
            lines.append("- **Severity breakdown:**")
            for severity, count in sorted(severities.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {severity.upper()}: {count}")
        
        # Log types
        log_types = summary.get("log_types", {})
        if log_types:
            lines.append("- **Log types:**")
            for log_type, count in sorted(log_types.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {log_type}: {count}")
        
        # Insights
        insights = analysis.get("insights", [])
        if insights:
            lines.append("- **Key findings:**")
            for insight in insights:
                lines.append(f"  - {insight}")
        
        # Critical logs
        critical_logs = analysis.get("critical_logs", [])
        if critical_logs:
            lines.extend(["", "### Critical Severity Logs"])
            for log in critical_logs[:3]:  # Show top 3
                lines.append(f"- **{log.get('message', 'N/A')}**")
                if log.get('author'):
                    lines.append(f"  - Author: {log.get('author')}")
                if log.get('details'):
                    lines.append(f"  - Details: {log.get('details')[:100]}")
        
        # High severity logs
        high_logs = analysis.get("high_logs", [])
        if high_logs and not critical_logs:  # Only show if no critical logs
            lines.extend(["", "### High Severity Logs"])
            for log in high_logs[:3]:
                lines.append(f"- **{log.get('message', 'N/A')}**")
                if log.get('details'):
                    lines.append(f"  - Details: {log.get('details')[:100]}")
    
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
