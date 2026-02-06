import json
import random
import datetime
import os
import string

def generate_random_hash(length=7):
    """Generate a random commit hash."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_timestamp(days_ago):
    """Generate a timestamp for a given number of days ago."""
    base_time = datetime.datetime(2026, 2, 6, 12, 0, 0)
    delta = datetime.timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59), seconds=random.randint(0, 59))
    timestamp = base_time - delta
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

def generate_logs(num_logs=20):
    """
    Generate dummy logs with errors.
    
    Args:
        num_logs (int): Number of log entries to generate. Default is 20.
    """
    authors = ["dev-team-alpha", "sre-lead", "backend-guru", "frontend-ninja", "data-engineer", "devops-master", "qa-specialist"]
    
    # Message templates categorized by type
    error_messages = [
        ("fix(api): NPE in user authentication flow", "Resolved NullPointerException when user profile data is incomplete. Added null checks in AuthController."),
        ("fix(core): memory leak in background worker", "Identified and fixed circular reference in task scheduler causing gradual memory increase over 24h."),
        ("bug(ui): fix navigation bar alignment on mobile", "Corrected CSS flexbox layout issues causing overlap on screens smaller than 768px."),
        ("fix(db): deadlock in transaction processing", "Resolved database deadlock caused by improper lock ordering in concurrent transactions."),
        ("fix(auth): session timeout not being enforced", "Fixed bug where user sessions were not expiring correctly. Updated session middleware."),
        ("bug(api): incorrect error codes returned", "Corrected HTTP status codes for validation failures. Changed from 500 to 400."),
        ("fix(cache): race condition in cache invalidation", "Fixed race condition causing stale data to be served. Added proper locking mechanism."),
        ("fix(network): connection pool exhaustion", "Resolved connection leak in HTTP client. Properly closing connections after use."),
        ("bug(parser): incorrect handling of edge cases", "Fixed parser crash on malformed input. Added validation and error handling."),
        ("fix(security): XSS vulnerability in user input", "Sanitized user input to prevent cross-site scripting attacks. Applied proper escaping."),
    ]
    
    feature_messages = [
        ("feat(analytics): refactor ReportAggregationEngine for parallel processing", "Moved from single-threaded to ThreadPoolExecutor to handle larger patient batches. Optimized heap allocation for PB-78421 series."),
        ("feat(ui): add dark mode support", "Implemented system-wide dark mode with user preference persistence. Updated all components."),
        ("feat(api): add pagination to list endpoints", "Added cursor-based pagination for better performance on large datasets."),
        ("feat(monitoring): integrate Prometheus metrics", "Added custom metrics for business KPIs. Configured Grafana dashboards."),
        ("feat(search): implement full-text search", "Integrated Elasticsearch for advanced search capabilities across all entities."),
    ]
    
    chore_messages = [
        ("chore: update base docker image to java-17-slim", "Routine security patch for the base runtime environment."),
        ("chore: bump dependency versions", "Updated all dependencies to latest stable versions. No breaking changes."),
        ("chore: refactor test utilities", "Consolidated test helper functions into shared module for better reusability."),
        ("chore: update CI/CD pipeline configuration", "Optimized build times by parallelizing test execution."),
        ("docs: update API documentation", "Added examples and clarified parameter descriptions for all endpoints."),
    ]
    
    perf_messages = [
        ("perf(db): add index to created_at column", "Significantly improved query performance for time-series data retrieval. Reduced latency by 40%."),
        ("perf(api): optimize JSON serialization", "Switched to faster JSON library. Reduced response time by 25%."),
        ("perf(cache): implement Redis caching layer", "Added distributed cache for frequently accessed data. Reduced database load by 60%."),
        ("perf(query): optimize N+1 query problem", "Implemented eager loading for related entities. Reduced query count from 1000+ to 10."),
    ]
    
    all_messages = error_messages + feature_messages + chore_messages + perf_messages
    
    logs = []
    version_major = 2
    version_minor = 4
    version_patch = 1
    
    for i in range(num_logs):
        commit_hash = generate_random_hash()
        timestamp = generate_timestamp(days_ago=i // 3)  # Group logs by days
        author = random.choice(authors)
        
        # Decrease version as we go back in time
        if i > 0 and i % 5 == 0:
            version_patch -= 1
            if version_patch < 0:
                version_patch = 9
                version_minor -= 1
                if version_minor < 0:
                    version_minor = 9
                    version_major -= 1
        
        version_tag = f"v{version_major}.{version_minor}.{version_patch}"
        
        # 40% chance of error/bug fix, 60% other types
        if random.random() < 0.4:
            message, details = random.choice(error_messages)
        else:
            message, details = random.choice(all_messages)
        
        log_entry = {
            "commit_hash": commit_hash,
            "timestamp": timestamp,
            "author": author,
            "version_tag": version_tag,
            "message": message,
            "details": details
        }
        
        logs.append(log_entry)
    
    # Use the repo's artifacts directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    artifacts_dir = os.path.join(repo_root, "artifacts")
    output_file = os.path.join(artifacts_dir, "dummy_logs.json")
    
    # Ensure directory exists
    if not os.path.exists(artifacts_dir):
        try:
            os.makedirs(artifacts_dir)
            print(f"Created directory: {artifacts_dir}")
        except Exception as e:
            print(f"Error creating directory {artifacts_dir}: {e}")
            output_file = "dummy_logs.json"

    with open(output_file, 'w') as f:
        json.dump(logs, f, indent=2)

    print(f"Successfully generated {num_logs} logs at: {output_file}")

if __name__ == "__main__":
    # You can change the number of logs to generate here
    generate_logs(num_logs=50)  # Generate 50 logs by default
