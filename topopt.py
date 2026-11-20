"""SIMP topology optimization of GW tidal coupling J = eta * omega for one tracked mode.

Why J = eta * omega? Every design is later rescaled laterally to put the tracked
mode exactly at 5 MHz. Under that rescaling eta ~ L ~ 1/omega. So maximizing
eta at a fixed 5 MHz is the same as maximizing the scale-invariant eta * omega
on the reference domain. No frequency constraint is needed.

Parameterization: design x -> density filter (radius r_min) -> tanh Heaviside
projection (beta continuation) -> physical density rho_bar.
  * Stiffness: SIMP E = Emin + rho_bar^p (1 - Emin), with p = 3.
  * Mass: linear, with the Pedersen-type rho^6 tail below 0.1. The tail
    suppresses spurious localized modes in void regions.
  * The minimum feature size is set by r_min together with the projection.

The adjoint is the eigenvector sensitivity (Nelson / Lee 2007 bordered system):
    [K - lam M   M phi] [psi]   [ -dJ/dphi ]
    [phi^T M       0  ] [ nu] = [ dJ/dlam  ]
    dJ/drho_e = dJ/drho_e|explicit + psi^T (K_e' - lam M_e') phi + (nu/2) phi^T M_e' phi
J is invariant to rescaling phi, so dJ/dphi . phi = 0 and nu = 0 up to roundoff.
"""
import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from coupling import POL, mac, mode_report

EMIN = 1e-9
PNORM = 64.0


# --------------------------------------------------------------------- interpolation
def simp_E(r, p=3.0):
    return EMIN + r**p * (1 - EMIN), p * r ** (p - 1) * (1 - EMIN)


def mass_interp(r):
    c = 0.1 ** -5
    m = np.where(r > 0.1, r, c * r**6)
    dm = np.where(r > 0.1, 1.0, 6 * c * r**5)
    return m, dm


def project(rt, beta, th=0.5):
    if beta <= 0:
        return rt, np.ones_like(rt)
    a, b = np.tanh(beta * th), np.tanh(beta * (1 - th))
    t = np.tanh(beta * (rt - th))
    return (a + t) / (a + b), beta * (1 - t**2) / (a + b)


# --------------------------------------------------------------------- objective
class Problem:
    """objective:
      'eta'    : J = omega * eta, the user's metric, with phi max-normalized over
                 SOLID material. A density-weighted p-norm stands in for max|phi|,
                 so displacement of void nodes cannot inflate eta.
      'energy' : J = lam * (phi.F)^2 / (phi^T M phi) / vol. This is proportional
                 to the energy deposited per unit plate volume once the design is
                 scaled to the target frequency. It does not depend on how phi is
                 normalized.
    """

    def __init__(self, mesh, pol="+", rmin=3.0, p=3.0, volfrac=0.4, objective="eta"):
        self.mesh, self.pol, self.p, self.volfrac = mesh, pol, p, volfrac
        self.objective = objective
        self.H = mesh.density_filter(rmin)
        self.c = np.array([0.5 * POL[pol][i, j] for (i, j) in [(0, 0), (0, 1), (1, 0), (1, 1)]])
        # nodal averaging of element densities: A (nn x ne)
        rows = mesh.enodes.ravel()
        cols = np.repeat(np.arange(mesh.ne), 4)
        A = sp.csr_matrix((np.ones(rows.size), (rows, cols)), shape=(mesh.nn, mesh.ne))
        self.A = sp.diags(1.0 / np.asarray(A.sum(1)).ravel()) @ A
        self.Fe = sum(self.c[k] * mesh.Ge[k] for k in range(4))

    def physical(self, x, beta):
        rt = self.H @ x
        rb, drb = project(rt, beta)
        return rb, drb

    def system(self, rb):
        E, dE = simp_E(rb, self.p)
        m, dm = mass_interp(rb)
        K, M = self.mesh.assemble(E, m)
        G = self.mesh.tidal_basis(m)
        return K, M, G, (E, dE, m, dm, rb)

    def node_weight(self, rb):
        rn = self.A @ rb
        return rn**3, 3 * rn**2

    def J_value(self, lam, phi, M, G, aux):
        return self.J_and_grad(lam, phi, None, M, G, aux, need_grad=False)[0]

    def select_mode(self, lam, V, M, G, phi_prev=None, mode="auto", chi_min=0.05, aux=None):
        """Pick the tracked mode. With phi_prev set, track by MAC. Otherwise use
        'auto' (the lowest elastic mode with J >= chi_min * max J), 'best' (max J),
        or an integer index into the elastic modes."""
        if phi_prev is not None:
            macs = np.array([mac(V[:, k], phi_prev, M) for k in range(V.shape[1])])
            return int(np.argmax(macs)), macs.max()
        Js = np.array([self.J_value(lam[k], V[:, k], M, G, aux) for k in range(V.shape[1])])
        if mode == "best":
            return int(np.argmax(Js)), 1.0
        if mode == "auto":
            ok = np.nonzero(Js >= chi_min * Js.max())[0]
            return int(ok[0]), 1.0
        return int(mode), 1.0

    def J_and_grad(self, lam, phi, K, M, G, aux, need_grad=True):
        mesh = self.mesh
        E, dE, m, dm, rb = aux
        phi = phi / np.sqrt(phi @ (M @ phi))  # M-normalized, so phi^T M phi = 1
        F = self.c @ G
        s = phi @ F
        if s < 0:                              # fix the sign so that s > 0
            phi, s = -phi, -s
        u = phi.reshape(-1, 2)
        if self.objective == "energy":
            vol = rb.mean()
            J = lam * s**2 / vol
            if not need_grad:
                return J, None
            g = J * (2 * F / s - 2 * (M @ phi))
            dJdlam = J / lam
            explicit_P = 0.0
        else:
            w, dw = self.node_weight(rb)
            a = (u**2).sum(1)
            amax = (w * a).max()
            an = a / amax
            S = (w * an ** (PNORM / 2)).sum()
            P = np.sqrt(amax) * S ** (1 / PNORM)   # smooth max over solid of |u|
            J = np.sqrt(lam) * s * P
            if not need_grad:
                return J, None
            dP_du = P * (w * an ** (PNORM / 2 - 1))[:, None] * u / (amax * S)
            g = J * (F / s + dP_du.ravel() / P - 2 * (M @ phi))
            dJdlam = J / (2 * lam)
            dP_dw = P / PNORM * an ** (PNORM / 2) / S
            explicit_P = J / P * (self.A.T @ (dP_dw * dw))
        Mphi = M @ phi
        Abig = sp.bmat([[K - lam * M, Mphi[:, None]], [Mphi[None, :], None]], format="csc")
        sol = spla.spsolve(Abig, np.concatenate([-g, [dJdlam]]))
        psi, nu = sol[:-1], sol[-1]
        pe = phi[mesh.edof]
        se = psi[mesh.edof]
        Ke_phi = pe @ mesh.Ke.T
        Me_phi = pe @ mesh.Me.T
        dK = dE * np.einsum("ei,ei->e", se, Ke_phi)
        dMterm = dm * np.einsum("ei,ei->e", se, Me_phi)
        phiMphi_e = dm * np.einsum("ei,ei->e", pe, Me_phi)
        dF = dm * np.einsum("ei,ei->e", pe, self.Fe)
        if self.objective == "energy":
            dJ = J * (2 * dF / s - phiMphi_e - 1.0 / (mesh.ne * vol))
        else:
            dJ = J * (dF / s - phiMphi_e) + explicit_P
        dJ = dJ + dK - lam * dMterm + 0.5 * nu * phiMphi_e
        return J, dJ


# --------------------------------------------------------------------- MMA (m = 1)
class MMA:
    """Svanberg's MMA (1987) for one inequality constraint. The convex
    separable subproblem is solved exactly through its 1-D dual (bisection)."""

    def __init__(self, n, move=0.1, asyinit=0.5, asyincr=1.2, asydecr=0.7):
        self.move, self.asyinit, self.asyincr, self.asydecr = move, asyinit, asyincr, asydecr
        self.xold1 = self.xold2 = None
        self.low = self.upp = None
        self.it = 0

    def step(self, x, f0, df0, g1, dg1, xmin=0.0, xmax=1.0):
        self.it += 1
        dx = xmax - xmin
        if self.it <= 2:
            low, upp = x - self.asyinit * dx, x + self.asyinit * dx
        else:
            z = (x - self.xold1) * (self.xold1 - self.xold2)
            gam = np.where(z > 0, self.asyincr, np.where(z < 0, self.asydecr, 1.0))
            low = x - gam * (self.xold1 - self.low)
            upp = x + gam * (self.upp - self.xold1)
            low = np.clip(low, x - 10 * dx, x - 0.01 * dx)
            upp = np.clip(upp, x + 0.01 * dx, x + 10 * dx)
        alpha = np.maximum.reduce([np.full_like(x, xmin), low + 0.1 * (x - low), x - self.move * dx])
        beta = np.minimum.reduce([np.full_like(x, xmax), upp - 0.1 * (upp - x), x + self.move * dx])

        def pq(df):
            ux, xl = (upp - x) ** 2, (x - low) ** 2
            reg = 1e-5 / dx
            p = ux * (1.001 * np.maximum(df, 0) + 0.001 * np.maximum(-df, 0) + reg)
            q = xl * (0.001 * np.maximum(df, 0) + 1.001 * np.maximum(-df, 0) + reg)
            return p, q

        p0, q0 = pq(df0)
        p1, q1 = pq(dg1)
        r1 = g1 - np.sum(p1 / (upp - x) + q1 / (x - low))

        def xsol(lmb):
            P, Q = p0 + lmb * p1, q0 + lmb * q1
            sp_, sq = np.sqrt(P), np.sqrt(Q)
            xs = (sp_ * low + sq * upp) / (sp_ + sq)
            return np.clip(xs, alpha, beta)

        def gval(xs):
            return r1 + np.sum(p1 / (upp - xs) + q1 / (xs - low))

        xs = xsol(0.0)
        if gval(xs) > 0:
            lo, hi = 0.0, 1.0
            while gval(xsol(hi)) > 0 and hi < 1e12:
                hi *= 2
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if gval(xsol(mid)) > 0:
                    lo = mid
                else:
                    hi = mid
            xs = xsol(hi)
        self.xold2, self.xold1 = self.xold1, x.copy()
        if self.xold2 is None:
            self.xold2 = x.copy()
        self.low, self.upp = low, upp
        return xs


# --------------------------------------------------------------------- driver
def _solve_modes(mesh, K, M, phi_prev, mode, n_eig, lam_prev):
    if phi_prev is None or mode == "best":
        return mesh.elastic_modes(K, M, k=n_eig + 3)
    lam, V = mesh.eig(K, M, k=n_eig, sigma=0.9 * lam_prev)
    good = lam > 1e-6 * abs(lam).max()
    return lam[good], V[:, good]


def optimize(problem, x0=None, betas=(1, 2, 4, 8, 16, 32), max_per_stage=50,
             max_iter=300, tol=0.01, n_eig=8, mode="auto", move=0.1, verbose=True):
    mesh = problem.mesh
    x = np.full(mesh.ne, problem.volfrac) if x0 is None else x0.copy()
    opt = MMA(mesh.ne, move=move)
    hist = []
    phi_prev, lam_prev, J0 = None, None, None
    it = 0
    stop = False
    t0 = time.time()
    for beta in betas:
        if stop:
            break
        for k in range(max_per_stage):
            if it >= max_iter:
                break
            rb, drb = problem.physical(x, beta)
            K, M, G, aux = problem.system(rb)
            try:
                lam, V = _solve_modes(mesh, K, M, phi_prev, mode, n_eig, lam_prev)
            except Exception as err:  # eigen-solver failure on a degenerate design
                print(f"Stopping at iteration {it}: eigensolver failed ({type(err).__name__}). "
                      f"Keeping the last design.", flush=True)
                stop = True
                break
            # mode == "best": re-pick the max-J mode every iteration (switching allowed)
            idx, mac_v = problem.select_mode(lam, V, M, G, None if mode == "best" else phi_prev, mode, aux=aux)
            if mode == "best" and phi_prev is not None:
                from coupling import mac as _mac
                mac_v = _mac(V[:, idx], phi_prev, M)
            phi, lm = V[:, idx], lam[idx]
            J, dJ = problem.J_and_grad(lm, phi, K, M, G, aux)
            if J0 is None:
                J0 = J
            vol = rb.mean()
            dJdx = problem.H.T @ (dJ * drb)
            dVdx = problem.H.T @ (drb / mesh.ne)
            xnew = opt.step(x, -J / J0, -dJdx / J0, vol / problem.volfrac - 1,
                            dVdx / problem.volfrac)
            change = np.abs(xnew - x).max()
            mnd = 4 * np.mean(rb * (1 - rb))
            hist.append(dict(it=it, beta=beta, J=J, f0=np.sqrt(lm) / (2 * np.pi), vol=vol,
                             mnd=mnd, mac=mac_v, change=change))
            if verbose:
                print(f"it {it:3d} beta {beta:4.0f}  J/J0 {J/J0:8.4f}  f0 {hist[-1]['f0']:8.1f} Hz"
                      f"  vol {vol:.3f}  MND {mnd:.3f}  MAC {mac_v:.3f}  dx {change:.3f}"
                      f"  [{time.time()-t0:5.1f}s]", flush=True)
            x = xnew
            phi_prev, lam_prev = phi, lm
            it += 1
            if change < tol and k > 5:
                break
    rb, _ = problem.physical(x, betas[-1])
    return x, rb, hist


def evaluate(problem, rb, phi_ref=None, n_modes=12, mode="auto"):
    """Elastic modes of a fixed physical design, plus the selected mode's report."""
    mesh = problem.mesh
    K, M, G, aux = problem.system(rb)
    lam, V = mesh.elastic_modes(K, M, k=n_modes)
    idx, _ = problem.select_mode(lam, V, M, G, phi_ref, mode, aux=aux)
    m = aux[2]
    reps = [mode_report(mesh, lam[k], V[:, k], G, M, m, problem.pol, rb) for k in range(len(lam))]
    return reps, idx, (K, M, G, aux)


def check_grad(problem, beta=2.0, n_check=6, h=1e-6, seed=0):
    """Finite-difference check of dJ/dx for the selected mode."""
    rng = np.random.default_rng(seed)
    mesh = problem.mesh
    x = np.clip(problem.volfrac + 0.2 * rng.standard_normal(mesh.ne), 0.05, 1)

    def Jx(xx, phi_ref=None, need_grad=False):
        rb, drb = problem.physical(xx, beta)
        K, M, G, aux = problem.system(rb)
        lam, V = mesh.elastic_modes(K, M, k=12)
        idx, _ = problem.select_mode(lam, V, M, G, phi_ref, "auto", aux=aux)
        J, dJ = problem.J_and_grad(lam[idx], V[:, idx], K, M, G, aux, need_grad)
        return J, (problem.H.T @ (dJ * drb) if need_grad else None), V[:, idx]

    J, g, phi = Jx(x, need_grad=True)
    errs = []
    for e in rng.choice(mesh.ne, n_check, replace=False):
        xp, xm = x.copy(), x.copy()
        xp[e] += h
        xm[e] -= h
        fd = (Jx(xp, phi)[0] - Jx(xm, phi)[0]) / (2 * h)
        errs.append((e, g[e], fd, abs(g[e] - fd) / (abs(fd) + 1e-30 * abs(J))))
    return errs
