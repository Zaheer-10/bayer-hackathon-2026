"""
Example: How Commander Agent would integrate with Log Agent

This demonstrates how the Commander Agent should pass filtered
log data (as dictionary objects) to the Log Agent.
"""

import json
from log_agent import LogAgent


def main():
    """Example integration between Commander Agent and Log Agent"""
    
    # Initialize Log Agent
    log_agent = LogAgent()
    
    # Example 1: Commander Agent passes a single log entry
    print("Example 1: Processing single log entry")
    print("=" * 50)
    
    single_log = {
        "commit_hash": "a1b2c3d",
        "timestamp": "2026-02-06T09:45:12Z",
        "author": "dev-team-alpha",
        "version_tag": "v2.4.1",
        "message": "feat(analytics): refactor ReportAggregationEngine for parallel processing",
        "details": "Moved from single-threaded to ThreadPoolExecutor to handle larger patient batches."
    }
    
    result = log_agent.process_log_entry(single_log)
    print(f"Log Type: {result['analysis']['log_type']}")
    print(f"Severity: {result['analysis']['severity']}")
    print(f"Keywords: {result['analysis']['keywords']}")
    print()
    
    # Example 2: Commander Agent passes multiple filtered logs
    print("Example 2: Processing multiple log entries")
    print("=" * 50)
    
    # Commander Agent would filter and select only required logs
    filtered_logs = [
        {
            "commit_hash": "e5f6g7h",
            "timestamp": "2026-02-05T14:20:00Z",
            "author": "sre-lead",
            "version_tag": "v2.4.0",
            "message": "chore: update base docker image to java-17-slim",
            "details": "Routine security patch for the base runtime environment."
        },
        {
            "commit_hash": "m2n3o4p",
            "timestamp": "2026-02-03T18:33:07Z",
            "author": "dev-team-beta",
            "version_tag": "v2.3.8",
            "message": "fix(ui): resolve chart rendering issue on Safari",
            "details": "Corrected CSS flexbox layout and upgraded Plotly dependency to v2.14.2."
        }
    ]
    
    log_agent.process_multiple_logs(filtered_logs)
    
    # Get summary
    summary = log_agent.get_summary()
    print(json.dumps(summary, indent=2, default=str))
    print()
    
    # Example 3: Filtering processed logs
    print("Example 3: Filtering by severity")
    print("=" * 50)
    
    critical_logs = log_agent.filter_by_severity("critical")
    print(f"Found {len(critical_logs)} critical logs")
    for log in critical_logs:
        print(f"  - {log['original']['message']}")


if __name__ == "__main__":
    main()
