"""CALYRA source-level CSS preflight. Not a rendering or CSS conformance test."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import tinycss2

ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = ROOT / "fixtures" / "reference.css"
RMLUI_INDEX = "https://mikke89.github.io/RmlUiDoc/pages/rcss/property_index.html"
GRID_PROPERTIES = set("""
grid-template-columns grid-template-rows grid-template-areas
grid-column grid-row grid-area grid-auto-columns grid-auto-rows grid-auto-flow
grid-column-start grid-column-end grid-row-start grid-row-end
place-items place-content place-self
""".split())
# Name-only evidence from the RCSS index. NOT proof of value or selector support.
RMLUI_DOCUMENTED_NAMES = set("""
display flex flex-grow flex-shrink flex-wrap flex-direction
align-items align-self justify-content gap row-gap column-gap
width height min-width max-width min-height max-height
background background-color color font font-family font-size font-style
font-weight font-kerning letter-spacing line-height text-align text-transform
text-overflow white-space word-break
margin margin-top margin-right margin-bottom margin-left
padding padding-top padding-right padding-bottom padding-left
border border-color border-width border-radius border-top
border-left border-bottom border-right border-top-color
border-bottom-color border-left-color border-right-color
box-sizing box-shadow caret-color cursor opacity overflow
overflow-x overflow-y overscroll-behavior pointer-events position
top bottom left right inset transition animation transform
transform-origin visibility vertical-align filter backdrop-filter
mask-image clear float text-decoration
""".split())

def declarations(source: str) -> list[dict]:
    result = []
    def visit(rules, context=""):
        for node in rules:
            if node.type == "qualified-rule":
                selector = tinycss2.serialize(node.prelude).strip()
                for item in tinycss2.parse_declaration_list(
                    node.content, skip_comments=True, skip_whitespace=True
                ):
                    if item.type == "declaration":
                        result.append({
                            "property": item.lower_name,
                            "value": tinycss2.serialize(item.value).strip(),
                            "selector": selector,
                            "condition": context,
                            "line": item.source_line,
                        })
            elif node.type == "at-rule" and node.lower_at_keyword == "keyframes":
                result.append({
                    "property": "@keyframes",
                    "value": tinycss2.serialize(node.prelude).strip(),
                    "selector": "@keyframes", "condition": context,
                    "line": node.source_line,
                })
            elif node.type == "at-rule" and node.content is not None:
                condition = "@" + node.lower_at_keyword + " " + tinycss2.serialize(node.prelude).strip()
                visit(tinycss2.parse_rule_list(
                    node.content, skip_comments=True, skip_whitespace=True
                ), (context + " / " + condition).strip(" /"))
    visit(tinycss2.parse_stylesheet(source, skip_comments=True, skip_whitespace=True))
    return result

def evidence(name: str, value: str) -> tuple[str, str]:
    low = value.lower()
    if name in GRID_PROPERTIES or (name == "display" and low in {"grid", "inline-grid"}):
        return "documented-incompatible", "RCSS index/display does not include CSS Grid"
    if name == "font-family" and "," in value:
        return "documented-difference", "RCSS supports a single font family"
    if name in {"background", "background-image"} and "gradient(" in low:
        return "documented-difference", "RCSS background excludes images; use decorators"
    if name == "border" and any(x in low.split() for x in {"solid","dashed","dotted"}):
        return "documented-difference", "RCSS border excludes border-style"
    if name == "@keyframes":
        return "documented-property-only", "Animations documented; keyframes unexecuted"
    if name in RMLUI_DOCUMENTED_NAMES:
        return "documented-property-only", "Name is documented, not tested"
    return "unverified", "Unclassified does not mean unsupported"

def audit(path: Path = CSS_PATH) -> dict:
    data = path.read_bytes()
    entries = declarations(data.decode("utf-8"))
    groups = defaultdict(lambda: {"count": 0, "classifications": Counter(), "sample": None})
    for item in entries:
        status,note = evidence(item["property"],item["value"])
        group = groups[item["property"]]
        group["count"] += 1
        group["classifications"][status] += 1
        if group["sample"] is None or status in {"documented-incompatible","documented-difference"}:
            group["sample"] = dict(item, status=status, note=note)
    props = [{
        "property": name, "occurrences": val["count"],
        "statuses": dict(sorted(val["classifications"].items())),
        "example": val["sample"]
    } for name,val in sorted(groups.items())]
    statuses = Counter()
    for item in props:
        statuses.update(item["statuses"])
    return {
        "schema": "calyra.css-source-audit.v1",
        "scope": "static-authored-CSS-only",
        "claim": "Documentation evidence only; no backend was run, and values, selectors, runtime interactions and fidelity were not verified",
        "fixture": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "sha256": sha256(data).hexdigest(),
        "declaration_count": len(entries),
        "unique_property_count": len(props),
        "occurrence_statuses": dict(sorted(statuses.items())),
        "rmlui_source_references": [RMLUI_INDEX, "https://github.com/mikke89/RmlUi"],
        "blitz_source_reference": "https://github.com/DioxusLabs/blitz",
        "risks": [p for p in props if "documented-incompatible" in p["statuses"] or "documented-difference" in p["statuses"]],
        "properties": props,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--css", type=Path, default=CSS_PATH)
    parser.add_argument("--out", type=Path, default=ROOT / "evidence" / "css-source-audit.json")
    args = parser.parse_args()
    result = audit(args.css)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "declaration_count", "unique_property_count", "occurrence_statuses"
    )}, indent=2))

if __name__ == "__main__":
    main()
