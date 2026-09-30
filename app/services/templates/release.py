from __future__ import annotations

from dataclasses import dataclass

from app.services.features import get_features
from app.services.templates.base import HASHTAG_MAP, SEPARATOR, PostTemplate
from app.services.templates.module_card import render_module_card
from app.services.module_parser import ModuleMetadata


@dataclass
class ReleaseContext:
    module: ModuleMetadata
    file_size: str = ""


def build_module_tags(meta: ModuleMetadata) -> list[str]:
    tags = ["#Android"]
    if meta.category:
        tags.insert(0, HASHTAG_MAP.get(meta.category, f"#{meta.category.replace(' ', '')}"))
    if meta.support:
        for token in ("Magisk", "KernelSU", "APatch", "Zygisk"):
            if token.lower() in meta.support.lower() and HASHTAG_MAP[token] not in tags:
                tags.append(HASHTAG_MAP[token])
    return tags


class ReleaseTemplate(PostTemplate):
    name = "release"
    header = "⚡ MODULAB • RELEASE"

    def _module_card_body(self, meta: ModuleMetadata, file_size: str) -> str:
        features = get_features(meta.name)
        return render_module_card(
            name=meta.name or "Untitled Module",
            description=meta.description or "",
            version=meta.version or "",
            author=meta.author or "",
            file_size=file_size,
            features=features,
        )

    def render(self, ctx: ReleaseContext) -> str:
        meta = ctx.module

        features = get_features(meta.name)
        if features is not None:
            body = self._module_card_body(meta, ctx.file_size)
            tags = build_module_tags(meta)
            return "\n".join([body.rstrip("\n"), "", " ".join(dict.fromkeys(tags))]).rstrip("\n")

        lines: list[str] = [f"<b>{self.header}</b>", "", f"<b>🧩 {meta.name or 'Untitled Module'}</b>", SEPARATOR, ""]

        lines += ["<b>📌 Version</b>", meta.version, ""]

        if meta.author:
            lines += ["<b>👤 Author</b>", meta.author, ""]
        if meta.description:
            lines += ["<b>📝 Description</b>", meta.description, ""]
        if meta.support:
            lines += ["<b>🛠 Compatibility</b>"]
            lines += [
                f"• {t.strip()}"
                for t in meta.support.replace("\n", ", ").split(",")
                if t.strip()
            ]
            lines += [""]

        lines.append(SEPARATOR)
        if ctx.file_size:
            lines += [f"<b>📦 {ctx.file_size}</b>", ""]

        tags = build_module_tags(meta)

        lines.append(" ".join(dict.fromkeys(tags)))
        return "\n".join(lines)
