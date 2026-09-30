from __future__ import annotations

import logging

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.database.database import get_session
from app.database.repositories.posts import add_post
from app.services.reposting import RepostData, publish_community

logger = logging.getLogger(__name__)


def _persist(repost: RepostData, message_id: int) -> None:
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

    _persist(repost, message_id)

    await query.edit_message_text(message, parse_mode=constants.ParseMode.HTML)
    context.user_data.pop("repost", None)


async def repost_list_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    reposts: list[RepostData] | None = context.user_data.get("repost_list")
    if not reposts:
        await query.edit_message_text("⚠️ Nothing to repost. Start again with /repost.")
        context.user_data.pop("repost_list", None)
        return

    await query.edit_message_text(f"⏳ Reposting {len(reposts)} items...")

    done = 0
    errors = 0
    for repost in reposts:
        ok, message, message_id = await publish_community(context, repost)
        if ok:
            done += 1
            _persist(repost, message_id)
        else:
            errors += 1
            logger.warning("List repost failed for %s: %s", repost.name, message)

    context.user_data.pop("repost_list", None)
    note = f" Reposting {done} of {len(reposts)} succeeded, {errors} failed." if errors else ""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ Done — reposted <b>{done}</b> item(s){note}",
        parse_mode=constants.ParseMode.HTML,
    )


async def repost_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("repost", None)
    context.user_data.pop("repost_list", None)
    await query.edit_message_text("❌ Repost cancelled.")

