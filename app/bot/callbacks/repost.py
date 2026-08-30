from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.database.database import get_session
from app.database.repositories.posts import add_post
from app.services.reposting import RepostData, publish_community


async def repost_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    repost: RepostData | None = context.user_data.get("repost")
    if repost is None or not repost.name:
        await query.edit_message_text("⚠️ No repost data. Start again with /repost.")
        return

    ok, message, message_id = await publish_community(context, repost)
    if not ok:
        await query.edit_message_text(message, parse_mode=constants.ParseMode.HTML)
        return

    with get_session() as session:
        add_post(
            session,
            None,
            chat_id=settings.channel_id,
            message_id=message_id,
            post_type="community",
            original_author=repost.original_author,
            source=repost.source,
            original_channel=repost.original_channel,
            notes=repost.notes,
        )

    await query.edit_message_text(message, parse_mode=constants.ParseMode.HTML)
    context.user_data.pop("repost", None)


async def repost_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("repost", None)
    await query.edit_message_text("❌ Repost cancelled.")
