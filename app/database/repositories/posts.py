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


def delete_post(session: Session, post_id: int) -> bool:
    post = session.get(Post, post_id)
    if post is None:
        return False
    session.delete(post)
    session.commit()
    return True


def get_post_by_message(
    session: Session, chat_id: str | int, message_id: int
) -> Post | None:
    """Fetch a post along with its linked release/module by Telegram chat+message."""
    stmt = (
        select(Post)
        .where(
            Post.telegram_chat_id == str(chat_id),
            Post.telegram_message_id == message_id,
        )
        .limit(1)
    )
    post = session.scalars(stmt).first()
    if post is not None:
        # eager-load relationships for convenient access
        if post.release is not None:
            _ = post.release.module
    return post
