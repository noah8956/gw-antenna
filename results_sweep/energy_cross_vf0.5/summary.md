# GW coupling: optimized vs disk (x polarization, 5 MHz, equal volume)

Objective optimized: **energy**, mesh 60x60, r_min 3 elements (about 52 um), 250 iterations. The binary design keeps the largest of 1 solid component(s).

| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |
|---|---|---|---|---|---|---|---|---|
| disk, lowest coupled mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 64.53 | 112.40 | 0.216 | 1.929e-05 |
| disk, best-eta mode | 0.7124 | 0.0275 | 0.04 | 1.097e-02 | 171.65 | 85.05 | 0.491 | 8.258e-05 |
| disk, best-energy mode | 0.7124 | 0.0275 | 0.04 | 1.097e-02 | 171.65 | 85.05 | 0.491 | 8.258e-05 |
| optimized (gray densities) | 0.4925 | 0.1310 | 0.27 | 1.097e-02 | 140.17 | 17.33 | 0.851 | 5.923e-05 |
| optimized (binary, connected) | 0.5153 | 0.1179 | 0.23 | 1.097e-02 | 137.27 | 22.53 | 0.820 | 6.203e-05 |

- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: 0.800, so NOT SUPPORTED**
  - same ratio for the gray (unthresholded) design: 0.817. A gap between the gray and binary ratios means the optimizer exploited intermediate densities.
- **Energy coupling per volume, optimized vs disk's best-energy mode: 0.751, so NOT SUPPORTED**
- Sky- and polarization-averaged energy per volume, optimized vs disk: 0.643

## Literature waveforms (Qm = 1e+06; SNR proxy = deposited energy / kT at 4 K)

| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |
|---|---|---|---|---|---|---|
| PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN) | 2.62e-21 | 1.002e-40 | 6.210e-41 | 0.619 | 1.82e-18 | 1.12e-18 |
| BAW-event sine-Gaussian 5.506 MHz, h0=1e-20 (illustrative) | 1.00e-20 | 1.453e-40 | 1.198e-41 | 0.082 | 2.63e-18 | 2.17e-19 |
| Boson-cloud CW (mu=1.03e-08 eV, M_BH=0.0013 Msun, 1 kpc), steady state | 7.75e-28 | 8.374e-44 | 5.186e-44 | 0.619 | 1.52e-21 | 9.39e-22 |
