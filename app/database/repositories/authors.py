from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Author


def get_or_create_author(
    session: Session, name: str, telegram_username: str | None = None
) -> Author:
    author = session.scalar(
        select(Author).where(Author.telegram_username == telegram_username)
    ) if telegram_username else None

    if author is None:
        author = session.scalar(
            select(Author).where(Author.name == name)
        )

    if author is None:
        author = Author(name=name, telegram_username=telegram_username)
        session.add(author)
        session.commit()
        session.refresh(author)
    return author
