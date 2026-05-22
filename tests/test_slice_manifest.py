"""Manifest rects fit reference image; sliced files exist after script run."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_rects_within_source() -> None:
    manifest_path = ROOT / "ui" / "assets" / "manifest.toml"
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    meta = data["meta"]
    sw = int(meta["source_width"])
    sh = int(meta["source_height"])
    source = ROOT / meta["source"]
    assert source.is_file()

    import struct

    header = source.read_bytes()[:24]
    w, h = struct.unpack(">II", header[16:24])
    assert (w, h) == (sw, sh)

    chrome = data.get("chrome", {})
    assert isinstance(chrome, dict)
    for _name, entry in chrome.items():
        if not isinstance(entry, dict):
            continue
        x, y, rw, rh = entry["rect"]
        assert x >= 0 and y >= 0
        assert x + rw <= sw and y + rh <= sh, f"{_name} rect out of bounds"


def test_chrome_slices_committed() -> None:
    manifest_path = ROOT / "ui" / "assets" / "manifest.toml"
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    missing: list[str] = []
    chrome = data.get("chrome", {})
    for _name, entry in chrome.items():
        if not isinstance(entry, dict):
            continue
        path = ROOT / entry["file"]
        if not path.is_file():
            missing.append(entry["file"])
    assert not missing, f"Run scripts/slice_ui_assets.py — missing: {missing}"
