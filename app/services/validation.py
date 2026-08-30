from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from io import BytesIO

from app.services.module_parser import ModuleMetadata

MAX_FILE_SIZE = 256 * 1024 * 1024  # 256 MB


@dataclass
class ValidationResult:
    valid: bool = False
    errors: list[str] = field(default_factory=list)

    def add(self, error: str) -> None:
        self.errors.append(error)

    def __bool__(self) -> bool:
        return self.valid


def validate_zip(zip_bytes: bytes, file_size: int | None = None) -> ValidationResult:
    result = ValidationResult()

    if file_size is not None and file_size > MAX_FILE_SIZE:
        result.add(
            f"File too large ({file_size / (1024 * 1024):.1f} MB); "
            f"max is {MAX_FILE_SIZE // (1024 * 1024)} MB."
        )

    if not zipfile.is_zipfile(BytesIO(zip_bytes)):
        result.add("Not a valid ZIP archive.")
        return result

    try:
        with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
            if zf.testzip() is not None:
                result.add("ZIP archive is corrupt.")
                return result
            names = zf.namelist()
    except (zipfile.BadZipFile, OSError) as exc:
        result.add(f"Could not read ZIP archive: {exc}")
        return result

    has_prop = any(
        name.endswith("module.prop")
        and not name.startswith(("/", "system/"))
        for name in names
    )
    if not has_prop:
        result.add("No module.prop found in archive.")

    for name in names:
        if name.startswith(("/", "..", "//")):
            result.add(f"Suspicious path in archive: {name}")

    if not result.errors:
        result.valid = True
    return result


def validate_metadata(meta: ModuleMetadata) -> ValidationResult:
    result = ValidationResult()

    if not meta.name.strip():
        result.add("Missing module name.")
    if not meta.version.strip():
        result.add("Missing module version.")
    if meta.module_id and not re.fullmatch(r"[A-Za-z0-9_.\-]+", meta.module_id):
        result.add("module_id contains invalid characters.")

    if not result.errors:
        result.valid = True
    return result


def validate_module(zip_bytes: bytes, file_size: int | None = None) -> ValidationResult:
    result = ValidationResult()
    errors = []
    errors.extend(result_errors(validate_zip(zip_bytes, file_size)))
    if errors:
        result.errors = errors
        return result

    from app.services.module_parser import extract_module_metadata

    try:
        meta = extract_module_metadata(zip_bytes)
    except Exception as exc:
        result.add(str(exc))
        return result

    errors.extend(result_errors(validate_metadata(meta)))
    result.valid = not bool(errors)
    result.errors = errors
    return result


def result_errors(r: ValidationResult) -> list[str]:
    return list(r.errors)
