from __future__ import annotations

import io
import zipfile


def make_module_zip(
    props: str = "id=example\nname=Example Module\nversion=v1.0\nversionCode=100\nauthor=Justine\ndescription=Test module\n",
    with_prop: bool = True,
    extra_dirs: dict[str, bytes] | None = None,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        if with_prop:
            zf.writestr("module.prop", props)
        for name, content in (extra_dirs or {}).items():
            zf.writestr(name, content)
    return buffer.getvalue()
