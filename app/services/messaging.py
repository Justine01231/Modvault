from __future__ import annotations

from dataclasses import dataclass

from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.services.footer import append_footer
from app.services.templates import REGISTRY, render_message

POST_LIMIT = 1024


@dataclass
class MessagePost:
    template: str
    title: str = ""
    body: str = ""
    fields: list[tuple[str, str]] | None = None
    tags: list[str] | None = None

    @property
    def text(self) -> str:
        return render_message(self.template, {"body": self.body, "title": self.title, "fields": self.fields, "tags": self.tags})


async def publish_message(
    context: ContextTypes.DEFAULT_TYPE,
    post: MessagePost,
    parse_mode: str | None = "HTML",
    max_length: int | None = None,
) -> tuple[bool, str, int | None]:
    text = append_footer(post.text)
    limit = max_length or POST_LIMIT
    if len(text) > limit:
        return False, f"❌ Post too long ({len(text)} chars, max {limit}).", None
    try:
        sent = await context.bot.send_message(
            chat_id=settings.channel_id, text=text, parse_mode=parse_mode
        )
        return True, f"✅ Published to <code>{settings.channel_id}</code>", sent.message_id
    except TelegramError as exc:
        return False, f"❌ Publish failed: {exc}", None
