# GW coupling: optimized vs disk (+ polarization, 5 MHz, equal volume)

Objective optimized: **eta**, mesh 60x60, r_min 3 elements (about 53 um), 250 iterations. The binary design keeps the largest of 1 solid component(s).

| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |
|---|---|---|---|---|---|---|---|---|
| disk, lowest coupled mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 112.40 | 64.53 | 0.656 | 5.853e-05 |
| disk, best-eta mode | 0.9418 | 0.0157 | 0.02 | 1.097e-02 | 116.22 | 64.77 | 0.086 | 2.532e-05 |
| disk, best-energy mode | 0.5189 | 0.0519 | 0.10 | 1.097e-02 | 112.40 | 64.53 | 0.656 | 5.853e-05 |
| optimized (gray densities) | 0.7661 | 0.0497 | 0.06 | 1.097e-02 | 154.96 | 10.49 | 0.044 | 8.352e-06 |
| optimized (binary, connected) | 0.5305 | 0.1032 | 0.19 | 1.097e-02 | 145.36 | 108.11 | 0.004 | 4.044e-07 |

- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: 1.251, so SUPPORTED**
  - same ratio for the gray (unthresholded) design: 1.333. A gap between the gray and binary ratios means the optimizer exploited intermediate densities.
- **Energy coupling per volume, optimized vs disk's best-energy mode: 0.007, so NOT SUPPORTED**
- Sky- and polarization-averaged energy per volume, optimized vs disk: 0.008

## Literature waveforms (Qm = 1e+06; SNR proxy = deposited energy / kT at 4 K)

| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |
|---|---|---|---|---|---|---|
| PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN) | 2.62e-21 | 7.586e-41 | 6.123e-43 | 0.008 | 1.37e-18 | 1.11e-20 |
| BAW-event sine-Gaussian 5.506 MHz, h0=1e-20 (illustrative) | 1.00e-20 | 4.195e-40 | 2.898e-42 | 0.007 | 7.60e-18 | 5.25e-20 |
| Boson-cloud CW (mu=1.03e-08 eV, M_BH=0.0013 Msun, 1 kpc), steady state | 7.75e-28 | 6.335e-44 | 5.114e-46 | 0.008 | 1.15e-21 | 9.26e-24 |
