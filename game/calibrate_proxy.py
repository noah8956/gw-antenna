#!/usr/bin/env python3
"""Check that the arcade coupling proxy used in ringdown.html ranks the repo's designs like the real solver.

Proxy (same as the JS):
  pull(cell)  = cos^2(2(theta - psi))         radial tidal tug, strongest along the wave's axes
  chi_proxy   = sum(rho r^2 pull) / sum(rho r^2)   over the largest connected solid piece
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
N = 32


def to_grid(d, n=N):
    """Resample a 60x60 density (NaN outside the disk) to an n x n binary disk grid."""
    d = np.nan_to_num(d)
    m = d.shape[0]
    idx = ((np.arange(n) + 0.5) * m / n - 0.5)
    yy, xx = np.meshgrid(idx, idx, indexing="ij")
    g = ndimage.map_coordinates(d, [yy, xx], order=1) > 0.5
    return g & disk_mask(n)


def disk_mask(n=N):
    c = (np.arange(n) + 0.5) - n / 2
    yy, xx = np.meshgrid(c, c, indexing="ij")
    return xx**2 + yy**2 <= (n / 2) ** 2


def largest_piece(g):
    lab, k = ndimage.label(g)
    if k == 0:
        return g
    sizes = ndimage.sum(g, lab, range(1, k + 1))
    return lab == (1 + int(np.argmax(sizes)))


def chi_proxy(g, psi):
    g = largest_piece(g)
    c = (np.arange(N) + 0.5) - N / 2
    yy, xx = np.meshgrid(c, c, indexing="ij")
    y = -yy  # row 0 is the top of the picture
    r2 = xx**2 + y**2
    th = np.arctan2(y, xx)
    pull = np.cos(2 * (th - psi)) ** 2
    return float((g * r2 * pull).sum() / max((g * r2).sum(), 1e-9))


def start_disk(vf=0.4):
    c = (np.arange(N) + 0.5) - N / 2
    yy, xx = np.meshgrid(c, c, indexing="ij")
    return xx**2 + yy**2 <= vf * (N / 2) ** 2


def main():
    psi = {"plus": 0.0, "cross": np.pi / 4}
    shapes, ok = {}, True
    disk = start_disk()
    print(f"{'design':28s} {'proxy +':>8s} {'proxy x':>8s} {'real chi':>9s} {'real chi other':>14s}")
    print(f"{'start disk (vf 0.4)':28s} {chi_proxy(disk, psi['plus']):8.3f} {chi_proxy(disk, psi['cross']):8.3f}")
    for pol in ("plus", "cross"):
        run = os.path.join(ROOT, "results_sweep", f"energy_{pol}_vf0.4")
        g = to_grid(np.load(os.path.join(run, "density.npy")))
        s = json.load(open(os.path.join(run, "summary.json")))
        des = s["designs"]["optimized (binary, connected)"]
        pp, px = chi_proxy(g, psi["plus"]), chi_proxy(g, psi["cross"])
        print(f"{'optimized for ' + pol:28s} {pp:8.3f} {px:8.3f} {des['chi']:9.3f} {des.get('chi_other_pol', float('nan')):14.3f}")
        own, other = (pp, px) if pol == "plus" else (px, pp)
        if not (own > other and own > chi_proxy(disk, psi[pol])):
            ok = False
        shapes[pol] = ["".join("1" if v else "0" for v in row) for row in g]
    out = os.path.join(HERE, "optimizer_shapes.json")
    json.dump({"n": N, "shapes": shapes}, open(out, "w"))
    print(f"wrote {out}")
    print("RANKING OK" if ok else "RANKING MISMATCH")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
