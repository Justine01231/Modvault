from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

import httpx

from app.services.reposting import RepostData

TELEGRAM_EMBED_URL = "https://t.me/{channel}/{msg_id}?embed=1"

_LINK_RE = re.compile(
    r"t(?:elegram)?\.me/(?:s/)?(?P<channel>[A-Za-z0-9_]{3,32})/(?P<msg>\d+)(?:\?.*)?$"
)
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


class TelegramLinkError(Exception):
    pass


def parse_link(url: str) -> tuple[str, str]:
    """Extract (channel, message_id) from a t.me link."""
    cleaned = (url or "").strip()
    match = _LINK_RE.search(cleaned)
    if not match:
        raise TelegramLinkError(
            "Please provide a valid Telegram link like t.me/username/123."
        )
    channel = match.group("channel")
    if channel.lower().startswith(("share", "addlist", "proxy", "bg", "joinchat")):
        raise TelegramLinkError("That doesn't look like a public channel post link.")
    return channel, match.group("msg")


async def fetch_message_text(
    channel: str, msg_id: str, *, client: httpx.AsyncClient | None = None
) -> str:
    """Fetch and return the plain text of a single public t.me post."""
    close = client is None
    client = client or httpx.AsyncClient(timeout=20, headers=_HEADERS)
    try:
        resp = await client.get(
            TELEGRAM_EMBED_URL.format(channel=channel, msg_id=msg_id)
        )
    finally:
        if close:
            await client.aclose()
    if resp.is_error or "tgme_widget_message" not in resp.text:
        raise TelegramLinkError(
            f"Could not fetch the post (HTTP {resp.status_code}). Make sure it's a public channel."
        )

    match = re.search(
        r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
        resp.text,
        re.DOTALL,
    )
    if not match:
        raise TelegramLinkError("No text found in that post.")
    return _strip_html(match.group(1))


def _strip_html(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", fragment)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def _split_heading(line: str) -> tuple[str, str]:
    name = re.sub(r"^[^\w#+]\s*", "", line).strip()
    match = re.search(r"\s+(v?[\d]+(?:[.\-][\d]+)+)\s*$", name)
    if match:
        version = match.group(1).lstrip("v")
        name = name[: match.start()].strip()
    else:
        version = ""
    return name, version


def repost_from_text(text: str, channel: str, github_url: str = "") -> RepostData:
    """Best-effort extraction of community post fields from a t.me post's text."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    name, version = _split_heading(lines[0]) if lines else ("", "")
    if not name:
        name = lines[0] if lines else ""

    notes_parts: list[str] = []
    original_author = ""
    source = ""
    github_link = ""

    for line in lines[1:]:
        low = line.lower()
        if line.startswith("×") or line.startswith("by "):
            author = re.sub(r"^[×x]\s*", "", line).strip()
            author = re.sub(r"^by\s+", "", author, flags=re.I).strip()
            original_author = author or original_author
            continue
        if line.startswith(("⚉", "🌐", "🔗", "source", "github")):
            label = re.sub(r"^[^\s]+\s*", "", line).strip()
            source = github_url or (github_link or label)
            continue
        if low.startswith(("◉", "same post", "☬", "donations", "lean", "|")):
            continue
        notes_parts.append(line)

    if not source and github_url:
        source = github_url

    return RepostData(
        name=name,
        version=version,
        original_author=original_author,
        source=source,
        original_channel=f"@{channel}",
        notes="\n".join(notes_parts).strip()[:600],
    )


async def fetch_repost(url: str) -> RepostData:
    """Parse a t.me link, fetch its post, and return a pre-filled RepostData."""
    channel, msg_id = parse_link(url)
    text, github_url, _fragment = await _fetch_with_urls(channel, msg_id)
    return repost_from_text(text, channel, github_url)


async def fetch_reposts(url: str) -> list[RepostData]:
    """Fetch a t.me link and return an item per post.

    If the post is a list of "@handle | Github(url)" entries, returns one
    RepostData per entry. Otherwise returns a single RepostData for the post.
    """
    channel, msg_id = parse_link(url)
    source_post = f"https://t.me/{channel}/{msg_id}"
    text, github_url, fragment = await _fetch_with_urls(channel, msg_id)

    entries = parse_client_list(fragment)
    if len(entries) >= 2:
        return [RepostData(
            name=name,
            source=source_url,
            original_channel=original_channel,
            source_post=source_post,
        ) for name, source_url, original_channel in entries]

    repost = repost_from_text(text, channel, github_url)
    repost.source_post = source_post
    return [repost]


def parse_client_list(fragment: str) -> list[tuple[str, str, str]]:
    """Return (name, source_url, original_channel) for each list entry.

    Works on the HTML fragment (with anchors preserved). Matches lines like:
        <a href="https://t.me/handle">@handle</a> | <a href="https://github.com/...">Github</a>
    """
    entries: list[tuple[str, str, str]] = []
    for raw_line in fragment.split("<br"):
        if "github.com/" not in raw_line:
            continue
        github_match = re.search(r"href=\"(https?://github\.com/[\w.\-]+/[\w.\-]+)\"", raw_line)
        if not github_match:
            continue
        source_url = github_match.group(1)

        handle_match = re.search(r"href=\"https?://t\.me/([A-Za-z0-9_]{3,32})\"[^>]*>(.*?)</a>", raw_line, re.S)
        channel = ""
        name = ""
        if handle_match:
            channel = f"@{handle_match.group(1)}"
            anchor_text = re.sub(r"<[^>]+>", "", handle_match.group(2))
            name = anchor_text.strip().lstrip("@")
        if not channel:
            text = re.sub(r"<[^>]+>", "", raw_line)
            label = text.split("|")[0].strip().lstrip("@")
            label = re.sub(r"^[^A-Za-z0-9#+]+", "", label).strip()
            name = label or ""

        if name or channel:
            entries.append((name or channel.lstrip("@"), source_url, channel))
    return entries


async def _fetch_with_urls(
    channel: str, msg_id: str
) -> tuple[str, str, str]:
    """Fetch the post text, first github URL, and the raw message fragment."""
    close = True
    client: httpx.AsyncClient | None = None
    try:
        client = httpx.AsyncClient(timeout=20, headers=_HEADERS)
        resp = await client.get(
            TELEGRAM_EMBED_URL.format(channel=channel, msg_id=msg_id)
        )
        if resp.is_error or "tgme_widget_message" not in resp.text:
            raise TelegramLinkError(
                f"Could not fetch the post (HTTP {resp.status_code}). Make sure it's a public channel."
            )
        match = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            resp.text,
            re.DOTALL,
        )
        if not match:
            raise TelegramLinkError("No text found in that post.")
        fragment = match.group(1)
        text = _strip_html(fragment)
        github_url = ""
        for href in re.findall(r'href="([^"]+)"', fragment):
            if "github.com/" in href:
                github_url = href
                break
        return text, github_url, fragment
    finally:
        if close and client is not None:
            await client.aclose()
