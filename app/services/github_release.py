from __future__ import annotations

from app.services.formatter import format_file_size
from app.services.github_client import GitHubRelease
from app.services.templates.base import SEPARATOR


def format_github_release(release: GitHubRelease) -> str:
    tag = release.tag or release.release_name

    lines: list[str] = [
        "⚡ MODULAB • GITHUB RELEASE",
        "",
        f"🧩 {release.repo_name}",
        SEPARATOR,
        "",
    ]

    if tag:
        lines += ["📌 Latest release", tag, ""]

    lines += ["👤 Author", release.owner, ""]

    if release.description:
        lines += ["📝 Description", release.description, ""]

    if release.body:
        body = release.body[:600]
        lines += ["📕 Release notes", body, ""]

    lines.append(SEPARATOR)

    if release.assets:
        asset = release.assets[0]
        size = f" · {format_file_size(asset['size'])}" if asset.get("size") else ""
        lines.append(f"📦 {asset['name']}{size}")

    lines.append("")
    lines.append(f"🌐 Source: {release.repo_url}")
    lines.append("⭐ GITHUB")

    return "\n".join(lines)
