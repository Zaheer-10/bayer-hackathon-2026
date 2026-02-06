from mock_boto3_wrapper import AWSDeploymentDetective, USE_REAL_AWS
from data_sources import get_commit_details  # Mock: Jira/GitHub details; Prod: CloudTrail has this


class DeploymentAgent:
    def __init__(self, name="DeployIntel-Agent", region_name="us-east-1"):
        self.name = name
        self.role = "DevOps Change Analyst"
        self.detective = AWSDeploymentDetective(region_name=region_name)

    def analyze_change_impact(self, service, version, incident_time):
        mode = "Boto3 (real AWS)" if USE_REAL_AWS else "Mock Boto3 (JSON logs)"
        print(f"[{self.name}] Investigating changes for {service} ({version})... [{mode}]")

        # 1. Fetch data via Boto3-like API (mock reads JSON logs; prod calls AWS)
        history = self.detective.get_deployment_history(service)
        event = self.detective.get_deployment_event(service, event_name="PutConfiguration")

        # 2. Logic: Is there a match?
        for change in history:
            if change.get("version") == version:
                details = get_commit_details(change.get("commit", ""))
                author_msg = ""
                if event:
                    author_msg = f" CloudTrail: User '{event['user']}' {event['details']}."
                return {
                    "agent": self.name,
                    "finding": "SUSPECT CHANGE DETECTED",
                    "version": version,
                    "change_log": change.get("message", ""),
                    "technical_context": details + author_msg,
                    "reccomendation": "Rollback to v2.4.0 immediately.",
                }

        return {"finding": "No suspicious deployments found in this window."}
