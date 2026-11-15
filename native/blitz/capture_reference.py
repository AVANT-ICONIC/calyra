#!/usr/bin/env python3
"""Optional local Chromium reference for the exact JS-free Blitz snapshots.

This is NOT a Blitz or GPU result and never silently substitutes for one.
"""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
from prepare_static import FIXTURE_NAMES, generate


def capture(root: Path, output: Path, fixture: str) -> Path:
    generate(root, output / 'snapshots', fixture)
    html = (output / 'snapshots' / fixture / 'index.html').read_text()
    outfile = output / f'chromium-{fixture}-static.png'
    outfile.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        import os, shutil
        executable = (os.environ.get('CALYRA_CHROMIUM_EXECUTABLE') or shutil.which('chromium'))
        browser = p.chromium.launch(executable_path=executable, headless=True,
                                    args=['--no-sandbox'] if hasattr(os,'geteuid') and os.geteuid()==0 else [])
        try:
            page = browser.new_page(viewport={'width':1060,'height':800},device_scale_factor=1,reduced_motion='reduce')
            # Navigation is blocked in some restricted sandboxes. set_content is
            # equivalent here because our CSS is explicitly inlined into HTML.
            page.set_content(html,wait_until='load')
            page.screenshot(path=str(outfile),full_page=False,animations='disabled')
        finally:
            browser.close()
    with Image.open(outfile) as image:
        assert image.size == (1060,800)
    return outfile


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fixture',choices=FIXTURE_NAMES,default='controls')
    args=parser.parse_args()
    print(capture(args.root,args.output,args.fixture))
