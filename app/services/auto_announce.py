from __future__ import annotations

import httpx

from app.config.settings import settings
from app.database.database import get_session
from app.database.repositories.posts import add_post
from app.database.repositories.releases import add_release
from app.services.github_client import GitHubRelease
from app.services.footer import append_footer
from app.services.module_parser import ModuleMetadata

TELEGRAM_API = f"https://api.telegram.org/bot{settings.bot_token}"


class WebhookPublishError(Exception):
    pass


async def send_channel_message(text: str, parse_mode: str = "HTML") -> tuple[int | None, str]:
    if not settings.bot_token:
        return None, "BOT_TOKEN not configured."
    payload = {"chat_id": settings.channel_id, "text": text, "parse_mode": parse_mode}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
    data = resp.json()
    if resp.is_error or not data.get("ok"):
        return None, f"Telegram send failed: {data.get('description', resp.status_code)}"
    return data["result"]["message_id"], ""


def _to_metadata(release: GitHubRelease) -> ModuleMetadata:
    return ModuleMetadata(
        name=release.repo_name,
        version=release.tag or release.release_name or "latest",
        author=release.owner,
        description=release.description or (release.body or "")[:300],
    )


async def announce_release(release: GitHubRelease) -> tuple[bool, str]:
    from app.services.github_release import format_github_release

    text = append_footer(format_github_release(release))
    message_id, error = await send_channel_message(text)
    if message_id is None:
        return False, error

    asset = release.assets[0] if release.assets else None
    metadata = _to_metadata(release)
    with get_session() as session:
        add_release(
            session,
            metadata,
            file_name=asset["name"] if asset and asset["name"] else None,
            file_size=asset["size"] if asset and asset["size"] else None,
            repository_url=release.repo_url,
        )
        add_post(
            session,
            None,
            chat_id=settings.channel_id,
            message_id=message_id,
            post_type="official",
        )
    return True, f"Announced {release.repo_full_name} {release.tag or ''} — {message_id}"
