# GW coupling: optimized vs disk (+ polarization, 5 MHz, equal volume)

Objective optimized: **energy**, mesh 60x60, r_min 3 elements (about 69 um), 250 iterations. The binary design keeps the largest of 1 solid component(s).

| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |
|---|---|---|---|---|---|---|---|---|
| disk, lowest coupled mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 112.40 | 64.53 | 0.656 | 5.853e-05 |
| disk, best-eta mode | 0.9418 | 0.0157 | 0.02 | 1.097e-02 | 116.22 | 64.77 | 0.086 | 2.532e-05 |
| disk, best-energy mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 112.40 | 64.53 | 0.656 | 5.853e-05 |
| optimized (gray densities) | 0.6843 | 0.0522 | 0.08 | 1.097e-02 | 232.03 | 30.25 | 0.897 | 9.367e-05 |
| optimized (binary, connected) | 0.6909 | 0.0511 | 0.07 | 1.097e-02 | 401.63 | 25.85 | 0.503 | 5.371e-05 |

- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: 3.456, so SUPPORTED**
  - same ratio for the gray (unthresholded) design: 1.996. A gap between the gray and binary ratios means the optimizer exploited intermediate densities.
- **Energy coupling per volume, optimized vs disk's best-energy mode: 0.918, so NOT SUPPORTED**
- Sky- and polarization-averaged energy per volume, optimized vs disk: 0.686

## Literature waveforms (Qm = 1e+06; SNR proxy = deposited energy / kT at 4 K)

| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |
|---|---|---|---|---|---|---|
| PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN) | 2.62e-21 | 7.586e-41 | 5.255e-41 | 0.693 | 1.37e-18 | 9.52e-19 |
| BAW-event sine-Gaussian 5.506 MHz, h0=1e-20 (illustrative) | 1.00e-20 | 4.195e-40 | 3.849e-40 | 0.918 | 7.60e-18 | 6.97e-18 |
| Boson-cloud CW (mu=1.03e-08 eV, M_BH=0.0013 Msun, 1 kpc), steady state | 7.75e-28 | 6.335e-44 | 4.390e-44 | 0.693 | 1.15e-21 | 7.95e-22 |
