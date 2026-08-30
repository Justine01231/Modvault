from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.database.database import get_session
from app.database.repositories.posts import add_post
from app.database.repositories.releases import add_release
from app.services.publishing import (
    ReleaseDraft,
    build_preview,
    publish_to_channel,
)


async def publish_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    draft: ReleaseDraft | None = context.user_data.get("draft")
    if draft is None or not draft.ready:
        await query.edit_message_text("⚠️ Draft is incomplete. Start again with /publish.")
        return

    result = await publish_to_channel(context, draft)
    if not result.ok:
        await query.edit_message_text(result.message, parse_mode=constants.ParseMode.HTML)
        return

    with get_session() as session:
        release = add_release(
            session,
            draft.metadata,
            file_name=draft.file_name,
            file_size=draft.file_size,
            file_hash=draft.file_hash,
            telegram_file_id=draft.telegram_file_id,
        )
        add_post(
            session,
            release,
            chat_id=settings.channel_id,
            message_id=result.message_id,
            post_type="official",
        )

    await query.edit_message_text(result.message, parse_mode=constants.ParseMode.HTML)
    context.user_data["draft"] = None
    context.user_data["draft_file"] = None


async def publish_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["draft"] = None
    context.user_data["draft_file"] = None
    await query.edit_message_text("❌ Publishing cancelled.")


async def publish_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    draft: ReleaseDraft | None = context.user_data.get("draft")
    if draft is None or draft.metadata is None:
        await query.edit_message_text("⚠️ No draft to edit. Start again with /publish.")
        return
    preview = build_preview(draft)
    await query.edit_message_text(
        text=f"{preview}\n\n✏️ Editing is not available yet in V0.1. "
        f"Publish or cancel and re-upload.",
        parse_mode=constants.ParseMode.HTML,
    )
