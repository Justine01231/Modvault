from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if chat is not None and chat.type != "private":
        await update.effective_message.reply_text(
            f"👋 {user.first_name}! This is the MODULAB discussion group.\n\n"
            f"Chat freely here 💬 and use:\n"
            f"/modules — list published modules\n"
            f"/search <query> — search modules\n"
            f"/help — see commands\n\n"
            f"Announcements and new modules are posted in the channel.",
        )
        return
    await update.effective_message.reply_text(
        f"⚡ MODULAB • MODULE VAULT\n\n"
        f"Welcome, {user.first_name}! 🧩\n\n"
        f"Use /help to see available commands.",
        parse_mode=ParseMode.HTML,
    )
