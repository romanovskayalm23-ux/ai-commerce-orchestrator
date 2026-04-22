import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required.")
    return value


@dataclass(frozen=True)
class Settings:
    bot_token: str
    db_path: str
    log_level: str
    openai_api_key: str


settings = Settings(
    bot_token=_required_env("BOT_TOKEN"),
    db_path=os.getenv(
        "DB_PATH",
        str(BASE_DIR / "commerce_orchestrator.db"),
    ).strip(),
    log_level=os.getenv("LOG_LEVEL", "info").strip().lower(),
    openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
)
