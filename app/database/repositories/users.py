from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User


def upsert_user(session: Session, telegram_id: int, username: str | None, display_name: str | None) -> User:
    user = session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, username=username, display_name=display_name)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    changed = False
    if username is not None and user.username != username:
        user.username = username
        changed = True
    if display_name is not None and user.display_name != display_name:
        user.display_name = display_name
        changed = True
    if changed:
        session.commit()
        session.refresh(user)
    return user
