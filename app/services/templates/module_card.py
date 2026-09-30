from __future__ import annotations

import html

from app.services.features import EXPANDED_ARROW, FEATURES_LABEL

# Plain-text Features header shown above the bullet list.
FEATURES_HEADER_EXPANDED = f"{EXPANDED_ARROW} {FEATURES_LABEL}:"


def render_module_card(
    *,
    name: str,
    description: str = "",
    version: str = "",
    author: str = "",
    file_size: str = "",
    features: list[str] | None = None,
) -> str:
    """Render the modern module card.

    The Features list is always shown in full (no collapsible block) when
    features are present. If there are no features, no Features section and no
    arrow is produced. Everything after the feature list (version, author, tags,
    footer) stays outside it, and there is never an expand/collapse control
    below the footer.

    Layout:
        🎯 <Name>

        <description>

        ▾ Features:
        - Feature 1
        - Feature 2

        📦 v1.0 • 9.4 KB
        👤 <Author>
    """
    lines: list[str] = [f"🎯 <b>{html.escape(name)}</b>", ""]

    if description:
        lines += [html.escape(description), ""]

    if features:
        lines.append(html.escape(f"{EXPANDED_ARROW} {FEATURES_LABEL}:"))
        lines += [f"- {html.escape(feature)}" for feature in features]
        lines.append("")

    meta: list[str] = []
    parts: list[str] = []
    if version:
        parts.append(f"v{version.lstrip('vV')}" if not version.startswith(("v", "V")) else version)
    if file_size:
        parts.append(file_size)
    if parts:
        meta.append(f"<b>📦 {' • '.join(parts)}</b>")
    if author:
        meta.append(f"👤 {html.escape(author)}")

    if meta:
        lines += meta

    return "\n".join(lines).rstrip("\n")
