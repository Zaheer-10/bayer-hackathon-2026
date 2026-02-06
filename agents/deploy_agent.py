"""
Deploy specialist: returns last N deployments before a given time.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DEPLOYMENTS_PATH = DATA_DIR / "deployments.json"


def get_recent_deployments(
    deployments_path: Optional[Path] = None,
    before_time: Optional[str] = None,
    n: int = 3,
) -> list[dict[str, Any]]:
    """
    Return the last n deployments before before_time.
    Each item: {id, timestamp, description}.
    """
    path = deployments_path or DEFAULT_DEPLOYMENTS_PATH
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    # Filter by before_time if provided
    if before_time:
        data = [d for d in data if (d.get("timestamp") or "") <= before_time]

    # Sort by timestamp descending and take first n
    sorted_deploys = sorted(data, key=lambda d: d.get("timestamp") or "", reverse=True)
    selected = sorted_deploys[:n]

    return [
        {
            "id": d.get("id", ""),
            "timestamp": d.get("timestamp", ""),
            "description": d.get("description", ""),
        }
        for d in selected
    ]
