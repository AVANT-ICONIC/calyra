#!/usr/bin/env python3
"""Stage A browserless STATIC CSS smoke test (WeasyPrint, NOT a native GPU candidate).

Keeps authored CSS unchanged. Only fixture visibility, motion, and page-sizing are
adapted to a paged, non-interactive document renderer. Produces a machine-readable
contract and screenshots that expose rather than hide rendering incompatibility.
"""
import argparse
import hashlib
import json
import platform
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
CONTRACT_PATH = ROOT / "harness" / "adapter-contract.schema.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_markup(fixture: str, state: str) -> str:
    from lxml import html as lxml_html

    source = (FIXTURES / "index.html").read_text(encoding="utf-8")
    # External CSS/JS links are not executed; the identical stylesheet is applied
    # explicitly by the renderer. No HTTP calls and no untrusted remote assets.
    dom = lxml_html.document_fromstring(source)
    for node in dom.xpath('//link[@rel="stylesheet"] | //script'):
        node.drop_tree()
    root = dom.xpath('/html')[0]
    root.set("data-motion", "off")
    body = dom.xpath('/html/body')[0]
    body.set("data-fixture", fixture)
    body.set("data-ready", "static-document")
    for section in dom.xpath('//*[@data-case]'):
        classes = section.get("class", "").split()
        if section.get("data-case") == fixture:
            section.attrib.pop("hidden", None)
            section.set("class", " ".join([*classes, "active"]))
        else:
            section.set("hidden", "")
            section.set("class", " ".join(c for c in classes if c != "active"))
    for link in dom.xpath('//*[@data-link]'):
        if link.get("data-link") == fixture:
            link.set("aria-current", "page")
        else:
            link.attrib.pop("aria-current", None)
    if fixture == "interaction" and state == "menu-open":
        dom.get_element_by_id("menu-popover").attrib.pop("hidden", None)
        dom.get_element_by_id("menu-toggle").set("aria-expanded", "true")
    return lxml_html.tostring(dom, encoding="unicode", method="html")


def run_weasyprint(fixture: str, width: int, height: int, state: str, output: Path) -> dict:
    import fitz
    import weasyprint
    from weasyprint import CSS, HTML
    from jsonschema import validate

    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    if fixture not in manifest["fixtures"]:
        raise ValueError("Unknown fixture")
    if not 240 <= width <= 4096 or not 240 <= height <= 4096:
        raise ValueError("Viewport must be 240..4096 CSS pixels")
    if state not in ("default", "menu-open") or state == "menu-open" and fixture != "interaction":
        raise ValueError("Unsupported fixture state")
    css = (FIXTURES / "reference.css").read_text(encoding="utf-8")
    # This reference only uses local, inline assets. Keep the smoke test offline.
    if re.search(r"@import\s|url\s*\(\s*['\"]?https?://", css, re.I):
        raise ValueError("Fixture contains network-dependent CSS")
    html = prepare_markup(fixture, state)
    output.mkdir(parents=True, exist_ok=True)
    target = f"{fixture}-{width}x{height}-{state}"
    paged_css = f"@page {{ size: {width}px {height}px; margin: 0; }}"
    # Deliberately NO replacement of grid, gradients, blurs or other styling.
    document = HTML(string=html, base_url=FIXTURES.as_uri() + "/", media_type="screen").render(
        stylesheets=[CSS(string=css), CSS(string=paged_css)]
    )
    pdf_path = output / f"{target}.pdf"
    document.write_pdf(pdf_path)
    png_paths = []
    pdf = fitz.open(pdf_path)
    for i, page in enumerate(pdf):
        screenshot = output / f"{target}-page{i+1}.png"
        page.get_pixmap(matrix=fitz.Matrix(96 / 72, 96 / 72), alpha=False).save(screenshot)
        png_paths.append(str(screenshot.relative_to(ROOT)))
    report = {
        "schema": "calyra.adapter-result.v1",
        "adapter": {"id": "weasyprint-static", "version": weasyprint.__version__, "kind": "document-only"},
        "fixture": {"name": fixture, "version": manifest["version"], "width_css_px": width, "height_css_px": height, "state": state, "motion": "off"},
        "source": {
            "html_sha256": sha256(FIXTURES / "index.html"),
            "css_sha256": sha256(FIXTURES / "reference.css"),
            "js_sha256": sha256(FIXTURES / "reference.js"),
            "css_modified": False,
            "dom_patched": True,
            "js_executed": False,
            "external_network_used": False,
            "adaptations": ["Injected static fixture visibility and selected nav state (no JavaScript)", "Paged-media viewport via @page; this is not an interactive app window", "PDF rasterized at 96 dpi for CSS-pixel capture", "Motion disabled via data-motion attribute"],
        },
        "environment": {"os": platform.platform(), "architecture": platform.machine(), "python_version": platform.python_version()},
        "execution": {"browser_engine": False, "gpu_backed": False, "interactive": False, "render_backend": "WeasyPrint CSS -> Pango/Cairo -> PDF -> MuPDF PNG"},
        "capture": {"success": bool(png_paths), "page_count": len(pdf), "png_paths": png_paths, "pdf_path": str(pdf_path.relative_to(ROOT)), "pixel_scale": 1.0, "measured_performance": False},
        "coverage": {f: "untested" for f in manifest["fixtures"][fixture]["features"]} | {"javascript-interactions": "unsupported", "animation-playback": "unsupported"},
        "eligibility": "restricted",
        "limitations": ["CPU/software document renderer, NOT a native GPU application or an interactive GUI", "No JavaScript execution, native controls, pointer/focus interaction or accessibility-tree verification", "Paged-media model may change responsive behavior and scroll semantics", "No property-level fidelity rating without explicit feature probes", "Any generated images are static PDF rasterizations, not live application screenshots", "This run does not establish speed, startup, memory or energy superiority"],
    }
    validate(report, json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
    report_path = output / f"{target}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=["weasyprint-static"], default="weasyprint-static")
    parser.add_argument("--fixture", choices=["controls", "dashboard", "visual", "interaction"], required=True)
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--state", default="default")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence" / "native-stage-a")
    args = parser.parse_args()
    try:
        result = run_weasyprint(args.fixture, args.width, args.height, args.state, args.output.resolve())
    except Exception as exc:
        parser.exit(1, f"Stage A failed: {type(exc).__name__}: {exc}\n")
    print(json.dumps({"adapter": result["adapter"], "fixture": result["fixture"], "capture": result["capture"], "eligibility": result["eligibility"]}, indent=2))


if __name__ == "__main__":
    main()
