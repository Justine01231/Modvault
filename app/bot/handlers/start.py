from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.effective_message.reply_text(
        f"⚡ MODULAB • MODULE VAULT\n\n"
        f"Welcome, {user.first_name}! 🧩\n\n"
        f"Use /help to see available commands.",
        parse_mode=ParseMode.HTML,
    )
