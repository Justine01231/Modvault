from __future__ import annotations

import httpx
import pytest

from app.services.github_client import GitHubError, _parse_repo, fetch_release
from app.services.github_release import format_github_release


def test_parse_repo_owner_slash_repo():
    assert _parse_repo("owner/repo") == ("owner", "repo")


def test_parse_repo_full_url():
    assert _parse_repo("https://github.com/owner/repo") == ("owner", "repo")
    assert _parse_repo("github.com/owner/repo/") == ("owner", "repo")


def test_parse_repo_invalid():
    with pytest.raises(GitHubError):
        _parse_repo("owner")


def _mock_client(repo_json: dict, release_json: dict) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/releases/latest"):
            return httpx.Response(200, json=release_json)
        return httpx.Response(200, json=repo_json)

    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport, base_url="https://api.github.com")


@pytest.mark.asyncio
async def test_fetch_release_ok():
    client = _mock_client(
        repo_json={
            "html_url": "https://github.com/owner/repo",
            "name": "Repo",
            "description": "A nice module",
        },
        release_json={
            "tag_name": "v1.0",
            "name": "Release 1",
            "body": "Notes here",
            "published_at": "2024-01-01T00:00:00Z",
            "assets": [{"name": "repo-v1.zip", "size": 1024, "browser_download_url": "https://github.com/owner/repo/releases/download/v1.0/repo-v1.zip"}],
        },
    )
    release = await fetch_release("owner/repo", client=client)
    assert release.repo_full_name == "owner/repo"
    assert release.repo_name == "Repo"
    assert release.tag == "v1.0"
    assert release.owner == "owner"
    assert release.assets[0]["name"] == "repo-v1.zip"


@pytest.mark.asyncio
async def test_fetch_release_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.github.com"
    )
    with pytest.raises(GitHubError):
        await fetch_release("owner/repo", client=client)
    await client.aclose()


def test_format_github_release():
    from app.services.github_client import GitHubRelease

    release = GitHubRelease(
        repo_full_name="owner/repo",
        repo_url="https://github.com/owner/repo",
        owner="owner",
        repo_name="Repo",
        description="A nice module",
        tag="v1.0",
        body="Notes",
        assets=[{"name": "repo-v1.zip", "size": 1024, "url": "https://github.com/owner/repo/"}],
    )
    text = format_github_release(release)
    assert "GITHUB RELEASE" in text
    assert "Repo" in text
    assert "v1.0" in text
    assert "owner" in text
    assert "repo-v1.zip" in text
    assert "1.0 KB" in text
    assert "Source: https://github.com/owner/repo" in text
