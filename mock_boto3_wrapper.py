"""
Mock Boto3 Wrapper - Boto3-Ready for Hackathon Demo

This module provides AWS client interfaces that:
- HACKATHON MODE: Read from fake JSON logs / mock data (no AWS calls)
- PRODUCTION MODE: Delegate to real Boto3 (set USE_REAL_AWS=1)

Swap the wrapper for real Boto3 when you go live - same interface, zero refactoring.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional

# Lazy import boto3 only when production mode is enabled
_boto3 = None

def _get_boto3():
    global _boto3
    if _boto3 is None:
        import boto3 as b3
        _boto3 = b3
    return _boto3


# =============================================================================
# TOGGLE: Set USE_REAL_AWS=1 to use real Boto3; otherwise uses mock (JSON logs)
# =============================================================================
USE_REAL_AWS = os.environ.get("USE_REAL_AWS", "0").strip().lower() in ("1", "true", "yes")

# Artifacts folder only - no other sources
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


def _artifact_path(filename: str) -> str:
    return os.path.join(ARTIFACTS_DIR, filename)


# -----------------------------------------------------------------------------
# Mock Data - Reads ONLY from artifacts folder (demo_logs.json, etc.)
# -----------------------------------------------------------------------------
def _load_mock_data():
    """Load mock data from artifacts/demo_logs.json only."""
    path = _artifact_path("demo_logs.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"git_history": [], "commit_details": {}, "config": {"memory_mb": 512}}
    # demo_logs format: commit_hash, version_tag, message, author, timestamp, details
    all_entries = []
    commit_details = {}
    for e in raw if isinstance(raw, list) else []:
        entry = {
            "version": e.get("version_tag", e.get("version", "?")),
            "commit": e.get("commit_hash", e.get("commit", "?")),
            "message": e.get("message", ""),
            "author": e.get("author", "unknown"),
            "timestamp": e.get("timestamp", ""),
        }
        all_entries.append(entry)
        if "details" in e:
            commit_details[entry["commit"]] = e["details"]
    return {
        "git_history": all_entries,
        "commit_details": commit_details,
        "config": {"memory_mb": 512, "db_connection_pool": 10},
    }


# -----------------------------------------------------------------------------
# Mock AWS Clients (same method signatures as Boto3)
# -----------------------------------------------------------------------------

class MockLambdaClient:
    """Mock boto3.client('lambda') - reads version from your logs/git history."""

    def get_function(self, FunctionName: str):
        """Production: boto3 lambda.get_function() | Mock: version from MOCK_GIT_HISTORY"""
        data = _load_mock_data()
        # Find latest version for this "function" (service)
        for entry in reversed(data["git_history"]):
            return {
                "Configuration": {
                    "FunctionName": FunctionName,
                    "Version": entry["version"],
                    "LastModified": entry["timestamp"],
                }
            }
        return {"Configuration": {"FunctionName": FunctionName, "Version": "unknown"}}


class MockCodePipelineClient:
    """Mock boto3.client('codepipeline') - reads pipeline state from git_history.json."""

    def get_pipeline_state(self, name: str):
        """Production: codepipeline.get_pipeline_state() | Mock: search MOCK_GIT_HISTORY"""
        data = _load_mock_data()
        stages = []
        for i, entry in enumerate(data["git_history"]):
            stages.append({
                "stageName": f"Source-{i}",
                "latestExecution": {
                    "status": "Succeeded",
                    "lastStatusChange": entry["timestamp"],
                    "summary": entry["message"],
                },
                "actionStates": [{
                    "actionName": "Deploy",
                    "currentRevision": {"revisionId": entry["commit"]},
                    "latestExecution": {"summary": entry["version"]},
                }],
            })
        return {
            "stageStates": stages,
            "pipelineName": name,
        }


class MockAppConfigClient:
    """Mock boto3.client('appconfig') - reads config from db-settings in logs."""

    def get_configuration(self, Application: str, Environment: str, Configuration: str, ClientId: str):
        """Production: appconfig.get_configuration() | Mock: config from mock data"""
        data = _load_mock_data()
        import json
        body = json.dumps(data["config"]).encode("utf-8")
        return {"Content": body}


class MockCloudTrailClient:
    """Mock boto3.client('cloudtrail') - finds who did it and when from git history."""

    def lookup_events(
        self,
        LookupAttributes=None,
        StartTime=None,
        EndTime=None,
        MaxResults=50,
    ):
        """Production: cloudtrail.lookup_events() | Mock: author/time from MOCK_GIT_HISTORY"""
        data = _load_mock_data()
        events = []
        for entry in data["git_history"]:
            ct_event = {
                "userIdentity": {"userName": entry["author"]},
                "requestParameters": {"configuration": entry["version"]},
                "eventTime": entry["timestamp"],
                "eventSource": "appconfig.amazonaws.com",
            }
            events.append({
                "EventId": entry["commit"],
                "Username": entry["author"],
                "EventTime": datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")),
                "EventName": "PutConfiguration",
                "CloudTrailEvent": json.dumps(ct_event),
            })
        return {"Events": events}


class MockCloudWatchLogsClient:
    """Mock boto3.client('logs') - fetches version strings from your logs."""

    def filter_log_events(
        self,
        logGroupName: str,
        startTime: Optional[int] = None,
        endTime: Optional[int] = None,
        filterPattern: Optional[str] = None,
    ):
        """Production: logs.filter_log_events() | Mock: version from MOCK_GIT_HISTORY"""
        data = _load_mock_data()
        events = []
        for entry in data["git_history"]:
            events.append({
                "message": json.dumps({
                    "version": entry["version"],
                    "timestamp": entry["timestamp"],
                    "message": entry["message"],
                }),
                "timestamp": int(datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")).timestamp() * 1000),
            })
        return {"events": events}


# -----------------------------------------------------------------------------
# Client Factory - returns Mock or Real based on USE_REAL_AWS
# -----------------------------------------------------------------------------

def get_aws_client(service_name: str, region_name: str = "us-east-1"):
    """
    Get an AWS client. Same interface in hackathon and production.

    Usage:
        lambda_client = get_aws_client('lambda')
        fn = lambda_client.get_function(FunctionName='my-service')

    Set USE_REAL_AWS=1 to use real Boto3.
    """
    if USE_REAL_AWS:
        b3 = _get_boto3()
        return b3.client(service_name, region_name=region_name)

    # Mock clients
    clients = {
        "lambda": MockLambdaClient(),
        "codepipeline": MockCodePipelineClient(),
        "appconfig": MockAppConfigClient(),
        "cloudtrail": MockCloudTrailClient(),
        "logs": MockCloudWatchLogsClient(),
    }
    if service_name not in clients:
        raise ValueError(f"Mock client for '{service_name}' not implemented. Available: {list(clients.keys())}")
    return clients[service_name]


# -----------------------------------------------------------------------------
# Deployment Agent Helper - High-level "detective" methods
# (What the agent would call; internally uses get_aws_client)
# -----------------------------------------------------------------------------

class AWSDeploymentDetective:
    """
    High-level API that mirrors what the real Deployment Agent would do with Boto3.
    Uses get_aws_client() under the hood - swap happens automatically via USE_REAL_AWS.
    """

    def __init__(self, region_name: str = "us-east-1"):
        self.region = region_name

    def get_deployment_version(self, service_name: str) -> Optional[str]:
        """Get version from Lambda/AppConfig - prod: get_function(), mock: git history."""
        client = get_aws_client("lambda", self.region)
        resp = client.get_function(FunctionName=service_name)
        return resp.get("Configuration", {}).get("Version")

    def get_pipeline_changes(self, pipeline_name: str, service_name: str):
        """Check deployment changes - prod: get_pipeline_state(), mock: git_history."""
        client = get_aws_client("codepipeline", self.region)
        state = client.get_pipeline_state(name=pipeline_name)
        changes = []
        for stage in state.get("stageStates", []):
            for action in stage.get("actionStates", []):
                rev = action.get("currentRevision", {}).get("revisionId")
                summary = action.get("latestExecution", {}).get("summary")
                if rev and summary:
                    changes.append({"commit": rev, "version": summary})
        return changes

    def get_configuration(self, application: str, environment: str, config_name: str) -> dict:
        """Check config (db-settings, memory) - prod: appconfig.get_configuration(), mock: mock data."""
        client = get_aws_client("appconfig", self.region)
        resp = client.get_configuration(
            Application=application,
            Environment=environment,
            Configuration=config_name,
            ClientId="deployment-agent",
        )
        import json
        return json.loads(resp["Content"].decode("utf-8"))

    def get_deployment_event(self, service_name: str, event_name: str = "PutConfiguration") -> Optional[dict]:
        """
        Mock: reads from artifacts/demo_logs.json - simulates CloudTrail.
        Prod: cloudtrail.lookup_events().
        Returns: {"event_id", "user", "time", "details"}
        """
        if not USE_REAL_AWS:
            data = _load_mock_data()
            for entry in data["git_history"]:
                return {
                    "event_id": entry.get("commit"),
                    "user": entry.get("author", "unknown"),
                    "time": entry.get("timestamp"),
                    "details": f"Executed {event_name} for {service_name} (Mock/artifacts)",
                }
            return None
        # Real AWS: CloudTrail
        client = get_aws_client("cloudtrail", self.region)
        start_time = datetime.utcnow() - timedelta(minutes=30)
        response = client.lookup_events(
            LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": event_name}],
            StartTime=start_time,
        )
        for event in response.get("Events", []):
            ct_event_str = event.get("CloudTrailEvent", "{}")
            if service_name not in ct_event_str:
                continue
            return {
                "event_id": event.get("EventId"),
                "user": event.get("Username"),
                "time": event.get("EventTime"),
                "details": f"Configuration update detected via Boto3",
            }
        return None

    def get_deployment_history(self, service_name: str) -> list:
        """
        Mock: reads from artifacts/demo_logs.json only.
        Prod: codepipeline.list_deployments() / list_deployment_instances().
        """
        if not USE_REAL_AWS:
            data = _load_mock_data()
            return data["git_history"]
        # Real AWS: use CodePipeline / CodeDeploy
        client = get_aws_client("codepipeline", self.region)
        state = client.get_pipeline_state(name=f"{service_name}-pipeline")
        history = []
        for stage in state.get("stageStates", []):
            for action in stage.get("actionStates", []):
                rev = action.get("currentRevision", {}).get("revisionId")
                exec_info = stage.get("latestExecution", {})
                summary = exec_info.get("summary", "")
                if rev:
                    data = _load_mock_data()
                    for g in data["git_history"]:
                        if g.get("commit") == rev or g.get("message") == summary:
                            history.append(g)
                            break
                    else:
                        history.append({
                            "version": action.get("latestExecution", {}).get("summary", "?"),
                            "commit": rev,
                            "message": summary,
                            "author": "unknown",
                            "timestamp": exec_info.get("lastStatusChange", ""),
                        })
        return history if history else []
