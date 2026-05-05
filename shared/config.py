"""
Configuration management for thread dump analysis system
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the application"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        # webMethods Integration Server settings
        self.WEBMETHODS_URL = os.getenv("WEBMETHODS_URL", "http://localhost:5555")
        self.WEBMETHODS_USER = os.getenv("WEBMETHODS_USER", "Administrator")
        self.WEBMETHODS_PASSWORD = os.getenv("WEBMETHODS_PASSWORD", "manage")
        
        # Slack settings
        self.SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
        self.SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#alerts")
        
        # Monitoring settings
        self.MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "60"))  # seconds
        self.HUNG_THREAD_THRESHOLD = int(os.getenv("HUNG_THREAD_THRESHOLD", "300"))  # seconds
        self.CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", "80.0"))  # percentage
        self.MEMORY_THRESHOLD = float(os.getenv("MEMORY_THRESHOLD", "85.0"))  # percentage
        self.POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))  # seconds
        self.DEADLOCK_CHECK_ENABLED = os.getenv("DEADLOCK_CHECK_ENABLED", "true").lower() == "true"
        self.ALERT_COOLDOWN = int(os.getenv("ALERT_COOLDOWN", "300"))  # seconds
        
        
        # AI/LLM settings
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, ollama
        
        # Storage settings
        self.DATA_DIR = os.getenv("DATA_DIR", "data")
        self.THREAD_DUMPS_DIR = os.path.join(self.DATA_DIR, "thread_dumps")
        self.ANALYSIS_RESULTS_DIR = os.path.join(self.DATA_DIR, "analysis_results")
        self.ALERTS_DIR = os.path.join(self.DATA_DIR, "alerts")
        
        # Logging settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_DIR = os.getenv("LOG_DIR", "logs")
        
        # Create directories if they don't exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.DATA_DIR,
            self.THREAD_DUMPS_DIR,
            self.ANALYSIS_RESULTS_DIR,
            self.ALERTS_DIR,
            self.LOG_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required settings
        if not self.WEBMETHODS_URL:
            errors.append("WEBMETHODS_URL is required")
        
        if not self.WEBMETHODS_USER:
            errors.append("WEBMETHODS_USER is required")
        
        if not self.WEBMETHODS_PASSWORD:
            errors.append("WEBMETHODS_PASSWORD is required")
        
        # Check LLM settings based on provider
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when using OpenAI provider")
        
        if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")
        
        # Check thresholds
        if self.HUNG_THREAD_THRESHOLD <= 0:
            errors.append("HUNG_THREAD_THRESHOLD must be positive")
        
        if not (0 <= self.CPU_THRESHOLD <= 100):
            errors.append("CPU_THRESHOLD must be between 0 and 100")
        
        if not (0 <= self.MEMORY_THRESHOLD <= 100):
            errors.append("MEMORY_THRESHOLD must be between 0 and 100")
        
        return len(errors) == 0, errors
    
    def get_webmethods_auth(self) -> tuple[str, str]:
        """Get webMethods authentication credentials"""
        return (self.WEBMETHODS_USER, self.WEBMETHODS_PASSWORD)
    
    def __repr__(self) -> str:
        """String representation (hiding sensitive data)"""
        return (
            f"Config("
            f"WEBMETHODS_URL={self.WEBMETHODS_URL}, "
            f"WEBMETHODS_USER={self.WEBMETHODS_USER}, "
            f"MONITOR_INTERVAL={self.MONITOR_INTERVAL}, "
            f"LLM_PROVIDER={self.LLM_PROVIDER})"
        )


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance"""
    return config


def reload_config():
    """Reload configuration from environment"""
    global config
    load_dotenv(override=True)
    config = Config()
    return config

# Made with Bob
