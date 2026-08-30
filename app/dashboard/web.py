from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from app.dashboard.serializers import module_to_dict
from app.database.database import get_session
from app.database.repositories.modules import (
    count_modules,
    count_releases,
    get_module,
    list_modules,
    search_modules,
    top_categories,
)
from app.database.repositories.posts import count_posts
from app.services.formatter import format_file_size

router = APIRouter()


def _render(request: Request, name: str, context: dict, **kwargs):
    return request.app.state.templates.TemplateResponse(
        request, name, context, **kwargs
    )


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with get_session() as session:
        modules = list_modules(session, limit=12)
        stats = {
            "modules": count_modules(session),
            "releases": count_releases(session),
            "community": count_posts(session, "community"),
            "top": [{"category": c, "count": n} for c, n in top_categories(session, limit=3)],
        }
    return _render(
        request, "home.html",
        {"modules": [module_to_dict(m) for m in modules], "stats": stats}
    )


@router.get("/module/{module_id}", response_class=HTMLResponse)
async def module_detail(request: Request, module_id: int):
    with get_session() as session:
        module = get_module(session, module_id)
        if module is None:
            return _render(request, "not_found.html", {}, status_code=404)
        data = module_to_dict(module)
        # add file size formatting for display
        for release in data["releases"]:
            release["file_size_display"] = (
                format_file_size(release["file_size"]) if release["file_size"] else None
            )
    return _render(request, "module.html", {"module": data})


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = Query("")):
    results = []
    if q.strip():
        with get_session() as session:
            results = [module_to_dict(m) for m in search_modules(session, q, limit=50)]
    return _render(request, "search.html", {"q": q, "results": results})


@router.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request):
    from app.database.repositories.categories import list_categories

    with get_session() as session:
        cats = list_categories(session)
        counts = {}
        for module in list_modules(session, limit=1000):
            if module.category:
                counts[module.category] = counts.get(module.category, 0) + 1
    return _render(
        request, "categories.html",
        {"categories": [{"name": c.name, "slug": c.slug} for c in cats], "counts": counts}
    )
