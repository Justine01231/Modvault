from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.database.database import get_session
from app.database.repositories.posts import add_post
from app.services.footer import append_footer
from app.services.formatter import format_file_size

_SEP = "━━━━━━━━━━━━━━━━"

_VERSION_RE = re.compile(r"(?i)(?:[-_ ]?v)?(\d+(?:\.\d+){1,3}(?:[-_a-z0-9.]*))")


@dataclass
class ApkDraft:
    file_name: str = ""
    file_size: int = 0
    file_hash: str = ""
    telegram_file_id: str = ""
    name: str = ""
    version: str = ""
    description: str = ""

    @property
    def ready(self) -> bool:
        return bool(self.telegram_file_id and self.file_name)


def _parse_filename(filename: str) -> tuple[str, str]:
    base = re.sub(r"(?i)\.apk$", "", (filename or "").strip()).strip()
    name = base
    version = ""
    match = _VERSION_RE.search(base)
    if match:
        version = match.group(1).lstrip("v.-_ ")
        start = match.start()
        name = base[:start].rstrip("_-. ")
        name = re.sub(r"(?i)[_\- ]v$", "", name)
    return (name.strip() or "APK"), version


async def from_document(update: Update) -> ApkDraft:
    document = update.effective_message.document
    file_obj = await document.get_file()
    data = bytes(await file_obj.download_as_bytearray())
    name, version = _parse_filename(document.file_name or "app.apk")
    return ApkDraft(
        file_name=document.file_name or "app.apk",
        file_size=document.file_size or len(data),
        telegram_file_id=document.file_id,
        file_hash=hashlib.sha256(data).hexdigest(),
        name=name,
        version=version,
    )


def build_card(draft: ApkDraft) -> str:
    lines: list[str] = [f"<b>📦 APK RELEASE</b>", "", f"<b>📱 {draft.name or 'Untitled'}</b>"]
    if draft.version:
        lines.append(f"<b>v{draft.version}</b>")
    lines += ["", _SEP, "", f"<b>📌 File</b>", draft.file_name, ""]
    if draft.description:
        lines += [f"<b>📝 Description</b>", draft.description, ""]
    lines.append(_SEP)
    if draft.file_size:
        lines.append(f"<b>📦 {format_file_size(draft.file_size)}</b>")
    return "\n".join(lines).rstrip("\n")


async def publish_apk(
    context: ContextTypes.DEFAULT_TYPE, draft: ApkDraft
) -> tuple[bool, str, int | None]:
    caption = append_footer(build_card(draft))
    try:
        sent = await context.bot.send_document(
            chat_id=settings.channel_id,
            document=draft.telegram_file_id,
            filename=draft.file_name,
            caption=caption,
            parse_mode="HTML",
        )
        msg = (
            f"✅ APK published to channel <code>{settings.channel_id}</code>\n\n"
            f"<b>{draft.file_name}</b>\n{draft.file_hash[:12]}…"
        )
        return True, msg, sent.message_id
    except TelegramError as exc:
        return False, f"❌ Publish failed: {exc}", None


def persist_apk(draft: ApkDraft, message_id: int) -> None:
    with get_session() as session:
        add_post(
            session,
            None,
            chat_id=settings.channel_id,
            message_id=message_id,
            post_type="apk",
            notes=f"{draft.file_name} | v{draft.version or '?'}",
            original_author=draft.name,
        )
