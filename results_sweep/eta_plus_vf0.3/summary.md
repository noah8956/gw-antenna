# GW coupling: optimized vs disk (+ polarization, 5 MHz, equal volume)

Objective optimized: **eta**, mesh 60x60, r_min 3 elements (about 67 um), 250 iterations. The binary design keeps the largest of 5 solid component(s).

| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |
|---|---|---|---|---|---|---|---|---|
| disk, lowest coupled mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 112.40 | 64.53 | 0.656 | 5.853e-05 |
| disk, best-eta mode | 0.9418 | 0.0157 | 0.02 | 1.097e-02 | 116.22 | 64.77 | 0.086 | 2.532e-05 |
| disk, best-energy mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 112.40 | 64.53 | 0.656 | 5.853e-05 |
| optimized (gray densities) | 0.5856 | 0.1443 | 0.25 | 1.097e-02 | 81.86 | 18.85 | 0.009 | 8.472e-07 |
| optimized (binary, connected) | 0.6737 | 0.1102 | 0.16 | 1.097e-02 | 306.12 | 16.74 | 0.033 | 4.039e-06 |

- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: 2.634, so SUPPORTED**
  - same ratio for the gray (unthresholded) design: 0.704. A gap between the gray and binary ratios means the optimizer exploited intermediate densities.
- **Energy coupling per volume, optimized vs disk's best-energy mode: 0.069, so NOT SUPPORTED**
- Sky- and polarization-averaged energy per volume, optimized vs disk: 0.055

## Literature waveforms (Qm = 1e+06; SNR proxy = deposited energy / kT at 4 K)

| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |
|---|---|---|---|---|---|---|
| PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN) | 2.62e-21 | 7.586e-41 | 3.947e-42 | 0.052 | 1.37e-18 | 7.15e-20 |
| BAW-event sine-Gaussian 5.506 MHz, h0=1e-20 (illustrative) | 1.00e-20 | 4.195e-40 | 2.895e-41 | 0.069 | 7.60e-18 | 5.24e-19 |
| Boson-cloud CW (mu=1.03e-08 eV, M_BH=0.0013 Msun, 1 kpc), steady state | 7.75e-28 | 6.335e-44 | 3.298e-45 | 0.052 | 1.15e-21 | 5.97e-23 |
