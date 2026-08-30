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
from app.services.messaging import MessagePost


class MessageState(enum.IntEnum):
    WAITING_TITLE = 1
    WAITING_BODY = 2
    PREVIEW = 3


HEADERS = {
    "announcement": "📢 ANNOUNCEMENT",
    "update": "🆕 UPDATE",
    "warning": "⚠️ WARNING",
}


def _keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ PUBLISH", callback_data="message_confirm"),
                InlineKeyboardButton("❌ CANCEL", callback_data="message_cancel"),
            ]
        ]
    )


def _make_start(template: str):
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not is_admin(user.id):
            await update.effective_message.reply_text("⛔ You are not authorized.")
            return ConversationHandler.END
        context.user_data["message_post"] = MessagePost(template=template)
        await update.effective_message.reply_text(
            f"{HEADERS[template]}\n\nSend a short title (or /skip):"
        )
        return MessageState.WAITING_TITLE

    return start


async def capture_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post: MessagePost = context.user_data.get("message_post")
    if post is None:
        return ConversationHandler.END
    text = (update.effective_message.text or "").strip()
    if text and not text.startswith("/skip"):
        post.title = text[:120]
    await update.effective_message.reply_text(
        "Now send the message body (text):"
    )
    return MessageState.WAITING_BODY


async def capture_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post: MessagePost = context.user_data.get("message_post")
    if post is None:
        return ConversationHandler.END
    body = (update.effective_message.text or "").strip()
    if not body or body.startswith("/skip"):
        await update.effective_message.reply_text("⚠️ Body is required.")
        return MessageState.WAITING_BODY
    post.body = body[:MAX_BODY]
    preview = post.text
    await update.effective_message.reply_text(
        f"👀 Preview:\n\n{preview}", parse_mode=constants.ParseMode.HTML, reply_markup=_keyboard()
    )
    return MessageState.PREVIEW


MAX_BODY = 900


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("message_post", None)
    await update.effective_message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


def build_message_conversation(command: str, template: str) -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler(command, private_dm_only(_make_start(template)))],
        states={
            MessageState.WAITING_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, capture_title)
            ],
            MessageState.WAITING_BODY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, capture_body)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel),
        ],
    )
