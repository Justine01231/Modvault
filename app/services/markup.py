from __future__ import annotations

import html
import re

BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


def post_to_html(text: str) -> str:
    """Convert **bold** markers to <b> and HTML-escape everything else.

    Safe for publishing with parse_mode="HTML": any <, >, & in the source
    text are escaped so they render literally, while **...** becomes bold.
    """
    escaped = html.escape(text or "")
    return BOLD_RE.sub(r"<b>\1</b>", escaped)
