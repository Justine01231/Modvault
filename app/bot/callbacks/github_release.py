from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.database.database import get_session
from app.database.repositories.posts import add_post
from app.database.repositories.releases import add_release
from app.services.github_client import GitHubRelease
from app.services.github_release import format_github_release
from app.services.footer import append_footer
from app.services.module_parser import ModuleMetadata


async def _persist(release: GitHubRelease) -> None:
    asset = release.assets[0] if release.assets else None
    version = release.tag or release.release_name or "latest"
    meta = ModuleMetadata(
        name=release.repo_name,
        version=version,
        author=release.owner,
        description=release.description or release.body[:300],
    )
    with get_session() as session:
        add_release(
            session,
            meta,
            file_name=asset["name"] if asset and asset["name"] else None,
            file_size=asset["size"] if asset and asset["size"] else None,
            repository_url=release.repo_url,
        )


async def gh_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    release: GitHubRelease | None = context.user_data.get("gh_release")
    if release is None:
        await query.edit_message_text("⚠️ No GitHub release data. Start again with /release.")
        return

    text = append_footer(format_github_release(release))
    try:
        sent = await context.bot.send_message(
            chat_id=settings.channel_id, text=text, parse_mode="HTML"
        )
    except Exception as exc:
        await query.edit_message_text(f"❌ Publish failed: {exc}")
        return

    await _persist(release)
    with get_session() as session:
        add_post(
            session,
            None,
            chat_id=settings.channel_id,
            message_id=sent.message_id,
            post_type="official",
        )

    await query.edit_message_text(
        f"✅ GitHub release published to <code>{settings.channel_id}</code>",
        parse_mode=constants.ParseMode.HTML,
    )
    context.user_data.pop("gh_release", None)


async def gh_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("gh_release", None)
    await query.edit_message_text("❌ Cancelled.")
