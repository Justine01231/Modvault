from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    engine = create_engine(url, future=True)
    if url.startswith("sqlite"):
        event.listen(
            engine,
            "connect",
            lambda dbapi_conn, _: dbapi_conn.execute("PRAGMA foreign_keys=ON"),
        )
    return engine


def init_engine(url: str | None = None) -> None:
    global engine, SessionLocal
    resolved = url or settings.database_url
    if resolved.startswith("sqlite:///"):
        path = resolved.replace("sqlite:///", "")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    engine = _make_engine(resolved)
    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def create_tables(engine_override=None) -> None:
    import app.database.models  # noqa: F401  (register models on Base.metadata)
    target = engine_override or engine
    Base.metadata.create_all(target)


engine = None
SessionLocal = None


def get_session() -> Session:
    if SessionLocal is None:
        init_engine()
    return SessionLocal()


def init_db() -> None:
    init_engine()
    create_tables()
    from app.database.repositories.categories import seed_categories
    with get_session() as session:
        seed_categories(session)
