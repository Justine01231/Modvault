from __future__ import annotations

import enum


class PublishState(enum.IntEnum):
    WAITING_FOR_FILE = 1
    PARSING_METADATA = 2
    WAITING_FOR_CATEGORY = 3
    PREVIEW = 4
    FINISHED = 5
