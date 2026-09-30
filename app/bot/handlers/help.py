from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.services.authorization import is_admin


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_admin_user = user is not None and is_admin(user.id)

    lines = ["⚡ MODULAB Commands"]
    if is_admin_user:
        lines += [
            "",
            "👤 For everyone:",
            "/start — Welcome",
            "/help — This help",
            "/modules — List published modules",
            "/search <query> — Search modules",
            "",
            "🔒 For admins (private chat):",
            "/publish — Publish a module",
            "/release — Publish a GitHub release",
            "/repost — Repost a community module",
            "/post — Post raw text to the channel",
            "/apk — Publish an APK file",
            "/announcement, /update, /warning — Message cards",
            "/admin — Admin panel",
        ]
    else:
        lines += [
            "",
            "/start — Welcome",
            "/modules — List published modules",
            "/search <query> — Search modules",
            "",
            "💬 Chat freely here — admin and publishing commands are reserved for the bot owner.",
        ]
    await update.effective_message.reply_text("\n".join(lines))
