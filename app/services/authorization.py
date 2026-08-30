from __future__ import annotations

from app.config.settings import settings


def is_admin(telegram_id: int | None) -> bool:
    if telegram_id is None:
        return False
    return telegram_id in settings.admin_ids


def require_admin(telegram_id: int | None) -> bool:
    return is_admin(telegram_id)
