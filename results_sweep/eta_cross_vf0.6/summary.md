# GW coupling: optimized vs disk (x polarization, 5 MHz, equal volume)

Objective optimized: **eta**, mesh 60x60, r_min 3 elements (about 41 um), 250 iterations. The binary design keeps the largest of 4 solid component(s).

| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |
|---|---|---|---|---|---|---|---|---|
| disk, lowest coupled mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 64.53 | 112.40 | 0.216 | 1.929e-05 |
| disk, best-eta mode | 0.7124 | 0.0275 | 0.04 | 1.097e-02 | 171.65 | 85.05 | 0.491 | 8.258e-05 |
| disk, best-energy mode | 0.7124 | 0.0275 | 0.04 | 1.097e-02 | 171.65 | 85.05 | 0.491 | 8.258e-05 |
| optimized (gray densities) | 0.1876 | 0.7674 | 4.09 | 1.097e-02 | 237.47 | 57.99 | 0.306 | 3.693e-06 |
| optimized (binary, connected) | 0.4124 | 0.1602 | 0.39 | 1.097e-02 | 230.04 | 98.73 | 0.016 | 9.207e-07 |

- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: 1.340, so SUPPORTED**
  - same ratio for the gray (unthresholded) design: 1.383. A gap between the gray and binary ratios means the optimizer exploited intermediate densities.
- **Energy coupling per volume, optimized vs disk's best-energy mode: 0.011, so NOT SUPPORTED**
- Sky- and polarization-averaged energy per volume, optimized vs disk: 0.014

## Literature waveforms (Qm = 1e+06; SNR proxy = deposited energy / kT at 4 K)

| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |
|---|---|---|---|---|---|---|
| PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN) | 2.62e-21 | 1.002e-40 | 1.063e-42 | 0.011 | 1.82e-18 | 1.92e-20 |
| BAW-event sine-Gaussian 5.506 MHz, h0=1e-20 (illustrative) | 1.00e-20 | 1.453e-40 | 1.215e-42 | 0.008 | 2.63e-18 | 2.20e-20 |
| Boson-cloud CW (mu=1.03e-08 eV, M_BH=0.0013 Msun, 1 kpc), steady state | 7.75e-28 | 8.374e-44 | 8.877e-46 | 0.011 | 1.52e-21 | 1.61e-23 |
