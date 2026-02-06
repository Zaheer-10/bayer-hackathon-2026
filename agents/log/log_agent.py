"""
Log Agent - Processes and analyzes log data passed from the Commander Agent

This agent receives log data as dictionary objects and performs various
analysis tasks such as filtering, parsing, and extracting insights.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class LogAgent:
    """
    Log Agent that processes log entries passed as dictionary objects.
    
    The Commander Agent will create and pass filtered log pieces to this agent
    for processing and analysis.
    """
    
    def __init__(self):
        """Initialize the Log Agent"""
        self.processed_logs = []
        
    def process_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single log entry (passed as dictionary from Commander Agent)
        
        Args:
            log_entry: Dictionary containing log data with fields like:
                - commit_hash
                - timestamp
                - author
                - version_tag
                - message
                - details
                
        Returns:
            Processed log entry with additional metadata
        """
        processed = {
            "original": log_entry,
            "processed_at": datetime.now().isoformat(),
            "analysis": self._analyze_log_entry(log_entry)
        }
        
        self.processed_logs.append(processed)
        return processed
    
    def process_multiple_logs(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple log entries
        
        Args:
            log_entries: List of log entry dictionaries
            
        Returns:
            List of processed log entries
        """
        return [self.process_log_entry(entry) for entry in log_entries]
    
    def _analyze_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a log entry and extract insights
        
        Args:
            log_entry: Log entry dictionary
            
        Returns:
            Analysis results
        """
        analysis = {
            "log_type": self._classify_log_type(log_entry.get("message", "")),
            "severity": self._determine_severity(log_entry),
            "parsed_timestamp": self._parse_timestamp(log_entry.get("timestamp")),
            "keywords": self._extract_keywords(log_entry),
        }
        
        return analysis
    
    def _classify_log_type(self, message: str) -> str:
        """
        Classify the type of log entry based on message
        
        Args:
            message: Commit message or log message
            
        Returns:
            Log type (feat, fix, chore, test, ci, etc.)
        """
        message_lower = message.lower()
        
        if message_lower.startswith("feat"):
            return "feature"
        elif message_lower.startswith("fix"):
            return "bugfix"
        elif message_lower.startswith("chore"):
            return "maintenance"
        elif message_lower.startswith("test"):
            return "testing"
        elif message_lower.startswith("ci"):
            return "ci/cd"
        elif message_lower.startswith("docs"):
            return "documentation"
        else:
            return "other"
    
    def _determine_severity(self, log_entry: Dict[str, Any]) -> str:
        """
        Determine the severity level of a log entry
        
        Args:
            log_entry: Log entry dictionary
            
        Returns:
            Severity level (critical, high, medium, low, info)
        """
        message = log_entry.get("message", "").lower()
        details = log_entry.get("details", "").lower()
        
        # Check for critical keywords
        critical_keywords = ["vulnerability", "security", "breach", "critical"]
        if any(keyword in message or keyword in details for keyword in critical_keywords):
            return "critical"
        
        # Check for high priority keywords
        high_keywords = ["fix", "bug", "error", "issue"]
        if any(keyword in message for keyword in high_keywords):
            return "high"
        
        # Check for medium priority
        medium_keywords = ["feature", "update", "improve"]
        if any(keyword in message for keyword in medium_keywords):
            return "medium"
        
        # Default to info
        return "info"
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """
        Parse timestamp string to datetime object
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not timestamp_str:
            return None
        
        try:
            # Handle ISO format with Z suffix
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            return datetime.fromisoformat(timestamp_str)
        except Exception:
            return None
    
    def _extract_keywords(self, log_entry: Dict[str, Any]) -> List[str]:
        """
        Extract important keywords from log entry
        
        Args:
            log_entry: Log entry dictionary
            
        Returns:
            List of extracted keywords
        """
        keywords = []
        
        # Extract from message
        message = log_entry.get("message", "")
        if ":" in message:
            parts = message.split(":")
            if len(parts) > 1:
                keywords.append(parts[0].strip())  # The prefix (feat, fix, etc.)
                scope = parts[1].strip().split()[0] if parts[1].strip() else ""
                if scope:
                    keywords.append(scope)
        
        # Add author as keyword
        author = log_entry.get("author")
        if author:
            keywords.append(author)
        
        # Add version tag
        version = log_entry.get("version_tag")
        if version:
            keywords.append(version)
        
        return keywords
    
    def filter_by_author(self, author: str) -> List[Dict[str, Any]]:
        """
        Filter processed logs by author
        
        Args:
            author: Author name to filter by
            
        Returns:
            List of logs by the specified author
        """
        return [
            log for log in self.processed_logs 
            if log["original"].get("author") == author
        ]
    
    def filter_by_type(self, log_type: str) -> List[Dict[str, Any]]:
        """
        Filter processed logs by type
        
        Args:
            log_type: Log type to filter by (feature, bugfix, etc.)
            
        Returns:
            List of logs of the specified type
        """
        return [
            log for log in self.processed_logs 
            if log["analysis"]["log_type"] == log_type
        ]
    
    def filter_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """
        Filter processed logs by severity
        
        Args:
            severity: Severity level to filter by
            
        Returns:
            List of logs with the specified severity
        """
        return [
            log for log in self.processed_logs 
            if log["analysis"]["severity"] == severity
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all processed logs
        
        Returns:
            Summary statistics
        """
        if not self.processed_logs:
            return {"total_logs": 0, "message": "No logs processed yet"}
        
        log_types = {}
        severities = {}
        authors = {}
        
        for log in self.processed_logs:
            # Count log types
            log_type = log["analysis"]["log_type"]
            log_types[log_type] = log_types.get(log_type, 0) + 1
            
            # Count severities
            severity = log["analysis"]["severity"]
            severities[severity] = severities.get(severity, 0) + 1
            
            # Count authors
            author = log["original"].get("author", "unknown")
            authors[author] = authors.get(author, 0) + 1
        
        return {
            "total_logs": len(self.processed_logs),
            "log_types": log_types,
            "severities": severities,
            "authors": authors,
            "latest_log": self.processed_logs[-1]["original"] if self.processed_logs else None
        }
    
    def export_analysis(self, filepath: Optional[str] = None) -> str:
        """
        Export the analysis results to JSON
        
        Args:
            filepath: Optional path to save the analysis
            
        Returns:
            JSON string of the analysis
        """
        analysis_data = {
            "summary": self.get_summary(),
            "processed_logs": self.processed_logs
        }
        
        json_output = json.dumps(analysis_data, indent=2, default=str)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_output)
        
        return json_output


# Example usage (for testing purposes)
if __name__ == "__main__":
    # This simulates how the Commander Agent would pass log data
    agent = LogAgent()
    
    # Load demo logs
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    demo_logs_path = os.path.join(project_root, "artifacts", "demo_logs.json")
    
    with open(demo_logs_path, "r") as f:
        demo_logs = json.load(f)
    
    # Process logs (Commander Agent would pass only required log pieces)
    print("Processing logs...")
    agent.process_multiple_logs(demo_logs)
    
    # Get summary
    summary = agent.get_summary()
    print("\n=== LOG ANALYSIS SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    
    # Filter examples
    print("\n=== FEATURE LOGS ===")
    feature_logs = agent.filter_by_type("feature")
    for log in feature_logs:
        print(f"- {log['original']['message']}")
    
    print("\n=== CRITICAL/HIGH SEVERITY LOGS ===")
    critical_logs = agent.filter_by_severity("critical")
    high_logs = agent.filter_by_severity("high")
    for log in critical_logs + high_logs:
        print(f"- [{log['analysis']['severity'].upper()}] {log['original']['message']}")
