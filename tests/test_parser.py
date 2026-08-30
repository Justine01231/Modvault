from __future__ import annotations

import pytest

from app.services.module_parser import (
    ModuleParseError,
    extract_module_metadata,
    parse_module_prop,
)
from tests.utils import make_module_zip


def test_parse_valid_prop():
    meta = parse_module_prop(
        b"id=example\nname=Example Module\nversion=v1.0\nversionCode=100\nauthor=Justine\ndescription=Test module\n"
    )
    assert meta.module_id == "example"
    assert meta.name == "Example Module"
    assert meta.version == "v1.0"
    assert meta.version_code == "100"
    assert meta.author == "Justine"
    assert meta.description == "Test module"


def test_parse_ignores_comments_and_empty():
    meta = parse_module_prop(b"# comment\n\nname=OnlyName\n")
    assert meta.name == "OnlyName"
    assert meta.module_id == ""


def test_extract_from_zip():
    meta = extract_module_metadata(make_module_zip())
    assert meta.name == "Example Module"
    assert meta.author == "Justine"


def test_extract_non_zip_raises():
    with pytest.raises(ModuleParseError):
        extract_module_metadata(b"not a zip")


def test_extract_missing_module_prop_raises():
    data = make_module_zip(with_prop=False)
    with pytest.raises(ModuleParseError):
        extract_module_metadata(data)


def test_default_category_from_support():
    meta = parse_module_prop(b"support=Zygisk KernelSU\n")
    assert meta.default_category == "KernelSU"
