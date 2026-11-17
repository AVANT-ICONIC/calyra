#!/usr/bin/env python3
"""Fail-closed isolated native range state/painter/Boa/AX research patch.

Applies after CALYRA's pinned SelectData + accessible-form-semantic patches,
ONLY in a disposable exact upstream Blitz checkout. No authored fixture edits.
"""
import argparse
from pathlib import Path

def change(root, rel, pairs):
    path=root / rel
    s=path.read_text(encoding="utf-8")
    original=s
    for old,new in pairs:
        count=s.count(old)
        if count!=1:
            raise AssertionError(f"{rel}: expected single anchor, got {count}: {old[:100]!r}")
        s=s.replace(old,new,1)
    assert original!=s,rel
    path.write_text(s,encoding="utf-8")
    print(f"CALYRA_RANGE_PATCHED={rel}")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    root=parser.parse_args().source.resolve()
    assert (root/"packages/blitz-dom/src/accessibility.rs").is_file()
    assert (root/"packages/blitz-dom/src/node/element.rs").read_text().count("Select(SelectData)")>=1
    assert (root/"packages/blitz-dom/src/accessibility.rs").read_text().count("fn calyra_ax_form_state") ==1

    change(root,"packages/blitz-dom/src/node/mod.rs",[
        ("mod text;\n","mod text;\nmod range;\n"),
        ("pub use text::{GeneratedTextInputEvent, INLINE_BOX_CHAR, SelectData, TextBrush, TextInputData, TextLayout};",
         "pub use text::{GeneratedTextInputEvent, INLINE_BOX_CHAR, SelectData, TextBrush, TextInputData, TextLayout};\npub use range::RangeData;"),
    ])
    # A real native DOM data type and no editor, caret or duplicate JS state.
    change(root,"packages/blitz-dom/src/node/element.rs",[
        ("use crate::node::{SelectData, TextBrush, TextInputData, TextLayout};",
         "use crate::node::{RangeData, SelectData, TextBrush, TextInputData, TextLayout};"),
        ("""    Select(SelectData),
    /// Checkbox checked state""",
         """    Select(SelectData),
    /// One native numeric range value, separate from HTML defaultValue.
    Range(RangeData),
    /// Checkbox checked state"""),
        ("""            Self::Select(data) => Self::Select(data.clone()),
            Self::CheckboxInput(data)""",
         """            Self::Select(data) => Self::Select(data.clone()),
            Self::Range(data) => Self::Range(data.clone()),
            Self::CheckboxInput(data)"""),
        ("""    pub fn select_data(&self) -> Option<&SelectData> {""",
         """    pub fn range_data(&self) -> Option<&RangeData> {
        match &self.special_data {
            SpecialElementData::Range(data) => Some(data),
            _ => None,
        }
    }

    pub fn range_data_mut(&mut self) -> Option<&mut RangeData> {
        match &mut self.special_data {
            SpecialElementData::Range(data) => Some(data),
            _ => None,
        }
    }

    pub fn select_data(&self) -> Option<&SelectData> {"""),
        ("""            SpecialElementData::Select(_) => f.write_str("NodeSpecificData::Select"),""",
         """            SpecialElementData::Select(_) => f.write_str("NodeSpecificData::Select"),
            SpecialElementData::Range(_) => f.write_str("NodeSpecificData::Range"),""")
    ])
    change(root,"packages/blitz-dom/src/layout/construct.rs",[
        ("""            } else if matches!(type_attr, Some("checkbox" | "radio")) {
                create_checkbox_input(doc, container_node_id);
                return;
            }
        }""",
         """            } else if matches!(type_attr, Some("checkbox" | "radio")) {
                create_checkbox_input(doc, container_node_id);
                return;
            } else if matches!(type_attr, Some("range")) {
                create_range_input(doc, container_node_id);
                return;
            }
        }"""),
        ("""fn create_checkbox_input(doc: &mut BaseDocument, input_element_id: NodeId) {""",
         """fn create_range_input(doc: &mut BaseDocument, id: NodeId) {
    let el = doc.nodes[id].element_data_mut().unwrap();
    if el.range_data().is_none() {
        // Only the first construction may initialize current from attributes.
        // Subsequent layout/CSS reconstruction must preserve live currentValue.
        let data = crate::node::RangeData::from_element(el);
        el.special_data = SpecialElementData::Range(data);
    }
}

fn create_checkbox_input(doc: &mut BaseDocument, input_element_id: NodeId) {""")
    ])
    change(root,"packages/blitz-dom/src/document.rs",[
        ("""    pub fn get_focussed_node_id(&self) -> Option<NodeId> {""",
         """    /// CALYRA experimental native range current state mutation.
    /// Native state is not the value HTML attribute/defaultValue. Programmatic
    /// writes never dispatch synthetic input/change user events.
    pub fn calyra_set_range_current(&mut self, id: NodeId, raw: &str) -> bool {
        let changed = self.nodes.get_mut(id)
            .and_then(|node| node.element_data_mut())
            .and_then(|el| el.range_data_mut())
            .is_some_and(|data| data.set_current(raw));
        if changed {
            self.has_changes = true;
            self.nodes[id].insert_damage(ALL_DAMAGE);
            self.nodes[id].mark_ancestors_dirty();
            self.shell_provider.request_redraw();
        }
        changed
    }

    pub fn get_focussed_node_id(&self) -> Option<NodeId> {""")
    ])
    change(root,"packages/blitz-dom/src/mutator.rs",[
        ("""                SpecialElementData::Select(_) => {}
                SpecialElementData::CheckboxInput(_) => {}""",
         """                SpecialElementData::Select(_) => {}
                SpecialElementData::Range(_) => {}
                SpecialElementData::CheckboxInput(_) => {}""")
    ])
    # Painter only draws after the native DOM RangeData actually exists.
    # Track and thumb geometry derive from the real computed border box + state.
    change(root,"packages/blitz-paint/src/render/form_controls.rs",[
        ("""        let Some(checked) = self.element.checkbox_input_checked() else {
            return;
        };

        let type_attr = self.node.attr(local_name!("type"));""",
         """        let type_attr = self.node.attr(local_name!("type"));
        if type_attr == Some("range") {
            if let Some(range) = self.element.range_data() {
                let border = self.frame.border_box;
                let width = border.width();
                let height = border.height();
                if width > 2.0 && height > 2.0 {
                    let radius = (height * 0.34).clamp(5.0, 9.0);
                    let left = border.x0 + radius;
                    let right = (border.x1 - radius).max(left);
                    let middle = border.center().y;
                    let line_height = (height * 0.16).clamp(2.0, 5.0);
                    let line = kurbo::Rect::new(left, middle - line_height / 2.0,
                        right, middle + line_height / 2.0).to_rounded_rect(line_height / 2.0);
                    let x = left + (right - left) * range.progress();
                    let progress_line = kurbo::Rect::new(left, middle - line_height / 2.0,
                        x.max(left), middle + line_height / 2.0)
                        .to_rounded_rect(line_height / 2.0);
                    let accent = if self.node.attr(local_name!("disabled")).is_some() {
                        Color::from_rgba8(150, 150, 150, 255)
                    } else {
                        self.style.clone_color().as_srgb_color()
                    };
                    scene.fill(Fill::NonZero, self.transform,
                        Color::from_rgba8(108, 117, 131, 255),
                        None, &line, AntiAliasing::Enabled);
                    if x > left {
                        scene.fill(Fill::NonZero, self.transform, accent,
                            None, &progress_line, AntiAliasing::Enabled);
                    }
                    let thumb = Circle::new(Point::new(x, middle), radius);
                    scene.fill(Fill::NonZero, self.transform,
                        Color::WHITE, None, &thumb, AntiAliasing::Enabled);
                    scene.stroke(&Stroke { width: 1.5, ..Stroke::default() },
                        self.transform, accent, None, &thumb, AntiAliasing::Enabled);
                }
            }
            return;
        }
        let Some(checked) = self.element.checkbox_input_checked() else {
            return;
        };""")
    ])
    # Bridge into the actual current DOM state; no duplicate JS map, no event synthesis.
    change(root,"packages/blitz-vibey-script/src/dom/element/form_controls.rs",[
        ("""    let value = {
        let doc = ctx.doc.borrow();""",
         """    // Native RangeData is the single current value authority. The
    // raw HTML 'value' attribute remains the defaultValue, not live state.
    let current_range_value = {
        let doc = ctx.doc.borrow();
        doc.get_node(node_id)
            .and_then(|node| node.element_data())
            .and_then(|el| el.range_data())
            .map(|range| range.value_text())
    };
    if let Some(value) = current_range_value {
        return Ok(js_str(&value));
    }
    let value = {
        let doc = ctx.doc.borrow();"""),
        ("""    attr_setter("value", this, args, context)
}

pub(super) fn get_checked(""",
         """    let value = crate::dom::to_rust_string(
        args.first().unwrap_or(&JsValue::undefined()), context)?;
    let range_id = {
        let ctx = dom_ctx(context)?;
        let id = this_node_id(this)?;
        let is_range = ctx.doc.borrow().get_node(id)
            .and_then(|node| node.element_data())
            .and_then(|el| el.range_data())
            .is_some();
        if is_range { Some(id) } else { None }
    };
    if let Some(id) = range_id {
        let ctx = dom_ctx(context)?;
        ctx.doc.borrow_mut().calyra_set_range_current(id, &value);
        return Ok(JsValue::undefined());
    }
    attr_setter("value", this, args, context)
}

pub(super) fn get_checked(""")
    ])
    # This patch is applied after apply_ax_form_semantics.py, preserving names.
    path=root/"packages/blitz-dom/src/accessibility.rs"
    s=path.read_text(encoding="utf-8")
    start=s.index('                "range" => {',s.index("fn calyra_ax_form_state"))
    end=s.index('                _ => {',start)
    old=s[start:end]
    new='''                "range" => {
                    if let Some(range) = el.range_data() {
                        builder.set_value(range.value_text());
                        builder.set_numeric_value(range.value);
                        builder.set_min_numeric_value(range.minimum);
                        builder.set_max_numeric_value(range.maximum);
                    }
                }
'''
    assert old.count("builder.set_numeric_value(value)") == 1
    s=s[:start]+new+s[end:]
    path.write_text(s,encoding="utf-8")
    print("CALYRA_RANGE_PATCHED=packages/blitz-dom/src/accessibility.rs")
    print("CALYRA_RANGE_MODEL_NO_TEXT_EDITOR=1")
    print("CALYRA_RANGE_OS_POINTER_KEYBOARD_NOT_IMPLEMENTED=1")
    print("CALYRA_RANGE_PROGRAMMATIC_EVENTS_NOT_DISPATCHED=1")

if __name__=="__main__":
    main()
