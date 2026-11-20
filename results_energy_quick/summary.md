# GW coupling: optimized vs disk (+ polarization, 5 MHz, equal volume)

Objective optimized: **energy**, mesh 40x40, r_min 2 elements (about 49 um), 60 iterations. The binary design keeps the largest of 2 solid component(s).

| design | width [mm] | thick. [mm] | t/w | volume [mm^3] | eta [um] | eta other pol [um] | chi | Gamma/V [kg/m] |
|---|---|---|---|---|---|---|---|---|
| disk, lowest coupled mode | 0.5177 | 0.0518 | 0.10 | 1.096e-02 | 112.76 | 64.97 | 0.654 | 5.843e-05 |
| disk, best-eta mode | 0.9335 | 0.0159 | 0.02 | 1.096e-02 | 122.06 | 64.35 | 0.090 | 2.601e-05 |
| disk, best-energy mode | 0.5177 | 0.0518 | 0.10 | 1.096e-02 | 112.76 | 64.97 | 0.654 | 5.843e-05 |
| optimized (gray densities) | 0.2019 | 1.1688 | 5.79 | 1.096e-02 | 61.56 | 20.48 | 0.588 | 5.709e-06 |
| optimized (binary, connected) | 0.4860 | 0.2122 | 0.44 | 1.096e-02 | 131.26 | 19.08 | 0.069 | 4.213e-06 |

- **eta ratio, optimized (binary, connected) vs disk's best-eta mode: 1.075, so SUPPORTED**
  - same ratio for the gray (unthresholded) design: 0.504. A gap between the gray and binary ratios means the optimizer exploited intermediate densities.
- **Energy coupling per volume, optimized vs disk's best-energy mode: 0.072, so NOT SUPPORTED**
- Sky- and polarization-averaged energy per volume, optimized vs disk: 0.065

## Literature waveforms (Qm = 1e+06; SNR proxy = deposited energy / kT at 4 K)

| waveform | peak h | E disk [J] | E opt [J] | E opt/disk | E/kT disk | E/kT opt |
|---|---|---|---|---|---|---|
| PBH inspiral 2x2e-4 Msun @ 1 kpc (2PN) | 2.62e-21 | 7.579e-41 | 4.188e-42 | 0.055 | 1.37e-18 | 7.58e-20 |
| BAW-event sine-Gaussian 5.506 MHz, h0=1e-20 (illustrative) | 1.00e-20 | 4.183e-40 | 3.017e-41 | 0.072 | 7.58e-18 | 5.46e-19 |
| Boson-cloud CW (mu=1.03e-08 eV, M_BH=0.0013 Msun, 1 kpc), steady state | 7.75e-28 | 6.330e-44 | 3.499e-45 | 0.055 | 1.15e-21 | 6.34e-23 |
