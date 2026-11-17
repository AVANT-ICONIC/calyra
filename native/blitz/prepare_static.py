#!/usr/bin/env python3
"""Make deterministic JS-free CALYRA HTML snapshots for Blitz's HTML frontend.

This does not translate CSS. It does perform deliberate DOM and asset-delivery
adaptations. Neither input behavior nor JavaScript is part of this preflight.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

FIXTURE_NAMES = ("controls", "dashboard", "visual", "interaction")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exactly_once(source: str, before: str, after: str) -> str:
    count = source.count(before)
    if count != 1:
        raise ValueError(f"Expected exactly one source marker, found {count}: {before[:80]}")
    return source.replace(before, after, 1)


def generate(root: Path, destination: Path, fixture: str) -> dict:
    if fixture not in FIXTURE_NAMES:
        raise ValueError("Unknown fixture: " + fixture)
    canonical = root / "fixtures"
    html_path = canonical / "index.html"
    css_path = canonical / "reference.css"
    js_path = canonical / "reference.js"
    html = html_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    js = js_path.read_bytes()
    if re.search(r"</style\s*>", css, flags=re.IGNORECASE):
        raise ValueError("Cannot safely inline stylesheet containing </style> token")
    # No network resources or rewritten CSS are permitted in this first probe.
    if re.search(r"@import\b|url\s*\(\s*['\"]?https?://", css, flags=re.IGNORECASE):
        raise ValueError("External CSS dependency requires a separate documented probe")
    html = exactly_once(html, '<html lang="en">', '<html lang="en" data-motion="off">')
    html = exactly_once(html, '<link rel="stylesheet" href="./reference.css">',
                        '<style data-calyra-original-css="true">\n' + css + '\n</style>')
    html = exactly_once(html, '<script src="./reference.js" defer></script>',
                        '<!-- No JavaScript execution in this static Blitz HTML probe -->')
    html = exactly_once(html, '<body data-fixture="controls" data-ready="false">',
                        f'<body data-fixture="{fixture}" data-ready="true">')
    html = exactly_once(html, f'<section class="case" data-case="{fixture}"',
                        f'<section class="case active" data-case="{fixture}"')
    html = exactly_once(html, f'<a data-link="{fixture}"',
                        f'<a data-link="{fixture}" aria-current="page"')
    # Required if JS-free snapshots are to remain comparable with live Chromium state.
    if html.count('class="case active"') != 1 or html.count('aria-current="page"') != 1:
        raise ValueError("Static fixture must have exactly one visible case and selected navigation link")
    dest = destination / fixture
    dest.mkdir(parents=True, exist_ok=True)
    result_html = dest / "index.html"
    result_html.write_text(html, encoding="utf-8")
    manifest = {
        "schema": "calyra.blitz-static-input.v1",
        "fixture": fixture,
        "canonical_sha256": {
            "index.html": sha256(html_path.read_bytes()),
            "reference.css": sha256(css_path.read_bytes()),
            "reference.js": sha256(js),
        },
        "generated_html_sha256": sha256(result_html.read_bytes()),
        "css_bytes_changed": False,
        "html_patched": True,
        "javascript_executed": False,
        "network_resources_used": False,
        "adaptations": [
            "Canonical stylesheet inlined verbatim into one style element; link delivery changed",
            "Removed script tag; browser JavaScript not run",
            f"Set data-fixture to {fixture}; marked its case active and its navigation link selected",
            "Set data-motion=off and data-ready=true as static render state",
        ],
        "limitations": [
            "This is a static HTML/CSS paint probe, NOT browser JavaScript or event behavior",
            "Existing hidden controls/sections remain in the DOM; only one .case is active",
            "Input/focus/IME/OS accessibility are not evaluated",
        ],
    }
    (dest / "snapshot.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", choices=FIXTURE_NAMES, default="controls")
    args = parser.parse_args()
    print(json.dumps(generate(args.root, args.output, args.fixture), indent=2))


if __name__ == "__main__":
    main()
