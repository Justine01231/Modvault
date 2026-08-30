from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.dashboard import api, web
from app.database.database import init_db

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))


def create_app(*, init: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if init:
            init_db()
        yield

    app = FastAPI(title="ModuLab Dashboard", lifespan=lifespan)

    app.state.templates = templates
    app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
    app.include_router(api.router)
    app.include_router(web.router)
    return app


app = create_app()
