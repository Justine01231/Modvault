from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.database.database import get_session
from app.database.repositories.modules import list_modules
from app.services.formatter import format_module_list


async def modules_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with get_session() as session:
        modules = list_modules(session, limit=20)

    if not modules:
        await update.effective_message.reply_text("📭 No modules published yet.")
        return

    text = format_module_list(modules)
    await update.effective_message.reply_text(
        text, parse_mode=constants.ParseMode.HTML
    )
