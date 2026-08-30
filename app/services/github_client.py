from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

from app.config.settings import settings

GITHUB_API = "https://api.github.com"


class GitHubError(Exception):
    pass


@dataclass
class GitHubRelease:
    repo_full_name: str
    repo_url: str
    owner: str
    repo_name: str
    description: str = ""
    tag: str = ""
    release_name: str = ""
    body: str = ""
    published_at: datetime | None = None
    assets: list[dict] = field(default_factory=list)


def _parse_repo(path: str) -> tuple[str, str]:
    cleaned = path.strip().rstrip("/")
    if "github.com/" in cleaned:
        cleaned = cleaned.split("github.com/", 1)[1]
    parts = [p for p in cleaned.split("/") if p]
    if len(parts) < 2:
        raise GitHubError(
            "Please provide a repository like github.com/owner/repo or owner/repo."
        )
    return parts[0], parts[1]


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def _github_error(resp: httpx.Response) -> GitHubError:
    if resp.status_code == 404:
        return GitHubError("Repository or release not found.")
    if resp.status_code == 403:
        return GitHubError(
            "GitHub rate limit reached. Add a GITHUB_TOKEN in .env for a higher limit."
        )
    return GitHubError(f"GitHub request failed ({resp.status_code}).")


def release_from_payload(payload: dict) -> GitHubRelease:
    """Build a GitHubRelease straight from a webhook payload (no API call)."""
    repo = payload.get("repository", {})
    release = payload.get("release", {})
    owner = "unknown"
    repo_full = repo.get("full_name", "")
    if "/" in repo_full:
        owner, _ = repo_full.split("/", 1)

    published_at = None
    if release.get("published_at"):
        try:
            published_at = datetime.fromisoformat(
                release["published_at"].replace("Z", "+00:00")
            )
        except ValueError:
            published_at = None

    assets = [
        {
            "name": a.get("name", ""),
            "size": a.get("size", 0),
            "url": a.get("browser_download_url", ""),
        }
        for a in release.get("assets", [])
    ]

    return GitHubRelease(
        repo_full_name=repo_full or repo.get("name", ""),
        repo_url=repo.get("html_url") or repo_full,
        owner=owner,
        repo_name=repo.get("name", owner),
        description=repo.get("description") or "",
        tag=release.get("tag_name", ""),
        release_name=release.get("name") or release.get("tag_name", ""),
        body=(release.get("body") or "").strip(),
        published_at=published_at,
        assets=assets,
    )


async def fetch_release(
    repo: str, *, client: httpx.AsyncClient | None = None
) -> GitHubRelease:
    owner, repo_name = _parse_repo(repo)

    close = client is None
    client = client or httpx.AsyncClient(timeout=15)

    try:
        repo_resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo_name}", headers=_headers()
        )
        if repo_resp.is_error:
            raise _github_error(repo_resp)
        repo_json = repo_resp.json()

        release_resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo_name}/releases/latest",
            headers=_headers(),
        )
        release_json: dict[str, Any] = {}
        if not release_resp.is_error:
            release_json = release_resp.json()
    finally:
        if close:
            await client.aclose()

    published_at = None
    if release_json.get("published_at"):
        try:
            published_at = datetime.fromisoformat(release_json["published_at"].replace("Z", "+00:00"))
        except ValueError:
            published_at = None

    assets = [
        {
            "name": a.get("name", ""),
            "size": a.get("size", 0),
            "url": a.get("browser_download_url", ""),
        }
        for a in release_json.get("assets", [])
    ]

    return GitHubRelease(
        repo_full_name=f"{owner}/{repo_name}",
        repo_url=repo_json.get("html_url", f"https://github.com/{owner}/{repo_name}"),
        owner=owner,
        repo_name=repo_json.get("name", repo_name),
        description=repo_json.get("description") or "",
        tag=release_json.get("tag_name", ""),
        release_name=release_json.get("name") or release_json.get("tag_name", ""),
        body=(release_json.get("body") or "").strip(),
        published_at=published_at,
        assets=assets,
    )
