from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from app.bot.callbacks.categories import category_selected
from app.bot.callbacks.github_release import gh_cancel, gh_confirm
from app.bot.callbacks.message import message_cancel, message_confirm
from app.bot.callbacks.publish import publish_cancel, publish_confirm, publish_edit
from app.bot.callbacks.repost import (
    repost_cancel,
    repost_confirm,
    repost_list_confirm,
)
from app.bot.handlers.admin import admin_command
from app.bot.handlers.apk import build_apk_conversation
from app.bot.handlers.debug import debug_command
from app.bot.handlers.github_release import build_gh_release_conversation
from app.bot.handlers.help import help_command
from app.bot.handlers.message import build_message_conversation
from app.bot.handlers.modules import modules_command
from app.bot.handlers.post import build_post_conversation
from app.bot.handlers.publish import build_publish_conversation
from app.bot.handlers.repost import build_repost_conversation
from app.bot.handlers.search import search_command
from app.bot.handlers.start import start
from app.bot.keyboards.main import build_main_keyboard
from app.config.settings import settings
from app.database.database import init_db
from app.services.guard import private_dm_only

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
)
logger = logging.getLogger(__name__)


async def _log_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    logger.info(
        "INCOMING update: type=%s chat_id=%s chat_type=%s text=%r",
        update.update_id,
        chat.id if chat else None,
        chat.type if chat else None,
        update.effective_message.text if update.effective_message else None,
    )


async def post_init(application: Application) -> None:
    init_db()
    commands = [
        ("start", "Welcome"),
        ("help", "Help"),
        ("debug", "Show chat ID / your ID"),
        ("publish", "Publish a module (admin)"),
        ("release", "Publish a GitHub release (admin)"),
        ("repost", "Repost a community module (admin)"),
        ("post", "Post raw text to channel (admin)"),
        ("apk", "Publish an APK file (admin)"),
        ("announcement", "Post an announcement (admin)"),
        ("update", "Post an update (admin)"),
        ("warning", "Post a warning (admin)"),
        ("modules", "List modules"),
        ("search", "Search modules"),
        ("admin", "Admin panel"),
    ]
    await application.bot.set_my_commands(commands)


def build_application() -> Application:
    application = (
        ApplicationBuilder().token(settings.bot_token).post_init(post_init).build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("debug", debug_command))
    application.add_handler(CommandHandler("ping", _log_incoming))
    application.add_handler(CommandHandler("modules", modules_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("admin", private_dm_only(admin_command)))
    application.add_handler(build_publish_conversation())
    application.add_handler(build_repost_conversation())
    application.add_handler(build_post_conversation())
    application.add_handler(build_apk_conversation())
    application.add_handler(build_gh_release_conversation())
    application.add_handler(build_message_conversation("announcement", "announcement"))
    application.add_handler(build_message_conversation("update", "update"))
    application.add_handler(build_message_conversation("warning", "warning"))

    application.add_handler(CallbackQueryHandler(category_selected, pattern=r"^category_"))
    application.add_handler(CallbackQueryHandler(publish_confirm, pattern=r"^publish_confirm$"))
    application.add_handler(CallbackQueryHandler(publish_edit, pattern=r"^publish_edit$"))
    application.add_handler(CallbackQueryHandler(publish_cancel, pattern=r"^publish_cancel$"))
    application.add_handler(CallbackQueryHandler(repost_confirm, pattern=r"^repost_confirm$"))
    application.add_handler(CallbackQueryHandler(repost_list_confirm, pattern=r"^repost_list_confirm$"))
    application.add_handler(CallbackQueryHandler(repost_cancel, pattern=r"^repost_cancel$"))
    application.add_handler(CallbackQueryHandler(message_confirm, pattern=r"^message_confirm$"))
    application.add_handler(CallbackQueryHandler(message_cancel, pattern=r"^message_cancel$"))
    application.add_handler(CallbackQueryHandler(gh_confirm, pattern=r"^gh_confirm$"))
    application.add_handler(CallbackQueryHandler(gh_cancel, pattern=r"^gh_cancel$"))

    return application


def main() -> None:
    if not settings.bot_token:
        raise SystemExit(
            "BOT_TOKEN is not set. Copy .env.example to .env and fill in your values."
        )

    application = build_application()
    logger.info("Starting ModuLab...")
    application.run_polling()


if __name__ == "__main__":
    main()
