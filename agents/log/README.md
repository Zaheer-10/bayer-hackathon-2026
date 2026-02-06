# Log Agent

A specialized agent for processing and analyzing log data passed from the Commander Agent.

## Overview

The Log Agent receives log entries as dictionary objects (created and filtered by the Commander Agent) and performs various analysis tasks including:

- **Classification**: Automatically categorizes logs by type (feature, bugfix, maintenance, etc.)
- **Severity Detection**: Determines the severity level of each log entry
- **Keyword Extraction**: Extracts important keywords and metadata
- **Filtering**: Supports filtering by author, type, and severity
- **Summarization**: Provides statistical summaries of processed logs

## Usage

### Basic Usage

```python
from agents.log import LogAgent

# Initialize the agent
agent = LogAgent()

# Process a single log entry (passed from Commander Agent)
log_entry = {
    "commit_hash": "a1b2c3d",
    "timestamp": "2026-02-06T09:45:12Z",
    "author": "dev-team-alpha",
    "version_tag": "v2.4.1",
    "message": "feat(analytics): refactor ReportAggregationEngine",
    "details": "Moved from single-threaded to ThreadPoolExecutor..."
}

processed = agent.process_log_entry(log_entry)
```

### Processing Multiple Logs

```python
# Process multiple logs at once
log_entries = [log1, log2, log3]  # From Commander Agent
agent.process_multiple_logs(log_entries)

# Get summary
summary = agent.get_summary()
print(summary)
```

### Filtering

```python
# Filter by author
dev_alpha_logs = agent.filter_by_author("dev-team-alpha")

# Filter by type
feature_logs = agent.filter_by_type("feature")
bugfix_logs = agent.filter_by_type("bugfix")

# Filter by severity
critical_logs = agent.filter_by_severity("critical")
high_priority = agent.filter_by_severity("high")
```

### Export Analysis

```python
# Export to JSON file
agent.export_analysis("log_analysis_report.json")

# Or get JSON string
json_output = agent.export_analysis()
```

## Integration with Commander Agent

The Commander Agent should:

1. Load logs from the data source (currently `artifacts/demo_logs.json`, later S3)
2. Filter and select only the required log pieces
3. Create dictionary objects with the relevant log data
4. Pass these dictionaries to the Log Agent for processing

```python
# Example Commander Agent integration
from agents.log import LogAgent

# Commander Agent creates filtered log data
filtered_logs = commander.filter_logs(criteria)

# Pass to Log Agent
log_agent = LogAgent()
log_agent.process_multiple_logs(filtered_logs)

# Get insights
summary = log_agent.get_summary()
```

## Log Entry Format

Expected dictionary structure for log entries:

```python
{
    "commit_hash": str,      # Unique identifier
    "timestamp": str,        # ISO format timestamp
    "author": str,           # Author/team name
    "version_tag": str,      # Version tag
    "message": str,          # Commit/log message
    "details": str           # Additional details
}
```

## Analysis Output

Processed logs include:

```python
{
    "original": {...},           # Original log entry
    "processed_at": str,         # Processing timestamp
    "analysis": {
        "log_type": str,         # feature, bugfix, maintenance, etc.
        "severity": str,         # critical, high, medium, info
        "parsed_timestamp": datetime,
        "keywords": [str]        # Extracted keywords
    }
}
```

## Development Notes

- **Current Data Source**: `artifacts/demo_logs.json`
- **Future Data Source**: S3 URL (to be integrated by Commander Agent)
- The Log Agent is designed to be stateless and can process logs independently
- All log data is passed as dictionaries, making it easy to integrate with any data source

## Testing

Run the standalone test:

```bash
cd agents/log
python log_agent.py
```

This will load the demo logs and demonstrate the agent's capabilities.
