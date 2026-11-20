#!/usr/bin/env python3
"""Proof of concept: does a topology-optimized SC-cut quartz plate couple more
strongly to MHz gravitational waves than a plain disk of equal volume at the
same frequency?

    python run_poc.py --selftest
    python run_poc.py --quick
    python run_poc.py                  # full run (100x100 mesh, up to 300 its)
"""
import argparse
import json
import os
import warnings

import numpy as np

# numpy 2.x + macOS Accelerate emits spurious FP warnings from matmul.
warnings.filterwarnings("ignore", message=".*encountered in matmul")

from quartz import (RHO_QUARTZ, sc_cut_plane_stress_D, quartz_C, rotate_C, rot_x, rot_z,
                    isotropic_plane_stress_D)
from fem import DiskMesh
from coupling import POL, scale_to_target, mode_report, max_normalize
from topopt import Problem, optimize, evaluate, check_grad
import waveforms as wf


# ============================================================== self test
def selftest():
    ok = True

    def report(name, cond, info=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {info}")

    D = sc_cut_plane_stress_D()
    report("SC-cut D symmetric positive definite",
           np.allclose(D, D.T) and np.all(np.linalg.eigvalsh(D) > 0),
           f"eig(D) = {np.round(np.linalg.eigvalsh(D)/1e9, 2)} GPa")
    # Isotropic C is invariant under rotation (checks the Bond matrix)
    lam_, mu_ = 50e9, 30e9
    Ciso = np.zeros((6, 6))
    Ciso[:3, :3] = lam_
    Ciso[np.arange(3), np.arange(3)] += 2 * mu_
    Ciso[np.arange(3, 6), np.arange(3, 6)] = mu_
    a = rot_x(0.4) @ rot_z(1.1)
    report("Bond rotation preserves an isotropic tensor", np.allclose(rotate_C(Ciso, a), Ciso, atol=1e-9 * Ciso.max()))
    report("Rotation by 0 leaves quartz unchanged", np.allclose(rotate_C(quartz_C(), np.eye(3)), quartz_C()))

    mesh = DiskMesh(30, D, RHO_QUARTZ)
    pr = Problem(mesh, "+", rmin=2.0)
    K, M, G, aux = pr.system(np.ones(mesh.ne))
    lam, V = mesh.eig(K, M, k=6)
    report("Free-free plate has 3 rigid-body modes",
           np.all(np.abs(lam[:3]) < 1e-6 * lam[3]) and lam[3] > 0,
           f"lam[:4] = {lam[:4]}")

    # Mesh convergence of the lowest elastic mode
    f = []
    for n in (30, 60):
        m_ = DiskMesh(n, D, RHO_QUARTZ)
        p_ = Problem(m_, "+", rmin=2.0)
        reps, idx, _ = evaluate(p_, np.ones(m_.ne))
        f.append(reps[idx]["f0"])
    report("Mesh convergence of the tracked disk mode (n=30 vs n=60, < 3%)",
           abs(f[0] - f[1]) / f[1] < 0.03, f"f0 = {f[0]:.1f}, {f[1]:.1f} Hz at W0 = 1 m")

    # eta is invariant to the sign of phi; eta*omega is invariant to lateral scale
    lam_e, V_e = mesh.elastic_modes(K, M)
    r1 = mode_report(mesh, lam_e[0], V_e[:, 0], G, M, aux[2], "+")
    r2 = mode_report(mesh, lam_e[0], -V_e[:, 0], G, M, aux[2], "+")
    report("eta invariant to phi -> -phi", np.isclose(r1["eta0"], r2["eta0"]))
    mesh2 = DiskMesh(30, D, RHO_QUARTZ, W0=2.0)
    K2, M2 = mesh2.assemble(np.ones(mesh2.ne), np.ones(mesh2.ne))
    G2 = mesh2.tidal_basis(np.ones(mesh2.ne))
    l2, V2 = mesh2.elastic_modes(K2, M2)
    r3 = mode_report(mesh2, l2[0], V2[:, 0], G2, M2, np.ones(mesh2.ne), "+")
    report("Scaling L by 2: f/2, eta*2, J unchanged",
           np.isclose(r3["f0"], r1["f0"] / 2, rtol=1e-6) and np.isclose(r3["eta0"], 2 * r1["eta0"], rtol=1e-6)
           and np.isclose(r3["J"], r1["J"], rtol=1e-6))
    report("Participation chi in [0, 1]", 0 <= r1["chi"] <= 1 + 1e-9, f"chi = {r1['chi']:.3f}")

    # Isotropic disk: the lowest elastic mode is a degenerate quadrupolar pair
    Di = isotropic_plane_stress_D(76.5e9, 0.17)
    mi = DiskMesh(40, Di, 2200.0)
    Ki, Mi = mi.assemble(np.ones(mi.ne), np.ones(mi.ne))
    li, _ = mi.elastic_modes(Ki, Mi)
    report("Isotropic disk: lowest modes form a near-degenerate pair (< 1% split)",
           abs(li[1] - li[0]) / li[0] < 0.01, f"f = {np.sqrt(li[:3])/2/np.pi}")

    errs = check_grad(Problem(DiskMesh(24, D, RHO_QUARTZ), "+", rmin=2.0))
    worst = max(e[3] for e in errs if abs(e[2]) > 1e-3 * max(abs(x[2]) for x in errs))
    report("Adjoint gradient vs central finite differences (< 1e-4 rel)", worst < 1e-4,
           f"worst rel err = {worst:.2e}")
    print("\nSELFTEST", "PASSED" if ok else "FAILED")
    return ok


# ============================================================== plotting
def grid_field(mesh, vals):
    A = np.full((mesh.n, mesh.n), np.nan)
    A[mesh.ix, mesh.iy] = vals
    return A.T  # imshow: rows = y


def element_umag(mesh, phi):
    u = max_normalize(phi).reshape(-1, 2)
    return np.sqrt((u[mesh.enodes] ** 2).sum(2)).mean(1)


def plot_all(out, mesh, rb, rcon, rep_d, rep_o, hist, wave_plots, obj):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def extent(rep):
        w = rep["width"] * 1e3
        return [-w / 2, w / 2, -w / 2, w / 2]

    # --- geometry + mode shapes
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.8))
    im = ax[0].imshow(grid_field(mesh, rb), origin="lower", cmap="Greys", vmin=0, vmax=1,
                      extent=extent(rep_o))
    ax[0].set_title(f"Optimized density, objective={obj} (width {rep_o['width']*1e3:.3f} mm)")
    plt.colorbar(im, ax=ax[0], fraction=0.046)
    for a, rep, mask, title in [
        (ax[1], rep_d, np.ones(mesh.ne), "Disk"),
        (ax[2], rep_o, rcon, "Optimized (binary, connected)")]:
        um = element_umag(mesh, rep["phi"])
        um = np.where(mask > 0.5, um, np.nan)
        im = a.imshow(grid_field(mesh, um), origin="lower", cmap="viridis", extent=extent(rep))
        u = max_normalize(rep["phi"]).reshape(-1, 2)
        s = rep["width"] * 1e3 / mesh.W0
        step = max(1, mesh.n // 14)
        sel = (np.round((mesh.xn[:, 0] + 0.5) / mesh.h) % step == 0) & \
              (np.round((mesh.xn[:, 1] + 0.5) / mesh.h) % step == 0)
        # only show arrows on solid material
        node_solid = np.zeros(mesh.nn)
        np.maximum.at(node_solid, mesh.enodes.ravel(), np.repeat(mask, 4))
        sel &= node_solid > 0.5
        a.quiver(mesh.xn[sel, 0] * s, mesh.xn[sel, 1] * s, u[sel, 0], u[sel, 1], color="w", scale=18)
        a.set_title(f"{title}: |phi| at {rep['f']/1e6:.2f} MHz, eta={rep['eta']*1e6:.1f} um")
        plt.colorbar(im, ax=a, fraction=0.046)
        a.set_xlabel("x [mm]")
    ax[0].set_xlabel("x [mm]")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "geometry_and_modes.png"), dpi=140)
    plt.close(fig)

    # --- convergence
    if hist:
        fig, ax = plt.subplots(1, 3, figsize=(14, 3.8))
        it = [h["it"] for h in hist]
        ax[0].plot(it, [h["J"] / hist[0]["J"] for h in hist])
        ax[0].axhline(1.0, ls="--", c="k")
        ax[0].set_title(f"objective J ({obj}), normalized to the disk")
        ax[1].plot(it, [h["vol"] for h in hist], label="volume fraction")
        ax[1].plot(it, [h["mnd"] for h in hist], label="non-discreteness")
        ax[1].plot(it, [h["mac"] for h in hist], label="MAC (tracking)")
        ax[1].legend()
        ax[2].plot(it, [h["f0"] for h in hist])
        ax[2].set_title("tracked f at W0 = 1 m [Hz]")
        for a in ax:
            a.set_xlabel("iteration")
        fig.tight_layout()
        fig.savefig(os.path.join(out, "convergence.png"), dpi=140)
        plt.close(fig)

    # --- waveform responses
    fig, ax = plt.subplots(len(wave_plots), 2, figsize=(13, 3.3 * len(wave_plots)))
    ax = np.atleast_2d(ax)
    for r, (name, t, hp, hc, qd, qo) in enumerate(wave_plots):
        ax[r, 0].plot(t * 1e6, hp, lw=0.6, label="h+")
        ax[r, 0].plot(t * 1e6, hc, lw=0.6, label="hx", alpha=0.7)
        ax[r, 0].set_title(f"{name}: strain")
        ax[r, 0].set_xlabel("t [us]")
        ax[r, 0].legend()
        ax[r, 1].plot(t * 1e6, qd, lw=0.6, label="disk")
        ax[r, 1].plot(t * 1e6, qo, lw=0.6, label="optimized", alpha=0.8)
        ax[r, 1].set_title(f"{name}: peak modal displacement [m]")
        ax[r, 1].set_xlabel("t [us]")
        ax[r, 1].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out, "waveform_response.png"), dpi=140)
    plt.close(fig)


# ============================================================== viewer export
def mode_arrows(mesh, rep, mask, step=3):
    """Subsampled nodal displacement arrows on solid material, in reference units."""
    u = max_normalize(rep["phi"]).reshape(-1, 2)
    node_solid = np.zeros(mesh.nn)
    np.maximum.at(node_solid, mesh.enodes.ravel(), np.repeat(mask, 4))
    gi = np.round((mesh.xn[:, 0] + mesh.W0 / 2) / mesh.h).astype(int)
    gj = np.round((mesh.xn[:, 1] + mesh.W0 / 2) / mesh.h).astype(int)
    sel = (gi % step == 0) & (gj % step == 0) & (node_solid > 0.5)
    return [[round(float(mesh.xn[k, 0] / mesh.W0 + 0.5), 4), round(float(mesh.xn[k, 1] / mesh.W0 + 0.5), 4),
             round(float(u[k, 0]), 3), round(float(u[k, 1]), 3)] for k in np.nonzero(sel)[0]]


def export_viewer(out, mesh, rb, rcon, disk, opt, hist, summary):
    def grid(vals, mask=None, nd=3):
        A = np.full((mesh.n, mesh.n), -1.0)
        v = np.round(vals, nd)
        if mask is not None:
            v = np.where(mask > 0.5, v, -1.0)
        A[mesh.iy, mesh.ix] = v  # row = y
        return A.tolist()
    data = dict(
        n=mesh.n, summary={k: v for k, v in summary.items() if k != "designs"},
        designs=summary["designs"],
        density=grid(rb, nd=2), binary=grid(rcon, nd=0),
        phi_opt=grid(element_umag(mesh, opt["phi"]), rcon), phi_disk=grid(element_umag(mesh, disk["phi"])),
        arrows_opt=mode_arrows(mesh, opt, rcon), arrows_disk=mode_arrows(mesh, disk, np.ones(mesh.ne)),
        width_opt_mm=opt["width"] * 1e3, width_disk_mm=disk["width"] * 1e3,
        history=[dict(it=h["it"], J=round(h["J"] / hist[0]["J"], 4), vol=round(h["vol"], 4),
                      beta=h["beta"]) for h in hist],
    )
    with open(os.path.join(out, "viewer.json"), "w") as fh:
        json.dump(data, fh, default=float, separators=(",", ":"))


# ============================================================== main
def largest_component(rbin, mesh):
    """Keep only the largest edge-connected solid region. Floating islands can't
    be part of one free-free plate."""
    from scipy import ndimage
    A = np.zeros((mesh.n, mesh.n), dtype=bool)
    A[mesh.ix, mesh.iy] = rbin > 0.5
    lab, nlab = ndimage.label(A)
    if nlab == 0:
        return rbin, 0
    sizes = ndimage.sum(A, lab, range(1, nlab + 1))
    keep = lab == (1 + int(np.argmax(sizes)))
    return keep[mesh.ix, mesh.iy].astype(float), nlab


def design_reports(pr, rb, n_modes=16):
    """Mode reports for a fixed design. phi is max-normalized over solid nodes."""
    mesh = pr.mesh
    K, M, G, aux = pr.system(rb)
    lam, V = mesh.elastic_modes(K, M, k=n_modes)
    afrac = rb.sum() * mesh.h**2
    reps = [mode_report(mesh, lam[k], V[:, k], G, M, aux[2], pr.pol, rb) for k in range(len(lam))]
    for r in reps:
        # energy coupling per unit volume once scaled to the target frequency, up to a
        # design-independent constant: Gamma/V ~ omega0^2 Gamma0 / area
        r["EV0"] = r["omega0"] ** 2 * r["Gamma0"] / afrac
    return reps, afrac


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check-grad", action="store_true")
    ap.add_argument("--quick", action="store_true", help="40x40 mesh, about 60 iterations")
    ap.add_argument("--objective", choices=["eta", "energy"], default="eta",
                    help="eta = the brief's metric (max-normalized phi); energy = deposited energy per volume")
    ap.add_argument("--n", type=int, default=100, help="elements across the domain")
    ap.add_argument("--pol", choices=["+", "x"], default="+")
    ap.add_argument("--mode", default="best",
                    help="'best' = re-pick the max-J mode every iteration; 'auto' = MAC-track the lowest "
                         "coupled mode; or an elastic-mode index")
    ap.add_argument("--rmin", type=float, default=None, help="filter radius in elements (default n/20)")
    ap.add_argument("--volfrac", type=float, default=0.4)
    ap.add_argument("--start", choices=["disk", "uniform"], default="disk")
    ap.add_argument("--f-target", type=float, default=5e6)
    ap.add_argument("--max-iter", type=int, default=300)
    ap.add_argument("--move", type=float, default=0.05, help="MMA move limit")
    ap.add_argument("--Qm", type=float, default=1e6, help="mechanical Q of the mode")
    ap.add_argument("--T", type=float, default=4.0, help="temperature for the kT SNR proxy [K]")
    ap.add_argument("--disk-aspect", type=float, default=0.1, help="disk thickness / diameter")
    ap.add_argument("--burst-h0", type=float, default=1e-20, help="illustrative burst amplitude")
    ap.add_argument("--waveform-file", default=None, help="CSV t,h+,hx (e.g. scaled NR)")
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--out", default=None, help="output directory (default results_<objective>)")
    args = ap.parse_args()

    if args.selftest:
        raise SystemExit(0 if selftest() else 1)
    if args.check_grad:
        D = sc_cut_plane_stress_D()
        for obj in ("eta", "energy"):
            print(f"objective = {obj}")
            for e in check_grad(Problem(DiskMesh(24, D, RHO_QUARTZ), args.pol, rmin=2.0, objective=obj)):
                print("  elem %5d  adjoint % .6e  fd % .6e  rel %.2e" % e)
        return

    if args.quick:
        args.n = 40
        betas, per_stage, args.max_iter = (2, 4, 8, 16), 15, min(args.max_iter, 60)
    else:
        betas, per_stage = (2, 4, 8, 16, 32), 50
    if args.rmin is None:
        args.rmin = max(2.0, args.n / 20)
    out = args.out or f"results_{args.objective}" + ("_quick" if args.quick else "")
    os.makedirs(out, exist_ok=True)

    D = sc_cut_plane_stress_D()
    mesh = DiskMesh(args.n, D, RHO_QUARTZ)
    pr = Problem(mesh, args.pol, rmin=args.rmin, volfrac=args.volfrac, objective=args.objective)
    print(f"Mesh {args.n}x{args.n}: {mesh.ne} elements, {mesh.ndof} DOFs. Polarization {args.pol}. "
          f"Objective {args.objective}.")

    # ---------------- baseline disk
    ones = np.ones(mesh.ne)
    reps_d, afrac_d = design_reports(pr, ones)
    i_low = next(k for k, r in enumerate(reps_d) if r["chi"] > 0.05)
    i_eta = int(np.argmax([r["J"] for r in reps_d]))
    i_en = int(np.argmax([r["EV0"] for r in reps_d]))
    print("\nDisk elastic modes (reference width W0 = 1 m):")
    for k, r in enumerate(reps_d):
        tags = [t for t, i in (("lowest coupled", i_low), ("best eta", i_eta), ("best energy", i_en)) if i == k]
        print(f"  {k:2d}  f0 {r['f0']:8.1f} Hz  eta*w {r['J']:9.2f}  chi(+/x) {r['chi']:.3f}/{r['chi_other']:.3f}"
              f"  {', '.join(tags)}")

    # ---------------- optimize
    x0 = ones.copy() if args.start == "disk" else None
    x, rb, hist = optimize(pr, x0=x0, betas=betas, max_per_stage=per_stage, max_iter=args.max_iter,
                           mode=args.mode, move=args.move)
    rcon, ncomp = largest_component((rb > 0.5).astype(float), mesh)
    reps_g, afrac_g = design_reports(pr, rb)
    reps_c, afrac_c = design_reports(pr, rcon)
    key = "J" if args.objective == "eta" else "EV0"
    i_g = int(np.argmax([r[key] for r in reps_g]))
    i_c = int(np.argmax([r[key] for r in reps_c]))

    # ---------------- scale to the target frequency at equal volume
    W_d = reps_d[i_low]["f0"] / args.f_target
    V_target = args.disk_aspect * W_d * afrac_d * W_d**2

    def phys(rep, afrac):
        W = rep["f0"] / args.f_target
        return scale_to_target(rep, args.f_target, thickness=V_target / (afrac * W**2), area_frac=afrac)

    rows = {
        "disk, lowest coupled mode": phys(reps_d[i_low], afrac_d),
        "disk, best-eta mode": phys(reps_d[i_eta], afrac_d),
        "disk, best-energy mode": phys(reps_d[i_en], afrac_d),
        "optimized (gray densities)": phys(reps_g[i_g], afrac_g),
        "optimized (binary, connected)": phys(reps_c[i_c], afrac_c),
    }
    disk_eta, disk_en = rows["disk, best-eta mode"], rows["disk, best-energy mode"]
    opt = rows["optimized (binary, connected)"]
    omega = 2 * np.pi * args.f_target

    # ---------------- literature waveforms
    print("\nBuilding literature waveform models ...")
    tc, hpc, hcc, _ = wf.pbh_inspiral()
    tb, hpb, hcb = wf.sine_gaussian_burst(h0=args.burst_h0)
    cw = wf.boson_cloud_cw(f_gw=args.f_target)
    waves = [("PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN)", tc, hpc, hcc),
             (f"BAW-event sine-Gaussian 5.506 MHz, h0={args.burst_h0:g} (illustrative)", tb, hpb, hcb)]
    if args.waveform_file:
        t_, p_, c_ = wf.load_waveform_csv(args.waveform_file)
        waves.append((os.path.basename(args.waveform_file), t_, p_, c_))
    kT = wf.KB * args.T
    cmp_designs = {"disk": disk_en, "opt": opt}
    wave_rows, wave_plots = [], []
    for name, t, hp, hc in waves:
        row = dict(waveform=name, peak_strain=float(np.max(np.hypot(hp, hc))))
        for dn, d in cmp_designs.items():
            E = wf.deposited_energy(t, hp, hc, d["Q"], d["Mn"], omega)
            row[f"E_{dn}"], row[f"SNR_{dn}"] = E, E / kT
        wave_rows.append(row)
        wave_plots.append((name, t, hp, hc,
                           wf.modal_time_response(t, hp, hc, disk_en["Q"], disk_en["Mn"], omega, args.Qm),
                           wf.modal_time_response(t, hp, hc, opt["Q"], opt["Mn"], omega, args.Qm)))
    row = dict(waveform=f"Boson-cloud CW (mu={cw['mu_eV']:.3g} eV, M_BH={cw['M_bh']:.2g} Msun, 1 kpc), "
                        f"steady state", peak_strain=cw["h0"])
    for dn, d in cmp_designs.items():
        qa, E, tring = wf.cw_steady_state(cw["hp"], cw["hc"], d["Q"], d["Mn"], omega, args.Qm)
        row[f"E_{dn}"], row[f"SNR_{dn}"], row[f"q_{dn}_m"] = E, E / kT, qa
    row["ring_up_time_s"] = tring
    wave_rows.append(row)
    for r in wave_rows:
        r["E_ratio"] = r["E_opt"] / r["E_disk"]
    sky = {dn: wf.sky_averaged_gamma(d["Q"], d["Mn"]) / d["volume"] for dn, d in cmp_designs.items()}

    # ---------------- summary
    e_other = POL["x" if args.pol == "+" else "+"]

    def summ(d):
        return dict(mode_f_at_W0_Hz=d["f0"], width_mm=d["width"] * 1e3, thickness_mm=d["thickness"] * 1e3,
                    t_over_w=d["thickness"] / d["width"], volume_mm3=d["volume"] * 1e9, eta_m=d["eta"],
                    eta_other_pol_m=0.5 * abs(np.sum(d["Q"] * e_other)) / d["Mn"],
                    chi=d["chi"], chi_other_pol=d["chi_other"], Mn_kg=d["Mn"],
                    Gamma_kg_m2=d["Gamma"], Gamma_per_volume_kg_per_m=d["Gamma"] / d["volume"])
    table = {k: summ(v) for k, v in rows.items()}
    r_eta = opt["eta"] / disk_eta["eta"]
    r_en = (opt["Gamma"] / opt["volume"]) / (disk_en["Gamma"] / disk_en["volume"])
    r_eta_gray = rows["optimized (gray densities)"]["eta"] / disk_eta["eta"]
    verdict = lambda r: "SUPPORTED" if r > 1.05 else ("NOT SUPPORTED" if r < 0.95 else "INCONCLUSIVE (within 5%)")
    summary = dict(objective=args.objective, polarization=args.pol, f_target_Hz=args.f_target, mesh=args.n,
                   rmin_elems=args.rmin, min_feature_um=2 * args.rmin * mesh.h * opt["width"] / mesh.W0 * 1e6,
                   volfrac=args.volfrac, final_volfrac_binary=rcon.mean(), iterations=len(hist),
                   n_solid_components_before_cleanup=int(ncomp),
                   eta_ratio=r_eta, eta_ratio_gray=r_eta_gray, energy_per_volume_ratio=r_en,
                   verdict_eta=verdict(r_eta), verdict_energy=verdict(r_en),
                   sky_avg_energy_per_volume_ratio=sky["opt"] / sky["disk"],
                   designs=table, waveforms=wave_rows, Qm=args.Qm, T_K=args.T)
    with open(os.path.join(out, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=float)

    L = [f"# GW coupling: optimized vs disk ({args.pol} polarization, {args.f_target/1e6:g} MHz, equal volume)",
         "", f"Objective optimized: **{args.objective}**, mesh {args.n}x{args.n}, r_min {args.rmin:g} elements "
         f"(about {summary['min_feature_um']:.0f} um), {len(hist)} iterations. The binary design keeps the "
         f"largest of {ncomp} solid component(s).", "",
         "| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k, v in table.items():
        L.append(f"| {k} | {v['width_mm']:.4f} | {v['thickness_mm']:.4f} | {v['t_over_w']:.2f} | "
                 f"{v['volume_mm3']:.3e} | {v['eta_m']*1e6:.2f} | {v['eta_other_pol_m']*1e6:.2f} | {v['chi']:.3f} | "
                 f"{v['Gamma_per_volume_kg_per_m']:.3e} |")
    L += ["",
          f"- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: {r_eta:.3f}, so {verdict(r_eta)}**",
          f"  - same ratio for the gray (unthresholded) design: {r_eta_gray:.3f}. A gap between the gray and binary "
          f"ratios means the optimizer exploited intermediate densities.",
          f"- **Energy coupling per volume, optimized vs disk's best-energy mode: {r_en:.3f}, so {verdict(r_en)}**",
          f"- Sky- and polarization-averaged energy per volume, optimized vs disk: {sky['opt']/sky['disk']:.3f}",
          "", f"## Literature waveforms (Qm = {args.Qm:g}; SNR proxy = deposited energy / kT at {args.T:g} K)", "",
          "| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |",
          "|---|---|---|---|---|---|---|"]
    for r in wave_rows:
        L.append(f"| {r['waveform']} | {r['peak_strain']:.2e} | {r['E_disk']:.3e} | {r['E_opt']:.3e} | "
                 f"{r['E_ratio']:.3f} | {r['SNR_disk']:.2e} | {r['SNR_opt']:.2e} |")
    md = "\n".join(L) + "\n"
    with open(os.path.join(out, "summary.md"), "w") as fh:
        fh.write(md)
    np.save(os.path.join(out, "density.npy"), grid_field(mesh, rb))
    print("\n" + md)
    disk_plot = disk_eta if args.objective == "eta" else disk_en
    export_viewer(out, mesh, rb, rcon, disk_plot, opt, hist, summary)
    if not args.no_plots:
        plot_all(out, mesh, rb, rcon, disk_plot, opt, hist, wave_plots, args.objective)
    print(f"Wrote {out}/: summary.md, summary.json, density.npy, geometry_and_modes.png, convergence.png, "
          f"waveform_response.png")


if __name__ == "__main__":
    main()
