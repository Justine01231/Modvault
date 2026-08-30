from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Post, Release


def add_post(
    session: Session,
    release: Release | None,
    chat_id: str,
    message_id: int,
    post_type: str = "official",
    *,
    original_author: str | None = None,
    source: str | None = None,
    original_channel: str | None = None,
    notes: str | None = None,
) -> Post:
    post = Post(
        release_id=release.id if release else None,
        telegram_chat_id=str(chat_id),
        telegram_message_id=message_id,
        post_type=post_type,
        original_author=original_author,
        source=source,
        original_channel=original_channel,
        notes=notes,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


def count_posts(session: Session, post_type: str | None = None) -> int:
    stmt = select(Post)
    if post_type:
        stmt = stmt.where(Post.post_type == post_type)
    return len(session.scalars(stmt).all())
