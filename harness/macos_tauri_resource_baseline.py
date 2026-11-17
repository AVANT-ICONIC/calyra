#!/usr/bin/env python3
"""Five sequential genuine macOS Tauri launches: bounded resource census.

No browserless comparison and no claim about unique WebKit helper accounting.
Every sample is from the real CALYRA executable after an app-owned OS window
exists. RSS includes shared memory; a five-run baseline is NOT a speed ranking.
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

def process_table() -> list[dict]:
    raw = subprocess.check_output(
        ["/bin/ps", "-A", "-o", "pid=,ppid=,rss=,vsz=,pcpu=,comm="],
        text=True,
    )
    rows = []
    for line in raw.splitlines():
        parts = line.strip().split(maxsplit=5)
        if len(parts) != 6:
            continue
        try:
            pid, parent, rss, vsz = [int(value) for value in parts[:4]]
            cpu = float(parts[4])
        except ValueError:
            continue
        rows.append({
            "pid": pid,
            "ppid": parent,
            "rss_kib": rss,
            "vsz_kib": vsz,
            "ps_cpu_percent_instantaneous": cpu,
            "comm": parts[5],
        })
    return rows

def descendants(rows: list[dict], root: int) -> list[dict]:
    selected = {root}
    while True:
        additional = {row["pid"] for row in rows if row["ppid"] in selected}
        if additional.issubset(selected):
            break
        selected |= additional
    return [row for row in rows if row["pid"] in selected]

def window_candidates(binary: str, pid: int) -> list[dict]:
    result = subprocess.run(
        [binary, "windows", str(pid)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"native CoreGraphics helper failed: {result.stderr}")
    payload = json.loads(result.stdout)
    assert payload["owner_pid"] == pid, payload
    return payload["visible_window_candidates"]

def main() -> None:
    assert len(sys.argv) == 4, (
        "usage: macos_tauri_resource_baseline.py <app executable> "
        "<compiled native window probe> <output dir>"
    )
    exe = Path(sys.argv[1]).resolve()
    native_probe = str(Path(sys.argv[2]).resolve())
    out = Path(sys.argv[3]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert exe.is_file() and os.access(exe, os.X_OK)
    assert Path(native_probe).is_file()
    assert exe.name == "calyra-tauri-reference"
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    trials = []
    errors = []
    for trial in range(1, 6):
        app_log = out / f"trial-{trial}-native-app.log"
        with app_log.open("w") as handle:
            start = time.monotonic()
            process = subprocess.Popen(
                [str(exe)],
                stdout=handle,
                stderr=subprocess.STDOUT,
            )
            try:
                first_window_ms = None
                window_id = None
                while time.monotonic() - start < 11:
                    if process.poll() is not None:
                        raise RuntimeError(
                            f"app pid {process.pid} exited early: {process.returncode}"
                        )
                    windows = window_candidates(native_probe, process.pid)
                    if windows:
                        first_window_ms = round((time.monotonic() - start) * 1000)
                        window_id = windows[0]["window_id"]
                        break
                    time.sleep(0.25)
                if window_id is None:
                    raise RuntimeError("no actual app-owned CGWindow after 11 seconds")

                # Uniform post-launch sample, regardless of window discovery
                # latency. This is a single instantaneous ps census, not a
                # private-memory footprint or a cold-start distribution.
                target_seconds = 12.0
                elapsed = time.monotonic() - start
                if elapsed < target_seconds:
                    time.sleep(target_seconds - elapsed)
                if process.poll() is not None:
                    raise RuntimeError("app exited before resource census")
                table = process_table()
                rows = descendants(table, process.pid)
                parent = next((r for r in rows if r["pid"] == process.pid), None)
                if not parent:
                    raise RuntimeError("live app missing from process table")
                record = {
                    "trial": trial,
                    "app_pid": process.pid,
                    "original_executable_sha256": digest,
                    "actual_app_owned_window_id": window_id,
                    "first_window_observed_ms_including_probe_overhead": first_window_ms,
                    "sample_at_seconds_after_launch": round(time.monotonic()-start, 3),
                    "parent_rss_kib": parent["rss_kib"],
                    "parent_vsz_kib": parent["vsz_kib"],
                    "parent_instantaneous_ps_cpu_percent": parent[
                        "ps_cpu_percent_instantaneous"
                    ],
                    "os_descendants_including_parent": rows,
                    "descendant_rss_sum_kib_not_unique": sum(
                        row["rss_kib"] for row in rows
                    ),
                    "webkit_processes_not_attributed": True,
                    "app_alive_during_sample": True,
                }
                trials.append(record)
                (out / f"trial-{trial}.json").write_text(
                    json.dumps(record, indent=2, sort_keys=True) + "\n"
                )
                print(
                    f"PASS trial {trial}: pid {process.pid}; "
                    f"window {window_id}; parent RSS {parent['rss_kib']} KiB",
                    flush=True,
                )
            except Exception as error:
                errors.append({"trial": trial, "error": str(error)})
                (out / "failed-trials.json").write_text(
                    json.dumps(errors, indent=2) + "\n"
                )
                raise
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=4)
        time.sleep(0.5)

    assert len(trials) == 5
    rss = [entry["parent_rss_kib"] for entry in trials]
    result = {
        "schema": "calyra.macos-tauri-resource-observation.v1",
        "platform": "macos-15-arm64",
        "observation_count": len(trials),
        "actual_mac_app_owned_window_verified_each_run": True,
        "original_executable_sha256": digest,
        "parent_rss_kib_median": statistics.median(rss),
        "parent_rss_kib_min": min(rss),
        "parent_rss_kib_max": max(rss),
        "trials": trials,
        "diagnostic_only_no_browserless_engine_comparison": True,
        "all_shared_pages_still_counted_in_rss": True,
        "unattributed_wkwebview_helpers_excluded_from_total": True,
        "no_first_meaningful_pixel_timing": True,
        "no_matched_CPU_GPU_or_private_footprint_claim": True,
    }
    (out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(
        f"PASS 5 real macOS Tauri runs; parent median RSS "
        f"{result['parent_rss_kib_median']} KiB. "
        "NOT private whole-process footprint.",
        flush=True,
    )

if __name__ == "__main__":
    main()
