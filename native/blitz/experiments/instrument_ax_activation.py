#!/usr/bin/env python3
"""Add diagnostic-only AccessKit event and tree-built logs to pinned Blitz.

For disposable upstream checkout only. Source anchors are exact and fail closed.
No tree/value/focus behavior changes, no fake accessibility nodes or OS actions.
"""
from pathlib import Path
import argparse

def replace_once(root: Path, rel: str, old: str, new: str) -> None:
    path = root / rel
    contents = path.read_text(encoding="utf-8")
    if contents.count(old) != 1:
        raise AssertionError(f"{rel}: expected one anchor, got {contents.count(old)}")
    path.write_text(contents.replace(old, new, 1), encoding="utf-8")
    print(f"CALYRA_AX_INSTRUMENTED_FILE={rel}")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    root = parser.parse_args().source.resolve()
    replace_once(
        root, "packages/blitz-shell/src/accessibility.rs",
        """    fn handle_accesskit_event(&self, event: AccessKitEvent) {
        self.proxy.send_event(BlitzShellEvent::Accessibility {""",
        """    fn handle_accesskit_event(&self, event: AccessKitEvent) {
        let kind = match &event {
            AccessKitEvent::InitialTreeRequested => "InitialTreeRequested",
            AccessKitEvent::AccessibilityDeactivated => "AccessibilityDeactivated",
            AccessKitEvent::ActionRequested(_) => "ActionRequested",
        };
        eprintln!("CALYRA_AX_BACKEND_EVENT_RECEIVED={kind}");
        self.proxy.send_event(BlitzShellEvent::Accessibility {""",
    )
    replace_once(
        root, "packages/blitz-shell/src/accessibility.rs",
        """    pub fn update_tree(&mut self, doc: &BaseDocument) {
        let _ = doc;
        self.adapter
            .update_if_active(|| doc.build_accessibility_tree());
    }""",
        """    pub fn update_tree(&mut self, doc: &BaseDocument) {
        eprintln!("CALYRA_AX_UPDATE_IF_ACTIVE_CALLED");
        self.adapter.update_if_active(|| {
            let tree = doc.build_accessibility_tree();
            eprintln!("CALYRA_AX_TREE_ACTUALLY_BUILT_NODES={}", tree.nodes.len());
            tree
        });
        eprintln!("CALYRA_AX_UPDATE_IF_ACTIVE_RETURNED");
    }""",
    )
    replace_once(
        root, "packages/blitz-shell/src/application.rs",
        """                        accesskit_xplat::WindowEvent::InitialTreeRequested => {
                            window.build_accessibility_tree();
                        }""",
        """                        accesskit_xplat::WindowEvent::InitialTreeRequested => {
                            eprintln!("CALYRA_AX_INITIAL_TREE_EVENT_DISPATCHED");
                            window.build_accessibility_tree();
                        }""",
    )
    print("CALYRA_AX_INSTRUMENTATION_LOG_ONLY=1")

if __name__ == "__main__":
    main()
