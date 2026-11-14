# Stage A diagnostic: GTK3 native CSS subset (Linux)

**Status:** locally executed; restricted; **not** Blitz, RmlUi, Electrobun GPU, or a modern-CSS candidate. This additional diagnostic does not replace or satisfy any named-engine task in OpenSpec.

## Why

The previous Tk and WeasyPrint tests did not test an actual native toolkit's CSS parser. The Linux environment already provides GTK3's dynamically linked libraries, while GitHub source cloning and the RmlUi/Blitz toolchains remain unavailable. GTK3's `GtkCssProvider` parses CSS-like rules directly and styles native widgets. That makes it useful as a *third negative/control path*, showing where a CSS-aware native widget toolkit differs from a browser.

GTK3 exposes a CSS syntax but **not web HTML/CSS layout semantics**. The experiment deliberately creates native GtkBox, GtkEntry, GtkComboBox, GtkScale, GtkCheckButton, and GtkButton widgets, rather than claiming to render source HTML. The selected `.action` declarations are extracted from `fixtures/reference.css`; CSS custom-property colors are substituted, and GTK-specific selectors/rules are added. This is **adapted CSS**, not unchanged stylesheet compatibility. The canonical source hashes are included in the adapter result.

## Reproduction

Linux with GTK3 runtime `libgtk-3.so.0`, GDK/GObject, X11 (or Xvfb), Python 3, tinycss2, Pillow, and jsonschema:

```bash
xvfb-run -a -s '-screen 0 1280x900x24' \
  python -m adapters.gtk3_css_probe \
  --capture evidence/native-gtk3/probe.png \
  --contract evidence/native-gtk3/contract.json \
  --no-loop

xvfb-run -a -s '-screen 0 1280x900x24' \
  python -m unittest discover -s tests -p 'test_*.py' -q
```

The probe uses ctypes for the **system** GTK3 shared library because Python GI bindings and GTK headers aren't installed in this sandbox. This is a testing bridge, **not a recommended CALYRA SDK architecture**. On systems without GTK3, tests skip instead of reporting success.

## Verified

- Actual native GTK window screenshot: 840×680 pixels captured from Xvfb.
- Native `GtkCssProvider` produced the action button's actual background color, independently read from its style context: `rgb(198,219,116)` from `--accent` in the canonical CSS.
- Real native input controls are present; invoking the actual GTK `clicked` signal updates label contents using input state; reset restores defaults.
- The adapter produces a JSON record validated against the existing `calyra.adapter-result.v1` schema. It reports adapted source CSS, reconstructed widget tree, missing Grid/Flexbox/JS semantics, and restricted eligibility.
- Four dedicated GTK3 tests and the full 24-test local suite passed using a real virtual display. No GitHub Actions were triggered.

## Not verified

- RmlUi, Blitz, Electrobun GPU, or Tauri execution; **none** is represented by this experiment.
- Web CSS Grid/Flexbox, animations, native GPU UI, CSS material fidelity, advanced fonts, IME, assistive-technology accessibility tree, real pointer click automation, performance, memory, or startup timings.
- macOS, Windows, or commercial distribution. GTK3 itself is a separate system runtime dependency; there is no universal standalone binary here.

## Engineering conclusion

A native application can use familiar CSS-like rules to style actual interactive controls **without Chromium**. However, providing CSS styling for GTK widgets is dramatically less work than supporting the browser's *layout, DOM, type, form, painting and accessibility contracts*. This proof strengthens the argument for measuring complete behaviors in the named engines rather than equating a color-matched button with general CSS portability.

Source: [GTK3 CssProvider documentation](https://docs.gtk.org/gtk3/class.CssProvider.html), [GTK3 CSS properties](https://docs.gtk.org/gtk3/css-properties.html).
