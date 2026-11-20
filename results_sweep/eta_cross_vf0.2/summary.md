# GW coupling: optimized vs disk (x polarization, 5 MHz, equal volume)

Objective optimized: **eta**, mesh 60x60, r_min 3 elements (about 121 um), 250 iterations. The binary design keeps the largest of 1 solid component(s).

| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |
|---|---|---|---|---|---|---|---|---|
| disk, lowest coupled mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 64.53 | 112.40 | 0.216 | 1.929e-05 |
| disk, best-eta mode | 0.7124 | 0.0275 | 0.04 | 1.097e-02 | 171.65 | 85.05 | 0.491 | 8.258e-05 |
| disk, best-energy mode | 0.7124 | 0.0275 | 0.04 | 1.097e-02 | 171.65 | 85.05 | 0.491 | 8.258e-05 |
| optimized (gray densities) | 0.2373 | 1.4622 | 6.16 | 1.097e-02 | 65.44 | 30.11 | 0.422 | 3.101e-06 |
| optimized (binary, connected) | 1.2116 | 0.0563 | 0.05 | 1.097e-02 | 111.91 | 76.09 | 0.032 | 6.081e-06 |

- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: 0.652, so NOT SUPPORTED**
  - same ratio for the gray (unthresholded) design: 0.381. A gap between the gray and binary ratios means the optimizer exploited intermediate densities.
- **Energy coupling per volume, optimized vs disk's best-energy mode: 0.074, so NOT SUPPORTED**
- Sky- and polarization-averaged energy per volume, optimized vs disk: 0.077

## Literature waveforms (Qm = 1e+06; SNR proxy = deposited energy / kT at 4 K)

| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |
|---|---|---|---|---|---|---|
| PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN) | 2.62e-21 | 1.002e-40 | 8.665e-42 | 0.086 | 1.82e-18 | 1.57e-19 |
| BAW-event sine-Gaussian 5.506 MHz, h0=1e-20 (illustrative) | 1.00e-20 | 1.453e-40 | 2.014e-41 | 0.139 | 2.63e-18 | 3.65e-19 |
| Boson-cloud CW (mu=1.03e-08 eV, M_BH=0.0013 Msun, 1 kpc), steady state | 7.75e-28 | 8.374e-44 | 7.239e-45 | 0.086 | 1.52e-21 | 1.31e-22 |
