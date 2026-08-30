from __future__ import annotations

from dataclasses import dataclass

from app.services.templates.base import HASHTAG_MAP, SEPARATOR, PostTemplate
from app.services.module_parser import ModuleMetadata


@dataclass
class ReleaseContext:
    module: ModuleMetadata
    file_size: str = ""


class ReleaseTemplate(PostTemplate):
    name = "release"
    header = "⚡ MODULAB • RELEASE"

    def render(self, ctx: ReleaseContext) -> str:
        meta = ctx.module
        lines: list[str] = [self.header, "", f"🧩 {meta.name or 'Untitled Module'}", SEPARATOR, ""]

        lines += ["📌 Version", meta.version, ""]

        if meta.author:
            lines += ["👤 Author", meta.author, ""]
        if meta.description:
            lines += ["📝 Description", meta.description, ""]
        if meta.support:
            lines += ["🛠 Compatibility"]
            lines += [
                f"• {t.strip()}"
                for t in meta.support.replace("\n", ", ").split(",")
                if t.strip()
            ]
            lines += [""]

        lines.append(SEPARATOR)
        if ctx.file_size:
            lines += [f"📦 {ctx.file_size}", ""]

        tags = ["#Android"]
        if meta.category:
            tags.insert(0, HASHTAG_MAP.get(meta.category, f"#{meta.category.replace(' ', '')}"))
        if meta.support:
            for token in ("Magisk", "KernelSU", "APatch", "Zygisk"):
                if token.lower() in meta.support.lower() and HASHTAG_MAP[token] not in tags:
                    tags.append(HASHTAG_MAP[token])

        lines.append(" ".join(dict.fromkeys(tags)))
        return "\n".join(lines)
