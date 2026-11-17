#!/usr/bin/env python3
"""Generate a deterministic, plain CALYRA testing icon using Python + macOS tools.

The icon is a BUILD RESOURCE ONLY, not a visual-fidelity fixture or output.
No third-party Python packages, network download, or source asset edits.
"""
from __future__ import annotations

import binascii
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib

SIZES = (16, 32, 128, 256, 512)
BASE = 1024
HERE = Path(__file__).resolve().parent
ICONS = HERE / "src-tauri" / "icons"


def write_png(path: Path) -> None:
    raw = bytearray()
    for y in range(BASE):
        raw.append(0)  # PNG filter: none
        dy = (y + 0.5 - BASE / 2) / (BASE / 2)
        for x in range(BASE):
            dx = (x + 0.5 - BASE / 2) / (BASE / 2)
            r = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            if r < 0.88:
                rgb = (20, 28, 40)
            else:
                rgb = (9, 13, 19)
            if 0.57 < r < 0.72 and abs(angle) > 0.65:
                rgb = (217, 240, 212)
            if 0.84 < r < 0.875:
                rgb = (67, 83, 93)
            raw.extend((*rgb, 255))

    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(
            ">I", binascii.crc32(payload) & 0xFFFFFFFF
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", BASE, BASE, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def main() -> None:
    ICONS.mkdir(parents=True, exist_ok=True)
    base = ICONS / "calyra-reference-source.png"
    write_png(base)
    # tauri::generate_context!() always expects this conventional source
    # icon on macOS, even when bundle.icon names only the generated .icns.
    icon_png = ICONS / "icon.png"
    shutil.copyfile(base, icon_png)
    assert icon_png.read_bytes() == base.read_bytes()
    if sys.platform != "darwin":
        # The same deterministic PNG is also usable for a Linux Tauri
        # compile smoke. macOS .icns packaging still requires Apple iconutil.
        print("CALYRA_APP_ICON_PNG_CREATED=true")
        return
    iconset = ICONS / "calyra-reference.iconset"
    iconset.mkdir(exist_ok=True)
    for size in SIZES:
        for scale in (1, 2):
            final = size * scale
            name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
            subprocess.run([
                "sips", "-z", str(final), str(final), str(base),
                "--out", str(iconset / name)
            ], check=True, capture_output=True, text=True)
    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(ICONS / "icon.icns")],
        check=True,
    )
    assert (ICONS / "icon.icns").stat().st_size > 2000
    print("CALYRA_APP_ICON_CREATED=true")


if __name__ == "__main__":
    main()
