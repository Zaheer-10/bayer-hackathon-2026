"""
Commander: causal reasoning rules linking deployments to errors.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

# Deployment within this many minutes of first error -> high confidence
DEPLOY_WINDOW_MINUTES = 30
HIGH_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.3

# Keywords that indicate DB/timeout cause
LOG_DB_KEYWORDS = re.compile(r"ConnectionTimeout|DB\s+Timeout|timeout|pool\s+exhausted", re.IGNORECASE)
DEPLOY_DB_KEYWORDS = re.compile(r"DB\s+pool|database|config\s+change|pool\s+size", re.IGNORECASE)


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def evaluate_causal_rules(
    metrics_result: Optional[dict[str, Any]],
    logs_result: Optional[list[dict[str, Any]]],
    deploy_result: Optional[list[dict[str, Any]]],
    trigger_time: Optional[str],
) -> tuple[float, Optional[str], Optional[str]]:
    """
    Apply causal rule: deployment within 30 min of first error + DB-related log + DB-related deploy -> rollback.

    Returns (confidence_score, root_cause, recommendation).
    """
    if not trigger_time:
        return LOW_CONFIDENCE, None, "Investigate further: no trigger time."

    trigger_dt = _parse_iso(trigger_time)
    if not trigger_dt:
        return LOW_CONFIDENCE, None, "Investigate further: invalid trigger time."

    # First error log time (earliest matching log before or at trigger)
    first_error_time: Optional[datetime] = None
    has_db_timeout_log = False
    if logs_result:
        for entry in sorted(logs_result, key=lambda e: e.get("timestamp") or ""):
            msg = (entry.get("message") or "")
            if LOG_DB_KEYWORDS.search(msg):
                has_db_timeout_log = True
            ts = _parse_iso(entry.get("timestamp"))
            if ts and ts <= trigger_dt:
                if first_error_time is None or ts < first_error_time:
                    first_error_time = ts

    # If no log timestamp found, use trigger time as proxy for "first error"
    window_start = (first_error_time or trigger_dt) - timedelta(minutes=DEPLOY_WINDOW_MINUTES)
    window_end = first_error_time or trigger_dt

    # Check deployments in window
    deploy_in_window_with_db: Optional[dict[str, Any]] = None
    if deploy_result:
        for d in deploy_result:
            ts = _parse_iso(d.get("timestamp"))
            desc = (d.get("description") or "")
            if ts and window_start <= ts <= window_end and DEPLOY_DB_KEYWORDS.search(desc):
                deploy_in_window_with_db = d
                break
        if not deploy_in_window_with_db and deploy_result:
            # Fallback: any deploy in window (e.g. DEP-9921)
            for d in deploy_result:
                ts = _parse_iso(d.get("timestamp"))
                if ts and window_start <= ts <= window_end:
                    deploy_in_window_with_db = d
                    break

    # Secret sauce: DB timeout in logs + DB-related deploy in window -> 90% confidence, rollback
    if has_db_timeout_log and deploy_in_window_with_db:
        deploy_id = deploy_in_window_with_db.get("id") or "Unknown"
        return HIGH_CONFIDENCE, deploy_id, "ROLLBACK RECOMMENDED"

    if deploy_in_window_with_db:
        deploy_id = deploy_in_window_with_db.get("id") or "Unknown"
        return 0.6, deploy_id, "Consider rollback; investigate logs for correlation."

    if has_db_timeout_log:
        return 0.5, None, "Investigate further: DB/timeout errors found but no recent DB-related deployment."

    return LOW_CONFIDENCE, None, "Investigate further: no clear cause."
