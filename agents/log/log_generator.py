import json
import random
import datetime
import os

def generate_logs():
    authors = ["dev-team-alpha", "sre-lead", "backend-guru", "frontend-ninja", "data-engineer"]
    
    logs = [
        {
            "commit_hash": "a1b2c3d",
            "timestamp": "2026-02-06T09:45:12Z",
            "author": "dev-team-alpha",
            "version_tag": "v2.4.1",
            "message": "feat(analytics): refactor ReportAggregationEngine for parallel processing",
            "details": "Moved from single-threaded to ThreadPoolExecutor to handle larger patient batches. Optimized heap allocation for PB-78421 series."
        },
        {
            "commit_hash": "e5f6g7h",
            "timestamp": "2026-02-05T14:20:00Z",
            "author": "sre-lead",
            "version_tag": "v2.4.0",
            "message": "chore: update base docker image to java-17-slim",
            "details": "Routine security patch for the base runtime environment."
        },
        {
            "commit_hash": "f8a9b0c",
            "timestamp": "2026-02-05T10:15:00Z",
            "author": "backend-guru",
            "version_tag": "v2.3.9",
            "message": "fix(api): NPE in user authentication flow",
            "details": "Resolved NullPointerException when user profile data is incomplete. Added null checks in AuthController."
        },
        {
             "commit_hash": "d4e5f6g",
             "timestamp": "2026-02-04T16:45:30Z",
             "author": "frontend-ninja",
             "version_tag": "v2.3.8",
             "message": "bug(ui): fix navigation bar alignment on mobile",
             "details": "Corrected CSS flexbox layout issues causing overlap on screens smaller than 768px."
        },
        {
            "commit_hash": "h1i2j3k",
            "timestamp": "2026-02-04T09:00:00Z",
            "author": "data-engineer",
            "version_tag": "v2.3.7",
            "message": "perf(db): add index to created_at column",
            "details": "Significantly improved query performance for time-series data retrieval. Reduced latency by 40%."
        },
        {
            "commit_hash": "l4m5n6o",
            "timestamp": "2026-02-03T11:20:15Z",
            "author": "dev-team-alpha",
            "version_tag": "v2.3.6",
            "message": "fix(core): memory leak in background worker",
            "details": "Identified and fixed circular reference in task scheduler causing gradual memory increase over 24h."
        }
    ]

    # Add more random logs if needed, but the static set covers the requirements well.
    
    
    # Use the repo's artifacts directory
    # Assuming the script is run from the project root or we can determine the path relative to this script
    # This script is in agents/log/log_generator.py, so artifacts is ../../artifacts relative to this file
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    artifact_dir = os.path.join(repo_root, "artifacts")
    
    output_file = os.path.join(artifact_dir, "dummy_logs.json")
    
    # Ensure directory exists
    if not os.path.exists(artifact_dir):
        try:
             os.makedirs(artifact_dir)
             print(f"Created directory: {artifact_dir}")
        except Exception as e:
            print(f"Error creating directory {artifact_dir}: {e}")
            output_file = "dummy_logs.json"

    with open(output_file, 'w') as f:
        json.dump(logs, f, indent=2)

    print(f"Logs successfully generated at: {output_file}")

if __name__ == "__main__":
    generate_logs()
