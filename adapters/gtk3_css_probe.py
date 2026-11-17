"""Native Gtk3 CSS subset probe. GTK parses CSS via GtkCssProvider; no browser involved.

This is a diagnostic **native widget and CPU/composited GTK rendering** path,
NOT a GPU renderer, modern CSS parity, or a replacement for RmlUi/Blitz.

Run: xvfb-run -a python -m adapters.gtk3_css_probe --capture evidence/native-gtk3/probe.png
"""
from __future__ import annotations
import argparse
import ctypes as C
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import time

import tinycss2

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'fixtures' / 'reference.css'
V = C.c_void_p
B = C.c_char_p
I = C.c_int
UI = C.c_uint


def api(library, symbol, result, *arguments):
    fun = getattr(library, symbol)
    fun.restype = result
    fun.argtypes = list(arguments)
    return fun


def select_native_styles(path: Path = SOURCE):
    """Extract only a documented Gtk compatible subset from original authored CSS.

    These rules are ADAPTED: no full stylesheet or CSS layout compatibility claimed.
    """
    css = path.read_text(encoding='utf-8')
    rules = tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True)
    tokens = {}
    for rule in rules:
        if rule.type == 'qualified-rule' and tinycss2.serialize(rule.prelude).strip() == ':root':
            for declaration in tinycss2.parse_declaration_list(rule.content, skip_whitespace=True, skip_comments=True):
                if declaration.type == 'declaration' and declaration.name.startswith('--'):
                    tokens[declaration.name] = tinycss2.serialize(declaration.value).strip()
    for key in ('--bg', '--fg', '--muted', '--accent', '--line'):
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', tokens.get(key, '')):
            raise ValueError(f'Missing solid reference token: {key}')
    recognized = {'border', 'border-radius', 'padding', 'font-size', 'font-weight', 'background-color', 'color'}
    selector_decls, extracted = {}, []
    for rule in rules:
        if rule.type != 'qualified-rule':
            continue
        selector = tinycss2.serialize(rule.prelude).strip()
        if selector not in ('.action', '.action.primary', '.action.secondary'):
            continue
        lines = []
        for declaration in tinycss2.parse_declaration_list(rule.content, skip_whitespace=True, skip_comments=True):
            if declaration.type != 'declaration' or declaration.name not in recognized:
                continue
            value = tinycss2.serialize(declaration.value).strip()
            substituted = False
            for key, color in tokens.items():
                candidate = f'var({key})'
                if candidate in value:
                    value = value.replace(candidate, color)
                    substituted = True
            if 'var(' in value:
                continue
            lines.append(f'{declaration.name}: {value};')
            extracted.append({'selector': selector, 'property': declaration.name, 'value': value, 'token_substituted': substituted})
        if lines:
            selector_decls[selector] = lines
    if not extracted:
        raise ValueError('No supported style declarations found in source CSS')
    # Gtk draws and manages its own widgets. Layout is programmatic GtkBox, not CSS Grid/Flexbox.
    adapted = [
        'window { background-color: '+tokens['--bg']+'; color: '+tokens['--fg']+'; }',
        '.calyra-header { background-color: #121922; border-bottom: 1px solid '+tokens['--line']+'; padding: 23px; }',
        '.calyra-main { background-color: '+tokens['--bg']+'; padding: 32px; }',
        '.calyra-heading { font-size: 34px; font-weight: 700; color: '+tokens['--fg']+'; }',
        '.calyra-muted { font-size: 12px; color: '+tokens['--muted']+'; }',
        '.calyra-accent { font-weight: 700; color: '+tokens['--accent']+'; }',
        'entry, combobox, scale { color: '+tokens['--fg']+'; font-size: 13px; margin-top: 8px; margin-bottom: 16px; }',
        'entry { background-color: #181f28; border: 1px solid '+tokens['--line']+'; border-radius: 8px; padding: 9px; }',
        'button.action { padding: 12px 17px; }',
        'button.action.primary { background-color: '+tokens['--accent']+'; color: #141c11; border-color: '+tokens['--accent']+'; }',
        'button.action.secondary { background-color: #1b2630; color: '+tokens['--fg']+'; }',
    ]
    for selector, lines in selector_decls.items():
        adapted.append('button' + selector + ' { ' + ' '.join(lines) + ' }')
    return '\n'.join(adapted), tokens, extracted


class Gtk3NativeProbe:
    def __init__(self):
        if not os.environ.get('DISPLAY'):
            raise RuntimeError('Gtk3 native probe requires a real X11 display, e.g. xvfb-run -a')
        self.gtk = C.CDLL('libgtk-3.so.0')
        self.gdk = C.CDLL('libgdk-3.so.0')
        self.gobject = C.CDLL('libgobject-2.0.so.0')
        g = self.gtk
        self.gtk_init_check = api(g, 'gtk_init_check', I, V, V)
        if not self.gtk_init_check(None, None):
            raise RuntimeError('GTK could not initialize the X11 display')
        self.gtk_window_new = api(g, 'gtk_window_new', V, I)
        self.gtk_window_set_title = api(g, 'gtk_window_set_title', None, V, B)
        self.gtk_window_set_default_size = api(g, 'gtk_window_set_default_size', None, V, I, I)
        self.gtk_window_get_position = api(g, 'gtk_window_get_position', None, V, C.POINTER(I), C.POINTER(I))
        self.gtk_window_get_size = api(g, 'gtk_window_get_size', None, V, C.POINTER(I), C.POINTER(I))
        self.gtk_box_new = api(g, 'gtk_box_new', V, I, I)
        self.gtk_box_pack_start = api(g, 'gtk_box_pack_start', None, V, V, I, I, UI)
        self.gtk_container_add = api(g, 'gtk_container_add', None, V, V)
        self.gtk_widget_show_all = api(g, 'gtk_widget_show_all', None, V)
        self.gtk_widget_destroy = api(g, 'gtk_widget_destroy', None, V)
        self.gtk_widget_get_style_context = api(g, 'gtk_widget_get_style_context', V, V)
        self.gtk_style_context_add_class = api(g, 'gtk_style_context_add_class', None, V, B)
        self.gtk_style_context_add_provider_for_screen = api(g, 'gtk_style_context_add_provider_for_screen', None, V, V, UI)
        self.gdk_screen_get_default = api(self.gdk, 'gdk_screen_get_default', V)
        self.gtk_css_provider_new = api(g, 'gtk_css_provider_new', V)
        self.gtk_css_provider_load_from_data = api(g, 'gtk_css_provider_load_from_data', I, V, B, C.c_ssize_t, V)
        self.gtk_label_new = api(g, 'gtk_label_new', V, B)
        self.gtk_label_get_text = api(g, 'gtk_label_get_text', B, V)
        self.gtk_label_set_text = api(g, 'gtk_label_set_text', None, V, B)
        self.gtk_label_set_xalign = api(g, 'gtk_label_set_xalign', None, V, C.c_float)
        self.gtk_entry_new = api(g, 'gtk_entry_new', V)
        self.gtk_entry_set_text = api(g, 'gtk_entry_set_text', None, V, B)
        self.gtk_entry_get_text = api(g, 'gtk_entry_get_text', B, V)
        self.gtk_combo_box_text_new = api(g, 'gtk_combo_box_text_new', V)
        self.gtk_combo_box_text_append_text = api(g, 'gtk_combo_box_text_append_text', None, V, B)
        self.gtk_combo_box_set_active = api(g, 'gtk_combo_box_set_active', None, V, I)
        self.gtk_combo_box_get_active = api(g, 'gtk_combo_box_get_active', I, V)
        self.gtk_button_new_with_label = api(g, 'gtk_button_new_with_label', V, B)
        self.gtk_check_button_new_with_label = api(g, 'gtk_check_button_new_with_label', V, B)
        self.gtk_toggle_button_set_active = api(g, 'gtk_toggle_button_set_active', None, V, I)
        self.gtk_scale_new_with_range = api(g, 'gtk_scale_new_with_range', V, I, C.c_double, C.c_double, C.c_double)
        self.gtk_range_set_value = api(g, 'gtk_range_set_value', None, V, C.c_double)
        self.gtk_range_get_value = api(g, 'gtk_range_get_value', C.c_double, V)
        self.gtk_events_pending = api(g, 'gtk_events_pending', I)
        self.gtk_main_iteration_do = api(g, 'gtk_main_iteration_do', I, I)
        self.gtk_main = api(g, 'gtk_main', None)
        self.gobject_connect = api(self.gobject, 'g_signal_connect_data', C.c_ulong, V, B, V, V, V, UI)
        self.gobject_emit = api(self.gobject, 'g_signal_emit_by_name', None, V, B)
        self.style, self.tokens, self.extracted = select_native_styles()
        self.provider = self.gtk_css_provider_new()
        if not self.gtk_css_provider_load_from_data(self.provider, self.style.encode(), -1, None):
            raise RuntimeError('GTK rejected adapted CSS input')
        self.gtk_style_context_add_provider_for_screen(self.gdk_screen_get_default(), self.provider, 800)
        self.window = self.gtk_window_new(0)
        self.gtk_window_set_title(self.window, b'CALYRA / Native GTK CSS Probe')
        self.gtk_window_set_default_size(self.window, 840, 680)
        root = self.gtk_box_new(1, 0)
        self.gtk_container_add(self.window, root)
        header = self.gtk_box_new(1, 6)
        self._class(header, 'calyra-header')
        self._pack(root, header)
        self._label(header, 'CALYRA   /   ENGINE LAB', 'calyra-accent')
        self._label(header, 'GTK3 CSS subset   /   native widgets   /   not a GPU benchmark', 'calyra-muted')
        body = self.gtk_box_new(1, 6)
        self._class(body, 'calyra-main')
        self._pack(root, body)
        self._label(body, 'Native CSS. Actual widgets.', 'calyra-heading')
        self._label(body, 'Canonical colors and button styles extracted from reference.css', 'calyra-muted')
        self._label(body, 'DISPLAY NAME', 'calyra-muted')
        self.entry = self.gtk_entry_new()
        self.gtk_entry_set_text(self.entry, b'Alex Rivera')
        self._pack(body, self.entry)
        self._label(body, 'RENDER PRIORITY', 'calyra-muted')
        self.combo = self.gtk_combo_box_text_new()
        for item in ('Balanced', 'Visual fidelity', 'Performance'):
            self.gtk_combo_box_text_append_text(self.combo, item.encode())
        self.gtk_combo_box_set_active(self.combo, 0)
        self._pack(body, self.combo)
        self._label(body, 'MATERIAL INTENSITY', 'calyra-muted')
        self.scale = self.gtk_scale_new_with_range(0, 0, 100, 1)
        self.gtk_range_set_value(self.scale, 64)
        self._pack(body, self.scale)
        self.check = self.gtk_check_button_new_with_label(b'Enable effects')
        self.gtk_toggle_button_set_active(self.check, 1)
        self._pack(body, self.check)
        actions = self.gtk_box_new(0, 12)
        self._pack(body, actions)
        self.apply_button = self.gtk_button_new_with_label(b'Apply settings')
        self._class(self.apply_button, 'action', 'primary')
        self._pack(actions, self.apply_button)
        self.reset_button = self.gtk_button_new_with_label(b'Reset')
        self._class(self.reset_button, 'action', 'secondary')
        self._pack(actions, self.reset_button)
        self.status = self._label(body, 'Ready for native GTK events', 'calyra-accent')
        CALLBACK = C.CFUNCTYPE(None, V, V)
        self._callbacks = [CALLBACK(lambda _widget, _data: self.apply()), CALLBACK(lambda _widget, _data: self.reset())]
        self.gobject_connect(self.apply_button, b'clicked', C.cast(self._callbacks[0], V), None, None, 0)
        self.gobject_connect(self.reset_button, b'clicked', C.cast(self._callbacks[1], V), None, None, 0)
        self.gtk_widget_show_all(self.window)
        self.pump()

    def _class(self, widget, *names):
        ctx = self.gtk_widget_get_style_context(widget)
        for name in names:
            self.gtk_style_context_add_class(ctx, name.encode())

    def _pack(self, box, widget):
        self.gtk_box_pack_start(box, widget, 0, 0, 0)

    def _label(self, box, text, klass):
        label = self.gtk_label_new(text.encode())
        self.gtk_label_set_xalign(label, 0.0)
        self._class(label, klass)
        self._pack(box, label)
        return label

    def pump(self):
        for _ in range(30):
            if not self.gtk_events_pending():
                break
            self.gtk_main_iteration_do(0)

    def apply(self):
        name = self.gtk_entry_get_text(self.entry).decode()
        selected = ('Balanced', 'Visual fidelity', 'Performance')[self.gtk_combo_box_get_active(self.combo)]
        intensity = round(self.gtk_range_get_value(self.scale))
        self.gtk_label_set_text(self.status, f'Saved: {name} / {selected} / {intensity}%'.encode())

    def reset(self):
        self.gtk_entry_set_text(self.entry, b'Alex Rivera')
        self.gtk_combo_box_set_active(self.combo, 0)
        self.gtk_range_set_value(self.scale, 64)
        self.gtk_toggle_button_set_active(self.check, 1)
        self.gtk_label_set_text(self.status, b'Reset to defaults')

    def emit_apply(self):
        self.gobject_emit(self.apply_button, b'clicked')
        self.pump()

    def emit_reset(self):
        self.gobject_emit(self.reset_button, b'clicked')
        self.pump()

    def get_status(self):
        return self.gtk_label_get_text(self.status).decode()

    def screenshot(self, path: Path):
        from PIL import ImageGrab
        self.pump()
        time.sleep(.25)
        self.pump()
        x, y, w, h = I(), I(), I(), I()
        self.gtk_window_get_position(self.window, C.byref(x), C.byref(y))
        self.gtk_window_get_size(self.window, C.byref(w), C.byref(h))
        if w.value < 100 or h.value < 100:
            raise RuntimeError(f'Invalid native window dimensions {w.value}x{h.value}')
        path.parent.mkdir(parents=True, exist_ok=True)
        ImageGrab.grab(bbox=(x.value, y.value, x.value+w.value, y.value+h.value)).save(path)
        return [w.value, h.value]

    def record(self, screenshot: Path | None, size: list[int] | None) -> dict:
        def hash_file(name: str) -> str:
            return hashlib.sha256((ROOT / 'fixtures' / name).read_bytes()).hexdigest()
        minor = api(self.gtk, 'gtk_get_minor_version', UI)()
        micro = api(self.gtk, 'gtk_get_micro_version', UI)()
        major = api(self.gtk, 'gtk_get_major_version', UI)()
        width, height = size if size is not None else (840, 680)
        return {
            'schema': 'calyra.adapter-result.v1',
            'adapter': {'id': 'gtk3-css-diagnostic', 'version': f'{major}.{minor}.{micro}', 'kind': 'browserless-software'},
            'fixture': {'name': 'controls', 'version': json.loads((ROOT / 'fixtures' / 'manifest.json').read_text())['version'],
                        'width_css_px': width, 'height_css_px': height, 'state': 'default', 'motion': 'off'},
            'source': {'html_sha256': hash_file('index.html'), 'css_sha256': hash_file('reference.css'),
                       'js_sha256': hash_file('reference.js'), 'css_modified': True, 'dom_patched': True,
                       'js_executed': False, 'external_network_used': False,
                       'adaptations': [
                           'Native GtkBox widget tree in place of source HTML DOM',
                           'Copy only Gtk-compatible .action rules and substitute CSS tokens',
                           'Supply GTK-specific rules for native button/entry/label nodes',
                           'No CSS Grid/Flexbox or JavaScript runtime; controls subset only',
                       ]},
            'environment': {'os': platform.platform(), 'architecture': platform.machine(), 'python_version': platform.python_version()},
            'execution': {'browser_engine': False, 'gpu_backed': False, 'interactive': True,
                          'render_backend': 'Gtk3 system widgets and GtkCssProvider (software/GDK; GPU not asserted)'},
            'capture': {'success': bool(screenshot and screenshot.exists()), 'page_count': 1 if screenshot and screenshot.exists() else 0,
                        'png_paths': [str(screenshot)] if screenshot and screenshot.exists() else [],
                        'pdf_path': None, 'pixel_scale': 1.0, 'measured_performance': False},
            'coverage': {'gtk-css-provider': 'direct', 'reference-action-rules': 'adapted',
                         'css-variables': 'adapted', 'css-grid': 'unsupported',
                         'css-flexbox': 'unsupported', 'js-interactions': 'unsupported',
                         'native-widget-interactions': 'direct', 'native-accessibility': 'untested',
                         'font-loading': 'untested', 'backdrop-filter': 'unsupported'},
            'eligibility': 'restricted',
            'limitations': ['Diagnostic beyond named engine candidates, not a replacement',
                            'Only derived CSS subset is submitted to GTK parser',
                            'No CSS Grid/Flexbox layout; GtkBox and native input are used',
                            'No JavaScript, browser DOM, or general CSS interoperability',
                            'GTK backend may be accelerated by compositor, but native GPU path unverified',
                            'Accessibility tree, IME, physical pointer input, timings and memory untested'],
        }

    def close(self):
        self.gtk_widget_destroy(self.window)
        self.pump()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--contract', type=Path, help='Write schema-valid diagnostic adapter result')
    parser.add_argument('--no-loop', action='store_true')
    args = parser.parse_args()
    app = Gtk3NativeProbe()
    try:
        size = app.screenshot(args.capture) if args.capture else None
        if args.evidence:
            result = {
                'experiment': 'gtk3-css-probe-v1', 'renderer': 'GTK3 native widgets (not GPU certified)',
                'browser_engine': False, 'gpu_backed': False, 'interactive': True,
                'direct_full_css': False, 'css_subset_extracted': True, 'css_translated': True,
                'fixture': 'controls subset', 'canonical_css_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'resolution': size, 'adapted_declarations': app.extracted,
                'gtk_version': '3.x (system runtime)', 'platform': platform.platform(),
                'input_testing': 'GTK clicked signal and state mutation; physical pointer event not tested',
                'limitations': ['GtkBox not CSS Grid/Flex layout', 'No JavaScript', 'No native GPU assertion', 'CSS subset and custom color token substitution', 'Not a replacement for named renderer candidates'],
            }
            args.evidence.parent.mkdir(parents=True, exist_ok=True)
            args.evidence.write_text(json.dumps(result, indent=2)+'\n')
        if args.contract:
            args.contract.parent.mkdir(parents=True, exist_ok=True)
            args.contract.write_text(json.dumps(app.record(args.capture, size), indent=2)+'\n')
        if not args.no_loop:
            app.gtk_main()
    finally:
        if args.no_loop:
            app.close()

if __name__=='__main__':
    main()
