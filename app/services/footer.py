from __future__ import annotations

from app.config.settings import settings


def build_footer() -> str:
    """Return the channel/discussion links footer appended to published cards."""
    lines: list[str] = []
    if settings.channel_username:
        lines.append(f"Follow @{settings.channel_username}")
    if settings.discussion_username:
        lines.append(f"Join @{settings.discussion_username}")
    if not lines:
        return ""
    return "\n".join(lines)


def append_footer(text: str) -> str:
    """Append the footer to a card's text, separated by a blank line."""
    footer = build_footer()
    if not footer:
        return text
    return f"{text}\n\n{footer}"
