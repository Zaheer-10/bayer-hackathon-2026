from deployment_agent import DeploymentAgent
import json
import os

# Artifacts folder only - demo_logs.json, dummy_logs.json
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")

# 1. Input: Load incident context from artifacts/demo_logs.json only
_logs_path = os.path.join(ARTIFACTS_DIR, "demo_logs.json")
with open(_logs_path, "r", encoding="utf-8") as f:
    logs = json.load(f)
# Use most recent deployment (first entry) as the incident we're investigating
entry = logs[0] if logs else {}
error_log = {
    "timestamp": entry.get("timestamp", ""),
    "service": "clinical-analytics-service",
    "message": entry.get("message", "Deployment change under investigation"),
    "version": entry.get("version_tag", entry.get("version", "unknown")),
}

# Instantiate the agent
deploy_agent = DeploymentAgent()

# 2. The Commander asks the Deployment Agent for help
result = deploy_agent.analyze_change_impact(
    service=error_log['service'],
    version=error_log['version'],
    incident_time=error_log['timestamp']
)

# 3. Final Multi-Agent Output
print("\n--- FINAL INCIDENT ANALYSIS ---")
print(f"Incident: {error_log['message']}")
if "change_log" in result:
    print(f"Root Cause: {result['change_log']}")
    print(f"Technical Reason: {result['technical_context']}")
    print(f"Action: {result['reccomendation']}")
else:
    print(f"Finding: {result['finding']}")
