from __future__ import annotations

import enum


class ApkState(enum.IntEnum):
    WAITING_FOR_FILE = 1
    WAITING_FOR_NAME = 2
    WAITING_FOR_DESCRIPTION = 3
    PREVIEW = 4
