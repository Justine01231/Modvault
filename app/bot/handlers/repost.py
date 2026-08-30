from __future__ import annotations

from telegram import Update, constants
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.states.repost import RepostState
from app.services.authorization import is_admin
from app.services.reposting import FIELDS, RepostData, build_community_message


def _current_field(repost: RepostData) -> tuple | None:
    for field, _, _ in FIELDS:
        if not getattr(repost, field, "").strip():
            return next(
                (item for item in FIELDS if item[0] == field), None
            )
    return None


async def start_repost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.effective_message.reply_text("⛔ You are not authorized to repost.")
        return ConversationHandler.END

    context.user_data["repost"] = RepostData()
    field, label, example = FIELDS[0]
    await update.effective_message.reply_text(
        f"🔄 Community repost — let's gather the details.\n\n"
        f"Step 1/{len(FIELDS)}: {label.capitalize()} ({example})"
    )
    return RepostState.CAPTURING


async def capture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    repost: RepostData = context.user_data.get("repost")
    if repost is None:
        await update.effective_message.reply_text("⚠️ Session lost. Start again with /repost.")
        return ConversationHandler.END

    text = (update.effective_message.text or "").strip()
    current = _current_field(repost)

    if current is None:
        return await _preview(update, context)

    field, label, _ = current

    if text.startswith("/skip"):
        setattr(repost, field, "")
        note = "(skipped)"
    else:
        limit = {"name": 120, "version": 40, "original_author": 120, "source": 300, "original_channel": 120, "notes": 600}.get(field, 120)
        if len(text) > limit:
            await update.effective_message.reply_text(
                f"⚠️ Too long ({len(text)} > {limit}). Please shorten."
            )
            return RepostState.CAPTURING
        setattr(repost, field, text)
        note = f"<code>{text[:40]}</code>"

    next_field = _current_field(repost)
    if next_field is None:
        return await _preview(update, context)

    field, label, example = next_field
    index = FIELDS.index(next_field) + 1
    await update.effective_message.reply_text(
        f"✅ {label.capitalize()}: {note}\n\n"
        f"Step {index}/{len(FIELDS)}: {label.capitalize()} ({example})",
        parse_mode=constants.ParseMode.HTML,
    )
    return RepostState.CAPTURING


async def _preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    repost: RepostData = context.user_data.get("repost")
    if repost is None:
        await update.effective_message.reply_text("⚠️ No repost data. Start with /repost.")
        return ConversationHandler.END

    if not repost.name:
        await update.effective_message.reply_text("⚠️ Module name is required.")
        return RepostState.CAPTURING

    preview = build_community_message(repost)
    await update.effective_message.reply_text(
        f"👀 Preview:\n\n{preview}",
        parse_mode=constants.ParseMode.HTML,
        reply_markup=_repost_keyboard(),
    )
    return RepostState.PREVIEW


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("repost", None)
    await update.effective_message.reply_text("❌ Repost cancelled.")
    return ConversationHandler.END


def _repost_keyboard():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ PUBLISH", callback_data="repost_confirm"),
                InlineKeyboardButton("❌ CANCEL", callback_data="repost_cancel"),
            ]
        ]
    )


def build_repost_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("repost", start_repost)],
        states={
            RepostState.CAPTURING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, capture)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel),
        ],
    )
