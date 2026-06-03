import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("BASE_URL", "https://team.addo.ai").rstrip("/")
    test_user_email: str = os.getenv("TEST_USER_EMAIL", "").strip()
    test_user_password: str = os.getenv("TEST_USER_PASSWORD", "").strip()
    browser: str = os.getenv("BROWSER", "chromium")
    headless: bool = os.getenv("HEADLESS", "false").lower() in ("1", "true", "yes")
    default_timeout: int = int(os.getenv("DEFAULT_TIMEOUT", "30000"))
    screenshot_dir: Path = _PROJECT_ROOT / "screenshots"

    @property
    def has_credentials(self) -> bool:
        return bool(self.test_user_email and self.test_user_password)


settings = Settings()
