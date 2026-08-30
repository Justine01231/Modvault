from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.dashboard.app import create_app
from app.database import database
from app.database.repositories.categories import seed_categories
from app.database.repositories.releases import add_release
from app.services.module_parser import ModuleMetadata


@pytest.fixture()
def client(tmp_path):
    database.init_engine(f"sqlite:///{tmp_path / 'dash.db'}")
    database.create_tables()
    with database.get_session() as session:
        seed_categories(session)
        add_release(
            session,
            ModuleMetadata(
                name="OnyxZygisk",
                version="1.07",
                author="OnyxDev",
                description="A Zygisk implementation",
                category="Zygisk",
            ),
            file_name="onyx.zip",
            file_size=1024,
        )
        add_release(
            session,
            ModuleMetadata(
                name="Magisk Module",
                version="v2",
                author="Dev",
                category="Magisk",
            ),
        )
    app = create_app(init=False)
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_list_modules(client):
    data = client.get("/api/modules").json()
    assert data["total"] == 2
    names = {m["name"] for m in data["modules"]}
    assert names == {"OnyxZygisk", "Magisk Module"}


def test_module_detail(client):
    data = client.get("/api/modules/1").json()
    assert data["name"] == "OnyxZygisk"
    assert data["author"]["name"] == "OnyxDev"
    assert data["releases"][0]["file_name"] == "onyx.zip"


def test_module_detail_missing(client):
    assert client.get("/api/modules/999").status_code == 404


def test_search(client):
    data = client.get("/api/search", params={"q": "zygisk"}).json()
    assert data["total"] == 1
    assert data["modules"][0]["name"] == "OnyxZygisk"


def test_categories(client):
    data = client.get("/api/categories").json()
    assert len(data["categories"]) == 9


def test_stats(client):
    data = client.get("/api/stats").json()
    assert data["modules"] == 2
    assert data["releases"] == 2


def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "OnyxZygisk" in resp.text


def test_module_page(client):
    resp = client.get("/module/1")
    assert resp.status_code == 200
    assert "OnyxZygisk" in resp.text
    assert "onyx.zip" in resp.text


def test_search_page(client):
    resp = client.get("/search", params={"q": "magisk"})
    assert resp.status_code == 200
    assert "Magisk Module" in resp.text


def test_categories_page(client):
    resp = client.get("/categories")
    assert resp.status_code == 200
    assert "Zygisk" in resp.text
