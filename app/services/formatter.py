from __future__ import annotations

from app.services.module_parser import ModuleMetadata
from app.services.templates.community import CommunityContext, CommunityTemplate
from app.services.templates.release import ReleaseContext, ReleaseTemplate

SEPARATOR = "━━━━━━━━━━━━━━━━"

HASHTAG_MAP = {
    "Magisk": "#Magisk",
    "KernelSU": "#KernelSU",
    "APatch": "#APatch",
    "Zygisk": "#Zygisk",
}


def format_release(meta: ModuleMetadata, file_size: str = "") -> str:
    return ReleaseTemplate().render(
        ReleaseContext(module=meta, file_size=file_size)
    )


def format_file_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size_bytes} B"


def format_module_list(modules) -> str:
    from app.database.models import Module

    lines = ["📚 MODULAB • MODULES", SEPARATOR]
    for module in modules:
        latest = module.releases[0] if module.releases else None
        version = latest.version if latest else "—"
        author = module.author.name if module.author else ""
        tag = f" · 👤 {author}" if author else ""
        lines.append(f"🧩 <b>{module.name}</b> <i>v{version}</i>{tag}")
    lines.append(SEPARATOR)
    lines.append(f"Total: {len(modules)}")
    return "\n".join(lines)


def format_stats(
    *,
    modules: int,
    releases: int,
    community_posts: int,
    top_categories: list[tuple[str, int]],
    latest: str | None,
) -> str:
    medals = ("🥇", "🥈", "🥉")
    lines = [
        "📊 MODULAB STATISTICS",
        SEPARATOR,
        f"Total modules      {modules}",
        f"Total releases    {releases}",
        f"Community posts   {community_posts}",
        "",
        "Most published category:",
    ]
    for i, (category, count) in enumerate(top_categories[:3]):
        medal = medals[i] if i < len(medals) else "•"
        lines.append(f"{medal} {category}  ({count})")
    if not top_categories:
        lines.append("—")
    lines.append("")
    lines.append("Latest release:")
    lines.append(latest or "—")
    return "\n".join(lines)


def format_community_post(
    *,
    name: str,
    version: str = "",
    original_author: str = "",
    source: str = "",
    original_channel: str = "",
    notes: str = "",
) -> str:
    return CommunityTemplate().render(
        CommunityContext(
            name=name,
            version=version,
            original_author=original_author,
            source=source,
            original_channel=original_channel,
            notes=notes,
        )
    )
