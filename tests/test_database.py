from __future__ import annotations

import pytest

from app.database import database
from app.database.models import Category, Module, Post, Release, User
from app.database.repositories.authors import get_or_create_author
from app.database.repositories.categories import get_category_by_slug, seed_categories
from app.database.repositories.modules import (
    count_modules,
    count_releases,
    list_modules,
    search_modules,
    top_categories,
)
from app.database.repositories.posts import add_post, count_posts
from app.database.repositories.releases import (
    add_release,
    get_or_create_module,
    release_has_version,
)
from app.database.repositories.users import upsert_user
from app.services.module_parser import ModuleMetadata


@pytest.fixture()
def session(tmp_path):
    db_path = tmp_path / "test.db"
    database.init_engine(f"sqlite:///{db_path}")
    database.create_tables()
    with database.get_session() as s:
        yield s
    database.init_engine(f"sqlite:///{tmp_path / 'cleanup.db'}")
    database.create_tables()


def test_seed_categories(session):
    created = seed_categories(session)
    assert created == 9
    assert seed_categories(session) == 0
    assert get_category_by_slug(session, "magisk").name == "Magisk"


def test_upsert_user(session):
    user = upsert_user(session, 123, "@justine", "Justine")
    assert user.telegram_id == 123
    again = upsert_user(session, 123, "@justine", "Justine Updated")
    assert again.display_name == "Justine Updated"
    assert session.query(User).count() == 1


def test_add_release_creates_module_and_author(session):
    meta = ModuleMetadata(
        name="OnyxZygisk",
        version="1.07",
        version_code="107",
        author="OnyxDev",
        description="Zygisk impl",
        category="Zygisk",
    )
    release = add_release(session, meta, file_name="onyx.zip", file_size=100, file_hash="abc")
    assert release.module.name == "OnyxZygisk"
    assert release.module.author.name == "OnyxDev"
    assert count_modules(session) == 1
    assert count_releases(session) == 1


def test_duplicate_version_does_not_duplicate(session):
    meta = ModuleMetadata(name="X", version="v1.0", author="A")
    add_release(session, meta)
    add_release(session, meta)
    assert count_releases(session) == 1
    assert count_modules(session) == 1


def test_release_has_version(session):
    module = get_or_create_module(session, "M", author=None)
    assert not release_has_version(session, module.id, "v1.0")
    meta = ModuleMetadata(name="M", version="v1.0", author="A")
    add_release(session, meta)
    assert release_has_version(session, module.id, "v1.0")


def test_add_post(session):
    meta = ModuleMetadata(name="M", version="v1.0")
    release = add_release(session, meta)
    add_post(session, release, chat_id="-100", message_id=42, post_type="official")
    assert count_posts(session, "official") == 1
    assert session.query(Post).count() == 1


def test_community_post_stores_attribution(session):
    add_post(
        session,
        None,
        chat_id="-100",
        message_id=7,
        post_type="community",
        original_author="@Dev",
        source="github.com/Dev/Repo",
        original_channel="@DevChannel",
        notes="mirror",
    )
    post = session.query(Post).first()
    assert post.post_type == "community"
    assert post.release_id is None
    assert post.original_author == "@Dev"
    assert post.source == "github.com/Dev/Repo"
    assert post.original_channel == "@DevChannel"
    assert post.notes == "mirror"
    assert count_posts(session, "community") == 1
    assert count_posts(session, "official") == 0


def test_top_categories(session):
    seed_categories(session)
    for name, cat in (("A", "Magisk"), ("B", "Magisk"), ("C", "KernelSU")):
        add_release(session, ModuleMetadata(name=name, version="v1", category=cat))
    top = top_categories(session)
    assert top[0] == ("Magisk", 2)


def test_list_modules_orders_newest_first(session):
    add_release(session, ModuleMetadata(name="First", version="v1"))
    add_release(session, ModuleMetadata(name="Second", version="v1"))
    modules = list_modules(session, limit=10)
    assert [m.name for m in modules] == ["Second", "First"]


def test_search_by_name(session):
    add_release(session, ModuleMetadata(name="OnyxZygisk", version="v1", author="OnyxDev"))
    add_release(session, ModuleMetadata(name="Other Tool", version="v1"))
    assert len(search_modules(session, "onyx")) == 1
    assert search_modules(session, "onyx")[0].name == "OnyxZygisk"


def test_search_by_author(session):
    add_release(session, ModuleMetadata(name="Tool", version="v1", author="Justine"))
    assert len(search_modules(session, "justine")) == 1


def test_search_by_description(session):
    add_release(
        session,
        ModuleMetadata(name="Tool", version="v1", description="A Zygisk implementation"),
    )
    assert len(search_modules(session, "zygisk implementation")) == 1


def test_search_empty_query_returns_nothing(session):
    add_release(session, ModuleMetadata(name="Tool", version="v1"))
    assert search_modules(session, "zzzz") == []
