#!/usr/bin/env python3
"""RmlUi 6.3 GLFW/GL3 Stage-A probe. Fail closed on missing native evidence.

A compiled executable is trusted only if its digest matches a manifest from
an actual completed CMake build with the pinned, clean upstream checkout.
A captured frame is not itself evidence of hardware GPU acceleration or
native OS input; GL renderer and programmatic RmlUi click evidence are distinct.
"""
import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'native' / 'rmlui'
FIXTURES = ROOT / 'fixtures'
UPSTREAM_SHA = 'ba95ffe8bfb6370efb2cdcca927eaad4710c5413'
PROVENANCE_FILE = 'rmlui-build-provenance.json'


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_pinned_checkout(path):
    if not (path / 'CMakeLists.txt').is_file() or not (path / 'LICENSE.txt').is_file():
        return False, 'RmlUi source and license files missing'
    try:
        rev = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True,
                             capture_output=True, timeout=5, check=True).stdout.strip()
        dirty = subprocess.run(['git', '-C', str(path), 'status', '--porcelain', '--untracked-files=no'],
                               text=True, capture_output=True, timeout=5, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        return False, f'Cannot verify RmlUi source revision/cleanliness: {e}'
    if rev != UPSTREAM_SHA:
        return False, f'Wrong RmlUi revision: {rev or "unknown"}; expected {UPSTREAM_SHA}'
    if dirty:
        return False, 'RmlUi checkout has modified tracked files; reproducible source cannot be verified'
    return True, ''


def gl_renderer_class(renderer):
    """Only classify explicitly identifiable GL renderers; unknown is not GPU proof."""
    name = renderer.lower()
    if not name:
        return 'unknown'
    if any(token in name for token in ('llvmpipe', 'softpipe', 'swrast', 'swiftshader',
                                      'software rasterizer', 'gdi generic', 'osmesa')):
        return 'software'
    if any(token in name for token in ('nvidia', 'geforce', 'radeon', 'intel',
                                      'apple', 'adreno', 'mali', 'powervr')):
        return 'hardware'
    return 'unknown'


def marker(output, key):
    match = re.search(r'^' + re.escape(key) + r'=(.*)$', output, re.MULTILINE)
    return match.group(1).strip() if match else None


def report_template(mode, issue=None):
    manifest = json.loads((FIXTURES / 'manifest.json').read_text())
    return {
        'schema': 'calyra.adapter-result.v1',
        'adapter': {'id': 'rmlui-6.3-glfw-gl3', 'version': '6.3', 'kind': 'browserless-gpu'},
        'fixture': {'name': 'controls', 'version': manifest['version'], 'width_css_px': 1060,
                    'height_css_px': 740, 'state': 'default', 'motion': 'off'},
        'source': {
            'html_sha256': hash_file(FIXTURES / 'index.html'),
            'css_sha256': hash_file(FIXTURES / 'reference.css'),
            'js_sha256': hash_file(FIXTURES / 'reference.js'),
            'css_modified': mode == 'adapted', 'dom_patched': True, 'js_executed': False,
            'external_network_used': False,
            'adaptations': [
                'Canonical HTML replaced by a documented limited RML controls translation (DOM adaptation)',
                'Browser JavaScript behavior not executed; RmlUi C++ event listener used',
                'RmlUi-native GLFW/OpenGL3 backend, not a browser or WebView',
            ] + (['Canonical CSS replaced by hand-adapted RCSS; never score as direct compatibility'] if mode == 'adapted' else
                 ['Canonical reference.css passed byte-for-byte into RmlUi style parser, unsupported declarations unfiltered']),
        },
        'environment': {'os': platform.platform(), 'architecture': platform.machine(),
                        'python_version': platform.python_version()},
        'execution': {'browser_engine': False, 'gpu_backed': False, 'interactive': False,
                      'render_backend': 'RmlUi 6.3 GLFW_GL3 (attempt; unverified until success)'},
        'capture': {'success': False, 'page_count': 0, 'png_paths': [], 'pdf_path': None,
                    'pixel_scale': 1.0, 'measured_performance': False},
        'coverage': {f: 'untested' for f in manifest['fixtures']['controls']['features']}
                    | {'html-dom': 'adapted', 'javascript-interactions': 'unsupported'},
        'eligibility': 'blocked',
        'limitations': [
            'No baseline performance measurements: only a first native rendering probe',
            'Canonical DOM is translated to RML; visual parity not established',
            'Font shaping, accessibility, IME and operating-system input remain unmeasured',
            'Programmatic RmlUi mouse-click smoke test does not prove OS pointer dispatch',
        ] + ([issue] if issue else []),
    }


def find_built_executable(builddir):
    # Makefiles/Ninja and macOS Xcode multi-config generators have distinct paths.
    for p in (builddir / 'calyra_rmlui_probe',
              builddir / 'Release' / 'calyra_rmlui_probe',
              builddir / 'Release' / 'calyra_rmlui_probe.exe',
              builddir / 'calyra_rmlui_probe.exe'):
        if p.is_file():
            return p.resolve()
    return None


def read_provenance(outdir, source, binary):
    p = outdir / PROVENANCE_FILE
    if not p.is_file():
        return False, 'No native CMake build provenance; run with --build'
    try:
        payload = json.loads(p.read_text())
        if payload.get('upstream_sha') != UPSTREAM_SHA:
            return False, 'Build manifest upstream SHA mismatch'
        if payload.get('source_root') != str(source.resolve()):
            return False, 'Build manifest points to a different source checkout'
        if payload.get('binary_path') != str(binary.resolve()):
            return False, 'Build manifest executable path mismatch'
        if payload.get('binary_sha256') != hash_file(binary):
            return False, 'Built executable was changed after recorded CMake build'
        return True, ''
    except (OSError, ValueError, KeyError) as e:
        return False, f'Build provenance invalid: {e}'


def run(args):
    outdir = Path(args.output).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    report = report_template(args.mode)
    src = Path(args.source).expanduser().resolve() if args.source else None
    binary = Path(args.binary).expanduser().resolve() if args.binary else outdir / 'build' / 'calyra_rmlui_probe'
    issue = None
    if src is None:
        issue = 'BLOCKED: pinned RmlUi source not provided; no network or substitute renderer used'
    else:
        verified, why = is_pinned_checkout(src)
        if not verified:
            issue = 'BLOCKED: ' + why
    if not issue and args.build:
        builddir = outdir / 'build'
        (outdir / PROVENANCE_FILE).unlink(missing_ok=True)
        (outdir / 'build-log.txt').unlink(missing_ok=True)
        for cmd in [
            ['cmake', '-S', str(NATIVE), '-B', str(builddir),
             '-DCALYRA_RMLUI_SOURCE=' + str(src), '-DCMAKE_BUILD_TYPE=Release'],
            ['cmake', '--build', str(builddir), '--config', 'Release',
             '--target', 'calyra_rmlui_probe', '--parallel', '2'],
        ]:
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
            except (OSError, subprocess.SubprocessError) as e:
                issue = f'BLOCKED: build command failed: {e}'
                break
            with (outdir / 'build-log.txt').open('a', encoding='utf8') as log:
                log.write('> ' + ' '.join(cmd) + '\n' + p.stdout[-12000:] + '\n' + p.stderr[-12000:] + '\n')
            if p.returncode:
                issue = f'BLOCKED: cmake returned {p.returncode}; see build-log.txt'
                break
        if not issue:
            built = find_built_executable(builddir)
            if not built:
                issue = 'BLOCKED: CMake succeeded but Release executable not found'
            elif args.binary and built != binary:
                issue = 'BLOCKED: supplied --binary does not match the current build output'
            else:
                binary = built
                (outdir / PROVENANCE_FILE).write_text(json.dumps({
                    'upstream_sha': UPSTREAM_SHA,
                    'source_root': str(src),
                    'binary_path': str(binary),
                    'binary_sha256': hash_file(binary),
                }, indent=2) + '\n')
    # Re-use a genuine multi-config build (e.g. macOS Xcode Release/) on the
    # second pass without --build. Do not accept arbitrary pre-existing binaries.
    if not issue and not args.build and not args.binary:
        previously_built = find_built_executable(outdir / 'build')
        if previously_built:
            binary = previously_built
    if not issue and not binary.is_file():
        issue = f'BLOCKED: executable does not exist ({binary}); build with --build'
    if not issue:
        valid, why = read_provenance(outdir, src, binary)
        if not valid:
            issue = 'BLOCKED: ' + why
    if not issue and not args.font:
        issue = 'BLOCKED: no system TTF font path supplied via --font'
    if not issue and not Path(args.font).is_file():
        issue = f'BLOCKED: font file not found ({args.font})'
    ppm = outdir / f'rmlui-{args.mode}-frame.ppm'
    png = outdir / f'rmlui-{args.mode}-frame.png'
    # A failed/blocked attempt must not leave an old screenshot masquerading
    # as this run's evidence, even when source or build validation fails.
    ppm.unlink(missing_ok=True)
    png.unlink(missing_ok=True)
    if not issue:
        css = FIXTURES / 'reference.css' if args.mode == 'direct' else NATIVE / 'controls.rcss'
        cmd = [str(binary), str(NATIVE / 'controls.rml'), str(css), str(Path(args.font).resolve()), str(ppm)]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=22)
            output = p.stdout + '\n' + p.stderr
            (outdir / f'runtime-{args.mode}.log').write_text(output)
            renderer = marker(output, 'CALYRA_GL_RENDERER')
            vendor = marker(output, 'CALYRA_GL_VENDOR')
            frame_marker = marker(output, 'CALYRA_NATIVE_FRAME')
            click_marker = marker(output, 'CALYRA_NATIVE_CLICK')
            style_marker = marker(output, 'CALYRA_COMPUTED_PRIMARY_BG')
            if p.returncode or marker(output, 'CALYRA_NATIVE_RENDER_OK') != '1':
                issue = f'BLOCKED: native executable failed: exit={p.returncode}; inspect runtime log'
            elif not renderer or not vendor:
                issue = 'BLOCKED: actual GL renderer and vendor were not reported'
            elif not frame_marker or not ppm.is_file():
                issue = 'BLOCKED: success marker without matching native framebuffer capture'
            elif click_marker != '1' or marker(output, 'CALYRA_INPUT_SOURCE') != 'synthetic_rmlui_event':
                issue = 'BLOCKED: native RmlUi programmatic click not independently recorded'
            elif not style_marker or not re.fullmatch(r'(?:\d{1,3},){3}\d{1,3}', style_marker):
                issue = 'BLOCKED: RmlUi computed style marker missing or malformed'
            elif args.mode == 'adapted' and style_marker != '198,219,116,255':
                issue = f'BLOCKED: adapted primary color not applied: {style_marker} (expected 198,219,116,255)'
            else:
                from PIL import Image
                with Image.open(ppm) as img:
                    img.verify()
                with Image.open(ppm) as img:
                    width, height = img.size
                    if frame_marker != f'{width}x{height}' or width < 800 or height < 500:
                        raise ValueError('native frame dimensions mismatch or too small')
                    rgb = img.convert('RGB')
                    if all(lo == hi for lo, hi in rgb.getextrema()):
                        raise ValueError('native frame is uniform color (blank or unrendered)')
                    rgb.save(png)
                kind = gl_renderer_class(renderer)
                if kind == 'unknown':
                    issue = 'BLOCKED: unknown GL renderer; cannot classify hardware vs software rasterizer'
                else:
                    report['adapter']['kind'] = 'browserless-gpu' if kind == 'hardware' else 'browserless-software'
                    report['execution'].update(gpu_backed=(kind == 'hardware'), interactive=True,
                                                render_backend=f'RmlUi 6.3 GLFW_GL3 / {renderer} / vendor {vendor}')
                    report['capture'].update(success=True, page_count=1,
                                             png_paths=[str(png.relative_to(ROOT))] if png.is_relative_to(ROOT) else [str(png)],
                                             pixel_scale=width / 1060)
                    report['eligibility'] = 'restricted'
                    report['limitations'].append(f'RmlUi computed primary background RGBA: {style_marker}; no color-space calibration')
                    report['limitations'].append('Synthetic RmlUi click passed; native OS input, IME and a11y still unverified')
                    report['limitations'].append(f'OpenGL renderer classified: {kind}; framebuffer {width}x{height}; no FPS metrics')
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            issue = f'BLOCKED: native execution or image verification failed: {e}'
    if issue:
        # Fail closed: no stale or unverified capture should be exported.
        png.unlink(missing_ok=True)
        ppm.unlink(missing_ok=True)
        report['limitations'].append(issue)
    resultpath = outdir / f'rmlui-{args.mode}-result.json'
    resultpath.write_text(json.dumps(report, indent=2) + '\n')
    try:
        from jsonschema import validate
        schema = json.loads((ROOT / 'harness' / 'adapter-contract.schema.json').read_text())
        validate(report, schema)
    except ImportError:
        pass
    print(json.dumps({'eligibility': report['eligibility'], 'capture': report['capture']['success'],
                      'report': str(resultpath), 'reason': issue}, indent=2))
    return 0 if report['capture']['success'] else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', help='Local verified git checkout of RmlUi at the pinned 6.3 commit')
    parser.add_argument('--binary', help='Compiled calyra_rmlui_probe path (must match build provenance)')
    parser.add_argument('--font', help='Local TTF font file, e.g. macOS Arial.ttf')
    parser.add_argument('--mode', choices=('direct', 'adapted'), default='direct')
    parser.add_argument('--build', action='store_true', help='Compile native RmlUi with CMake; never auto-fetch sources')
    parser.add_argument('--output', default=str(ROOT / 'evidence' / 'native-stage-a' / 'rmlui'))
    sys.exit(run(parser.parse_args()))
