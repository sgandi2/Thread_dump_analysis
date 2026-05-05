"""Configuration management for Thread Dump Analysis AI Agent."""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()


class Config:
    """Central configuration class for all agents."""
    
    # webMethods Integration Server
    WEBMETHODS_URL: str = os.getenv("WEBMETHODS_URL", "http://localhost:5555")
    WEBMETHODS_USER: str = os.getenv("WEBMETHODS_USER", "Administrator")
    WEBMETHODS_PASSWORD: str = os.getenv("WEBMETHODS_PASSWORD", "manage")
    
    # Slack Configuration
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#alerts")
    SLACK_BOT_TOKEN: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
    
    # Ollama Configuration (for AI recommendations)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Thresholds
    HUNG_THREAD_THRESHOLD: int = int(os.getenv("HUNG_THREAD_THRESHOLD", "300"))  # seconds
    CPU_THRESHOLD: int = int(os.getenv("CPU_THRESHOLD", "80"))  # percentage
    MEMORY_THRESHOLD: int = int(os.getenv("MEMORY_THRESHOLD", "85"))  # percentage
    DEADLOCK_CHECK_ENABLED: bool = os.getenv("DEADLOCK_CHECK_ENABLED", "true").lower() == "true"
    
    # Monitoring Configuration
    POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "30"))  # seconds
    ALERT_COOLDOWN: int = int(os.getenv("ALERT_COOLDOWN", "300"))  # seconds (5 min)
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # MCP Server
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8080"))
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "localhost")
    
    # Data Storage
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    THREAD_DUMPS_DIR: str = os.path.join(DATA_DIR, "thread_dumps")
    ANALYSIS_RESULTS_DIR: str = os.path.join(DATA_DIR, "analysis_results")
    ALERTS_DIR: str = os.path.join(DATA_DIR, "alerts")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration values."""
        if not cls.SLACK_WEBHOOK_URL and not cls.SLACK_BOT_TOKEN:
            print("Warning: No Slack configuration found. Notifications will be disabled.")
            return False
        return True
    
    @classmethod
    def get_webmethods_auth(cls) -> tuple:
        """Get webMethods authentication credentials."""
        return (cls.WEBMETHODS_USER, cls.WEBMETHODS_PASSWORD)


# Create singleton instance
config = Config()

# Made with Bob
