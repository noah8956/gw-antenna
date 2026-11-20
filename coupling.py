"""GW tidal coupling metrics, mode tracking, and scaling to the target frequency.

Tidal force (proper detector frame, long-wavelength limit):
    f_i = (1/2) rho * hddot_ij * x_j
This is the geodesic-deviation result: R_i0j0 = -hddot_ij / 2. The user's brief
writes f = -rho hddot_ij x_j without the 1/2. That only rescales every eta by
the same factor 2, so the optimized/disk ratio is unchanged.

For a monochromatic wave h_ij = h e_ij cos(wt), |f| = (1/2) rho w^2 h e_ij x_j.
Then
    eta_n = |int phi_n . f dV| / (M_n w^2 h) = (1/2) |Q_n : e| / M_n,
    Q_n^ij = int rho phi_n,i x_j dV,   M_n = int rho |phi_n|^2 dV,
with phi_n normalized so that max_nodes |phi_n| = 1. eta then has units of
length.
"""
import numpy as np

POL = {
    "+": np.array([[1.0, 0.0], [0.0, -1.0]]),
    "x": np.array([[0.0, 1.0], [1.0, 0.0]]),
}


def solid_nodes(mesh, rb, thr=0.5):
    """Nodes touching at least one element with density > thr."""
    mask = np.zeros(mesh.nn, dtype=bool)
    mask[mesh.enodes[rb > thr].ravel()] = True
    return mask


def max_normalize(phi, node_mask=None):
    """Scale phi so that the largest nodal |u| over solid material is 1."""
    u = phi.reshape(-1, 2)
    a = np.sqrt((u**2).sum(1))
    if node_mask is not None:
        a = a[node_mask]
    return phi / a.max()


def modal_tensor(phi, G):
    """Q_ij = phi^T G_ij (G from DiskMesh.tidal_basis), as a 2x2 array."""
    return (G @ phi).reshape(2, 2)


def mac(a, b, M):
    return (a @ (M @ b)) ** 2 / ((a @ (M @ a)) * (b @ (M @ b)))


def eta_from(Q, Mn, e):
    return 0.5 * abs(np.sum(Q * e)) / Mn


def tidal_inertia(mesh, mf, e):
    """I_e = int rho m |e (x - x_com)|^2 dA, using element centers (O(h^2) error)."""
    w = mesh.rho * mf * mesh.h**2
    xcom = (w[:, None] * mesh.xc).sum(0) / w.sum()
    ex = (mesh.xc - xcom) @ e.T
    return (w * (ex**2).sum(1)).sum()


def chi_from(Q, Mn, I_e, e):
    """Normalization-free participation fraction in [0, 1]:
    chi = (int rho phi . e x)^2 / (M_n * int rho |e x|^2). It is the fraction of
    the tidal pattern's 'mass' that this mode captures (Cauchy-Schwarz)."""
    return np.sum(Q * e) ** 2 / (Mn * I_e)


def mode_report(mesh, lam, phi, G, M, mf, pol, rb=None):
    """Reference-domain (W0 = 1 m, unit thickness) quantities for one mode.
    phi is max-normalized over solid nodes (rb > 0.5); with rb=None, over all nodes."""
    phi = max_normalize(phi, None if rb is None else solid_nodes(mesh, rb))
    Q = modal_tensor(phi, G)
    Mn = phi @ (M @ phi)
    e = POL[pol]
    omega = np.sqrt(lam)
    eta = eta_from(Q, Mn, e)
    return dict(
        f0=omega / (2 * np.pi), omega0=omega, Q0=Q, M0=Mn, eta0=eta,
        J=eta * omega,
        Gamma0=np.sum(Q * e) ** 2 / Mn,   # normalization-free; energy ~ Gamma
        chi=chi_from(Q, Mn, tidal_inertia(mesh, mf, e), e),
        chi_other=chi_from(Q, Mn, tidal_inertia(mesh, mf, POL["x" if pol == "+" else "+"]),
                           POL["x" if pol == "+" else "+"]),
        phi=phi,
    )


def scale_to_target(rep, f_target, W0=1.0, thickness=None, area_frac=None):
    """Rescale a reference-domain mode so that it sits at f_target.

    Lateral scale s = f0/f_target, so f is proportional to 1/L. In plane stress
    the in-plane eigenfrequencies don't depend on thickness, so the thickness t
    is free and is used to equalize the volume between designs.
    Scalings: eta ~ s, M_n ~ t s^2, Q_ij ~ t s^3.
    """
    s = rep["f0"] / f_target
    out = dict(rep)
    out.update(
        scale=s, width=W0 * s, f=f_target,
        eta=rep["eta0"] * s,
    )
    if thickness is not None:
        out.update(thickness=thickness, Mn=thickness * s**2 * rep["M0"],
                   Q=thickness * s**3 * rep["Q0"],
                   Gamma=thickness * s**4 * rep["Gamma0"],
                   area=area_frac * (W0 * s) ** 2,
                   volume=thickness * area_frac * (W0 * s) ** 2)
    return out
