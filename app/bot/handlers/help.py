from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "⚡ MODULAB Commands\n\n"
        "/start — Welcome\n"
        "/help — This help\n"
        "/publish — Publish a module (admin)\n"
        "/release — Publish a GitHub release (admin)\n"
        "/repost — Repost a community module (admin)\n"
        "/announcement, /update, /warning — Message cards (admin)\n"
        "/modules — List published modules\n"
        "/search — Search modules\n"
        "/admin — Admin panel\n"
    )
