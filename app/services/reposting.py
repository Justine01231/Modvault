from __future__ import annotations

from dataclasses import dataclass, field

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.services.formatter import format_community_post


@dataclass
class RepostData:
    name: str = ""
    version: str = ""
    original_author: str = ""
    source: str = ""
    original_channel: str = ""
    notes: str = ""


POST_LIMIT = 1024
FIELD_LIMITS = {
    "name": 120,
    "version": 40,
    "original_author": 120,
    "source": 300,
    "original_channel": 120,
    "notes": 600,
}

FIELDS = (
    ("name", "module name", "e.g. OnyxZygisk"),
    ("version", "version (optional)", "e.g. v1.07 or /skip"),
    ("original_author", "original author", "e.g. @Developer"),
    ("source", "source URL (optional)", "e.g. github.com/Developer/Module or /skip"),
    ("original_channel", "original channel (optional)", "e.g. @DeveloperChannel or /skip"),
    ("notes", "notes (optional)", "e.g. any attribution note or /skip"),
)


def build_community_message(repost: RepostData) -> str:
    return format_community_post(
        name=repost.name,
        version=repost.version,
        original_author=repost.original_author,
        source=repost.source,
        original_channel=repost.original_channel,
        notes=repost.notes,
    )


async def publish_community(
    context: ContextTypes.DEFAULT_TYPE, repost: RepostData
) -> tuple[bool, str, int | None]:
    text = build_community_message(repost)
    if len(text) > POST_LIMIT:
        return (
            False,
            f"❌ Community post too long ({len(text)} chars, max {POST_LIMIT}).",
            None,
        )
    try:
        sent = await context.bot.send_message(
            chat_id=settings.channel_id, text=text, parse_mode="HTML"
        )
        return True, f"✅ Community post published to <code>{settings.channel_id}</code>", sent.message_id
    except TelegramError as exc:
        return False, f"❌ Publish failed: {exc}", None
