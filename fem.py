"""Minimal 2D plane-stress Q4 FEM on a structured grid with a disk-shaped domain.

Everything is in SI units on a reference domain of width W0 = 1 m and unit
thickness. Results are rescaled to the 5 MHz target afterwards (see coupling.py):
linear elastodynamics has no intrinsic length scale.

The plate is free-free (no supports). It has three rigid-body modes, and a
uniform tidal body force does no work on elastic modes.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

GAUSS = np.array([-1.0, 1.0]) / np.sqrt(3.0)
NODE_XI = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], dtype=float)
# order of the in-plane tidal tensor components (i, j) -> G[k]
TENSOR_IJ = [(0, 0), (0, 1), (1, 0), (1, 1)]


def shape(xi, eta):
    N = 0.25 * (1 + NODE_XI[:, 0] * xi) * (1 + NODE_XI[:, 1] * eta)
    dN = 0.25 * np.stack([NODE_XI[:, 0] * (1 + NODE_XI[:, 1] * eta),
                          NODE_XI[:, 1] * (1 + NODE_XI[:, 0] * xi)])  # (2, 4)
    return N, dN


def element_matrices(D, h, rho):
    """Q4 stiffness Ke (8x8), consistent mass Me (8x8, density rho) and the
    tidal integrals for a square element of side h.

    Returns g0 (2x8x... see below):
      Nint[a]       = int N_a dA
      Nxi[a, d]     = int N_a * (x - xc)_d dA
    """
    Ke = np.zeros((8, 8))
    Me = np.zeros((8, 8))
    Nint = np.zeros(4)
    Nxi = np.zeros((4, 2))
    detJ = h * h / 4.0
    for xi in GAUSS:
        for eta in GAUSS:
            N, dN = shape(xi, eta)
            dNdx = dN * (2.0 / h)
            B = np.zeros((3, 8))
            B[0, 0::2] = dNdx[0]
            B[1, 1::2] = dNdx[1]
            B[2, 0::2] = dNdx[1]
            B[2, 1::2] = dNdx[0]
            Ke += B.T @ D @ B * detJ
            Nm = np.zeros((2, 8))
            Nm[0, 0::2] = N
            Nm[1, 1::2] = N
            Me += rho * Nm.T @ Nm * detJ
            Nint += N * detJ
            Nxi += np.outer(N, np.array([xi, eta]) * h / 2) * detJ
    return Ke, Me, Nint, Nxi


class DiskMesh:
    """n x n structured grid on [-W0/2, W0/2]^2. Elements whose centers lie
    inside the inscribed disk form the design domain."""

    def __init__(self, n, D, rho, W0=1.0):
        self.n, self.W0, self.rho, self.D = n, W0, rho, D
        h = W0 / n
        self.h = h
        ix, iy = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
        xc = (-W0 / 2 + (ix + 0.5) * h).ravel()
        yc = (-W0 / 2 + (iy + 0.5) * h).ravel()
        active = xc**2 + yc**2 <= (W0 / 2) ** 2
        self.ix, self.iy = ix.ravel()[active], iy.ravel()[active]
        self.xc = np.stack([xc[active], yc[active]], axis=1)
        self.ne = active.sum()
        # global node ids on the full grid, then compress to used nodes
        nid = lambda i, j: i * (n + 1) + j
        en = np.stack([nid(self.ix, self.iy), nid(self.ix + 1, self.iy),
                       nid(self.ix + 1, self.iy + 1), nid(self.ix, self.iy + 1)], axis=1)
        used, inv = np.unique(en, return_inverse=True)
        self.enodes = inv.reshape(en.shape)
        self.nn = used.size
        gi, gj = used // (n + 1), used % (n + 1)
        self.xn = np.stack([-W0 / 2 + gi * h, -W0 / 2 + gj * h], axis=1)
        self.ndof = 2 * self.nn
        self.edof = np.empty((self.ne, 8), dtype=np.int64)
        self.edof[:, 0::2] = 2 * self.enodes
        self.edof[:, 1::2] = 2 * self.enodes + 1
        self.iK = np.repeat(self.edof, 8, axis=1).ravel()
        self.jK = np.tile(self.edof, (1, 8)).ravel()
        self.Ke, self.Me, Nint, Nxi = element_matrices(D, h, rho)
        # Element tidal basis vectors: Ge[k][e, :] = rho * int N^T e_i x_j dA
        # for (i, j) = TENSOR_IJ[k], x measured from the domain center.
        self.Ge = []
        for (i, j) in TENSOR_IJ:
            g = np.zeros((self.ne, 8))
            g[:, i::2] = rho * (Nint[None, :] * self.xc[:, j:j + 1] + Nxi[None, :, j])
            self.Ge.append(g)

    # ------------------------------------------------------------------ assembly
    def assemble(self, Ef, mf):
        """K = sum Ef_e Ke, M = sum mf_e Me (Ef, mf are per-element factors)."""
        K = sp.csc_matrix((np.outer(Ef, self.Ke.ravel()).ravel(), (self.iK, self.jK)),
                          shape=(self.ndof, self.ndof))
        M = sp.csc_matrix((np.outer(mf, self.Me.ravel()).ravel(), (self.iK, self.jK)),
                          shape=(self.ndof, self.ndof))
        return K, M

    def tidal_basis(self, mf):
        """Global vectors G[k] with Q_ij = phi^T G[k] = int rho m(x) phi_i x_j dA."""
        out = []
        for g in self.Ge:
            v = np.zeros(self.ndof)
            np.add.at(v, self.edof, mf[:, None] * g)
            out.append(v)
        return np.array(out)  # (4, ndof)

    # ------------------------------------------------------------------ eigen
    def eig(self, K, M, k=12, sigma=None):
        """Generalized eigenpairs via shift-invert. Default sigma < 0 gives the
        lowest k modes (including the 3 rigid-body modes)."""
        if sigma is None:
            sigma = -1e-3 * (K.diagonal().mean() / M.diagonal().mean())
        try:
            lam, V = spla.eigsh(K, k=k, M=M, sigma=sigma, which="LM")
        except spla.ArpackNoConvergence:
            # clustered spectra (near-void designs): retry with a larger Krylov space
            lam, V = spla.eigsh(K, k=k, M=M, sigma=sigma, which="LM", ncv=max(4 * k, 40), maxiter=20000)
        o = np.argsort(lam)
        return lam[o], V[:, o]

    def elastic_modes(self, K, M, k=12, sigma=None):
        lam, V = self.eig(K, M, k=k, sigma=sigma)
        scale = np.abs(lam).max()
        keep = lam > 1e-6 * scale
        return lam[keep], V[:, keep]

    # ------------------------------------------------------------------ filter
    def density_filter(self, rmin_elems):
        """Linear (cone) density filter matrix H (row-normalized)."""
        r = rmin_elems
        rows, cols, vals = [], [], []
        lookup = -np.ones((self.n, self.n), dtype=np.int64)
        lookup[self.ix, self.iy] = np.arange(self.ne)
        R = int(np.ceil(r))
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                w = r - np.hypot(dx, dy)
                if w <= 0:
                    continue
                jx, jy = self.ix + dx, self.iy + dy
                ok = (jx >= 0) & (jx < self.n) & (jy >= 0) & (jy < self.n)
                nb = np.full(self.ne, -1)
                nb[ok] = lookup[jx[ok], jy[ok]]
                ok &= nb >= 0
                rows.append(np.nonzero(ok)[0])
                cols.append(nb[ok])
                vals.append(np.full(ok.sum(), w))
        H = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                          shape=(self.ne, self.ne))
        Hs = np.asarray(H.sum(axis=1)).ravel()
        return sp.diags(1.0 / Hs) @ H

    def nodal_field(self, u):
        return u.reshape(-1, 2)
