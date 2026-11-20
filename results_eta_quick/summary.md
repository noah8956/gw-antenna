# GW coupling: optimized vs disk (+ polarization, 5 MHz, equal volume)

Objective optimized: **eta**, mesh 40x40, r_min 2 elements (about 131 um), 60 iterations. The binary design keeps the largest of 5 solid component(s).

| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |
|---|---|---|---|---|---|---|---|---|
| disk, lowest coupled mode | 0.5177 | 0.0518 | 0.10 | 1.096e-02 | 112.76 | 64.97 | 0.654 | 5.843e-05 |
| disk, best-eta mode | 0.9335 | 0.0159 | 0.02 | 1.096e-02 | 122.06 | 64.35 | 0.090 | 2.601e-05 |
| disk, best-energy mode | 0.5177 | 0.0518 | 0.10 | 1.096e-02 | 112.76 | 64.97 | 0.654 | 5.843e-05 |
| optimized (gray densities) | 0.0156 | 175.2583 | 11211.33 | 1.096e-02 | 5.01 | 0.69 | 0.248 | 1.660e-08 |
| optimized (binary, connected) | 1.3115 | 0.0275 | 0.02 | 1.096e-02 | 237.46 | 110.92 | 0.016 | 6.760e-06 |

- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: 1.945, so SUPPORTED**
  - same ratio for the gray (unthresholded) design: 0.041. A gap between the gray and binary ratios means the optimizer exploited intermediate densities.
- **Energy coupling per volume, optimized vs disk's best-energy mode: 0.116, so NOT SUPPORTED**
- Sky- and polarization-averaged energy per volume, optimized vs disk: 0.115

## Literature waveforms (Qm = 1e+06; SNR proxy = deposited energy / kT at 4 K)

| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |
|---|---|---|---|---|---|---|
| PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN) | 2.62e-21 | 7.579e-41 | 8.015e-42 | 0.106 | 1.37e-18 | 1.45e-19 |
| BAW-event sine-Gaussian 5.506 MHz, h0=1e-20 (illustrative) | 1.00e-20 | 4.183e-40 | 4.840e-41 | 0.116 | 7.58e-18 | 8.76e-19 |
| Boson-cloud CW (mu=1.03e-08 eV, M_BH=0.0013 Msun, 1 kpc), steady state | 7.75e-28 | 6.330e-44 | 6.697e-45 | 0.106 | 1.15e-21 | 1.21e-22 |
