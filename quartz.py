"""SC-cut quartz: rotated stiffness tensor and anisotropic plane-stress reduction.

Conventions
-----------
* Crystal axes X, Y, Z (Z = optic axis). Voigt order: 11, 22, 33, 23, 13, 12.
* Elastic constants of alpha-quartz from Bechmann (1958), GPa, at 25 C.
* IEEE Std 176 doubly rotated cut (YXwl) phi/theta. We start from a Y-cut plate
  (thickness along Y, length along X, width along Z), rotate by phi about Z
  (the "w" rotation), then by theta about the new X axis (the "l" rotation).
  SC-cut: phi = 22.4 deg, theta = 33.88 deg.
* Plate frame after rotation: x1' = length (in-plane), x2' = thickness normal,
  x3' = width (in-plane). The 2D model uses (x, y) = (x1', x3').
"""
import numpy as np

RHO_QUARTZ = 2650.0  # kg/m^3

# Bechmann alpha-quartz stiffnesses (Pa)
_C11, _C12, _C13, _C14, _C33, _C44 = 86.74e9, 6.99e9, 11.91e9, -17.91e9, 107.2e9, 57.94e9
_C66 = 0.5 * (_C11 - _C12)  # = 39.88 GPa (trigonal class 32)


def quartz_C():
    """6x6 Voigt stiffness of alpha-quartz in crystal axes (trigonal 32)."""
    C = np.zeros((6, 6))
    C[0, 0] = C[1, 1] = _C11
    C[2, 2] = _C33
    C[0, 1] = _C12
    C[0, 2] = C[1, 2] = _C13
    C[0, 3] = _C14
    C[1, 3] = -_C14
    C[4, 5] = _C14
    C[3, 3] = C[4, 4] = _C44
    C[5, 5] = _C66
    return C + np.triu(C, 1).T


def rot_x(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[1, 0, 0], [0, c, s], [0, -s, c]])


def rot_z(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])


def bond_matrix(a):
    """Bond stress-transformation matrix M so that C' = M C M^T (Auld)."""
    M = np.empty((6, 6))
    pairs = [(0, 0), (1, 1), (2, 2), (1, 2), (2, 0), (0, 1)]
    for I, (i, j) in enumerate(pairs):
        for J, (k, l) in enumerate(pairs):
            if J < 3:
                M[I, J] = a[i, k] * a[j, l]
            else:
                M[I, J] = a[i, k] * a[j, l] + a[i, l] * a[j, k]
    return M


def rotate_C(C, a):
    M = bond_matrix(a)
    return M @ C @ M.T


def sc_cut_C(phi_deg=22.4, theta_deg=33.88):
    """Stiffness in the plate frame of a (YXwl) phi/theta doubly rotated cut."""
    a = rot_x(np.radians(theta_deg)) @ rot_z(np.radians(phi_deg))
    return rotate_C(quartz_C(), a)


def plane_stress_D(C3d, inplane=(0, 2, 4)):
    """Exact anisotropic plane-stress constitutive matrix.

    Setting the out-of-plane stresses (normal index 2: sigma_22, sigma_23,
    sigma_12) to zero is equivalent to keeping the in-plane block of the
    compliance S = C^-1 and inverting it. The default in-plane Voigt indices
    (11, 33, 13) correspond to (xx, yy, xy) of the 2D model, with engineering
    shear strain gamma_xy.
    """
    S = np.linalg.inv(C3d)
    idx = np.array(inplane)
    return np.linalg.inv(S[np.ix_(idx, idx)])


def sc_cut_plane_stress_D(phi_deg=22.4, theta_deg=33.88):
    D = plane_stress_D(sc_cut_C(phi_deg, theta_deg))
    return 0.5 * (D + D.T)


def isotropic_plane_stress_D(E, nu):
    return E / (1 - nu**2) * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])


if __name__ == "__main__":
    np.set_printoptions(precision=3, suppress=True)
    print("SC-cut plane-stress D (GPa):\n", sc_cut_plane_stress_D() / 1e9)
