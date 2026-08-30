from __future__ import annotations

from telegram import Update, constants
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from app.bot.keyboards.publish import build_category_keyboard
from app.bot.states.publish import PublishState
from app.services.authorization import is_admin
from app.services.publishing import download_document, validate_upload


async def start_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.effective_message.reply_text("⛔ You are not authorized to publish.")
        return ConversationHandler.END

    context.user_data["draft"] = None
    context.user_data["draft_file"] = None
    await update.effective_message.reply_text(
        "📤 Send me the module ZIP file to begin publishing."
    )
    return PublishState.WAITING_FOR_FILE


async def receive_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.effective_message.document
    if document is None or not (document.file_name or "").lower().endswith(".zip"):
        await update.effective_message.reply_text(
            "⚠️ Please send a ZIP file.\n\nSend a .zip or type /cancel to abort."
        )
        return PublishState.WAITING_FOR_FILE

    data, draft = await download_document(update)
    ok, message = await validate_upload(data, draft)
    if not ok:
        await update.effective_message.reply_text(message)
        return ConversationHandler.END

    context.user_data["draft"] = draft
    context.user_data["draft_file"] = data

    meta = draft.metadata
    await update.effective_message.reply_text(
        f"✅ ZIP parsed successfully:\n\n"
        f"🧩 Name: <b>{meta.name or '—'}</b>\n"
        f"📌 Version: <b>{meta.version or '—'}</b>\n"
        f"👤 Author: {meta.author or '—'}\n"
        f"📝 Description: {(meta.description or '—')[:60]}\n\n"
        f"Select a category:",
        parse_mode=constants.ParseMode.HTML,
        reply_markup=build_category_keyboard(),
    )
    return PublishState.WAITING_FOR_CATEGORY


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["draft"] = None
    context.user_data["draft_file"] = None
    await update.effective_message.reply_text("❌ Publishing cancelled.")
    return ConversationHandler.END


def build_publish_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("publish", start_publish)],
        states={
            PublishState.WAITING_FOR_FILE: [
                MessageHandler(
                    filters.Document.ALL & ~filters.COMMAND, receive_document
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel),
        ],
    )
