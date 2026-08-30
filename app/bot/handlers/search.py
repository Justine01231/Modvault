from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.database.database import get_session
from app.database.repositories.modules import search_modules
from app.services.formatter import format_module_list


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    query = " ".join(args).strip()

    if not query:
        await update.effective_message.reply_text(
            "🔍 Usage: /search <query>\n\nExample: /search zygisk"
        )
        return

    with get_session() as session:
        modules = search_modules(session, query, limit=20)

    if not modules:
        await update.effective_message.reply_text(f"🔍 No results for <b>{query}</b>.",
                                                  parse_mode=constants.ParseMode.HTML)
        return

    text = format_module_list(modules)
    await update.effective_message.reply_text(
        f"🔍 Results for <b>{query}</b>:\n\n{text}",
        parse_mode=constants.ParseMode.HTML,
    )
