from __future__ import annotations

import enum


class RepostState(enum.IntEnum):
    CAPTURING = 1
    PREVIEW = 2
    LIST_PREVIEW = 3
