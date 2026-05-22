#!/usr/bin/env python3
"""Slice UI chrome PNGs from implementation/ui_reference.png per ui/assets/manifest.toml."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_manifest(path: Path) -> dict:
    """Minimal TOML reader for ui/assets/manifest.toml (no external deps)."""
    text = path.read_text(encoding="utf-8")
    data: dict = {}
    section: str | None = None
    chrome_key: str | None = None
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"\[([^\]]+)\]", line)
        if m:
            name = m.group(1)
            chrome_key = None
            if name.startswith("chrome."):
                if "chrome" not in data:
                    data["chrome"] = {}
                chrome_key = name.split(".", 1)[1]
                data["chrome"].setdefault(chrome_key, {})
            elif name != "chrome":
                section = name
                data.setdefault(section, {})
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            parsed: object = [int(x.strip()) for x in val[1:-1].split(",") if x.strip()]
        elif val.startswith('"') and val.endswith('"'):
            parsed = val[1:-1]
        elif val.lower() in ("true", "false"):
            parsed = val.lower() == "true"
        else:
            try:
                parsed = int(val)
            except ValueError:
                parsed = val.strip('"')
        if chrome_key is not None:
            data["chrome"][chrome_key][key] = parsed
        elif section is not None:
            data[section][key] = parsed
    return data


def main() -> int:
    manifest_path = ROOT / "ui" / "assets" / "manifest.toml"
    data = _load_manifest(manifest_path)
    meta = data.get("meta", {})
    source_rel = meta.get("source", "implementation/ui_reference.png")
    source_path = ROOT / source_rel
    if not source_path.is_file():
        print(f"Missing source image: {source_path}", file=sys.stderr)
        return 1

    try:
        from PIL import Image
    except ImportError:
        print("Install Pillow: pip install pillow", file=sys.stderr)
        return 1

    sheet = Image.open(source_path).convert("RGBA")
    sw, sh = sheet.size
    expected_w = meta.get("source_width")
    expected_h = meta.get("source_height")
    if expected_w and expected_h and (sw, sh) != (expected_w, expected_h):
        print(
            f"Warning: source size {sw}x{sh} differs from manifest {expected_w}x{expected_h}",
            file=sys.stderr,
        )

    written = 0
    chrome = data.get("chrome", {})
    if not isinstance(chrome, dict):
        print("No [chrome] section in manifest", file=sys.stderr)
        return 1
    for name, entry in chrome.items():
        if not isinstance(entry, dict):
            continue
        rect = entry.get("rect")
        out_rel = entry.get("file")
        if not rect or not out_rel:
            continue
        x, y, w, h = rect
        if x + w > sw or y + h > sh:
            print(f"Skip {name}: rect {rect} outside {sw}x{sh}", file=sys.stderr)
            continue
        out_path = ROOT / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        crop = sheet.crop((x, y, x + w, y + h))
        crop.save(out_path)
        written += 1
        print(f"Wrote {out_rel}")

    print(f"Done: {written} slices")
    return 0 if written > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
