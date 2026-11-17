#!/usr/bin/env python3
"""CALYRA: source-pinned, opt-in native AccessKit form semantics experiment.

Applies only to a disposable exact-revision upstream Blitz 0.3.0-beta.4
checkout AFTER the previously verified SelectData patches. It changes
generic AX node construction, never authored CALYRA HTML/CSS/JS or controls.
This is not complete HTML-AAM, accessible action routing or a range widget.
"""
from pathlib import Path
import argparse

TARGET = "packages/blitz-dom/src/accessibility.rs"

HELPERS = r'''
    /// CALYRA AX experiment: collect descendant visible text without including
    /// aria-hidden ornamental spans. Not a complete HTML accessible-name algorithm.
    fn calyra_ax_visible_text(&self, node: &BlitzDomNode, out: &mut FlatText) {
        if node.attr(local_name!("aria-hidden")) == Some("true") {
            return;
        }
        match &node.data {
            NodeData::Text(data) => out.push(&data.content),
            NodeData::Element(..) | NodeData::AnonymousBlock(..) => {
                for child_id in &node.children {
                    if let Some(child) = self.get_node(*child_id) {
                        self.calyra_ax_visible_text(child, out);
                    }
                }
            }
            _ => {}
        }
    }

    /// Only the common HTML 'label for', enclosing 'label', and native button
    /// text cases. Preserve aria-label and aria-labelledby precedence elsewhere.
    fn calyra_ax_associated_name(&self, node: &BlitzDomNode) -> Option<String> {
        let element = node.element_data()?;
        let is_control = matches!(
            &*element.name.local,
            "input" | "select" | "textarea" | "button"
        );
        if !is_control {
            return None;
        }
        let mut text = FlatText::default();
        if let Some(target) = node.attr(local_name!("id")) {
            self.visit(|_, maybe_label| {
                if text.text.is_empty()
                    && maybe_label
                        .element_data()
                        .is_some_and(|el| el.name.local == local_name!("label"))
                    && maybe_label.attr(local_name!("for")) == Some(target)
                {
                    self.calyra_ax_visible_text(maybe_label, &mut text);
                }
            });
        }
        if text.text.is_empty() {
            let mut ancestor = node.parent;
            while let Some(parent_id) = ancestor {
                let Some(parent) = self.get_node(parent_id) else {
                    break;
                };
                if parent.data.is_element_with_tag_name(&local_name!("label")) {
                    self.calyra_ax_visible_text(parent, &mut text);
                    break;
                }
                ancestor = parent.parent;
            }
        }
        if text.text.is_empty() && element.name.local == local_name!("button") {
            self.calyra_ax_visible_text(node, &mut text);
        }
        if text.text.is_empty() { None } else { Some(text.text) }
    }

    /// Record already-available native input state. For type=range, Blitz has
    /// no live RangeInput special data at this pinned revision: only the static
    /// attribute-derived value is exposed, which is NOT live range semantics.
    fn calyra_ax_form_state(&self, node: &BlitzDomNode, builder: &mut AccessKitNode) {
        let Some(el) = node.element_data() else { return };
        if el.name.local == local_name!("select") {
            if let Some(data) = el.select_data() {
                builder.set_value(data.label.clone());
            }
        } else if el.name.local == local_name!("input") {
            match el.attr(local_name!("type")).unwrap_or("text") {
                "checkbox" | "radio" => {
                    let checked = el.checkbox_input_checked()
                        .unwrap_or(el.has_attr(local_name!("checked")));
                    builder.set_toggled(if checked {
                        accesskit::Toggled::True
                    } else {
                        accesskit::Toggled::False
                    });
                    // The native AX adapter should derive the checkbox state
                    // from toggled. Confirm both role and AXValue on macOS.
                }
                "range" => {
                    let minimum = el.attr_parsed::<f64>(local_name!("min"))
                        .filter(|v| v.is_finite())
                        .unwrap_or(0.0);
                    let maximum = el.attr_parsed::<f64>(local_name!("max"))
                        .filter(|v| v.is_finite() && *v >= minimum)
                        .unwrap_or(100.0_f64.max(minimum));
                    let value = el.attr_parsed::<f64>(local_name!("value"))
                        .filter(|v| v.is_finite())
                        .unwrap_or((minimum + maximum) / 2.0)
                        .clamp(minimum, maximum);
                    builder.set_value(value.to_string());
                    builder.set_numeric_value(value);
                    builder.set_min_numeric_value(minimum);
                    builder.set_max_numeric_value(maximum);
                }
                _ => {
                    if let Some(data) = el.text_input_data() {
                        builder.set_value(data.editor.raw_text().to_string());
                    } else if let Some(initial) = el.attr(local_name!("value")) {
                        builder.set_value(initial);
                    }
                }
            }
        } else if el.name.local == local_name!("textarea") {
            if let Some(data) = el.text_input_data() {
                builder.set_value(data.editor.raw_text().to_string());
            }
        }
    }

'''

def apply(root: Path) -> None:
    path = root / TARGET
    original = path.read_text(encoding="utf-8")
    anchor = "    fn referenced_dom_ids_to_node_ids<'a>(\n"
    if original.count(anchor) != 1:
        raise AssertionError(f"{TARGET}: helper insertion anchor count {original.count(anchor)}")
    updated = original.replace(anchor, HELPERS + anchor, 1)
    old = '''            if let Some(aria_label) = element_data.attr(local_name!("aria-label")) {
                builder.set_label(aria_label);
            }
            if let Some(aria_description) = element_data.attr(local_name!("aria-description")) {'''
    new = '''            if let Some(aria_label) = element_data.attr(local_name!("aria-label")) {
                builder.set_label(aria_label);
            } else if element_data.attr(local_name!("aria-labelledby")).is_none() {
                if let Some(native_name) = self.calyra_ax_associated_name(node) {
                    builder.set_label(native_name);
                }
            }
            self.calyra_ax_form_state(node, &mut builder);
            if let Some(aria_description) = element_data.attr(local_name!("aria-description")) {'''
    if updated.count(old) != 1:
        raise AssertionError(f"{TARGET}: node insertion anchor count {updated.count(old)}")
    updated = updated.replace(old, new, 1)
    path.write_text(updated, encoding="utf-8")
    print(f"CALYRA_AX_FORM_SEMANTICS_PATCHED={TARGET}")
    print("CALYRA_AX_FORM_SEMANTICS_STATIC_RANGE_ONLY=1")
    print("CALYRA_AX_FORM_SEMANTICS_ACTIONS_NOT_IMPLEMENTED=1")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    root = parser.parse_args().source.resolve()
    if not (root / "packages/blitz-dom/src/accessibility.rs").is_file():
        raise FileNotFoundError("expected pinned upstream Blitz checkout")
    apply(root)

if __name__ == "__main__":
    main()
