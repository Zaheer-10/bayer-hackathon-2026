import json
import os

# Artifacts folder only - no other sources
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


def get_commit_details(commit_hash: str) -> str:
    """Reads commit details from artifacts/demo_logs.json only."""
    path = os.path.join(ARTIFACTS_DIR, "demo_logs.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for e in (data if isinstance(data, list) else []):
            if e.get("commit_hash", e.get("commit")) == commit_hash:
                return e.get("details", "No details available.")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return "No details available."
