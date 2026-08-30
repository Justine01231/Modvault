from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from io import BytesIO

MODULE_PROP_NAME = "module.prop"


class ModuleParseError(Exception):
    pass


@dataclass
class ModuleMetadata:
    module_id: str = ""
    name: str = ""
    version: str = ""
    version_code: str = ""
    author: str = ""
    description: str = ""
    support: str = ""
    category: str = ""

    @property
    def default_category(self) -> str:
        support = self.support.strip()
        if not support:
            return ""
        for token in ("KernelSU", "APatch", "Magisk"):
            if token.lower() in support.lower():
                return token
        return ""

    def is_complete(self) -> bool:
        return bool(self.name and self.version)


def _decode(raw: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").strip()


def parse_module_prop(content: bytes) -> ModuleMetadata:
    meta = ModuleMetadata()
    for raw_line in content.splitlines():
        line = _decode(raw_line)
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        field_map = {
            "id": "module_id",
            "name": "name",
            "version": "version",
            "versionCode": "version_code",
            "author": "author",
            "description": "description",
            "support": "support",
            "category": "category",
        }
        field_name = field_map.get(key)
        if field_name:
            setattr(meta, field_name, value)
    return meta


def extract_module_metadata(zip_bytes: bytes) -> ModuleMetadata:
    if not zipfile.is_zipfile(BytesIO(zip_bytes)):
        raise ModuleParseError("Not a valid ZIP archive.")

    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise ModuleParseError(f"Corrupt archive member: {bad}")

        for name in zf.namelist():
            if name.endswith("module.prop") and not name.startswith(("/", "system/")):
                content = zf.read(name)
                return parse_module_prop(content)

    raise ModuleParseError(
        "No module.prop found in archive. Is this a Magisk-style module?"
    )


def load_module_from_file(filepath: str) -> ModuleMetadata:
    with open(filepath, "rb") as fh:
        return extract_module_metadata(fh.read())
