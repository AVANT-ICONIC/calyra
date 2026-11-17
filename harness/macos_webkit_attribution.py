#!/usr/bin/env python3
"""CALYRA: scoped WKWebView helper ownership and physical-footprint probe.

Never call a merely new WebKit process an owned CALYRA process. Require
responsibility==the measured app PID (private, optional system API) or actual
parent lineage. Keep all provisional candidates and any unavailable metrics.
Observed resource usage is a *per-process metric*, never a unique system-memory
sum or an engine performance ranking. No OS events are posted.
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

from macos_tauri_resource_baseline import descendants, process_table, window_candidates


def webkit(row: dict) -> bool:
    # Full path from ps -o comm (on Darwin) is expected; do not match arbitrary
    # browser executables or user paths containing only 'webkit'.
    name = row['comm'].rsplit('/', 1)[-1]
    return name.startswith('com.apple.WebKit.') or name.startswith('WebKit.')


def probe_metadata(binary: str, pids: list[int]) -> dict[int, dict]:
    if not pids:
        return {}
    process = subprocess.run(
        [binary], input=''.join(f'{p}\n' for p in sorted(set(pids))),
        text=True, capture_output=True, timeout=15, check=True,
    )
    result: dict[int, dict] = {}
    lines = process.stdout.splitlines()
    assert lines and lines[0].split('\t') == [
        'pid', 'responsible_pid', 'resident_bytes',
        'physical_footprint_bytes', 'rusage_status'
    ], lines[:1]
    for line in lines[1:]:
        pieces = line.split('\t')
        assert len(pieces) == 5, line
        pid, responsible, resident, footprint = map(int, pieces[:4])
        assert pieces[4] in ('ok', 'unavailable'), pieces[4]
        assert pid in pids and pid not in result, pid
        result[pid] = {
            'responsible_pid': responsible if responsible > 0 else None,
            'resident_bytes': resident if resident >= 0 else None,
            'physical_footprint_bytes': footprint if footprint >= 0 else None,
            'rusage_status': pieces[4]
        }
    assert set(result) == set(pids), (set(result), set(pids))
    return result


def classify(before: list[dict], during: list[dict], app_pid: int,
             metadata: dict[int, dict]) -> dict:
    """Conservatively separate confirmed from temporal-correlation candidates."""
    baseline = {row['pid'] for row in before}
    present = {row['pid'] for row in during}
    assert app_pid not in baseline and app_pid in present, 'app must be freshly launched'
    direct = {row['pid'] for row in descendants(during, app_pid)}
    confirmed, uncertain, preexisting = [], [], []
    for row in during:
        if not webkit(row):
            continue
        pid = row['pid']
        meta = metadata.get(pid, {})
        record = {**row, **meta, 'new_since_baseline': pid not in baseline}
        # Process existed before app launch: never attach it as new app cost.
        if pid in baseline:
            record['classification'] = 'preexisting_unassigned'
            preexisting.append(record)
        elif pid in direct or meta.get('responsible_pid') == app_pid:
            record['classification'] = (
                'confirmed_parent_lineage' if pid in direct else
                'confirmed_os_responsibility'
            )
            confirmed.append(record)
        else:
            record['classification'] = 'new_temporal_correlation_only'
            uncertain.append(record)
    return {
        'confirmed': sorted(confirmed, key=lambda x: x['pid']),
        'new_unconfirmed': sorted(uncertain, key=lambda x: x['pid']),
        'preexisting_unassigned': sorted(preexisting, key=lambda x: x['pid']),
        'native_descendants': sorted(direct),
        'baseline_webkit_count': len([x for x in before if webkit(x)]),
        'during_webkit_count': len([x for x in during if webkit(x)]),
    }


def sample(exe: Path, native_window_probe: str, metadata_tool: str, out: Path,
           trial: int) -> dict:
    before = process_table()
    logfile = out / f'trial-{trial}-native-app.log'
    with logfile.open('w') as log:
        started = time.monotonic()
        app = subprocess.Popen([str(exe)], stdout=log, stderr=subprocess.STDOUT)
        try:
            window_id = None
            while time.monotonic() - started < 10.0:
                if app.poll() is not None:
                    raise RuntimeError(f'Tauri exited before window, status={app.returncode}')
                candidates = window_candidates(native_window_probe, app.pid)
                if candidates:
                    window_id = candidates[0]['window_id']
                    break
                time.sleep(0.30)
            if window_id is None:
                raise RuntimeError('no native app-owned CGWindow in 10 seconds')
            remaining = 12.0 - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
            assert app.poll() is None, 'native app exited during measurement'
            during = process_table()
            assert any(r['pid'] == app.pid and r['comm'].endswith(exe.name)
                       for r in during), 'native app pid/executable mismatch'
            pids = [r['pid'] for r in during if webkit(r)] + [app.pid]
            metadata = probe_metadata(metadata_tool, pids)
            groups = classify(before, during, app.pid, metadata)
            parent = next(x for x in during if x['pid'] == app.pid)
            result = {
                'trial': trial,
                'app_pid': app.pid,
                'app_owned_window_id': window_id,
                'post_launch_seconds_at_snapshot': round(time.monotonic() - started, 3),
                'original_exe_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
                'parent_ps_rss_kib': parent['rss_kib'],
                'parent_native_process_metadata': metadata[app.pid],
                'webkit': groups,
                'helper_rss_kib_sum_not_unique': sum(
                    row['rss_kib'] for row in groups['confirmed']),
                'helper_physical_footprint_bytes_sum_diagnostic_only': (
                    sum(row['physical_footprint_bytes']
                        for row in groups['confirmed'])
                    if groups['confirmed'] and
                       all(isinstance(row.get('physical_footprint_bytes'), int)
                           for row in groups['confirmed']) else None
                ),
                'unassigned_webkit_candidates_excluded_from_totals': True,
                'private_os_responsibility_api_diagnostic_only': True,
                'unique_total_memory_established': False,
            }
            (out / f'trial-{trial}-attribution.json').write_text(
                json.dumps(result, indent=2, sort_keys=True) + '\n')
            return result
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
        'usage: macos_webkit_attribution.py <tauri-exe> <window-probe> '
        '<pid-resource-probe> <out-dir>')
    exe = Path(sys.argv[1]).resolve()
    window_probe = str(Path(sys.argv[2]).resolve())
    resource_probe = str(Path(sys.argv[3]).resolve())
    output = Path(sys.argv[4]).resolve()
    assert exe.is_file() and os.access(exe, os.X_OK)
    assert exe.name == 'calyra-tauri-reference'
    assert Path(window_probe).is_file() and Path(resource_probe).is_file()
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for trial in range(1, 6):
        record = sample(exe, window_probe, resource_probe, output, trial)
        records.append(record)
        print(f"trial {trial}: native Tauri window={record['app_owned_window_id']} "
              f"confirmed WebKit={len(record['webkit']['confirmed'])}; "
              f"new unconfirmed WebKit={len(record['webkit']['new_unconfirmed'])}",
              flush=True)
        time.sleep(.6)
    parent_rss = [r['parent_ps_rss_kib'] for r in records]
    report = {
        'schema': 'calyra.macos-wkwebview-process-attribution.v1',
        'sample_count': len(records),
        'macos_apple_silicon_native_window_per_trial': True,
        'parent_ps_rss_kib_median': statistics.median(parent_rss),
        'webkit_confirmed_counts': [len(r['webkit']['confirmed']) for r in records],
        'webkit_new_unconfirmed_counts': [len(r['webkit']['new_unconfirmed']) for r in records],
        'trials': records,
        'no_whole_app_unique_ram_claim': True,
        'private_responsibility_lookup_optional_not_production_api': True,
        'process_snapshot_race_and_shared_pages_limit_precision': True,
        'not_matched_to_native_browserless_engine': True,
    }
    (output / 'attribution-result.json').write_text(
        json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('PASS: 5 native-window trials and honest process attribution categories')


if __name__ == '__main__':
    main()
