"use strict";
(function () {
  const query = new URLSearchParams(window.__calyraFixtureQuery || location.search);
  const allowed = new Set(["controls", "dashboard", "visual", "interaction"]);
  const fixture = allowed.has(query.get("fixture")) ? query.get("fixture") : "controls";
  if (query.get("motion") === "off") document.documentElement.dataset.motion = "off";
  document.body.dataset.fixture = fixture;
  for (const section of document.querySelectorAll("[data-case]")) {
    const current = section.dataset.case === fixture;
    section.classList.toggle("active", current);
    section.hidden = !current;
  }
  for (const link of document.querySelectorAll("[data-link]")) {
    if (link.dataset.link === fixture) link.setAttribute("aria-current", "page");
  }
  const name = document.getElementById("person-name");
  const priority = document.getElementById("priority");
  const intensity = document.getElementById("intensity");
  const intensityOutput = document.getElementById("intensity-output");
  const effects = document.getElementById("effects");
  const status = document.getElementById("action-status");
  intensity.addEventListener("input", () => { intensityOutput.value = `${intensity.value}%`; });
  document.getElementById("apply").addEventListener("click", () => {
    status.value = `Applied: ${name.value.trim() || "Anonymous"} · ${priority.value} · ${intensity.value}% · ${effects.checked ? "on" : "off"}`;
  });
  document.getElementById("reset").addEventListener("click", () => {
    name.value = "Alex Rivera"; priority.value = "balanced"; intensity.value = "64"; intensityOutput.value = "64%"; effects.checked = true; status.value = "Settings reset";
  });
  const toggle = document.getElementById("menu-toggle");
  const popover = document.getElementById("menu-popover");
  const iStatus = document.getElementById("interaction-status");
  function setMenu(open) {
    popover.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    iStatus.value = open ? "Menu open" : "Menu closed";
    if (open) popover.querySelector("button").focus();
    else toggle.focus();
  }
  toggle.addEventListener("click", () => setMenu(popover.hidden));
  for (const command of popover.querySelectorAll("[data-command]")) {
    command.addEventListener("click", () => { const action = command.dataset.command; setMenu(false); iStatus.value = `Command: ${action}`; });
  }
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !popover.hidden) { event.preventDefault(); setMenu(false); }
  });
  document.getElementById("focus-target").addEventListener("click", () => {
    document.getElementById("destination").focus(); iStatus.value = "Destination focused";
  });
  if (query.get("state") === "menu-open" && fixture === "interaction") setMenu(true);
  document.body.dataset.ready = "true";
})();
