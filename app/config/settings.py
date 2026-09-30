from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    channel_id: str
    admin_ids: frozenset[int] = field(default_factory=frozenset)
    log_level: str = "INFO"
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'modulab.db'}"
    github_token: str = ""
    webhook_secret: str = ""
    webhook_port: int = 8080
    auto_announce_repos: frozenset[str] = field(default_factory=frozenset)
    discussion_group_id: str = ""
    channel_username: str = ""
    discussion_username: str = ""
    dashboard_admin_token: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        admin_ids = frozenset(
            int(x.strip())
            for x in os.getenv("ADMIN_IDS", "").split(",")
            if x.strip().lstrip("-").isdigit()
        )
        auto_announce_repos = frozenset(
            p.strip().lower()
            for p in os.getenv("AUTO_ANNOUNCE_REPOS", "").split(",")
            if p.strip()
        )
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            channel_id=os.getenv("TELEGRAM_CHANNEL_ID", ""),
            admin_ids=admin_ids,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            database_url=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'modulab.db'}"),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            webhook_secret=os.getenv("WEBHOOK_SECRET", ""),
            webhook_port=int(os.getenv("WEBHOOK_PORT", "8080")),
            auto_announce_repos=auto_announce_repos,
            discussion_group_id=os.getenv("DISCUSSION_GROUP_ID", ""),
            channel_username=os.getenv("CHANNEL_USERNAME", ""),
            discussion_username=os.getenv("DISCUSSION_USERNAME", ""),
            dashboard_admin_token=os.getenv("DASHBOARD_ADMIN_TOKEN", ""),
        )


settings = Settings.from_env()
