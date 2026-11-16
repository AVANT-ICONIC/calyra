#!/usr/bin/env python3
"""CALYRA one-shot, fail-closed source patch for a read-only native select.

Applies ONLY to the pinned, clean Blitz checkout after the six documented
baseline patches. The exact resulting git diff is archived by the CI workflow.
This is an experimental compatibility probe, not a general select widget.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_exact(contents: str, old: str, new: str, path: str) -> str:
    count = contents.count(old)
    if count != 1:
        raise AssertionError(f"{path}: expected one anchor, found {count}: {old[:95]!r}")
    return contents.replace(old, new, 1)


def apply(root: Path, rel: str, edits: list[tuple[str, str]]) -> None:
    file = root / rel
    original = file.read_text(encoding="utf-8")
    changed = original
    for old, new in edits:
        changed = replace_exact(changed, old, new, rel)
    assert changed != original, rel
    file.write_text(changed, encoding="utf-8")
    print(f"CALYRA_READONLY_PATCHED={rel}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    root = args.source.resolve()
    assert (root / "packages/blitz-dom/src/node/text.rs").is_file()
    assert (root / "packages/blitz-paint/src/render.rs").is_file()

    apply(root, "packages/blitz-dom/src/node/text.rs", [(
        "pub struct TextInputData {",
        """/// CALYRA Stage A: a noneditable selected-option label and current selection.
#[derive(Clone, Default)]
pub struct SelectData {
    pub selected_option: Option<NodeId>,
    pub label: String,
    pub layout: parley::layout::Layout<TextBrush>,
}

pub struct TextInputData {"""
    )])

    apply(root, "packages/blitz-dom/src/node/mod.rs", [(
        "pub use text::{GeneratedTextInputEvent, INLINE_BOX_CHAR, TextBrush, TextInputData, TextLayout};",
        "pub use text::{GeneratedTextInputEvent, INLINE_BOX_CHAR, SelectData, TextBrush, TextInputData, TextLayout};"
    )])

    apply(root, "packages/blitz-dom/src/node/element.rs", [
        ("use crate::node::{TextBrush, TextInputData, TextLayout};",
         "use crate::node::{SelectData, TextBrush, TextInputData, TextLayout};"),
        ("""    /// Parley text editor (text inputs)
    TextInput(TextInputData),
    /// Checkbox checked state""",
         """    /// Parley text editor (text inputs)
    TextInput(TextInputData),
    /// Read-only selected-option label (no editor, caret, clipboard or IME).
    Select(SelectData),
    /// Checkbox checked state"""),
        ("""            Self::TextInput(data) => Self::TextInput(data.clone()),
            Self::CheckboxInput(data)""",
         """            Self::TextInput(data) => Self::TextInput(data.clone()),
            Self::Select(data) => Self::Select(data.clone()),
            Self::CheckboxInput(data)"""),
        ("""    pub fn text_input_data(&self) -> Option<&TextInputData> {""",
         """    pub fn select_data(&self) -> Option<&SelectData> {
        match &self.special_data {
            SpecialElementData::Select(data) => Some(data),
            _ => None,
        }
    }

    pub fn select_data_mut(&mut self) -> Option<&mut SelectData> {
        match &mut self.special_data {
            SpecialElementData::Select(data) => Some(data),
            _ => None,
        }
    }

    pub fn text_input_data(&self) -> Option<&TextInputData> {"""),
        ("""            SpecialElementData::TextInput(_) => f.write_str("NodeSpecificData::TextInput"),""",
         """            SpecialElementData::TextInput(_) => f.write_str("NodeSpecificData::TextInput"),
            SpecialElementData::Select(_) => f.write_str("NodeSpecificData::Select"),""")
    ])

    apply(root, "packages/blitz-dom/src/layout/construct.rs", [(
        """        #[cfg(feature = "svg")]
        if matches!(tag_name, "svg") {""",
        """        // CALYRA Stage A: create a native read-only label, never TextInputData.
        if tag_name == "select" {
            create_select_label(doc, container_node_id);
            return;
        }

        #[cfg(feature = "svg")]
        if matches!(tag_name, "svg") {"""
    ), (
        "fn create_text_editor(doc: &mut BaseDocument, input_element_id: NodeId, is_multiline: bool) {",
        """fn create_select_label(doc: &mut BaseDocument, select_id: NodeId) {
    // Initial current selection uses the final selected attribute, or first direct
    // option. Subsequent reconstruction keeps the native current selection.
    let (selected, already_created) = {
        let select = &doc.nodes[select_id];
        let existing = select.element_data().and_then(|el| el.select_data());
        let selected = if let Some(data) = existing {
            data.selected_option
        } else {
            let options: Vec<NodeId> = select.children.iter().copied().filter(|id| {
                doc.get_node(*id).is_some_and(|node|
                    node.data.is_element_with_tag_name(&local_name!("option")))
            }).collect();
            options.iter().copied().rev().find(|id| {
                doc.get_node(*id).is_some_and(|node|
                    node.attr(local_name!("selected")).is_some())
            }).or_else(|| options.first().copied())
        };
        (selected, existing.is_some())
    };
    if !already_created {
        doc.nodes[select_id].element_data_mut().unwrap().special_data =
            SpecialElementData::Select(crate::node::SelectData::default());
    }
    doc.calyra_set_select_selection(select_id, selected);
}

fn create_text_editor(doc: &mut BaseDocument, input_element_id: NodeId, is_multiline: bool) {"""
    )])

    apply(root, "packages/blitz-dom/src/document.rs", [(
        """    pub fn get_focussed_node_id(&self) -> Option<NodeId> {""",
        """    /// CALYRA Stage A: selectedness lives on the native DOM select.
    /// Rebuild only the label's noneditable Parley layout, not the document.
    pub fn calyra_set_select_selection(&mut self, select_id: NodeId, selected: Option<NodeId>) {
        let Some(select_node) = self.nodes.get(select_id) else { return };
        if select_node.element_data().and_then(|el| el.select_data()).is_none() {
            return;
        }
        let label = selected.and_then(|id| self.nodes.get(id))
            .map(|node| node.text_content().trim().to_string())
            .unwrap_or_default();
        let text_style = select_node.primary_styles()
            .as_ref()
            .map(|s| crate::stylo_to_parley::style(select_id, s))
            .unwrap_or_default();
        let direction = select_node.primary_styles().as_ref().map(|s|
            crate::stylo_to_parley::base_direction(
                s.clone_direction(), s.clone_unicode_bidi()
            ));
        let scale = self.viewport.scale_f64() as f32;
        let data = self.nodes[select_id].element_data_mut().unwrap()
            .select_data_mut().unwrap();
        data.selected_option = selected;
        data.label = label.clone();

        let mut fonts = self.font_ctx.lock().unwrap();
        let mut builder = self.layout_ctx.tree_builder(
            &mut fonts, scale, true, &text_style
        );
        if let Some(direction) = direction {
            builder.set_base_direction(direction);
        }
        builder.push_text(&label);
        builder.build_into(&mut data.layout);
        data.layout.break_all_lines(None);
        self.shell_provider.request_redraw();
    }

    pub fn get_focussed_node_id(&self) -> Option<NodeId> {"""
    )])

    apply(root, "packages/blitz-paint/src/render.rs", [
        ("""    ListItemLayout, ListItemLayoutPosition, Marker, NodeData, RasterImageData, TextInputData,
    TextNodeData,""",
         """    ListItemLayout, ListItemLayoutPosition, Marker, NodeData, RasterImageData, SelectData,
    TextInputData, TextNodeData,"""),
        ("""                || element.and_then(|e| e.text_input_data()).is_some()
                || contain_paint""",
         """                || element.and_then(|e| e.text_input_data()).is_some()
                || element.and_then(|e| e.select_data()).is_some()
                || contain_paint"""),
        ("""                                cx.draw_text_input_text(scene, content_position);
                                cx.draw_inline_layout(scene, content_position);""",
         """                                cx.draw_text_input_text(scene, content_position);
                                cx.draw_select_label(scene, content_position);
                                cx.draw_inline_layout(scene, content_position);"""),
        ("""            text_input: element.text_input_data(),
            list_item: element.list_item_data.as_deref(),""",
         """            text_input: element.text_input_data(),
            select_data: element.select_data(),
            list_item: element.list_item_data.as_deref(),"""),
        ("""    text_input: Option<&'dom TextInputData>,
    list_item: Option<&'dom ListItemLayout>,""",
         """    text_input: Option<&'dom TextInputData>,
    select_data: Option<&'dom SelectData>,
    list_item: Option<&'dom ListItemLayout>,"""),
        ("""    fn draw_marker(&self, scene: &mut impl PaintScene, pos: Point) {""",
         """    fn draw_select_label(&self, scene: &mut impl PaintScene, pos: Point) {
        let Some(select) = self.select_data else { return };
        // Reuse the native glyph painter only. Unlike the TextInput path,
        // no editor exists to render or accept a caret, selection or IME.
        let content_height = self.node.final_layout().content_box_height();
        let label_height = select.layout.height() / self.scale as f32;
        let y_offset = ((content_height - label_height) / 2.0).max(0.0);
        let transform = self.transform * Affine::translate((
            pos.x * self.scale,
            (pos.y + y_offset as f64) * self.scale,
        ));
        let mut draw_ctx = self.context.draw_text_context.borrow_mut();
        crate::text::stroke_text(
            scene, select.layout.lines(), self.context.dom, transform,
            TextPaintOptions { scale: self.scale, brush_override: None },
            self.node.id, &mut draw_ctx,
        );
    }

    fn draw_marker(&self, scene: &mut impl PaintScene, pos: Point) {""")
    ])
    print("CALYRA_READONLY_PATCH_COMPLETE=1")


if __name__ == "__main__":
    main()
