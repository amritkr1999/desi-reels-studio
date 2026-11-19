"""Centralized strongly-typed configuration for DesiReels Studio."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Base Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MEMORY_DIR = PROJECT_ROOT / "memory"
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
REFERENCE_VIDEOS_DIR = PROJECT_ROOT / "reference_videos"
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMP_DIR = PROJECT_ROOT / "temp"
OUTPUT_DIR = PROJECT_ROOT / "output"
DOCS_DIR = PROJECT_ROOT / "docs"

# Load .env file manually if python-dotenv is not yet installed in sandbox
def _load_env_file() -> None:
    env_path = PROJECT_ROOT / ".env"
    if env_path.is_file():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass

_load_env_file()


class Config:
    """System runtime settings with sensible, safe defaults."""

    # 1. Pipeline Execution & Safety
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")
    DATABASE_PATH: Path = PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/studio.db")

    # 2. Local AI & Scripting (Ollama)
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    OLLAMA_VISION_MODEL: str = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")
    OLLAMA_TIMEOUT_SECONDS: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))

    # 3. Audio & Subtitle Engine
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "auto")
    MACOS_SAY_VOICE: str = os.getenv("MACOS_SAY_VOICE", "Rishi")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base.en")
    TARGET_WPM: int = int(os.getenv("TARGET_WPM", "160"))

    # 4. Visual Media & B-Roll
    PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")

    # 5. YouTube Shorts Publishing
    YOUTUBE_CLIENT_SECRETS_FILE: Path = PROJECT_ROOT / os.getenv(
        "YOUTUBE_CLIENT_SECRETS_FILE", "credentials/youtube_client_secret.json"
    )
    YOUTUBE_TOKEN_FILE: Path = PROJECT_ROOT / os.getenv(
        "YOUTUBE_TOKEN_FILE", "credentials/youtube_token.json"
    )
    YOUTUBE_PRIVACY_STATUS: str = os.getenv("YOUTUBE_PRIVACY_STATUS", "private")

    # 6. Instagram Reels Publishing
    INSTAGRAM_ACCOUNT_ID: str = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

    # 7. Facebook Reels Publishing
    FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")
    FACEBOOK_PAGE_ACCESS_TOKEN: str = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")

    # 8. Local Dashboard Configuration
    DASHBOARD_HOST: str = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "8500"))

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required runtime directories exist."""
        for d in [
            DATA_DIR,
            MEMORY_DIR,
            CREDENTIALS_DIR,
            REFERENCE_VIDEOS_DIR,
            ASSETS_DIR,
            ASSETS_DIR / "audio",
            ASSETS_DIR / "fonts",
            ASSETS_DIR / "visuals",
            TEMP_DIR,
            OUTPUT_DIR,
            DOCS_DIR,
        ]:
            d.mkdir(parents=True, exist_ok=True)


config = Config()
config.ensure_directories()
