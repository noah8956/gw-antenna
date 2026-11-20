#!/usr/bin/env python3
"""Collect results_sweep/*/viewer.json into one self-contained HTML page (viewer.html)."""
import glob
import json
import os
import re

runs, vfs = {}, set()
for path in sorted(glob.glob("results_sweep/*/viewer.json")):
    name = os.path.basename(os.path.dirname(path))
    m = re.match(r"(energy|eta)_(plus|cross)_vf([\d.]+)$", name)
    if not m:
        continue
    with open(path) as fh:
        d = json.load(fh)
    runs[name] = d
    vfs.add(m.group(3))
if not runs:
    raise SystemExit("No results_sweep/*/viewer.json found. Run sweep.py first.")
n = next(iter(runs.values()))["n"]
data = dict(n=n, volfracs=sorted(vfs, key=float), runs=runs)
html = open("viewer_template.html").read().replace("/*DATA*/", json.dumps(data, separators=(",", ":")))
with open("viewer.html", "w") as fh:
    fh.write(html)
print(f"Wrote viewer.html: {len(runs)} designs, {len(html)/1e6:.2f} MB")
