#!/usr/bin/env python3
"""Run CALYRA's isolated native-select semantics baseline in real Chromium.

Prerequisite: pip install playwright; provide an installed Chromium executable.
This is intentionally *not* a native Blitz test or a benchmark. It uses a
small independent single-select HTML page; canonical CALYRA files are untouched.
"""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML = '''<!doctype html><html><head><meta charset="UTF-8"><style>
body {background:#121922; color:#e8e9e4; font:16px Arial;}
select {width:300px;height:48px;padding:8px;background:#181f28;color:#e8e9e4;}
</style></head><body><select id="priority">
<option value="balanced">Balanced</option>
<option value="quality">Visual fidelity</option>
<option value="performance">Performance</option>
</select></body></html>'''

SCENARIO = r'''() => {
const s=document.querySelector('#priority'), trace=[];
for(const event of ['input','change']) s.addEventListener(event,()=>
  trace.push({type:event,index:s.selectedIndex,value:s.value}));
const record=name=>({
  name,index:s.selectedIndex,value:s.value,
  selected:Array.from(s.options,o=>o.selected),
  defaultSelected:Array.from(s.options,o=>o.defaultSelected),
  attribute:Array.from(s.options,o=>o.hasAttribute('selected')),
  events:trace.slice()
});
const a=[record('initial')];
s.value='quality';a.push(record('value=quality'));
s.selectedIndex=2;a.push(record('index=2'));
s.options[0].selected=true;a.push(record('option0.selected=true'));
s.value='nonexistent';a.push(record('value=nonexistent'));
s.selectedIndex=1;a.push(record('index=1'));
s.options[2].defaultSelected=true;a.push(record('option2.defaultSelected=true'));
return a;
}'''

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--chromium',default=shutil.which('chromium'))
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if not args.chromium:
        parser.error('Explicit Chromium executable required')
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=args.chromium,headless=True,
                                  args=['--no-sandbox'] if hasattr(__import__('os'),'geteuid') and __import__('os').geteuid()==0 else [])
        page=browser.new_page(viewport={'width':650,'height':200},device_scale_factor=1)
        page.set_content(HTML)
        result={
            'chromium_version':browser.version,
            'scenario':'isolated single-select',
            'original_fixtures_modified':False,
            'snapshots':page.evaluate(SCENARIO)
        }
        browser.close()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'snapshots':len(result['snapshots']),
                      'programmatic_events':sum(len(s['events']) for s in result['snapshots'])}))

if __name__=='__main__':
    main()
