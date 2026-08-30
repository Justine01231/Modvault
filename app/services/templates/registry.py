from __future__ import annotations

from app.services.templates.base import PostContext, PostTemplate
from app.services.templates.community import CommunityContext, CommunityTemplate
from app.services.templates.message import (
    AnnouncementTemplate,
    UpdateTemplate,
    WarningTemplate,
)
from app.services.templates.release import ReleaseContext, ReleaseTemplate

REGISTRY: dict[str, type[PostTemplate]] = {
    ReleaseTemplate.name: ReleaseTemplate,
    CommunityTemplate.name: CommunityTemplate,
    AnnouncementTemplate.name: AnnouncementTemplate,
    UpdateTemplate.name: UpdateTemplate,
    WarningTemplate.name: WarningTemplate,
}


def render_message(template_name: str, context: PostContext | dict) -> str:
    template = REGISTRY[template_name]()
    if isinstance(context, dict):
        context = PostContext(**context)
    return template.render(context)
