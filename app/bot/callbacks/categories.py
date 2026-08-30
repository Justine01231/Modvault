from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.bot.keyboards.publish import CATEGORIES, build_preview_keyboard
from app.services.publishing import ReleaseDraft, build_preview


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    draft: ReleaseDraft | None = context.user_data.get("draft")
    if draft is None or draft.metadata is None:
        await query.edit_message_text("⚠️ No draft found. Start again with /publish.")
        return

    data = query.data
    if data == "category_skip":
        category = ""
    else:
        key = data.split("_", 1)[1]
        category = CATEGORIES.get(key, "")

    draft.metadata.category = category
    preview = build_preview(draft)

    await query.edit_message_text(
        f"👀 Preview:\n\n{preview}\n\n"
        f"{'Category: ' + category if category else 'No category set.'} — Ready to publish?",
        parse_mode=constants.ParseMode.HTML,
        reply_markup=build_preview_keyboard(),
    )
