from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Author, Module, Release
from app.database.repositories.authors import get_or_create_author
from app.services.module_parser import ModuleMetadata


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "module"


def get_or_create_module(
    session: Session,
    name: str,
    author: Author | None,
    description: str | None = None,
    category: str | None = None,
    repository_url: str | None = None,
) -> Module:
    module = session.scalar(select(Module).where(Module.name == name))
    if module is None:
        module = Module(
            name=name,
            slug=_slugify(name),
            description=description,
            category=category,
            repository_url=repository_url,
            author_id=author.id if author else None,
        )
        session.add(module)
        session.commit()
        session.refresh(module)
    else:
        changed = False
        if description is not None and module.description != description:
            module.description = description
            changed = True
        if category is not None and module.category != category:
            module.category = category
            changed = True
        if author is not None and module.author_id != author.id:
            module.author_id = author.id
            changed = True
        if repository_url is not None and module.repository_url != repository_url:
            module.repository_url = repository_url
            changed = True
        if changed:
            session.commit()
            session.refresh(module)
    return module


def add_release(
    session: Session,
    metadata: ModuleMetadata,
    *,
    file_name: str | None = None,
    file_size: int | None = None,
    file_hash: str | None = None,
    telegram_file_id: str | None = None,
    repository_url: str | None = None,
) -> Release:
    author = None
    if metadata.author:
        author = get_or_create_author(session, metadata.author)

    module = get_or_create_module(
        session,
        metadata.name,
        author=author,
        description=metadata.description or None,
        category=metadata.category or None,
        repository_url=repository_url,
    )

    existing = session.scalar(
        select(Release).where(Release.module_id == module.id, Release.version == metadata.version)
    )
    if existing is not None:
        return existing

    release = Release(
        module_id=module.id,
        version=metadata.version,
        version_code=metadata.version_code or None,
        file_name=file_name,
        file_size=file_size,
        file_hash=file_hash,
        telegram_file_id=telegram_file_id,
    )
    session.add(release)
    session.commit()
    session.refresh(release)
    return release


def release_has_version(session: Session, module_id: int, version: str) -> bool:
    return (
        session.scalar(
            select(Release.id).where(
                Release.module_id == module_id, Release.version == version
            )
        )
        is not None
    )
