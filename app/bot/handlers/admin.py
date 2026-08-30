from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.database.database import get_session
from app.database.repositories.modules import (
    count_modules,
    count_releases,
    latest_releases,
    top_categories,
)
from app.database.repositories.posts import count_posts
from app.services.authorization import is_admin
from app.services.formatter import format_stats


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin(user.id):
        await update.effective_message.reply_text("⛔ You are not authorized to access the admin panel.")
        return

    with get_session() as session:
        latest_rows = latest_releases(session, limit=1)
        latest = None
        if latest_rows:
            rel = latest_rows[0]
            latest = f"{rel.module.name} {rel.version}" if rel.module else rel.version

        text = format_stats(
            modules=count_modules(session),
            releases=count_releases(session),
            community_posts=count_posts(session, "community"),
            top_categories=top_categories(session, limit=3),
            latest=latest,
        )

    await update.effective_message.reply_text(text, parse_mode=constants.ParseMode.HTML)
