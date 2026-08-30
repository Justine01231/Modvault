from __future__ import annotations

import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from app.services.github_client import release_from_payload
from app import webhook


def _sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_verify_signature_ok():
    body = b'{"hello":"world"}'
    sig = _sign("s3cret", body)
    assert webhook.verify_signature("s3cret", body, sig) is True


def test_verify_signature_bad_body():
    sig = _sign("s3cret", b"something")
    assert webhook.verify_signature("s3cret", b"else", sig) is False


def test_verify_signature_no_secret():
    assert webhook.verify_signature("", b"x", _sign("x", b"x")) is False


def test_verify_signature_bad_header():
    assert webhook.verify_signature("s", b"x", "notsha") is False


def _payload():
    return {
        "action": "published",
        "repository": {
            "full_name": "owner/repo",
            "name": "Repo",
            "html_url": "https://github.com/owner/repo",
            "description": "A module",
        },
        "release": {
            "tag_name": "v1.0",
            "name": "v1.0",
            "body": "Notes",
            "published_at": "2024-01-01T00:00:00Z",
            "assets": [
                {
                    "name": "repo-v1.0.zip",
                    "size": 2048,
                    "browser_download_url": "https://github.com/owner/repo/releases/download/v1.0/repo-v1.0.zip",
                }
            ],
        },
    }


def test_release_from_payload():
    release = release_from_payload(_payload())
    assert release.repo_full_name == "owner/repo"
    assert release.owner == "owner"
    assert release.repo_name == "Repo"
    assert release.tag == "v1.0"
    assert release.assets[0]["name"] == "repo-v1.0.zip"


@pytest.fixture()
def client(monkeypatch):
    async def fake_announce(release):
        return True, "ok"

    monkeypatch.setattr(webhook, "announce_release", fake_announce)
    monkeypatch.setattr(webhook, "verify_signature", lambda *a, **k: True)
    return TestClient(webhook.app)


def test_webhook_valid_request(client):
    resp = client.post(
        "/webhook/github",
        json=_payload(),
        headers={"X-GitHub-Event": "release", "X-Hub-Signature-256": "sha256=x"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_webhook_non_release_event(client):
    resp = client.post(
        "/webhook/github",
        json={},
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": "sha256=x"},
    )
    assert resp.status_code == 200
    assert resp.json()["skipped"] is True


def test_webhook_bad_signature(client, monkeypatch):
    monkeypatch.setattr(webhook, "verify_signature", lambda *a, **k: False)
    resp = client.post(
        "/webhook/github",
        json=_payload(),
        headers={"X-GitHub-Event": "release", "X-Hub-Signature-256": "sha256=bad"},
    )
    assert resp.status_code == 401
