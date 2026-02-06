"""
Deploy specialist: Enhanced deployment agent with AWS-compatible mock Boto3 wrapper.

Provides two levels of deployment analysis:
1. Simple deployment listing (backward compatible with engine.py)
2. Detailed change impact analysis using mock AWS clients
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from mock_boto3_wrapper import AWSDeploymentDetective, USE_REAL_AWS
    from data_sources import get_commit_details
    ENHANCED_MODE = True
except ImportError:
    ENHANCED_MODE = False

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
    
    Backward compatible with existing engine.py usage.
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


class DeploymentAgent:
    """
    Enhanced Deployment Agent with AWS-compatible Boto3 wrapper.
    
    In HACKATHON MODE: Reads from artifacts/demo_logs.json (mock data)
    In PRODUCTION MODE: Uses real Boto3 to query AWS services
    
    Toggle via USE_REAL_AWS environment variable.
    """
    
    def __init__(self, name: str = "DeployIntel-Agent", region_name: str = "us-east-1"):
        self.name = name
        self.role = "DevOps Change Analyst"
        self.region = region_name
        
        if ENHANCED_MODE:
            self.detective = AWSDeploymentDetective(region_name=region_name)
            self.mode = "Boto3 (real AWS)" if USE_REAL_AWS else "Mock Boto3 (data/demo_logs.json)"
        else:
            self.detective = None
            self.mode = "Simple (data/deployments.json)"
    
    def analyze_change_impact(
        self, 
        service: str, 
        version: str, 
        incident_time: str
    ) -> dict[str, Any]:
        """
        Analyze deployment change impact for a specific service version.
        
        Returns detailed analysis including:
        - Change log message
        - Technical context (commit details)
        - CloudTrail event info (who made the change)
        - Recommendation
        
        Args:
            service: Service name (e.g., "clinical-analytics-service")
            version: Version tag (e.g., "v2.4.1")
            incident_time: ISO timestamp of incident
            
        Returns:
            Dict with finding, version, change_log, technical_context, recommendation
        """
        if not ENHANCED_MODE:
            return {
                "agent": self.name,
                "finding": "Enhanced mode not available (mock_boto3_wrapper not imported)",
                "mode": self.mode,
            }
        
        print(f"[{self.name}] Investigating changes for {service} ({version})... [{self.mode}]")
        
        # 1. Fetch deployment history via Boto3-like API
        history = self.detective.get_deployment_history(service)
        
        # 2. Get CloudTrail event (who made the change)
        event = self.detective.get_deployment_event(service, event_name="PutConfiguration")
        
        # 3. Find matching version in history
        for change in history:
            if change.get("version") == version or change.get("version_tag") == version:
                # Get detailed commit information
                commit_hash = change.get("commit") or change.get("commit_hash", "")
                details = get_commit_details(commit_hash) if commit_hash else "No details available."
                
                # Add CloudTrail context if available
                author_msg = ""
                if event:
                    author_msg = f" CloudTrail: User '{event['user']}' {event['details']}."
                
                return {
                    "agent": self.name,
                    "finding": "SUSPECT CHANGE DETECTED",
                    "version": version,
                    "change_log": change.get("message", ""),
                    "commit_hash": commit_hash,
                    "author": change.get("author", "unknown"),
                    "timestamp": change.get("timestamp", ""),
                    "technical_context": details + author_msg,
                    "recommendation": f"Rollback to previous stable version recommended.",
                    "mode": self.mode,
                }
        
        return {
            "agent": self.name,
            "finding": "No suspicious deployments found in this window.",
            "mode": self.mode,
        }
    
    def get_deployment_version(self, service_name: str) -> Optional[str]:
        """Get current deployed version for a service."""
        if not ENHANCED_MODE or not self.detective:
            return None
        return self.detective.get_deployment_version(service_name)
    
    def get_configuration(
        self, 
        application: str, 
        environment: str, 
        config_name: str
    ) -> dict[str, Any]:
        """Get configuration from AppConfig (or mock data)."""
        if not ENHANCED_MODE or not self.detective:
            return {}
        return self.detective.get_configuration(application, environment, config_name)
