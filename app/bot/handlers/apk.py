from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.states.apk import ApkState
from app.services.apk import build_card, from_document, publish_apk, persist_apk
from app.services.authorization import is_admin
from app.services.guard import private_dm_only


def _keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ PUBLISH", callback_data="apk_confirm"),
                InlineKeyboardButton("📝 EDIT", callback_data="apk_edit"),
                InlineKeyboardButton("❌ CANCEL", callback_data="apk_cancel"),
            ]
        ]
    )


async def start_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.effective_message.reply_text("⛔ You are not authorized.")
        return ConversationHandler.END

    context.user_data["apk"] = None
    await update.effective_message.reply_text(
        "📦 Send me the <b>APK file</b> to publish to the channel.\n"
        "Send /cancel to abort.",
        parse_mode=constants.ParseMode.HTML,
    )
    return ApkState.WAITING_FOR_FILE


async def receive_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.effective_message.document
    if document is None or not (document.file_name or "").lower().endswith(".apk"):
        await update.effective_message.reply_text(
            "⚠️ Please send a <b>.apk</b> file.\nSend /cancel to abort.",
            parse_mode=constants.ParseMode.HTML,
        )
        return ApkState.WAITING_FOR_FILE

    draft = await from_document(update)
    context.user_data["apk"] = draft

    auto = f" (from filename)" if draft.version else ""
    await update.effective_message.reply_text(
        f"✅ APK received.\n\n"
        f"📌 File: <b>{draft.file_name}</b>\n\n"
        f"Send the <b>app name</b> (parsed: <code>{draft.name}</code>){auto}, "
        f"or /skip to keep it:",
        parse_mode=constants.ParseMode.HTML,
    )
    return ApkState.WAITING_FOR_NAME


async def capture_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = context.user_data.get("apk")
    if draft is None:
        return ConversationHandler.END
    text = (update.effective_message.text or "").strip()
    if text and not text.startswith("/skip"):
        draft.name = text[:120]
    await update.effective_message.reply_text(
        "Send a <b>description</b> (optional), or /skip:",
        parse_mode=constants.ParseMode.HTML,
    )
    return ApkState.WAITING_FOR_DESCRIPTION


async def capture_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = context.user_data.get("apk")
    if draft is None:
        return ConversationHandler.END
    text = (update.effective_message.text or "").strip()
    if text and not text.startswith("/skip"):
        draft.description = text[:600]
    return await _show_preview(update, context)


async def _show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = context.user_data.get("apk")
    if draft is None:
        await update.effective_message.reply_text("⚠️ No APK data. Start again with /apk.")
        return ConversationHandler.END
    await update.effective_message.reply_text(
        f"👀 Preview:\n\n{build_card(draft)}",
        parse_mode=constants.ParseMode.HTML,
        reply_markup=_keyboard(),
    )
    return ApkState.PREVIEW


async def apk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    draft = context.user_data.get("apk")
    if draft is None or not draft.ready:
        await query.edit_message_text("⚠️ No APK data. Start again with /apk.")
        return ConversationHandler.END

    ok, message, message_id = await publish_apk(context, draft)
    if ok and message_id is not None:
        persist_apk(draft, message_id)

    await query.edit_message_text(message, parse_mode=constants.ParseMode.HTML)
    context.user_data.pop("apk", None)
    return ConversationHandler.END


async def apk_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Send the <b>app name</b>, or /cancel to abort.",
        parse_mode=constants.ParseMode.HTML,
    )
    return ApkState.WAITING_FOR_NAME


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("apk", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ APK publish cancelled.")
    else:
        await update.effective_message.reply_text("❌ APK publish cancelled.")
    return ConversationHandler.END


def build_apk_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("apk", private_dm_only(start_apk))],
        states={
            ApkState.WAITING_FOR_FILE: [
                MessageHandler(filters.Document.ALL & ~filters.COMMAND, receive_apk)
            ],
            ApkState.WAITING_FOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, capture_name)
            ],
            ApkState.WAITING_FOR_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, capture_description)
            ],
            ApkState.PREVIEW: [
                CallbackQueryHandler(apk_confirm, pattern=r"^apk_confirm$"),
                CallbackQueryHandler(apk_edit, pattern=r"^apk_edit$"),
                CallbackQueryHandler(cancel, pattern=r"^apk_cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel),
        ],
        per_message=False,
    )
