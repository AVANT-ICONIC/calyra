#!/usr/bin/env python3
"""Five real macOS Tauri+WKWebView runs with *direct* WebKit PID identity.

The native opt-in Tauri binary writes real WebKit-owned process IDs into a
unique directory per launch. Validate each PID against the macOS process
table, then capture libproc resident/physical-footprint values. Shared memory
is never reported as a unique or whole-machine allocation. No browserless
comparison, OS input, or production private API dependency.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

from macos_tauri_resource_baseline import process_table, window_candidates
from macos_webkit_attribution import probe_metadata

ROLES = {
    'ui': ('tauri_ui_process_pid', 'calyra-tauri-reference'),
    'webcontent': ('webkit_webcontent_pid', 'com.apple.WebKit.WebContent'),
    'networking': ('webkit_network_pid', 'com.apple.WebKit.Networking'),
    'gpu': ('webkit_gpu_pid', 'com.apple.WebKit.GPU'),
}


def verify_and_sample(doc: dict, app_pid: int, table: list[dict],
                      native_tool: str) -> dict:
    assert doc['schema'] == 'calyra.macos-native-wkwebview-pids.v1', doc
    assert doc['tauri_ui_process_pid'] == app_pid, doc
    assert doc['canonical_html_css_js_unmodified'] is True
    assert doc['private_diagnostic_only'] is True
    by_pid = {entry['pid']: entry for entry in table}
    selected = {}
    pids = []
    for role, (field, expected) in ROLES.items():
        pid = doc.get(field)
        if pid is None:
            assert role in ('networking', 'gpu'), (role, doc)
            selected[role] = None
            continue
        assert isinstance(pid, int) and pid > 0 and pid in by_pid, (role, pid)
        row = by_pid[pid]
        assert row['comm'].rsplit('/', 1)[-1] == expected, (role, row)
        assert pid not in pids, f'duplicate process identity {pid}'
        pids.append(pid)
        selected[role] = {**row, 'role': role, 'direct_wkwebview_pid': pid}
    native = probe_metadata(native_tool, pids)
    for role, entry in selected.items():
        if entry is not None:
            entry.update(native[entry['pid']])
            assert entry['rusage_status'] == 'ok', (role, entry)
            assert entry['resident_bytes'] is not None
            assert entry['physical_footprint_bytes'] is not None
    return selected


def run_trial(exe: Path, window_tool: str, native_tool: str, out: Path,
              trial: int, binary_sha: str) -> dict:
    trialdir = out / f'trial-{trial}'
    trialdir.mkdir(parents=True, exist_ok=False)
    path = trialdir / 'actual-wkwebview-process-pids.json'
    logpath = trialdir / 'native-app.log'
    env = os.environ.copy()
    env['CALYRA_STAGE_A_PID_DIR'] = str(trialdir)
    with logpath.open('w') as logfile:
        start = time.monotonic()
        app = subprocess.Popen([str(exe)], stdout=logfile,
                               stderr=subprocess.STDOUT, env=env)
        try:
            found = False
            while time.monotonic() - start < 10:
                if app.poll() is not None:
                    raise RuntimeError(f'app exited before callback: {app.returncode}')
                if path.is_file() and path.stat().st_size >= 100:
                    found = True
                    break
                time.sleep(.25)
            if not found:
                raise RuntimeError('no real WKWebView native PID callback within 10 sec')
            doc = json.loads(path.read_text())
            window = window_candidates(window_tool, app.pid)
            if not window:
                raise RuntimeError('no real native app-owned CGWindow on macOS')
            remaining = 12.0 - (time.monotonic() - start)
            if remaining > 0:
                time.sleep(remaining)
            assert app.poll() is None, 'app died before process-resource snapshot'
            table = process_table()
            selected = verify_and_sample(doc, app.pid, table, native_tool)
            values = [p for p in selected.values() if p is not None]
            row = {
                'trial': trial,
                'ui_pid': app.pid,
                'native_window_id': window[0]['window_id'],
                'sample_seconds_after_launch': round(time.monotonic()-start, 3),
                'native_executable_sha256': binary_sha,
                'processes': selected,
                'rss_sum_kib_not_unique': sum(p['rss_kib'] for p in values),
                'physical_footprint_sum_bytes_diagnostic_only': sum(
                    p['physical_footprint_bytes'] for p in values),
                'incomplete_network_or_gpu_identity': (
                    selected['networking'] is None or selected['gpu'] is None),
                'total_unique_application_memory_verified': False,
                'verified_live_pid_identity_from_private_wkwebview_research_api': True,
            }
            (trialdir / 'verified-process-sample.json').write_text(
                json.dumps(row, indent=2, sort_keys=True)+'\n')
            return row
        finally:
            if app.poll() is None:
                app.terminate()
                try:
                    app.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    app.kill()
                    app.wait(timeout=4)


def main() -> None:
    assert len(sys.argv) == 5, (
        'usage: macos_direct_pid_resource_five_run.py '
        '<research-tauri-exe> <mac-window-inspector> <pid-metadata-tool> <outdir>')
    exe = Path(sys.argv[1]).resolve()
    window_tool = str(Path(sys.argv[2]).resolve())
    native_tool = str(Path(sys.argv[3]).resolve())
    out = Path(sys.argv[4]).resolve()
    assert exe.name == 'calyra-tauri-reference'
    assert exe.is_file() and os.access(exe, os.X_OK)
    assert Path(window_tool).is_file() and Path(native_tool).is_file()
    out.mkdir(parents=True, exist_ok=True)
    binary_sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    trials = []
    for trial in range(1, 6):
        result = run_trial(exe, window_tool, native_tool, out, trial, binary_sha)
        trials.append(result)
        present = {k: p['pid'] for k,p in result['processes'].items() if p}
        print(f'PASS trial {trial}: actual WKWebView process IDs {present}', flush=True)
        time.sleep(.5)
    assert len({r['ui_pid'] for r in trials}) == 5
    roles = {}
    for role in ROLES:
        entries = [r['processes'][role] for r in trials]
        good = [e for e in entries if e]
        roles[role] = {
            'observed_count': len(good),
            'rss_kib_median_if_all_five': statistics.median(
                e['rss_kib'] for e in good) if len(good)==5 else None,
            'physical_footprint_bytes_median_if_all_five': statistics.median(
                e['physical_footprint_bytes'] for e in good) if len(good)==5 else None,
        }
    summary = {
        'schema':'calyra.macos-direct-wkwebview-process-resources.v1',
        'trial_count':5,
        'native_debug_executable_sha256': binary_sha,
        'roles':roles,
        'trials':trials,
        'rss_sum_kib_median_NOT_unique':statistics.median(
            r['rss_sum_kib_not_unique'] for r in trials),
        'result_not_an_optimized_normal_tauri_release_build':True,
        'no_browserless_engine_comparison':True,
        'no_unique_total_memory_or_shared_pages_deduplication':True,
        'web_kit_private_api_not_for_production':True,
        'no_gpu_or_os_input_claim':True,
    }
    (out / 'five-run-direct-pid-result.json').write_text(
        json.dumps(summary, indent=2, sort_keys=True)+'\n')
    print('PASS 5 sequential real native Tauri WKWebViews; no total unique RAM claim')


if __name__ == '__main__':
    main()
