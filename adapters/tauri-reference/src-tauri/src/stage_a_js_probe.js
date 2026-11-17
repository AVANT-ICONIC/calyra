// Executed ONLY by the opt-in Rust Stage A macOS probe, via real WKWebView eval.
// Original fixtures/reference.js is never patched, imported or copied here.
(() => {
  const assertions = [];
  const report = {
    schema: "calyra.tauri-macos-native-js.v1",
    fixture: new URLSearchParams(location.search).get("fixture"),
    url: location.href,
    protocol: location.protocol,
    user_agent: navigator.userAgent,
    viewport_css_px: [innerWidth, innerHeight],
    device_pixel_ratio: devicePixelRatio,
    document_ready: document.readyState,
    assertions,
    pass: false
  };
  const check = (name, actual, expected) => {
    assertions.push({ name, actual, expected, pass: actual === expected });
  };
  const el = id => {
    const found = document.getElementById(id);
    if (!found) throw new Error("Missing canonical fixture element: " + id);
    return found;
  };
  try {
    check("original_js_ready", document.body.dataset.ready, "true");
    check("canonical_active_section",
      document.querySelector(".case.active")?.dataset.case, report.fixture);
    check("native_webkit_user_agent", /AppleWebKit/.test(navigator.userAgent), true);

    if (report.fixture === "controls") {
      const name = el("person-name");
      const priority = el("priority");
      const intensity = el("intensity");
      const output = el("intensity-output");
      const effects = el("effects");
      const status = el("action-status");

      check("initial_name", name.value, "Alex Rivera");
      check("initial_select", priority.value, "balanced");
      check("initial_slider", intensity.value, "64");
      check("initial_status", status.value, "Ready for input");

      name.value = "Calyra macOS JS";
      priority.value = "quality";
      intensity.value = "73";
      intensity.dispatchEvent(new Event("input", { bubbles: true }));
      effects.checked = false;
      check("slider_original_input_handler", output.value, "73%");
      el("apply").click();
      check("apply_original_click_handler", status.value,
        "Applied: Calyra macOS JS · quality · 73% · off");
      el("reset").click();
      check("reset_original_click_handler", status.value, "Settings reset");
      check("reset_name", name.value, "Alex Rivera");
      check("reset_select", priority.value, "balanced");
      check("reset_slider", intensity.value, "64");
      check("reset_slider_output", output.value, "64%");
      check("reset_checkbox", effects.checked, true);

    } else if (report.fixture === "interaction") {
      const menu = el("menu-toggle");
      const popover = el("menu-popover");
      const status = el("interaction-status");

      check("initial_menu_closed", popover.hidden, true);
      menu.click();
      check("menu_opens", popover.hidden, false);
      check("menu_aria_expanded", menu.getAttribute("aria-expanded"), "true");
      check("menu_command_focus", document.activeElement?.dataset.command, "inspect");

      document.dispatchEvent(new KeyboardEvent("keydown",
        { key: "Escape", bubbles: true, cancelable: true }));
      check("document_escape_handler", popover.hidden, true);
      check("escape_restores_focus", document.activeElement?.id, "menu-toggle");

      menu.click();
      popover.querySelector('[data-command="inspect"]').click();
      check("command_original_click_handler", status.value, "Command: inspect");
      check("command_closes_menu", popover.hidden, true);

      el("focus-target").click();
      check("focus_target_original_click_handler", document.activeElement?.id,
        "destination");
      check("focus_status_original_click_handler", status.value,
        "Destination focused");

      const scroll = el("scroll-region");
      scroll.scrollTop = 120;
      check("programmatic_scroll", scroll.scrollTop > 0, true);
    } else {
      throw new Error("Unexpected fixture for native Tauri probe: " + report.fixture);
    }
  } catch (error) {
    report.exception = String(error?.stack || error);
  }
  report.pass = !report.exception &&
    assertions.length >= 10 && assertions.every(assertion => assertion.pass);
  return report;
})()
