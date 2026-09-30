from __future__ import annotations

import enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.services.authorization import is_admin
from app.services.guard import private_dm_only
from app.services.messaging import MessagePost, publish_message

MAX_BODY = 4000


class PostState(enum.IntEnum):
    WAITING_BODY = 1
    PREVIEW = 2


def _keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ PUBLISH", callback_data="post_confirm"),
                InlineKeyboardButton("📝 EDIT", callback_data="post_edit"),
                InlineKeyboardButton("❌ CANCEL", callback_data="post_cancel"),
            ]
        ]
    )


async def start_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.effective_message.reply_text("⛔ You are not authorized to post.")
        return ConversationHandler.END

    text = update.effective_message.text or ""
    parts = text.split(maxsplit=1)
    content = parts[1].strip() if len(parts) > 1 else ""

    if content:
        return await _show_preview(update, context, content)

    context.user_data["post_body"] = ""
    await update.effective_message.reply_text(
        "📝 Send the text to post to the channel. It is sent verbatim (footer added).\n"
        "Wrap part in <code>**...</code> to make it bold, e.g. <code>**Alternative clients**</code>.\n"
        "Send /cancel to cancel."
    )
    return PostState.WAITING_BODY


async def capture_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.effective_message.text or "").strip()
    if not text or text.startswith("/cancel"):
        return await cancel(update, context)

    return await _show_preview(update, context, text[:MAX_BODY])


async def _show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, content: str):
    post = MessagePost(template="post", body=content)
    context.user_data["post_body"] = content
    await update.effective_message.reply_text(
        f"👀 Preview:\n\n{post.text}",
        parse_mode=constants.ParseMode.HTML,
        reply_markup=_keyboard(),
    )
    return PostState.PREVIEW


async def post_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    body = context.user_data.get("post_body")
    if not body:
        await query.edit_message_text("⚠️ No post text. Start again with /post.")
        return ConversationHandler.END

    post = MessagePost(template="post", body=body)
    ok, message, message_id = await publish_message(
        context, post, parse_mode="HTML", max_length=MAX_BODY
    )
    if not ok:
        await query.edit_message_text(message, parse_mode=constants.ParseMode.HTML)
        return ConversationHandler.END

    from app.config.settings import settings
    from app.database.database import get_session
    from app.database.repositories.posts import add_post

    with get_session() as session:
        add_post(
            session,
            None,
            chat_id=settings.channel_id,
            message_id=message_id,
            post_type="post",
        )

    await query.edit_message_text(message, parse_mode=constants.ParseMode.HTML)
    context.user_data.pop("post_body", None)
    return ConversationHandler.END


async def post_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 Send the new text to post (max 4000 chars), or send /cancel to cancel."
    )
    return PostState.WAITING_BODY


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("post_body", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Post cancelled.")
    else:
        await update.effective_message.reply_text("❌ Post cancelled.")
    return ConversationHandler.END


def build_post_conversation() -> ConversationHandler:
    from telegram.ext import CallbackQueryHandler

    return ConversationHandler(
        entry_points=[CommandHandler("post", private_dm_only(start_post))],
        states={
            PostState.WAITING_BODY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, capture_body)
            ],
            PostState.PREVIEW: [
                CallbackQueryHandler(post_confirm, pattern=r"^post_confirm$"),
                CallbackQueryHandler(post_edit, pattern=r"^post_edit$"),
                CallbackQueryHandler(cancel, pattern=r"^post_cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel),
        ],
        per_message=False,
    )
