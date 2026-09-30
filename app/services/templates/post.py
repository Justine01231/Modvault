from __future__ import annotations

from app.services.markup import post_to_html
from app.services.templates.base import PostContext, PostTemplate


class PlainPostTemplate(PostTemplate):
    """Raw free-form text post sent verbatim to the channel (no header).

    Supports **...** for bold; all other text is HTML-escaped so it renders
    literally when published with parse_mode="HTML".
    """

    name = "post"

    def render(self, ctx: PostContext) -> str:
        return post_to_html(ctx.body)
