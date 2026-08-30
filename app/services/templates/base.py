from __future__ import annotations

from dataclasses import dataclass

SEPARATOR = "━━━━━━━━━━━━━━━━"
BRAND = "MODULAB"

HASHTAG_MAP = {
    "Magisk": "#Magisk",
    "KernelSU": "#KernelSU",
    "APatch": "#APatch",
    "Zygisk": "#Zygisk",
}


@dataclass
class PostContext:
    """Generic context for rendering any template card."""

    body: str = ""
    title: str = ""
    fields: list[tuple[str, str]] | None = None
    tags: list[str] | None = None


class PostTemplate:
    """Base template: a card with a header, body, optional fields and tags."""

    name = "post"
    header: str = ""
    extra_footer: str | None = None

    def render(self, ctx: PostContext) -> str:
        lines: list[str] = []

        if self.header:
            lines.append(self.header)
            lines.append("")

        if ctx.title:
            lines.append(ctx.title)
            lines.append(SEPARATOR)

        if ctx.body:
            lines.append(ctx.body)
            lines.append("")

        if ctx.fields:
            for label, value in ctx.fields:
                lines += [label, value, ""]

        if self.extra_footer:
            lines.append(self.extra_footer)

        if ctx.tags:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(" ".join(dict.fromkeys(ctx.tags)))

        return "\n".join(lines).rstrip("\n")
