from __future__ import annotations

from app.services.templates.base import PostTemplate


class AnnouncementTemplate(PostTemplate):
    name = "announcement"
    header = "📢 MODULAB • ANNOUNCEMENT"


class UpdateTemplate(PostTemplate):
    name = "update"
    header = "🆕 MODULAB • UPDATE"


class WarningTemplate(PostTemplate):
    name = "warning"
    header = "⚠️ MODULAB • WARNING"
