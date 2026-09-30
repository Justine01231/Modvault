from __future__ import annotations

from app.services.messaging import MessagePost
from app.services.templates import (
    AnnouncementTemplate,
    CommunityContext,
    CommunityTemplate,
    UpdateTemplate,
    WarningTemplate,
)
from app.services.templates.base import PostContext
from app.services.templates.registry import REGISTRY, render_message


def test_registry_contains_all_templates():
    assert set(REGISTRY) == {"release", "community", "announcement", "update", "warning", "post"}


def test_announcement_template():
    text = AnnouncementTemplate().render(
        PostContext(title="Big News", body="Something happened.", tags=["#Magisk"])
    )
    assert "📢 MODULAB • ANNOUNCEMENT" in text
    assert "Big News" in text
    assert "Something happened." in text
    assert "#Magisk" in text


def test_update_template():
    text = UpdateTemplate().render(PostContext(title="v2.0", body="New features."))
    assert "🆕 MODULAB • UPDATE" in text
    assert "v2.0" in text
    assert "New features." in text


def test_warning_template():
    text = WarningTemplate().render(PostContext(title="Careful", body="Read before install."))
    assert "⚠️ MODULAB • WARNING" in text
    assert "Careful" in text


def test_render_message_dispatch():
    text = render_message(
        "announcement", {"title": "X", "body": "Y"}
    )
    assert "MODULAB • ANNOUNCEMENT" in text
    assert "X" in text
    assert "Y" in text


def test_render_message_with_fields():
    text = render_message(
        "update",
        {
            "title": "Patch",
            "body": "Fixed bugs.",
            "fields": [("📌 Version", "1.0.1")],
        },
    )
    assert "📌 Version" in text
    assert "1.0.1" in text


def test_message_post_text():
    post = MessagePost(template="warning", title="Title", body="Body")
    assert "MODULAB • WARNING" in post.text


def test_community_template_renders():
    text = CommunityTemplate().render(
        CommunityContext(name="X", original_author="@D", source="github.com/D/X")
    )
    assert "COMMUNITY RELEASE" in text
