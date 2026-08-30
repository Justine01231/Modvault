from __future__ import annotations

import pytest

from app.services.module_parser import ModuleMetadata
from app.services.validation import (
    MAX_FILE_SIZE,
    validate_metadata,
    validate_module,
    validate_zip,
)
from tests.utils import make_module_zip


def test_validate_valid_module():
    result = validate_module(make_module_zip(), len(make_module_zip()))
    assert result.valid
    assert result.errors == []


def test_validate_not_zip():
    result = validate_zip(b"garbage", 10)
    assert not result.valid
    assert any("ZIP" in e for e in result.errors)


def test_validate_missing_module_prop():
    result = validate_zip(make_module_zip(with_prop=False), 10)
    assert not result.valid
    assert any("module.prop" in e for e in result.errors)


def test_validate_file_too_large():
    result = validate_zip(make_module_zip(), MAX_FILE_SIZE + 1)
    assert not result.valid
    assert any("too large" in e for e in result.errors)


def test_validate_suspicious_path():
    data = make_module_zip(extra_dirs={"../bad": b"x"})
    result = validate_zip(data, len(data))
    assert not result.valid
    assert any("suspicious" in e.lower() or "../" in e for e in result.errors)


def test_validate_metadata_missing_name():
    meta = ModuleMetadata(version="v1.0")
    result = validate_metadata(meta)
    assert not result.valid
    assert any("name" in e for e in result.errors)


def test_validate_metadata_valid():
    meta = ModuleMetadata(name="X", version="v1.0", module_id="x")
    result = validate_metadata(meta)
    assert result.valid
