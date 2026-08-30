from __future__ import annotations

from dataclasses import dataclass, field

from app.services.templates.base import SEPARATOR, PostTemplate


@dataclass
class CommunityContext:
    name: str
    version: str = ""
    original_author: str = ""
    source: str = ""
    original_channel: str = ""
    notes: str = ""


class CommunityTemplate(PostTemplate):
    name = "community"

    def render(self, ctx: CommunityContext) -> str:
        lines: list[str] = ["🔄 COMMUNITY RELEASE", "", f"🧩 {ctx.name or 'Untitled Module'}"]
        if ctx.version:
            lines.append(f"v{ctx.version}")
        lines += ["", SEPARATOR]

        attribution: list[tuple[str, str]] = []
        if ctx.original_author:
            attribution.append(("👤 Original Author", ctx.original_author))
        if ctx.source:
            attribution.append(("🌐 Source", ctx.source))
        if ctx.original_channel:
            attribution.append(("📢 Original Channel", ctx.original_channel))
        if ctx.notes:
            attribution.append(("📝 Notes", ctx.notes))

        if attribution:
            for label, value in attribution:
                lines += [label, value, ""]

        lines += [
            "⚠️ This project is not developed or maintained by MODULAB.",
            "All rights belong to the original developer.",
        ]
        return "\n".join(lines)
