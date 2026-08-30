from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📦 Publish", callback_data="start_publish"),
                InlineKeyboardButton("🔄 Repost", callback_data="start_repost"),
            ],
            [
                InlineKeyboardButton("📚 Modules", callback_data="list_modules"),
                InlineKeyboardButton("📊 Stats", callback_data="show_stats"),
            ],
        ]
    )
