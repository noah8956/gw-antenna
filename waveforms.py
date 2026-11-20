"""Modeled MHz gravitational-wave signals from the recent literature, plus modal response.

There is no numerical relativity here. The plate is a weak-field, linear test
body that is much smaller than lambda_GW (about 60 m at 5 MHz), so the source and
the detector decouple:
  1. Compute h_+(t) and h_x(t) at the detector (analytic models below, or a CSV
     from NR / a surrogate).
  2. Project them into the plate frame: h_ab = h_+ e+_ab + h_x ex_ab (a, b in-plane).
  3. Apply the modal force F_n(t) = (1/2) hddot_ab(t) Q_n^ab. Q_n comes from the FEM.

Models and sources:
  * Sub-solar-mass / primordial-black-hole binary inspiral. Restricted
    post-Newtonian (PN) amplitude, with orbital evolution to 2PN (TaylorT4 form;
    Blanchet, Living Rev. Rel. 17, 2 (2014)). Inspirals that sweep through MHz
    need M_tot < ~1e-3 M_sun. This is the headline coherent source class in
    Aggarwal et al., "Challenges and opportunities of gravitational-wave
    searches above 10 kHz", Living Rev. Rel. 28, 10 (2025), arXiv:2501.11723
    (updating Living Rev. Rel. 24, 4 (2021)).
  * Superradiant boson-cloud annihilation: a quasi-monochromatic signal with
    f_GW = 2 mu c^2 / h. The order-of-magnitude amplitude scaling
    h0 ~ 6e-24 (M/10 M_sun)(alpha/0.1)^7 (1 kpc/D)(dchi/0.1) follows
    Arvanitaki et al., PRD 91, 084011 (2015) and PRD 95, 043001 (2017), and is
    reviewed in Aggarwal et al. (2025). 5 MHz needs mu ~ 1e-8 eV and, at
    alpha ~ 0.1, a ~1e-3 M_sun (primordial) black hole.
  * The BAW "rare event" burst: Goryachev et al., PRL 127, 071102 (2021),
    arXiv:2102.05859. Events were seen in the 5.506 MHz mode of a cryogenic
    quartz BAW antenna. They are modeled here as a sine-Gaussian. The amplitude
    is ILLUSTRATIVE (a CLI parameter) and not a fit to the paper. A GW origin
    for these events has been disputed (arXiv:2110.13319).
"""
import numpy as np

G = 6.67430e-11
C = 299792458.0
MSUN = 1.98847e30
KPC = 3.0857e19
HBAR = 1.054571817e-34
EV = 1.602176634e-19
KB = 1.380649e-23
TSUN = G * MSUN / C**3  # 4.925e-6 s


# ----------------------------------------------------------------- PBH inspiral
def pbh_inspiral(m1=2e-4, m2=2e-4, D_kpc=1.0, iota=0.0, f_start=1.0e6, dt=None):
    """Time-domain 2PN (TaylorT4) inspiral up to ISCO, x = 1/6.

    The masses are in M_sun. Returns (t, h_plus, h_cross, f_gw(t)).
    """
    M = m1 + m2
    nu = m1 * m2 / M**2
    Mt = M * TSUN
    f_isco = C**3 / (6**1.5 * np.pi * G * M * MSUN)
    if dt is None:
        dt = 1.0 / (40 * f_isco)

    def xdot(x):
        return (64 / 5) * nu / Mt * x**5 * (
            1 - (743 / 336 + 11 / 4 * nu) * x + 4 * np.pi * x**1.5
            + (34103 / 18144 + 13661 / 2016 * nu + 59 / 18 * nu**2) * x**2)

    x = (np.pi * Mt * f_start) ** (2 / 3)  # x = (M omega_orb)^(2/3), f_gw = 2 f_orb
    phase = 0.0
    xs, ph = [x], [phase]
    while x < 1 / 6:
        # RK4 on (x, phase)
        def rhs(xx):
            return xdot(xx), xx**1.5 / Mt
        k1 = rhs(x)
        k2 = rhs(x + 0.5 * dt * k1[0])
        k3 = rhs(x + 0.5 * dt * k2[0])
        k4 = rhs(x + dt * k3[0])
        x += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        phase += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        xs.append(x)
        ph.append(phase)
    xs, ph = np.array(xs), np.array(ph)
    t = np.arange(xs.size) * dt
    D = D_kpc * KPC
    amp = 4 * nu * (G * M * MSUN / C**2) * xs / D
    hp = -amp * (1 + np.cos(iota) ** 2) / 2 * np.cos(2 * ph)
    hc = -amp * np.cos(iota) * np.sin(2 * ph)
    # Taper the first and last few cycles (Hann) so that h -> 0 at both ends.
    fgw = xs**1.5 / (np.pi * Mt)
    w = np.ones_like(t)
    n0 = int(4 / (fgw[0] * dt))
    n1 = int(2 / (fgw[-1] * dt))
    w[:n0] = 0.5 * (1 - np.cos(np.pi * np.arange(n0) / n0))
    w[-n1:] = 0.5 * (1 + np.cos(np.pi * np.arange(n1) / n1))
    return t, hp * w, hc * w, fgw


# ----------------------------------------------------------------- boson cloud CW
def boson_cloud_cw(f_gw=5e6, alpha=0.1, D_kpc=1.0, dchi=0.1, iota=0.0):
    """Quasi-monochromatic annihilation signal, tuned to f_gw (a best-case resonant
    search). Returns the parameters and polarization amplitudes."""
    mu_eV = 2 * np.pi * HBAR * f_gw / 2 / EV  # f_gw = 2 mu c^2 / h
    mu_s = mu_eV * EV / HBAR                  # mu c^2 / hbar, in 1/s
    M_bh = alpha / (mu_s * TSUN)              # alpha = G M mu / (hbar c)
    h0 = 6e-24 * (M_bh / 10) * (alpha / 0.1) ** 7 * (1 / D_kpc) * (dchi / 0.1)
    return dict(f=f_gw, mu_eV=mu_eV, M_bh=M_bh, h0=h0,
                hp=h0 * (1 + np.cos(iota) ** 2) / 2, hc=h0 * np.cos(iota))


# ----------------------------------------------------------------- BAW burst
def sine_gaussian_burst(f0=5.506e6, Qsg=9.0, h0=1e-20, pol_angle=0.0, dt=None):
    """Sine-Gaussian burst (the Goryachev et al. 2021 event morphology class).
    The h0 default is illustrative."""
    tau = Qsg / (np.sqrt(2) * np.pi * f0)
    if dt is None:
        dt = 1 / (40 * f0)
    t = np.arange(-6 * tau, 6 * tau, dt)
    env = h0 * np.exp(-(t / tau) ** 2)
    hp = env * np.cos(2 * np.pi * f0 * t) * np.cos(2 * pol_angle)
    hc = env * np.cos(2 * np.pi * f0 * t) * np.sin(2 * pol_angle)
    return t - t[0], hp, hc


def load_waveform_csv(path, mass_scale=1.0, dist_scale=1.0):
    """Load (t, h+, hx) from a CSV, e.g. an SXS/NR waveform. Vacuum GR is scale-free:
    t -> mass_scale * t and h -> h * mass_scale / dist_scale."""
    d = np.loadtxt(path, delimiter=",", comments="#")
    return d[:, 0] * mass_scale, d[:, 1] * mass_scale / dist_scale, d[:, 2] * mass_scale / dist_scale


# ----------------------------------------------------------------- response
E_PLUS = np.array([[1.0, 0.0], [0.0, -1.0]])
E_CROSS = np.array([[0.0, 1.0], [1.0, 0.0]])


def modal_force_contraction(Q, hp, hc):
    """Q : h(t) for normal incidence, with h_ab = h+ e+ + hx ex."""
    return hp * np.sum(Q * E_PLUS) + hc * np.sum(Q * E_CROSS)


def deposited_energy(t, hp, hc, Q, Mn, omega):
    """Energy deposited in an initially quiet, high-Q mode by a transient much
    shorter than the ring-down time. Exact for an undamped oscillator:
        E = |F~(omega)|^2 / (2 M_n),  F~ = int (1/2) hddot:Q e^{-i w t} dt
                                         = -(w^2/2) int h:Q e^{-i w t} dt
    (integrated by parts, since the tapered h vanishes at both ends)."""
    dt = t[1] - t[0]
    s = modal_force_contraction(Q, hp, hc)
    Ft = -(omega**2 / 2) * np.sum(s * np.exp(-1j * omega * t)) * dt
    return abs(Ft) ** 2 / (2 * Mn)


def modal_time_response(t, hp, hc, Q, Mn, omega, Qm=1e6):
    """Integrate q'' + (w/Qm) q' + w^2 q = F/M_n in time, where F = (1/2) hddot:Q.
    The displacement is q * phi. phi is max-normalized, so q is the peak
    displacement in meters."""
    from scipy import signal
    s = modal_force_contraction(Q, hp, hc)
    dt = t[1] - t[0]
    sdd = np.gradient(np.gradient(s, dt), dt)
    sys = signal.lti([1.0], [1.0, omega / Qm, omega**2])
    _, q, _ = signal.lsim(sys, 0.5 * sdd / Mn, t)
    return q


def cw_steady_state(h_amp_p, h_amp_c, Q, Mn, omega, Qm=1e6):
    """Resonant steady state for a monochromatic wave at omega:
    |q| = Qm * (1/2)|Q:h| / M_n  (= Qm * eta * h for a pure polarization).
    Ring-up time 2 Qm / omega."""
    sp = 0.5 * abs(np.sum(Q * E_PLUS)) * h_amp_p / Mn
    sc = 0.5 * abs(np.sum(Q * E_CROSS)) * h_amp_c / Mn
    qamp = Qm * np.hypot(sp, sc)  # + and x are in quadrature for circular pol.
    E = 0.5 * Mn * omega**2 * qamp**2
    return qamp, E, 2 * Qm / omega


def sky_averaged_gamma(Q, Mn, n=20000, seed=1):
    """<|Q : h_hat|^2> / M_n over isotropic directions and polarization angles,
    with unit-amplitude + polarization in the wave frame. Proportional to the
    expected deposited energy for randomly oriented sources."""
    rng = np.random.default_rng(seed)
    ct = rng.uniform(-1, 1, n)
    st = np.sqrt(1 - ct**2)
    ph = rng.uniform(0, 2 * np.pi, n)
    psi = rng.uniform(0, np.pi, n)
    nhat = np.stack([st * np.cos(ph), st * np.sin(ph), ct], 1)
    a = np.stack([-np.sin(ph), np.cos(ph), np.zeros(n)], 1)
    b = np.cross(nhat, a)
    p = np.cos(psi)[:, None] * a + np.sin(psi)[:, None] * b
    q = -np.sin(psi)[:, None] * a + np.cos(psi)[:, None] * b
    ep = np.einsum("ni,nj->nij", p, p) - np.einsum("ni,nj->nij", q, q)
    val = np.einsum("nij,ij->n", ep[:, :2, :2], Q)
    return np.mean(val**2) / Mn
