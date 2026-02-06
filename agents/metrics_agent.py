"""
Metrics specialist: computes normal vs current latency and delta.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

# Default path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_METRICS_PATH = DATA_DIR / "metrics.json"


def get_metrics_delta(
    metrics_path: Optional[Path] = None,
    incident_time: Optional[str] = None,
    normal_window_minutes: int = 60,
    current_points: int = 5,
) -> dict[str, Any]:
    """
    Compute normal (pre-incident) vs current (recent) latency and delta.

    - normal_ms: median of points before incident window
    - current_ms: median of last current_points
    - delta_ms: current_ms - normal_ms
    - p95: optional 95th percentile of current window (if enough points)
    """
    path = metrics_path or DEFAULT_METRICS_PATH
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "normal_ms": None,
            "current_ms": None,
            "delta_ms": None,
            "p95": None,
            "error": "Failed to load metrics",
        }

    if not isinstance(data, list) or not data:
        return {
            "normal_ms": None,
            "current_ms": None,
            "delta_ms": None,
            "p95": None,
            "error": "No metrics data",
        }

    latencies = [d.get("latency_ms") for d in data if d.get("latency_ms") is not None]
    if not latencies:
        return {
            "normal_ms": None,
            "current_ms": None,
            "delta_ms": None,
            "p95": None,
            "error": "No latency values",
        }

    # Current: last N points
    current_slice = latencies[-current_points:]
    current_ms = _median(current_slice)
    p95 = _percentile(current_slice, 95) if len(current_slice) >= 3 else None

    # Normal: all points except the last current_points (or before incident_time if provided)
    if incident_time and len(data) > current_points:
        # Use only entries before incident_time
        normal_latencies = [
            d.get("latency_ms")
            for d in data
            if d.get("timestamp") and d["timestamp"] < incident_time and d.get("latency_ms") is not None
        ]
    else:
        normal_latencies = latencies[:-current_points] if len(latencies) > current_points else latencies

    normal_ms = _median(normal_latencies) if normal_latencies else current_ms
    delta_ms = (current_ms - normal_ms) if (normal_ms is not None and current_ms is not None) else None

    return {
        "normal_ms": round(normal_ms, 2) if normal_ms is not None else None,
        "current_ms": round(current_ms, 2) if current_ms is not None else None,
        "delta_ms": round(delta_ms, 2) if delta_ms is not None else None,
        "p95": round(p95, 2) if p95 is not None else None,
    }


def _median(values: list[float]) -> float:
    n = len(values)
    if not n:
        return 0.0
    s = sorted(values)
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    return s[f] + (k - f) * (s[c] - s[f]) if c > f else s[f]
