"""
Logs specialist: regex/substring search for error keywords in logs.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_LOGS_PATH = DATA_DIR / "logs.json"

# Default keywords for DB/timeout/errors
DEFAULT_KEYWORDS = ["Timeout", "Refused", "500", "ConnectionTimeout", "ERROR"]


def search_logs(
    logs_path: Optional[Path] = None,
    keywords: Optional[list[str]] = None,
    since_time: Optional[str] = None,
    until_time: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Search logs for keywords (regex or substring). Optionally filter by time window.

    Returns list of {timestamp, message, level} for matching entries.
    """
    path = logs_path or DEFAULT_LOGS_PATH
    kw = keywords or DEFAULT_KEYWORDS
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    pattern = re.compile("|".join(re.escape(k) for k in kw), re.IGNORECASE)
    results = []

    for entry in data:
        ts = entry.get("timestamp") or ""
        if since_time and ts < since_time:
            continue
        if until_time and ts > until_time:
            continue
        msg = entry.get("message") or ""
        if pattern.search(msg):
            results.append({
                "timestamp": ts,
                "message": msg,
                "level": entry.get("level", "INFO"),
            })

    return results
