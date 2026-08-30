from __future__ import annotations

from app.database.models import Author, Module, Release


def release_to_dict(release: Release) -> dict:
    return {
        "id": release.id,
        "version": release.version,
        "version_code": release.version_code,
        "file_name": release.file_name,
        "file_size": release.file_size,
        "file_hash": release.file_hash,
        "created_at": release.created_at.isoformat() if release.created_at else None,
    }


def author_to_dict(author: Author | None) -> dict | None:
    if author is None:
        return None
    return {
        "id": author.id,
        "name": author.name,
        "telegram_username": author.telegram_username,
        "github_username": author.github_username,
        "telegram_url": author.telegram_url,
        "github_url": author.github_url,
    }


def module_to_dict(module: Module, *, include_releases: bool = True) -> dict:
    data = {
        "id": module.id,
        "name": module.name,
        "slug": module.slug,
        "description": module.description,
        "category": module.category,
        "repository_url": module.repository_url,
        "author": author_to_dict(module.author),
        "created_at": module.created_at.isoformat() if module.created_at else None,
        "updated_at": module.updated_at.isoformat() if module.updated_at else None,
    }
    if include_releases:
        data["releases"] = [
            release_to_dict(r) for r in module.releases
        ]
    return data
