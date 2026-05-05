"""
Configuration example for CPU Specialist Agent
Copy this file to config.py and update with your settings
"""

# OpenAI API Configuration
OPENAI_API_KEY = "your-openai-api-key-here"
OPENAI_MODEL = "gpt-4"
OPENAI_TEMPERATURE = 0.1

# webMethods Integration Server Configuration
WEBMETHODS_SERVER_URL = "http://localhost:5555"
WEBMETHODS_AUTH_TOKEN = "your-auth-token-here"
WEBMETHODS_USERNAME = "Administrator"
WEBMETHODS_PASSWORD = "manage"

# CPU Analysis Thresholds
CPU_THRESHOLDS = {
    "high_cpu_percent": 80.0,              # Alert if CPU > 80%
    "critical_cpu_percent": 95.0,          # Critical if CPU > 95%
    "high_runnable_ratio": 0.5,            # Alert if runnable threads > 50%
    "high_blocked_ratio": 0.1,             # Alert if blocked threads > 10%
    "cpu_per_core_warning": 90.0,          # Warn if any core > 90%
    "load_average_threshold": 8.0,         # Alert if load average > cores
}

# Analysis Configuration
ANALYSIS_CONFIG = {
    "enable_llm_analysis": True,
    "enable_rule_based_analysis": True,
    "detailed_logging": True,
    "save_analysis_results": True,
    "results_directory": "./analysis_results",
    "include_thread_correlation": True,
    "max_hotspots_to_report": 10,
}

# Integration Points
INTEGRATION = {
    "send_to_remediation_agent": True,
    "send_to_dashboard": True,
    "send_slack_notifications": False,
    "slack_webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
}

# Monitoring Configuration
MONITORING = {
    "collection_interval_seconds": 60,     # Collect metrics every 60 seconds
    "analysis_interval_seconds": 300,      # Run analysis every 5 minutes
    "retention_days": 7,                   # Keep data for 7 days
}

# Logging Configuration
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "cpu_specialist.log",
}

# Made with Bob
