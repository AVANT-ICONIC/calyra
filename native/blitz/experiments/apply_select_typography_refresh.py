#!/usr/bin/env python3
"""CALYRA Stage A: targeted computed-CSS typography invalidation for native SelectData.

Apply after apply_readonly_select.py AND apply_select_option_text_refresh.py
to a pinned disposable Blitz checkout. Fail closed on source drift.
This is an experimental read-only label integration, not general CSS parity.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_exact(root: Path, relative: str, anchor: str, replacement: str) -> None:
    file = root / relative
    before = file.read_text(encoding="utf-8")
    matches = before.count(anchor)
    if matches != 1:
        raise AssertionError(f"{relative}: anchor found {matches} times: {anchor[:95]!r}")
    file.write_text(before.replace(anchor, replacement, 1), encoding="utf-8")
    print(f"CALYRA_TYPOGRAPHY_PATCHED={relative}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    root = parser.parse_args().source.resolve()
    for file in (
        "packages/blitz-dom/src/node/text.rs",
        "packages/blitz-dom/src/document.rs",
        "packages/blitz-dom/src/resolve.rs",
    ):
        assert (root / file).is_file(), file

    replace_exact(
        root, "packages/blitz-dom/src/node/text.rs",
        """    pub selected_option: Option<NodeId>,
    pub label: String,
    pub layout: parley::layout::Layout<TextBrush>,
}""",
        """    pub selected_option: Option<NodeId>,
    pub label: String,
    pub layout: parley::layout::Layout<TextBrush>,
    /// Computed CSS typography of the last Parley shaping pass.
    pub typography_fingerprint: String,
}"""
    )

    replace_exact(
        root, "packages/blitz-dom/src/document.rs",
        """    /// CALYRA Stage A: selectedness lives on the native DOM select.
    /// Rebuild only the label's noneditable Parley layout, not the document.
    pub fn calyra_set_select_selection""",
        """    /// CALYRA Stage A: a narrow computed-typography fingerprint.
    /// The style source is computed Stylo CSS, NOT the literal style attribute:
    /// changes from classes, inherited rules and CSS variables can be detected.
    /// Keep label typography separate from text paint color/background which
    /// Vello reads from the node at paint time.
    fn calyra_select_typography_fingerprint(&self, select_id: NodeId) -> Option<String> {
        let node = self.nodes.get(select_id)?;
        if node.element_data().and_then(|el| el.select_data()).is_none() {
            return None;
        }
        if node.primary_styles().is_none() { return None; }
        const FIELDS: &[&str] = &[
            "font-family", "font-size", "font-weight", "font-style",
            "font-stretch", "font-variation-settings", "font-feature-settings",
            "font-variant", "line-height", "letter-spacing", "word-spacing",
            "white-space", "text-transform", "text-wrap-mode",
            "word-break", "line-break", "overflow-wrap", "direction",
            "unicode-bidi"
        ];
        let mut sig = format!("scale:{:.6};", self.viewport.scale_f64());
        for key in FIELDS {
            sig.push_str(key);
            sig.push('=');
            sig.push_str(&self.resolved_style_value(select_id, key));
            sig.push(';');
        }
        Some(sig)
    }

    /// Refresh only selects whose *computed* CSS typography has changed after
    /// Stylo restyle. No unconditional repaint on unchanged resolve passes.
    pub fn calyra_refresh_select_typography_after_restyle(&mut self) {
        let select_ids: Vec<NodeId> = self.nodes.iter().filter_map(|(id, node)| {
            node.element_data()
                .and_then(|el| el.select_data())
                .map(|_| id)
        }).collect();
        for id in select_ids {
            let Some(fingerprint) = self.calyra_select_typography_fingerprint(id) else {
                continue;
            };
            let data = self.nodes[id].element_data().unwrap().select_data().unwrap();
            if data.typography_fingerprint == fingerprint { continue; }
            // Selection identity and DOM nodes remain unchanged.
            let selected = data.selected_option;
            self.calyra_set_select_selection(id, selected);
        }
    }

    /// CALYRA Stage A: selectedness lives on the native DOM select.
    /// Rebuild only the label's noneditable Parley layout, not the document.
    pub fn calyra_set_select_selection"""
    )

    replace_exact(
        root, "packages/blitz-dom/src/document.rs",
        """        let scale = self.viewport.scale_f64() as f32;
        let data = self.nodes[select_id].element_data_mut().unwrap()
            .select_data_mut().unwrap();
        data.selected_option = selected;
        data.label = label.clone();""",
        """        let scale = self.viewport.scale_f64() as f32;
        let fingerprint = self.calyra_select_typography_fingerprint(select_id).unwrap_or_default();
        let data = self.nodes[select_id].element_data_mut().unwrap()
            .select_data_mut().unwrap();
        data.selected_option = selected;
        data.label = label.clone();
        data.typography_fingerprint = fingerprint;"""
    )

    replace_exact(
        root, "packages/blitz-dom/src/resolve.rs",
        """        self.resolve_stylist(current_time_for_animations);
        timer.record_time("style");""",
        """        self.resolve_stylist(current_time_for_animations);
        // CALYRA Stage A: regenerate a noneditable select glyph layout only
        // when CSS-computed typography changes (not every frame).
        self.calyra_refresh_select_typography_after_restyle();
        timer.record_time("style");"""
    )

    print("CALYRA_TYPOGRAPHY_PATCH_COMPLETE=1")


if __name__ == "__main__":
    main()
