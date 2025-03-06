import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    # API Keys
    TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY")
    if not TWOCAPTCHA_API_KEY:
        raise ValueError("TWOCAPTCHA_API_KEY environment variable is required")

    # Application Settings
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30000"))

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = Path(os.getenv("LOG_FILE", BASE_DIR / "logs" / "application.log"))
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Browser Settings
    BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")
    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    # File Paths
    RESUME_DIR = BASE_DIR / "data" / "resumes"
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    USER_METADATA_PATH = BASE_DIR / "data" / "user_metadata.json"

    @classmethod
    def validate(cls):
        """Validate all settings are properly configured."""
        if not cls.TWOCAPTCHA_API_KEY:
            raise ValueError("2Captcha API key is required")
        if not cls.USER_METADATA_PATH.exists():
            raise FileNotFoundError(
                f"User metadata file not found at {cls.USER_METADATA_PATH}"
            )


# Create settings instance
settings = Settings()
