"""
Test Commander Agent - Entry Point
Orchestrates log_agent.py and triggers log analysis based on user alerts/errors
"""

import json
import os
from agents.log.log_agent import LogAgent


class CommanderAgent:
    """
    Commander Agent that orchestrates log analysis
    Receives alerts/errors from user and triggers log agent
    """
    
    def __init__(self, log_source_path: str):
        """
        Initialize Commander Agent
        
        Args:
            log_source_path: Path to log source (currently JSON file, later S3 URL)
        """
        self.log_source_path = log_source_path
        self.log_agent = LogAgent()
        self.all_logs = self._load_logs()
    
    def _load_logs(self):
        """Load logs from source"""
        try:
            with open(self.log_source_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading logs: {e}")
            return []
    
    def filter_logs_by_alert(self, alert_message: str):
        """
        Filter logs based on alert/error message
        
        Args:
            alert_message: User's alert or error message
            
        Returns:
            Filtered log entries relevant to the alert
        """
        filtered = []
        alert_lower = alert_message.lower()
        
        # Search for relevant keywords in logs
        for log in self.all_logs:
            message = log.get('message', '').lower()
            details = log.get('details', '').lower()
            author = log.get('author', '').lower()
            
            # Check if alert keywords match log content
            if any(keyword in message or keyword in details or keyword in author 
                   for keyword in alert_lower.split()):
                filtered.append(log)
        
        return filtered
    
    def process_alert(self, alert_message: str):
        """
        Main method to process user alert/error
        
        Args:
            alert_message: Alert or error message from user
            
        Returns:
            Analysis results
        """
        print(f"\n{'='*60}")
        print(f"ALERT RECEIVED: {alert_message}")
        print(f"{'='*60}\n")
        
        # Filter relevant logs
        print("Filtering relevant logs...")
        filtered_logs = self.filter_logs_by_alert(alert_message)
        
        if not filtered_logs:
            print("No relevant logs found for this alert.")
            return None
        
        print(f"Found {len(filtered_logs)} relevant log(s)\n")
        
        # Pass filtered logs to Log Agent
        print("Processing logs with Log Agent...")
        self.log_agent.process_multiple_logs(filtered_logs)
        
        # Get analysis
        summary = self.log_agent.get_summary()
        
        # Display results
        self._display_results(summary, filtered_logs)
        
        return summary
    
    def _display_results(self, summary, filtered_logs):
        """Display analysis results"""
        print("\n" + "="*60)
        print("LOG ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\nTotal Logs Analyzed: {summary['total_logs']}")
        
        print("\nLog Types:")
        for log_type, count in summary['log_types'].items():
            print(f"  - {log_type}: {count}")
        
        print("\nSeverity Levels:")
        for severity, count in summary['severities'].items():
            print(f"  - {severity.upper()}: {count}")
        
        print("\nAuthors:")
        for author, count in summary['authors'].items():
            print(f"  - {author}: {count}")
        
        # Show critical/high severity logs
        critical_logs = self.log_agent.filter_by_severity("critical")
        high_logs = self.log_agent.filter_by_severity("high")
        
        if critical_logs or high_logs:
            print("\n" + "!"*60)
            print("ATTENTION: Critical/High Severity Logs Found!")
            print("!"*60)
            for log in critical_logs + high_logs:
                severity = log['analysis']['severity']
                message = log['original']['message']
                print(f"  [{severity.upper()}] {message}")
        
        print("\nDetailed Log Entries:")
        for log in filtered_logs:
            print(f"\n  Commit: {log.get('commit_hash')}")
            print(f"  Author: {log.get('author')}")
            print(f"  Version: {log.get('version_tag')}")
            print(f"  Message: {log.get('message')}")
            print(f"  Details: {log.get('details')}")
    
    def interactive_mode(self):
        """Interactive mode for continuous alert processing"""
        print("\n" + "#"*60)
        print("COMMANDER AGENT - Interactive Mode")
        print("#"*60)
        print("\nCommands:")
        print("  - Type an alert/error message to analyze logs")
        print("  - Type 'all' to process all logs")
        print("  - Type 'quit' to exit")
        print("\n")
        
        while True:
            try:
                user_input = input("Enter alert/error (or 'quit'): ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    print("\nExiting Commander Agent...")
                    break
                
                if user_input.lower() == 'all':
                    print("\nProcessing all logs...")
                    self.log_agent.process_multiple_logs(self.all_logs)
                    summary = self.log_agent.get_summary()
                    self._display_results(summary, self.all_logs)
                else:
                    self.process_alert(user_input)
                
                print("\n")
                
            except KeyboardInterrupt:
                print("\n\nExiting Commander Agent...")
                break
            except Exception as e:
                print(f"\nError: {e}")


def main():
    """Main entry point"""
    # Get log source path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_source = os.path.join(current_dir, "artifacts", "demo_logs.json")
    
    # Initialize Commander Agent
    commander = CommanderAgent(log_source)
    
    # Example: Process specific alerts
    print("\n### DEMO: Processing Predefined Alerts ###\n")
    
    # Alert 1: Security issue
    commander.process_alert("security vulnerability scan")
    
    # Alert 2: UI issue
    commander.process_alert("ui rendering issue safari")
    
    # Alert 3: Analytics issue
    commander.process_alert("analytics parallel processing")
    
    # Start interactive mode
    print("\n\n### Starting Interactive Mode ###")
    commander.interactive_mode()


if __name__ == "__main__":
    main()
