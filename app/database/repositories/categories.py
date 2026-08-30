from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Category


SEED_CATEGORIES = [
    ("Magisk", "magisk"),
    ("KernelSU", "kernelsu"),
    ("APatch", "apatch"),
    ("Zygisk", "zygisk"),
    ("LSPosed", "lsposed"),
    ("Android", "android"),
    ("Kernel", "kernel"),
    ("Utility", "utility"),
    ("Other", "other"),
]


def seed_categories(session: Session) -> int:
    created = 0
    existing = {c.slug for c in session.scalars(select(Category)).all()}
    for name, slug in SEED_CATEGORIES:
        if slug not in existing:
            session.add(Category(name=name, slug=slug))
            created += 1
    if created:
        session.commit()
    return created


def get_category_by_slug(session: Session, slug: str) -> Category | None:
    return session.scalar(select(Category).where(Category.slug == slug))


def list_categories(session: Session) -> list[Category]:
    return list(session.scalars(select(Category).order_by(Category.name)).all())
