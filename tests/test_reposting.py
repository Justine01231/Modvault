from __future__ import annotations

from app.services.reposting import RepostData, build_community_message


def _data(**kwargs) -> RepostData:
    defaults = dict(
        name="Example",
        version="v1.0",
        original_author="",
        source="",
        original_channel="",
        notes="",
    )
    defaults.update(kwargs)
    return RepostData(**defaults)


def test_build_message_with_all_attribution():
    text = build_community_message(
        _data(
            original_author="@Dev",
            source="github.com/Dev/Repo",
            original_channel="@DevChannel",
            notes="Mirror",
        )
    )
    assert "COMMUNITY RELEASE" in text
    assert "@Dev" in text
    assert "github.com/Dev/Repo" in text
    assert "@DevChannel" in text
    assert "Mirror" in text


def test_build_message_minimal():
    text = build_community_message(_data(version=""))
    assert "Example" in text
    assert "v1.0" not in text
