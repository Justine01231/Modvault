from __future__ import annotations

import hashlib
from dataclasses import dataclass

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.services.footer import append_footer
from app.services.formatter import format_file_size, format_release
from app.services.module_parser import ModuleMetadata, extract_module_metadata
from app.services.validation import validate_module


@dataclass
class ReleaseDraft:
    file_name: str = ""
    file_size: int = 0
    file_hash: str = ""
    telegram_file_id: str = ""
    metadata: ModuleMetadata | None = None

    @property
    def ready(self) -> bool:
        return self.metadata is not None and bool(self.metadata.name and self.metadata.version)


async def download_document(update: Update) -> tuple[bytes, ReleaseDraft]:
    document = update.effective_message.document
    file_obj = await document.get_file()
    data = bytes(await file_obj.download_as_bytearray())
    draft = ReleaseDraft(
        file_name=document.file_name or "module.zip",
        file_size=document.file_size or len(data),
        telegram_file_id=document.file_id,
        file_hash=hashlib.sha256(data).hexdigest(),
    )
    return data, draft


def build_preview(draft: ReleaseDraft) -> str:
    meta = draft.metadata
    if meta is None:
        return ""
    if not meta.category:
        meta.category = meta.default_category
    return format_release(meta, format_file_size(draft.file_size))


@dataclass
class PublishResult:
    ok: bool
    message: str
    message_id: int | None = None


async def publish_to_channel(
    context: ContextTypes.DEFAULT_TYPE, draft: ReleaseDraft
) -> PublishResult:
    caption = append_footer(build_preview(draft))
    try:
        sent = await context.bot.send_document(
            chat_id=settings.channel_id,
            document=draft.telegram_file_id,
            filename=draft.file_name,
            caption=caption,
            parse_mode="HTML",
        )
        msg = (
            f"✅ Published to channel <code>{settings.channel_id}</code>\n\n"
            f"<b>{draft.file_name}</b>\n{draft.file_hash[:12]}…"
        )
        return PublishResult(ok=True, message=msg, message_id=sent.message_id)
    except TelegramError as exc:
        return PublishResult(ok=False, message=f"❌ Publish failed: {exc}")


async def validate_upload(data: bytes, draft: ReleaseDraft) -> tuple[bool, str]:
    validation = validate_module(data, draft.file_size)
    if not validation:
        return False, "\n".join(["❌ Validation failed:", *validation.errors])
    try:
        draft.metadata = extract_module_metadata(data)
    except Exception as exc:
        return False, f"❌ Could not parse module: {exc}"
    return True, ""
