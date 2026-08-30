from __future__ import annotations

from functools import wraps
from typing import Awaitable, Callable, TypeVar

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.services.authorization import is_admin

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[object]]
T = TypeVar("T")


def private_dm_only(handler: Handler) -> Handler:
    """Only run a command from a private DM; otherwise tell the user to use the DM.

    This keeps admin/management commands out of the public group so other
    members cannot see them, while still routing the admin to a private chat.
    """

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> object:
        chat = update.effective_chat
        user = update.effective_user
        if chat is not None and chat.type != "private":
            # Non-admins: say nothing public; admins: quietly redirect to DM.
            if user is None or not is_admin(user.id):
                return None
            await update.effective_message.reply_text(
                "🔒 Admin commands only work in a private chat with me. "
                "Please open @Mod_Vault_Bot and use the command there."
            )
            return None
        return await handler(update, context)

    return wrapper


def admin_only(handler: Handler) -> Handler:
    """Enforce admin-only access from a private DM."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> object:
        user = update.effective_user
        if user is None or not is_admin(user.id):
            await update.effective_message.reply_text(
                "⛔ This command is restricted to admins."
            )
            return None
        return await handler(update, context)

    return wrapper
