from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CATEGORIES = {
    "magisk": "Magisk",
    "kernelsu": "KernelSU",
    "apatch": "APatch",
    "zygisk": "Zygisk",
    "lsposed": "LSPosed",
    "android": "Android",
    "kernel": "Kernel",
    "utility": "Utility",
    "other": "Other",
}


def build_preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ PUBLISH", callback_data="publish_confirm"),
                InlineKeyboardButton("✏️ EDIT", callback_data="publish_edit"),
            ],
            [InlineKeyboardButton("❌ CANCEL", callback_data="publish_cancel")],
        ]
    )


def build_category_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(name, callback_data=f"category_{key}")
        for key, name in CATEGORIES.items()
    ]
    rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton("▶️ CONTINUE", callback_data="category_skip")])
    return InlineKeyboardMarkup(rows)
