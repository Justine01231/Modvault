from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    bot = (await context.bot.get_me()).username
    lines = [
        f"🤖 <b>Bot:</b> @{bot}",
        f"💬 <b>This chat ID:</b> <code>{chat.id}</code>",
        f"Chat type: <code>{chat.type}</code>",
        f"👤 <b>Your user ID:</b> <code>{user.id}</code>",
    ]
    await update.effective_message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.HTML
    )
