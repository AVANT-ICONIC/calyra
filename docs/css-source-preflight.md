# CALYRA: CSS source-level preflight

**Source analysis, NOT executed native rendering or a compatibility rating.**

Fixture SHA256: `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`

Local analysis of fixtures/reference.css: **489 declarations, 89 unique properties/at-rule markers**.

| RmlUi documentation classification | Declaration occurrences |
| --- | ---: |
| Documented incompatible | 26 |
| Documented syntax difference | 12 |
| Documented property name ONLY | 419 |
| Unverified | 32 |

Documented limitations in the authored CSS: CSS Grid (`display:grid`, grid tracks/placement), gradient images in `background` (RmlUi uses decorators), font fallback lists (`font-family` supports a single family), and the CSS `solid` border-style shorthand. These categories are *source statements*, not observed runtime failures.

Do not interpret these counts as a percentage of working CSS: even a recognized property name may fail with a particular value, selector, or rendering backend.

Evidence: [RmlUi property index](https://mikke89.github.io/RmlUiDoc/pages/rcss/property_index.html), [RmlUi README](https://github.com/mikke89/RmlUi), [Blitz README](https://github.com/DioxusLabs/blitz). Blitz's HTML wrapper and Dioxus Native have different interactivity contracts.

Reproduce: `python harness/css_audit.py` then `python -m unittest discover -s tests -p 'test_css_audit.py' -v`.

**Pending:** Actual RmlUi/Blitz/Electrobun GUI adapters and GPU/CPU benchmarks. This sandbox lacks their source/toolchains and external terminal DNS access.
