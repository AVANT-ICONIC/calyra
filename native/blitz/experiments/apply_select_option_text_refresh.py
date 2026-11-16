#!/usr/bin/env python3
"""CALYRA isolated Stage A adapter for selected <option> text mutations.

Apply *after* the existing six baseline Blitz patches and the verified
apply_readonly_select.py adapter, in a clean pinned disposable upstream tree.
This is a narrow Boa Node.textContent/nodeValue experiment, not a full
MutationObserver or production invalidation engine.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise AssertionError(f"{relative}: anchor count {count}, expected 1: {old[:90]!r}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")
    print(f"CALYRA_OPTION_TEXT_PATCHED={relative}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    root = parser.parse_args().source.resolve()

    document = "packages/blitz-dom/src/document.rs"
    node = "packages/blitz-vibey-script/src/dom/node.rs"
    assert (root / document).is_file() and (root / node).is_file()

    # Native DOM selection is authoritative. Recompute the generated label
    # only when the mutated option is currently selected and its visible
    # text actually changed. The JS setter already holds an exclusive
    # document borrow, so call only *after* its mutator has been released.
    replace_once(
        root, document,
        "    pub fn get_focussed_node_id(&self) -> Option<NodeId> {",
        """    /// CALYRA Stage A: targeted noneditable select-label text invalidation.
    /// Handles selected direct-option textContent and direct text-child
    /// nodeValue updates. It deliberately does not cover all DOM mutations.
    pub fn calyra_refresh_select_after_option_text_mutation(&mut self, node_id: NodeId) {
        let is_option = |id: NodeId| {
            self.nodes.get(id).is_some_and(|node|
                node.data.is_element_with_tag_name(&local_name!("option")))
        };
        let option_id = if is_option(node_id) {
            node_id
        } else {
            let Some(parent_id) = self.nodes.get(node_id).and_then(|node| node.parent) else {
                return;
            };
            if !is_option(parent_id) { return; }
            parent_id
        };
        let Some(select_id) = self.nodes.get(option_id).and_then(|node| node.parent) else {
            return;
        };
        let Some(select_node) = self.nodes.get(select_id) else { return; };
        if !select_node.data.is_element_with_tag_name(&local_name!("select")) {
            return;
        }
        let Some(select_data) = select_node.element_data().and_then(|el| el.select_data()) else {
            return;
        };
        // Never select a different option or reset an empty selection.
        if select_data.selected_option != Some(option_id) { return; }
        let new_label = self.nodes[option_id].text_content().trim().to_string();
        if select_data.label == new_label { return; }
        self.calyra_set_select_selection(select_id, Some(option_id));
    }

    pub fn get_focussed_node_id(&self) -> Option<NodeId> {"""
    )

    # Both JS entry points have an existing native DocumentMutator. Drop that
    # borrow before calling into the read-only Parley label update.
    replace_once(
        root, node,
        """            mutr.append_children(node_id, &[text_id]);
        }
    }
    Ok(JsValue::undefined())
}

fn node_value(""",
        """            mutr.append_children(node_id, &[text_id]);
        }
    }
    drop(mutr);
    doc.calyra_refresh_select_after_option_text_mutation(node_id);
    Ok(JsValue::undefined())
}

fn node_value("""
    )
    replace_once(
        root, node,
        """    doc.mutate().set_node_text(node_id, &text);
    Ok(JsValue::undefined())
}

// === Tree mutation ===""",
        """    doc.mutate().set_node_text(node_id, &text);
    doc.calyra_refresh_select_after_option_text_mutation(node_id);
    Ok(JsValue::undefined())
}

// === Tree mutation ==="""
    )
    print("CALYRA_OPTION_TEXT_PATCH_COMPLETE=1")


if __name__ == "__main__":
    main()
