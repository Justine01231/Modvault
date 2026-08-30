from __future__ import annotations

from app.services.formatter import (
    format_community_post,
    format_file_size,
    format_module_list,
    format_release,
    format_stats,
)
from app.services.module_parser import ModuleMetadata


class _Rel:
    version = "v1.0"


class _Author:
    name = "Justine"


class _Mod:
    def __init__(self, name, rels, author=None):
        self.name = name
        self.releases = rels
        self.author = author


def _meta(**kwargs) -> ModuleMetadata:
    defaults = dict(
        module_id="example",
        name="Example Module",
        version="v1.0",
        version_code="100",
        author="Justine",
        description="A test module",
        support="Magisk",
        category="Magisk",
    )
    defaults.update(kwargs)
    return ModuleMetadata(**defaults)


def test_format_release_contains_key_fields():
    text = format_release(_meta(), file_size="1.2 MB")
    assert "MODULAB" in text
    assert "Example Module" in text
    assert "v1.0" in text
    assert "Justine" in text
    assert "A test module" in text
    assert "1.2 MB" in text
    assert "#Magisk" in text


def test_format_release_no_author_description():
    text = format_release(_meta(author="", description="", support="", category=""))
    assert "Justine" not in text
    assert "#Android" in text


def test_format_release_compat_list():
    meta = _meta(support="Magisk, KernelSU, APatch")
    text = format_release(meta)
    assert "• Magisk" in text
    assert "• KernelSU" in text
    assert "• APatch" in text


def test_format_file_size():
    assert format_file_size(512) == "512 B"
    assert format_file_size(2048) == "2.0 KB"
    assert format_file_size(5 * 1024 * 1024) == "5.0 MB"


def test_format_module_list():
    mods = [
        _Mod("OnyxZygisk", [_Rel()], _Author()),
        _Mod("Empty", []),
    ]
    text = format_module_list(mods)
    assert "MODULES" in text
    assert "OnyxZygisk" in text
    assert "Justine" in text
    assert "Empty" in text
    assert "Total: 2" in text


def test_format_stats():
    text = format_stats(
        modules=10,
        releases=20,
        community_posts=3,
        top_categories=[("Magisk", 8), ("KernelSU", 2)],
        latest="OnyxZygisk v1.07",
    )
    assert "Total modules      10" in text
    assert "Total releases    20" in text
    assert "Community posts   3" in text
    assert "🥇 Magisk  (8)" in text
    assert "OnyxZygisk v1.07" in text


def test_format_community_post_full():
    text = format_community_post(
        name="Example Module",
        version="v2.0",
        original_author="@Developer",
        source="github.com/Developer/Example",
        original_channel="@DeveloperChannel",
        notes="Unofficial mirror.",
    )
    assert "COMMUNITY RELEASE" in text
    assert "Example Module" in text
    assert "v2.0" in text
    assert "@Developer" in text
    assert "github.com/Developer/Example" in text
    assert "@DeveloperChannel" in text
    assert "not developed or maintained by MODULAB" in text


def test_format_community_post_minimal():
    text = format_community_post(name="Tool")
    assert "COMMUNITY RELEASE" in text
    assert "Tool" in text
    assert "Original Author" not in text
    assert "not developed or maintained by MODULAB" in text
