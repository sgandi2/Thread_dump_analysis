"""
Configuration example for GC Specialist Agent
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

# GC Analysis Thresholds
GC_THRESHOLDS = {
    "max_pause_time_seconds": 1.0,          # Alert if GC pause > 1 second
    "full_gc_per_minute": 1,                # Alert if Full GC > 1 per minute
    "old_gen_growth_rate_percent": 10,      # Alert if old gen grows > 10% per hour
    "heap_utilization_warning_percent": 85, # Warn if heap > 85% utilized
    "young_gc_frequency_seconds": 5,        # Expected Young GC frequency
}

# Analysis Configuration
ANALYSIS_CONFIG = {
    "enable_llm_analysis": True,
    "enable_rule_based_analysis": True,
    "detailed_logging": True,
    "save_analysis_results": True,
    "results_directory": "./analysis_results",
}

# Integration Points
INTEGRATION = {
    "send_to_remediation_agent": True,
    "send_to_dashboard": True,
    "send_slack_notifications": False,
    "slack_webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
}

# Logging Configuration
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "gc_specialist.log",
}

# Made with Bob
