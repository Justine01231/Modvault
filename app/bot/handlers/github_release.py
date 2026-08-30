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
from app.services.github_client import GitHubError, fetch_release
from app.services.github_release import format_github_release
from app.services.guard import private_dm_only


class GitHubState(enum.IntEnum):
    WAITING_REPO = 1
    PREVIEW = 2


def _keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ PUBLISH", callback_data="gh_confirm"),
                InlineKeyboardButton("❌ CANCEL", callback_data="gh_cancel"),
            ]
        ]
    )


async def start_gh_release(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.effective_message.reply_text("⛔ You are not authorized.")
        return ConversationHandler.END

    context.user_data.pop("gh_release", None)
    await update.effective_message.reply_text(
        "🐙 Send a GitHub repository.\n\n"
        "Examples:\n"
        "github.com/owner/repo\n"
        "owner/repo"
    )
    return GitHubState.WAITING_REPO


async def receive_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    repo = (update.effective_message.text or "").strip()

    if not repo or repo.startswith("/"):
        await update.effective_message.reply_text("⚠️ Please send a valid repository.")
        return GitHubState.WAITING_REPO

    await update.effective_message.reply_text("⏳ Fetching GitHub data...")

    try:
        release = await fetch_release(repo)
    except GitHubError as exc:
        await update.effective_message.reply_text(f"❌ {exc}")
        return GitHubState.WAITING_REPO

    context.user_data["gh_release"] = release
    preview = format_github_release(release)
    await update.effective_message.reply_text(
        f"👀 Preview:\n\n{preview}",
        parse_mode=constants.ParseMode.HTML,
        reply_markup=_keyboard(),
    )
    return GitHubState.PREVIEW


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("gh_release", None)
    await update.effective_message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


def build_gh_release_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("release", private_dm_only(start_gh_release))],
        states={
            GitHubState.WAITING_REPO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_repo)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel),
        ],
    )
