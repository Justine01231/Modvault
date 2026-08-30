from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.models import Author, Module, Release


def count_modules(session: Session) -> int:
    return len(session.scalars(select(Module.id)).all())


def count_releases(session: Session) -> int:
    return len(session.scalars(select(Release.id)).all())


def list_modules(session: Session, limit: int = 20, offset: int = 0) -> list[Module]:
    return list(
        session.scalars(
            select(Module)
            .options(selectinload(Module.author), selectinload(Module.releases))
            .order_by(Module.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )


def get_module(session: Session, module_id: int) -> Module | None:
    return session.scalar(
        select(Module)
        .options(selectinload(Module.author), selectinload(Module.releases))
        .where(Module.id == module_id)
    )


def search_modules(session: Session, query: str, limit: int = 20) -> list[Module]:
    term = f"%{query.strip()}%"
    return list(
        session.scalars(
            select(Module)
            .outerjoin(Author, Module.author_id == Author.id)
            .options(selectinload(Module.author), selectinload(Module.releases))
            .where(
                or_(
                    Module.name.ilike(term),
                    Module.description.ilike(term),
                    Module.category.ilike(term),
                    Author.name.ilike(term),
                )
            )
            .order_by(Module.created_at.desc())
            .limit(limit)
        )
    )


def latest_releases(session: Session, limit: int = 10) -> list[Release]:
    return list(
        session.scalars(
            select(Release)
            .options(selectinload(Release.module).selectinload(Module.author))
            .order_by(Release.created_at.desc())
            .limit(limit)
        )
    )


def top_categories(session: Session, limit: int = 3) -> list[tuple[str, int]]:
    rows = session.execute(
        select(Module.category, func.count(Module.id))
        .where(Module.category.isnot(None))
        .group_by(Module.category)
        .order_by(func.count(Module.id).desc())
        .limit(limit)
    ).all()
    return [(category, count) for category, count in rows]
