#!/usr/bin/env python3
"""Build a flashable Magisk module zip from the gpu-boost/ source dir.

Magisk requires the entry names to NOT have a leading './' and for
META-INF/com/google/android/update-binary to exist at the archive root.
Executable bit is preserved via external_attr so scripts are runnable after
extraction, matching the install-time chmod done in customize.sh.
"""
from __future__ import annotations

import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "gpu-boost")
OUT = os.path.join(ROOT, "gpu-boost-v1.0.zip")

EXECUTABLE = {
    "engine.sh",
    "customize.sh",
    "service.sh",
    "action.sh",
    "uninstall.sh",
    "webroot/api.cgi",
    "META-INF/com/google/android/update-binary",
}


def main() -> int:
    if not os.path.isdir(SRC):
        print(f"source dir not found: {SRC}", file=sys.stderr)
        return 1

    if os.path.exists(OUT):
        os.remove(OUT)

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(SRC):
            for fname in files:
                if fname.startswith(".") or fname.endswith(".md"):
                    continue
                abs_path = os.path.join(root, fname)
                # strip the src prefix + leading slash -> archive path
                rel = os.path.relpath(abs_path, SRC).replace(os.sep, "/")

                info = zipfile.ZipInfo(rel)
                st = os.stat(abs_path)
                mode = st.st_mode & 0o777
                # keep executable on the shell/applet scripts
                if rel in EXECUTABLE:
                    mode |= 0o111
                info.external_attr = (mode & 0xFFFF) << 16

                with open(abs_path, "rb") as fh:
                    zf.writestr(info, fh.read())

    with zipfile.ZipFile(OUT) as zf:
        names = zf.namelist()
        print(f"built {OUT} ({len(names)} entries)")
        for n in names:
            print(" -", n)

    # sanity: update-binary present at root without './'
    with zipfile.ZipFile(OUT) as zf:
        for required in (
            "module.prop",
            "customize.sh",
            "META-INF/com/google/android/update-binary",
            "META-INF/com/google/android/updater-script",
        ):
            if required not in zf.namelist():
                print(f"MISSING ENTRY: {required}", file=sys.stderr)
                return 1
    print("structure OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
