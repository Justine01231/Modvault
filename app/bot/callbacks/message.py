from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.database.database import get_session
from app.database.repositories.posts import add_post
from app.services.messaging import MessagePost, publish_message


async def message_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    post: MessagePost | None = context.user_data.get("message_post")
    if post is None or not post.body:
        await query.edit_message_text("⚠️ No post data. Start again.")
        return

    ok, message, message_id = await publish_message(context, post)
    if not ok:
        await query.edit_message_text(message, parse_mode=constants.ParseMode.HTML)
        return

    with get_session() as session:
        add_post(
            session,
            None,
            chat_id=settings.channel_id,
            message_id=message_id,
            post_type=post.template,
        )

    await query.edit_message_text(message, parse_mode=constants.ParseMode.HTML)
    context.user_data.pop("message_post", None)


async def message_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("message_post", None)
    await query.edit_message_text("❌ Cancelled.")
