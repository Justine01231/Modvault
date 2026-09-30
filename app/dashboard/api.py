from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.config.settings import settings
from app.dashboard.serializers import module_to_dict
from app.database.database import get_session
from app.database.repositories.modules import (
    count_modules,
    count_releases,
    delete_module,
    get_module,
    list_modules,
    latest_releases,
    search_modules,
    top_categories,
)
from app.database.repositories.posts import count_posts, delete_post
from app.database.repositories.categories import list_categories

router = APIRouter(prefix="/api")


def require_admin(x_admin_token: str | None = None) -> None:
    """Refuse mutating requests when DASHBOARD_ADMIN_TOKEN is set and mismatched."""
    if settings.dashboard_admin_token and x_admin_token != settings.dashboard_admin_token:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/modules")
async def modules(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    with get_session() as session:
        items = list_modules(session, limit=limit, offset=offset)
        total = count_modules(session)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "modules": [module_to_dict(m) for m in items],
    }


@router.get("/modules/{module_id}")
async def module_detail(module_id: int):
    with get_session() as session:
        module = get_module(session, module_id)
        if module is None:
            raise HTTPException(status_code=404, detail="Module not found")
        return module_to_dict(module)


@router.delete("/modules/{module_id}")
async def delete_module_endpoint(module_id: int, x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    with get_session() as session:
        if not delete_module(session, module_id):
            raise HTTPException(status_code=404, detail="Module not found")
    return {"status": "deleted", "module_id": module_id}


@router.delete("/posts/{post_id}")
async def delete_post_endpoint(post_id: int, x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    with get_session() as session:
        if not delete_post(session, post_id):
            raise HTTPException(status_code=404, detail="Post not found")
    return {"status": "deleted", "post_id": post_id}


@router.get("/search")
async def search(q: str = Query("", min_length=1)):
    with get_session() as session:
        items = search_modules(session, q, limit=50)
    return {"query": q, "total": len(items), "modules": [module_to_dict(m) for m in items]}


@router.get("/categories")
async def categories():
    with get_session() as session:
        cats = list_categories(session)
    return {"categories": [{"id": c.id, "name": c.name, "slug": c.slug} for c in cats]}


@router.get("/stats")
async def stats():
    with get_session() as session:
        modules = count_modules(session)
        releases = count_releases(session)
        community = count_posts(session, "community")
        top = [{"category": c, "count": n} for c, n in top_categories(session, limit=5)]
        latest = latest_releases(session, limit=1)
        latest_meta = None
        if latest:
            rel = latest[0]
            latest_meta = {
                "module": rel.module.name if rel.module else None,
                "version": rel.version,
            }
    return {
        "modules": modules,
        "releases": releases,
        "community_posts": community,
        "top_categories": top,
        "latest_release": latest_meta,
    }
