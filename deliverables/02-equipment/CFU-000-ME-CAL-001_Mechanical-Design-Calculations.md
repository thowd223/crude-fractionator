# CFU-000-ME-CAL-001 - Mechanical Design Calculations

**Project:** 100 kBPSD Crude & Vacuum Distillation Unit | **Client:** Generic Refinery - Gulf Coast | **Rev A** - Issued for review (FEED) | 2026-10-02 | Prepared: CLAUDE CODE

## 1. Purpose and scope

FEED-level mechanical design of the CDU/VDU pressure equipment: shell/head/cone thickness to ASME VIII Div.1, external pressure (C-201 full vacuum) with stiffening rings, hydrotest pressures, empty / operating / hydrotest weights, skirt heights, ASCE 7 wind loads with skirt and anchor-bolt checks, API 530 fired-heater tube thickness, and main-column nozzle sizing. Inputs are read from data/equipment.json, streams.json, process_results.json and psv.json (generator cfu/mech). Results are exported to data/mech.json for the layout, civil/foundation and cost-estimate work. Datasheets: CFU-000-ME-DS-001..007; GA drawings: CFU-100/200-ME-GA-001..008.

## 2. Design basis and assumptions

* Code: ASME BPVC VIII Div.1 (2023) - UG-16, UG-23, UG-27, UG-28, UG-29, UG-32, UG-33, UG-99; ASME II-D Table 1A allowable stresses (Section 3). Flanges ASME B16.5 / B16.47 Group 1.1 ratings.
* Design pressure / temperature and corrosion allowance from equipment.json. Static liquid head to HLL added to the design pressure of bottom courses and bottom heads (operating liquid density from H&MB).
* Joint efficiency E = 1.0 (full RT) for columns, desalters and drums >= 2.0 m ID; E = 0.85 (spot RT) for smaller drums. Skirt-to-head weld efficiency 0.7.
* Fabrication minimum: t_min (excl. CA) = max(UG-16(b) 1.5 mm, D/1000 + 2.5 mm); plus CA. Heads: 2:1 semi-ellipsoidal, nominal = max(min. after forming + 1.5 mm thinning, adjoining shell). Cones: 30 deg half-angle, UG-32(g); junction reinforcement per App. 1-5/1-8 by fabricator.
* Cladding / linings (410S, 317L, Monel 400) are corrosion barriers only - not credited for strength; included in weights (3 mm clad, 2 mm Monel lining).
* External pressure (C-201): 1.034 bar (15 psi) full vacuum at design temperature. Factor A from the Div.2 4.4.5.1 closed form (the basis of Fig. G), factor B = A.E/2 in the elastic range with a plastic knee at 0.5 Sy(T) representing chart CS-2. <b>Stiffening rings: external flat-bar rings at max. 3.0 m spacing</b> on all C-201 cylindrical courses (rings double as insulation/platform supports); cone-cylinder junctions taken as lines of support (to be confirmed by App. 1-8).
* Wind: ASCE 7-16 Ch.26/29, V = 150 mph (67.1 m/s, 3-s gust), Exposure C, Kd = 0.95, Kzt = 1.0, Cf = 0.7 (round, moderately smooth), effective diameter = insulated OD + 0.6 m (ladders, piping), platforms 1.2 m2 x Cf 2.0 each. Gust factor G = 0.85 for rigid structures (n1 >= 1 Hz); Gf per 26.11.5 (beta = 1 %) for flexible columns. Stress checks use ASD 0.6W (+ 0.6D for anchor uplift).
* Longitudinal stress (UG-23): tension (windward, design pressure, empty weight) <= S.E; compression (leeward, operating weight, + vacuum for C-201) <= B (UG-23(b), A = 0.125/(Ro/t)). No 1.2 wind increase taken.
* Skirt height set by NPSH of the bottoms pump: LLL >= pump CL (EL 100.800) + NPSHr(est.) + 1.0 m margin + 0.6 m suction losses, with minimum 3.0 m (5.0 m C-101, 6.0 m C-201). NPSHr estimated from suction-specific speed 200 (metric) - see datasheet CFU-000-ME-DS-006.
* Weights: steel density 7850 kg/m3; nozzles 1.6 NPS^1.75 kg (manways x1.4 + 150 kg); valve trays 60-75 kg/m2 + support ring; structured packing 150-210 kg/m3, grid 380 kg/m3; distributors 120 kg/m2; collector trays 220 kg/m2; platforms 250 kg/m2 (60 % wrap, 1.2 m wide) + ladders 35 kg/m; insulation mineral wool 130 kg/m3 + 6 kg/m2 cladding; skirt fireproofing 50 mm both faces. Operating liquid: tray clear liquid + downcomer backup, packing hold-up 5 %, sump to NLL. Hydrotest: vessel full of water (internals installed, no insulation).
* Accuracy: thickness to nominal plate; weights +/-15 % (vessels), +/-30 % (fired heaters, exchangers, air coolers). All values to be superseded by vendor/fabricator calculations.

## 3. Material allowable stresses (ASME II-D Table 1A)

| Spec | Material | 40 C | 100 C | 150 C | 200 C | 250 C | 300 C | 325 C | 350 C | 375 C | 400 C | 425 C | 450 C | 475 C | 500 C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SA-516-70 | SA-516 Gr.70 (CS plate, normalised) | 138 | 138 | 138 | 138 | 138 | 135 | 132 | 128 | 122 | 101 | 84 | 67 | 51 | 34 |
| SA-387-11-2 | SA-387 Gr.11 Cl.2 (1.25Cr-0.5Mo) | 148 | 148 | 148 | 148 | 148 | 148 | 148 | 148 | 147 | 145 | 142 | 139 | 131 | 107 |
| SA-387-5-2 | SA-387 Gr.5 Cl.2 (5Cr-0.5Mo) | 148 | 148 | 148 | 148 | 148 | 148 | 148 | 147 | 146 | 144 | 140 | 128 | 99 | 79 |

*S in MPa; customary-unit values converted and interpolated. SA-516-70 above 425 C is subject to graphitisation limits (not used above 415 C here).*

| Tag | Base material | Design T (C) | S at design T (MPa) | S at test T (MPa) | E | CA (mm) |
|---|---|---|---|---|---|---|
| C-101 | SA-516-70 | 390 | 109.3 | 137.9 | 1.0 | 3.0 |
| C-102 | SA-516-70 | 250 | 137.9 | 137.9 | 1.0 | 3.0 |
| C-103 | SA-516-70 | 330 | 131.6 | 137.9 | 1.0 | 6.0 |
| C-104 | SA-516-70 | 375 | 121.6 | 137.9 | 1.0 | 6.0 |
| C-105 | SA-516-70 | 235 | 137.9 | 137.9 | 1.0 | 3.0 |
| C-106 | SA-516-70 | 185 | 137.9 | 137.9 | 1.0 | 3.0 |
| C-201 | SA-516-70 | 415 | 90.8 | 137.9 | 1.0 | 6.0 |
| D-101A | SA-516-70 | 165 | 137.9 | 137.9 | 1.0 | 3.0 |
| D-101B | SA-516-70 | 165 | 137.9 | 137.9 | 1.0 | 3.0 |
| D-102 | SA-516-70 | 160 | 137.9 | 137.9 | 1.0 | 6.0 |
| D-103 | SA-516-70 | 90 | 137.9 | 137.9 | 0.85 | 3.0 |
| D-104 | SA-516-70 | 280 | 136.4 | 137.9 | 1.0 | 3.0 |
| D-105 | SA-516-70 | 95 | 137.9 | 137.9 | 0.85 | 3.0 |
| D-106 | SA-516-70 | 120 | 137.9 | 137.9 | 1.0 | 3.0 |
| D-201 | SA-516-70 | 100 | 137.9 | 137.9 | 0.85 | 3.0 |
| D-202 | SA-516-70 | 100 | 137.9 | 137.9 | 0.85 | 3.0 |

## 4. Formulae

* Shell, circumferential stress UG-27(c)(1): t = P.R / (S.E - 0.6 P); longitudinal UG-27(c)(2): t = P.R / (2 S.E + 0.4 P); R = inside radius in corroded condition.
* 2:1 ellipsoidal head UG-32(d): t = P.D / (2 S.E - 0.2 P). Cone UG-32(g): t = P.D / (2 cos(a) (S.E - 0.6 P)).
* External pressure UG-28(c): Pa = 4B / (3 Do/t); UG-33(d) ellipsoidal head: Pa = B / (Ro/t), Ro = 0.9 Do; cone UG-33(f): equivalent cylinder Le = (L/2)(1 + Ds/DL), te = t cos(a).
* Stiffening ring UG-29: Is = Do^2 Ls (t + As/Ls) A / 14, A from B = 0.75 P Do / (t + As/Ls).
* Hydrotest UG-99(b): Pt = 1.3 MAWP (S_test / S_design), MAWP taken = design pressure (top); bottom adds water head. Membrane stress at test <= 0.9 Sy (vertical field test).
* API 530: elastic t_sigma = P_el.Do / (2 sigma_el + P_el), t = t_sigma + CA; rupture t_sigma = P_r.Do / (2 sigma_r + P_r), t = t_sigma + f_corr.CA (f_corr = 0.6).

## 5. Columns - shell, cone and head thickness (internal pressure)

### C-101 - Atmospheric crude fractionator (SA-516-70, P = 3.5 barg, T = 390 C, S = 109.3 MPa, E = 1.0, CA = 3.0 mm)

| Component | ID (mm) | z (m from BTL) | P calc (barg) | t circ | t long | t min fab | CA | t req (int) | t ext (FV) | t wind | t nominal (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Stripping section | 4,140 | 0.00-10.02 | 3.74 | 7.11 | 3.55 | 6.6 | 3.0 | 10.1 | - | 20 | <b>20</b> |
| Swage 30 deg | 6,900 | 10.02-12.41 | 3.50 | 12.79 | - | 9.4 | 3.0 | 15.8 | - | 18 | <b>18</b> |
| Flash zone / rectifying section | 6,900 | 12.41-40.50 | 3.50 | 11.08 | 5.53 | 9.4 | 3.0 | 14.1 | - | - | <b>16</b> |
| Head (top) 2:1 SE | 6,900 | - | 3.50 | 11.06 | - | - | 3.0 | 14.1 | - | - | <b>16</b> (min 14.1 formed) |
| Head (bottom) 2:1 SE | 4,140 | - | 3.81 | 7.24 | - | - | 3.0 | 10.2 | - | - | <b>12</b> (min 10.2 formed) |

### C-102 - Kero side stripper (SA-516-70, P = 3.5 barg, T = 250 C, S = 137.9 MPa, E = 1.0, CA = 3.0 mm)

| Component | ID (mm) | z (m from BTL) | P calc (barg) | t circ | t long | t min fab | CA | t req (int) | t ext (FV) | t wind | t nominal (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Stripping section | 1,700 | 0.00-9.20 | 3.65 | 2.26 | 1.13 | 4.2 | 3.0 | 7.2 | - | - | <b>8</b> |
| Head (top) 2:1 SE | 1,700 | - | 3.50 | 2.17 | - | - | 3.0 | 7.2 | - | - | <b>10</b> (min 7.2 formed) |
| Head (bottom) 2:1 SE | 1,700 | - | 3.68 | 2.27 | - | - | 3.0 | 7.2 | - | - | <b>10</b> (min 7.2 formed) |

### C-103 - Diesel side stripper (SA-516-70, P = 3.5 barg, T = 330 C, S = 131.6 MPa, E = 1.0, CA = 6.0 mm)

| Component | ID (mm) | z (m from BTL) | P calc (barg) | t circ | t long | t min fab | CA | t req (int) | t ext (FV) | t wind | t nominal (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Stripping section | 1,900 | 0.00-9.20 | 3.65 | 2.65 | 1.32 | 4.4 | 6.0 | 10.4 | - | - | <b>12</b> |
| Head (top) 2:1 SE | 1,900 | - | 3.50 | 2.54 | - | - | 6.0 | 10.4 | - | - | <b>12</b> (min 10.4 formed) |
| Head (bottom) 2:1 SE | 1,900 | - | 3.67 | 2.67 | - | - | 6.0 | 10.4 | - | - | <b>12</b> (min 10.4 formed) |

### C-104 - Ago side stripper (SA-516-70, P = 3.5 barg, T = 375 C, S = 121.6 MPa, E = 1.0, CA = 6.0 mm)

| Component | ID (mm) | z (m from BTL) | P calc (barg) | t circ | t long | t min fab | CA | t req (int) | t ext (FV) | t wind | t nominal (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Stripping section | 1,400 | 0.00-9.20 | 3.66 | 2.13 | 1.06 | 3.9 | 6.0 | 9.9 | - | - | <b>10</b> |
| Head (top) 2:1 SE | 1,400 | - | 3.50 | 2.03 | - | - | 6.0 | 9.9 | - | - | <b>12</b> (min 9.9 formed) |
| Head (bottom) 2:1 SE | 1,400 | - | 3.68 | 2.14 | - | - | 6.0 | 9.9 | - | - | <b>12</b> (min 9.9 formed) |

### C-105 - Naphtha stabiliser (debutaniser) (SA-516-70, P = 13.0 barg, T = 235 C, S = 137.9 MPa, E = 1.0, CA = 3.0 mm)

| Component | ID (mm) | z (m from BTL) | P calc (barg) | t circ | t long | t min fab | CA | t req (int) | t ext (FV) | t wind | t nominal (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Shell | 2,100 | 0.00-18.00 | 13.13 | 10.08 | 5.00 | 4.6 | 3.0 | 13.1 | - | - | <b>14</b> |
| Head (top) 2:1 SE | 2,100 | - | 13.00 | 9.94 | - | - | 3.0 | 12.9 | - | - | <b>16</b> (min 12.9 formed) |
| Head (bottom) 2:1 SE | 2,100 | - | 13.16 | 10.06 | - | - | 3.0 | 13.1 | - | - | <b>16</b> (min 13.1 formed) |

### C-106 - Naphtha splitter (SA-516-70, P = 3.5 barg, T = 185 C, S = 137.9 MPa, E = 1.0, CA = 3.0 mm)

| Component | ID (mm) | z (m from BTL) | P calc (barg) | t circ | t long | t min fab | CA | t req (int) | t ext (FV) | t wind | t nominal (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Shell | 3,100 | 0.00-29.50 | 3.65 | 4.11 | 2.05 | 5.6 | 3.0 | 8.6 | - | 12 | <b>12</b> |
| Head (top) 2:1 SE | 3,100 | - | 3.50 | 3.94 | - | - | 3.0 | 8.6 | - | - | <b>12</b> (min 8.6 formed) |
| Head (bottom) 2:1 SE | 3,100 | - | 3.69 | 4.16 | - | - | 3.0 | 8.6 | - | - | <b>12</b> (min 8.6 formed) |

### C-201 - Vacuum column (wet, packed) (SA-516-70, P = 3.5 barg + FV, T = 415 C, S = 90.8 MPa, E = 1.0, CA = 6.0 mm)

| Component | ID (mm) | z (m from BTL) | P calc (barg) | t circ | t long | t min fab | CA | t req (int) | t ext (FV) | t wind | t nominal (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Boot (stripping / quench) | 3,000 | 0.00-7.77 | 3.75 | 6.24 | 3.11 | 5.5 | 6.0 | 12.2 | 18 | 25 | <b>25</b> |
| Lower cone 30 deg | 6,600 | 7.77-10.89 | 3.50 | 14.75 | - | 9.1 | 6.0 | 20.7 | 25 | - | <b>25</b> |
| Main shell (beds 2-4, flash zone) | 6,600 | 10.89-27.04 | 3.50 | 12.77 | 6.37 | 9.1 | 6.0 | 18.8 | 24 | - | <b>25</b> |
| Upper cone 30 deg | 6,600 | 27.04-30.50 | 3.50 | 14.75 | - | 9.1 | 6.0 | 20.7 | 25 | - | <b>25</b> |
| Top section (bed 1) | 2,600 | 30.50-36.00 | 3.50 | 5.04 | 2.51 | 5.1 | 6.0 | 11.1 | 17 | - | <b>18</b> |
| Head (top) 2:1 SE | 2,600 | - | 3.50 | 5.03 | - | - | 6.0 | 11.1 | 14 | - | <b>18</b> (min 14.0 formed) |
| Head (bottom) 2:1 SE | 3,000 | - | 3.81 | 6.32 | - | - | 6.0 | 12.3 | 15 | - | <b>18</b> (min 15.0 formed) |

## 6. C-201 external pressure (full vacuum) and stiffening rings

| Course | Do (mm) | t nom | t corr/eff | L (mm) | L/Do | Do/t | A | B (MPa) | Pa (bar) | Req. (bar) | t if no rings |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Boot (stripping / quench) | 3,036 | 18 | 12.0 | 3,000 | 0.988 | 253 | 2.66e-04 | 23.2 | 1.222 | 1.034 | 24 |
| Lower cone 30 deg | 6,650 | 25 | 16.5 | 2,267 | 0.341 | 404 | 4.00e-04 | 34.6 | 1.141 | 1.034 | - |
| Main shell (beds 2-4, flash zone) | 6,648 | 24 | 18.0 | 3,000 | 0.451 | 369 | 3.41e-04 | 29.6 | 1.070 | 1.034 | 43 |
| Upper cone 30 deg | 6,650 | 25 | 16.5 | 2,414 | 0.363 | 404 | 3.74e-04 | 32.4 | 1.070 | 1.034 | - |
| Top section (bed 1) | 2,634 | 17 | 11.0 | 3,000 | 1.139 | 239 | 2.49e-04 | 21.7 | 1.209 | 1.034 | 20 |

*Design temperature 415 C, material SA-516-70, CA 6.0 mm; cones use the equivalent-cylinder method. Without rings the main shell would need the thickness in the last column.*

| Course | No. of rings | Spacing Ls (mm) | Flat bar h x b (mm) | As (mm2) | A | B (MPa) | Is req (10^6 mm4) | I provided (10^6 mm4) |
|---|---|---|---|---|---|---|---|---|
| Boot (stripping / quench) | 2 | 3,000 | 160 x 16 | 2,560 | 2.10e-04 | 18.3 | 5.33 | 5.46 |
| Main shell (beds 2-4, flash zone) | 5 | 3,000 | 300 x 25 | 7,500 | 2.88e-04 | 25.1 | 55.96 | 56.25 |
| Top section (bed 1) | 1 | 3,000 | 140 x 16 | 2,240 | 1.99e-04 | 17.4 | 3.48 | 3.66 |

*External rings, continuous fillet welds both sides (UG-30). Ring stiffeners also carry insulation support. Internal bed-support / collector rings are not credited.*

Heads under external pressure (UG-33(d)): top head t = 14 mm, bottom head t = 15 mm minimum (corroded 6.0 mm deducted); nominal 18 / 18 mm.

## 7. Hydrotest

| Tag | MAWP (barg) | S_test/S_des | Pt top (barg) | Pt bottom (barg) | sigma bottom (MPa) | 0.9 Sy (MPa) | Check | Test position |
|---|---|---|---|---|---|---|---|---|
| C-101 | 3.5 | 1.262 | 5.74 | 9.98 | 104 | 234 | OK | Vertical (field) |
| C-102 | 3.5 | 1.000 | 4.55 | 5.54 | 59 | 234 | OK | Vertical (field) |
| C-103 | 3.5 | 1.048 | 4.77 | 5.76 | 46 | 234 | OK | Vertical (field) |
| C-104 | 3.5 | 1.134 | 5.16 | 6.13 | 43 | 234 | OK | Vertical (field) |
| C-105 | 13.0 | 1.000 | 16.90 | 18.77 | 142 | 234 | OK | Vertical (field) |
| C-106 | 3.5 | 1.000 | 4.55 | 7.60 | 99 | 234 | OK | Vertical (field) |
| C-201 | 3.5 | 1.518 | 6.91 | 10.58 | 64 | 234 | OK | Vertical (field) |
| D-101A | 17.0 | 1.000 | 22.10 | 22.47 | - | - | OK | Horizontal (shop) |
| D-101B | 17.0 | 1.000 | 22.10 | 22.47 | - | - | OK | Horizontal (shop) |
| D-102 | 3.5 | 1.000 | 4.55 | 4.88 | - | - | OK | Horizontal (shop) |
| D-103 | 7.0 | 1.000 | 9.10 | 9.19 | - | - | OK | Vertical |
| D-104 | 3.5 | 1.011 | 4.60 | 4.81 | - | - | OK | Horizontal (shop) |
| D-105 | 15.2 | 1.000 | 19.76 | 19.93 | - | - | OK | Horizontal (shop) |
| D-106 | 3.5 | 1.000 | 4.55 | 4.81 | - | - | OK | Horizontal (shop) |
| D-201 | 3.5 | 1.000 | 4.55 | 4.68 | - | - | OK | Horizontal (shop) |
| D-202 | 3.5 | 1.000 | 4.55 | 4.61 | - | - | OK | Vertical |

*Foundations for C-101 / C-201 shall be checked for the full-of-water hydrotest weight (Section 8) unless a pneumatic/hydro-pneumatic or horizontal shop test is specified.*

## 8. Weights

| Tag | Shell + heads | Skirt + base | Nozzles | Internals | Clad | Platf./ladders | Insul./fireproof. | EMPTY | Op. liquid | OPERATING | Volume (m3) | HYDROTEST |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C-101 | 115.0 | 17.0 | 8.8 | 119.0 | 15.7 | 38.9 | 38.4 | <b>352.8</b> | 85.6 | <b>438.3</b> | 1,296 | <b>1629.1</b> |
| C-102 | 3.7 | 2.8 | 1.8 | 1.4 | 0.0 | 4.6 | 5.7 | <b>19.9</b> | 2.9 | <b>22.9</b> | 22 | <b>41.2</b> |
| C-103 | 6.1 | 3.4 | 1.8 | 1.6 | 1.4 | 4.9 | 7.3 | <b>26.5</b> | 3.6 | <b>30.1</b> | 28 | <b>53.1</b> |
| C-104 | 3.7 | 2.2 | 1.7 | 1.1 | 1.0 | 4.3 | 4.4 | <b>18.4</b> | 2.1 | <b>20.4</b> | 15 | <b>32.3</b> |
| C-105 | 14.7 | 4.4 | 2.8 | 5.3 | 0.0 | 9.9 | 11.0 | <b>48.1</b> | 5.8 | <b>53.9</b> | 65 | <b>110.7</b> |
| C-106 | 29.8 | 9.6 | 4.7 | 24.8 | 0.0 | 18.3 | 21.3 | <b>108.7</b> | 21.0 | <b>129.7</b> | 230 | <b>334.1</b> |
| C-201 | 113.8 | 10.8 | 8.8 | 97.9 | 12.8 | 24.0 | 25.9 | <b>294.0</b> | 43.2 | <b>337.1</b> | 763 | <b>1043.4</b> |

*Tonnes. EMPTY = installed, incl. internals, platforms, insulation and fireproofing (erection lift excludes platforms/insulation if installed after setting).*

### Drums and desalters - thickness and weights

| Tag | Service | ID x T/T (m) | Material | P calc (barg) | Shell t req | Shell t nom | Head t req | Head t nom | Fabricated (t) | Empty (t) | Operating (t) | Hydrotest (t) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-101A | Electrostatic desalter, 1st stage | 3.8 x 30.0 | SA-516-70 | 17.29 | 27.0 | <b>28</b> | 26.9 | <b>28</b> | 119.0 | 137.4 | 414.0 | 487.1 |
| D-101B | Electrostatic desalter, 2nd stage | 3.8 x 30.0 | SA-516-70 | 17.29 | 27.0 | <b>28</b> | 26.9 | <b>28</b> | 119.0 | 137.4 | 414.0 | 487.1 |
| D-102 | Atm. overhead reflux drum (3-phase) | 3.4 x 12.0 | SA-516-70 | 3.73 | 11.9 | <b>12</b> | 11.9 | <b>12</b> | 19.4 | 19.4 | 63.0 | 144.0 |
| D-103 | Fuel gas knock-out drum | 0.9 x 2.5 | SA-516-70 | 7.17 | 6.4 | <b>8</b> | 6.4 | <b>8</b> | 1.2 | 1.2 | 1.8 | 3.0 |
| D-104 | Flare knock-out drum (unit) | 2.1 x 6.5 | SA-516-70 | 3.64 | 7.6 | <b>8</b> | 7.6 | <b>8</b> | 4.5 | 5.2 | 13.9 | 29.5 |
| D-105 | Stabiliser reflux drum | 1.7 x 5.5 | SA-516-70 | 15.32 | 14.2 | <b>16</b> | 14.2 | <b>16</b> | 6.2 | 6.2 | 11.2 | 20.4 |
| D-106 | Splitter reflux drum | 2.7 x 8.5 | SA-516-70 | 3.69 | 8.2 | <b>10</b> | 8.2 | <b>10</b> | 8.9 | 8.9 | 27.8 | 62.8 |
| D-201 | Ejector hotwell / sour water separator | 1.3 x 5.5 | SA-516-70 | 3.63 | 6.8 | <b>8</b> | 6.8 | <b>8</b> | 2.5 | 2.5 | 6.4 | 10.4 |
| D-202 | Vacuum off-gas knock-out drum | 0.6 x 2.0 | SA-516-70 | 3.64 | 6.1 | <b>8</b> | 6.1 | <b>8</b> | 0.9 | 0.9 | 1.1 | 1.5 |

*Desalters operate liquid-full (crude/water, 780 kg/m3); include 3 transformers (4.5 t each) and 18 t internals. Drums at 50 % liquid. Boots included (D-102, D-105).*

## 9. Skirt height, wind load and longitudinal stress

| Tag | Bottoms pump | NPSHr est. (m) | LLL above BTL (m) | Skirt height (m) | BTL elevation | Skirt t (mm) | Skirt OD (mm) |
|---|---|---|---|---|---|---|---|
| C-101 | P-112A/B | 4.2 | 0.6 | 6.5 | 106.500 | 20 | 4,180 |
| C-102 | P-109A/B | 1.9 | 0.5 | 4.0 | 104.000 | 8 | 1,716 |
| C-103 | P-110A/B | 2.2 | 0.5 | 4.5 | 104.500 | 8 | 1,924 |
| C-104 | P-111A/B | 1.5 | 0.5 | 3.5 | 103.500 | 8 | 1,420 |
| C-105 | - (no pump) | - | 0.5 | 6.0 | 106.000 | 8 | 2,128 |
| C-106 | P-117A/B | 5.4 | 0.5 | 7.5 | 107.500 | 12 | 3,124 |
| C-201 | P-204A/B | 2.6 | 0.6 | 6.0 | 106.000 | 18 | 3,050 |

*C-105 bottoms flow under pressure to C-106 / kettle E-116; skirt 6.0 m for kettle liquid head and bottom piping.*

| Tag | Height (m) | n1 (Hz) | Type | G / Gf | Kz top | qh (kPa) | Base shear (kN) | Base moment (kNm) | ASD moment (kNm) | Vortex Vcr (m/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| C-101 | 48.7 | 0.83 | flexible | 1.113 | 1.397 | 3.66 | 863 | 24,853 | 14,912 | 29.7 |
| C-102 | 13.6 | 4.25 | rigid | 0.890 | 1.068 | 2.80 | 60 | 485 | 291 | 39.3 |
| C-103 | 14.2 | 4.26 | rigid | 0.889 | 1.077 | 2.82 | 67 | 562 | 337 | 44.8 |
| C-104 | 13.0 | 3.59 | rigid | 0.890 | 1.059 | 2.77 | 53 | 416 | 250 | 28.7 |
| C-105 | 24.5 | 1.66 | rigid | 0.882 | 1.209 | 3.17 | 138 | 1,992 | 1,195 | 18.6 |
| C-106 | 37.8 | 1.16 | rigid | 0.876 | 1.324 | 3.47 | 294 | 6,308 | 3,785 | 18.9 |
| C-201 | 42.6 | 0.81 | flexible | 1.223 | 1.358 | 3.56 | 650 | 15,673 | 9,404 | 11.6 |

*Strength-level wind. Vortex shedding: critical velocity Vcr = n1.D/0.2. Columns with Vcr < ~25 m/s and D/t > 200 to be checked in detail (helical strakes not expected for insulated columns with platforms).*

### C-101 - wind / weight longitudinal stress check (corroded, ASD)

| Section (bottom of) | Elev. above grade (m) | t nom | M ASD (MNm) | sig P | sig M | sig W | Tension | Allow. S.E | Compression | Allow. B | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Stripping section | 6.50 | 20 | 12 | 21.3 | 50.4 | 17.7 | 57.9 | 109.3 | 68.1 | 73.3 | OK |
| Swage 30 deg | 16.52 | 18 | 7 | 27.9 | 40.3 | 19.1 | 52.3 | 109.3 | 59.5 | 62.9 | OK |
| Flash zone / rectifying section | 18.91 | 16 | 6 | 46.4 | 12.5 | 11.0 | 49.9 | 109.3 | 23.6 | 40.9 | OK |
| Skirt (base, 1.5 mm CA, E = 0.7) | 0.00 | 20 | 15 | - | 58.2 | 16.9 | 44.8 | 96.5 | 75.1 | 93.5 | OK |

Anchor bolts C-101: 32 x M56 ASTM F1554 Gr.55 on 4.43 m BCD; max. tension 363 kN/bolt (0.6D + 0.6W, empty), required root area 1910 mm2. Hydrotest skirt compression 80.0 MPa (25 % wind). Base shear 863 kN, base moment 24853 kNm (strength) for foundation design.

### C-201 - wind / weight longitudinal stress check (corroded, ASD)

| Section (bottom of) | Elev. above grade (m) | t nom | M ASD (MNm) | sig P | sig M | sig W | Tension | Allow. S.E | Compression | Allow. B | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Boot (stripping / quench) | 6.00 | 25 | 7 | 13.8 | 52.4 | 17.0 | 51.6 | 90.8 | 73.5 | 80.2 | OK |
| Lower cone 30 deg | 13.77 | 25 | 4 | 16.0 | 37.8 | 17.2 | 38.4 | 90.8 | 59.7 | 78.4 | OK |
| Main shell (beds 2-4, flash zone) | 16.89 | 25 | 3 | 30.4 | 5.3 | 6.4 | 30.1 | 90.8 | 20.7 | 58.1 | OK |
| Upper cone 30 deg | 33.04 | 25 | 0 | 35.1 | 0.7 | 1.0 | 34.8 | 90.8 | 12.1 | 51.8 | OK |
| Top section (bed 1) | 36.50 | 18 | 0 | 19.0 | 2.6 | 2.3 | 19.4 | 90.8 | 10.5 | 75.1 | OK |
| Skirt (base, 1.5 mm CA, E = 0.7) | 0.00 | 18 | 9 | - | 77.2 | 20.0 | 59.8 | 96.5 | 97.2 | 102.2 | OK |

Anchor bolts C-201: 24 x M64 ASTM F1554 Gr.55 on 3.30 m BCD; max. tension 409 kN/bolt (0.6D + 0.6W, empty), required root area 2154 mm2. Hydrotest skirt compression 83.7 MPa (25 % wind). Base shear 650 kN, base moment 15673 kNm (strength) for foundation design.

## 10. Fired heater tubes - API 530 (9Cr-1Mo, 100,000 h)

| Item | H-101 radiant | H-201 radiant |
|---|---|---|
| Radiant average flux (kW/m2, OD) | 31.5 | 25.0 |
| Peak flux (x1.8 circ. x1.1 long.) (kW/m2) | 62.4 | 49.5 |
| Inside peak flux (kW/m2) | 71.7 | 56.9 |
| Bulk fluid T at outlet (C) | 365.7 | 398.4 |
| Inside film coefficient (W/m2K, EOR) | 1,100 | 650 |
| Coke/fouling resistance EOR (m2K/W) | 0.0005 | 0.0009 |
| dT film (C) | 65.2 | 87.6 |
| dT coke (C) | 35.9 | 51.2 |
| dT wall (C) | 27.2 | 21.6 |
| Estimated max. TMT EOR (C) | 494 | 559 |
| <b>Design metal temperature (TMT + 15 C)</b> | 510 | 575 |
| equipment.json des_T (C) | 455 | 490 |
| Elastic design pressure (MPa) | 3.85 | 1.98 |
| Rupture design pressure (MPa, coil inlet op.) | 1.70 | 1.90 |
| sigma_el at Tdm (MPa) | 101.8 | 78.0 |
| sigma_r 100,000 h at Tdm (MPa) | 83.0 | 35.0 |
| Corrosion allowance (mm) | 3.0 | 3.0 |
| Elastic t_sigma (mm) | 3.12 | 2.11 |
| Rupture t_sigma (mm) | 1.71 | 4.45 |
| Elastic t_min = t_sigma + CA | 6.12 | 5.11 |
| Rupture t_min = t_sigma + f_corr CA | 3.51 | 6.25 |
| <b>Minimum thickness (mm)</b> | 6.12 | 6.25 |
| Governing | elastic | rupture |
| Minimum schedule | Sch 40 (7.11 mm) | Sch 40 (7.11 mm) |
| <b>Selected</b> (OD 168.3 mm, A335 P9) | <b>Sch 80 (10.97 mm)</b> | <b>Sch 80 (10.97 mm)</b> |

*Sch 80 is retained (process mass-flux basis ID 146.3 mm) - gives margin for coke spalling/erosion and decoking. 9Cr-1Mo stresses digitised from API 530 curves: 425 C: 123/205, 450 C: 118/160, 475 C: 112/123, 500 C: 105/93, 525 C: 97/68, 550 C: 88/49, 575 C: 78/35, 600 C: 67/25 MPa (sigma_el/sigma_r).*

| Heater | Fired (MW) | APH duty (MW) | Radiant (MW) | Flue gas (t/h) | BWT (C) | Crossover (C) | Flue out conv. (C) | LMTD (C) | Conv. bare area (m2) | Rows (shock+studded+coils) | Utility coil req. (MW) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H-101 | 67.4 | 6.4 | 38.7 | 96 | 1,044 | 306 | 381 | 327 | 607 | 2 + 6 + 2 SS + 0 util. | 0.00 |
| H-201 | 16.7 | 0.0 | 9.5 | 24 | 854 | 366 | 399 | 192 | 185 | 2 + 3 + 0 SS + 2 util. | 1.40 |

*Convection estimate: U = 105 W/m2K on bare-tube area (studded), 50 C minimum approach to process inlet. Vendor to optimise.*

## 11. Nozzle sizing summary (main columns)

### C-101 - Atmospheric crude fractionator

| Mark | Service | Size | Rating | z from BTL (m) | Flow (m3/h act.) | rho (kg/m3) | v (m/s) | Criterion |
|---|---|---|---|---|---|---|---|---|
| N1 | Feed - transfer line from H-101 (tangential, vapour horn) | 36" | 150# | 14.71 | 34,016 | 17 | 15.0 | two-phase feed rho_m.v2 <= 6000 Pa |
| N2 | Overhead vapour to A-101 | 36" | 150# | 40.50 | 45,065 | 5.09 | 19.9 | vapour outlet rho.v2 <= 3000 Pa |
| N3 | Reflux from P-103 | 8" | 150# | 38.85 | 145 | 698 | 1.2 | reflux / pumped liquid <= 2.0 m/s |
| N4 | TPA return | 8" | 150# | 38.80 | 246 | 679 | 2.1 | pumped liquid return <= 2.5 m/s |
| N5 | TPA draw to P-106 (draw sump) | 14" | 150# | 36.83 | 270 | 617 | 0.8 | gravity draw / pump suction <= 0.9 m/s (self-venting) |
| N8 | MPA return | 10" | 150# | 32.25 | 320 | 650 | 1.7 | pumped liquid return <= 2.5 m/s |
| N9 | MPA draw to P-107 (draw sump) | 16" | 150# | 30.28 | 352 | 591 | 0.8 | gravity draw / pump suction <= 0.9 m/s (self-venting) |
| N12 | BPA return | 8" | 150# | 24.48 | 263 | 630 | 2.3 | pumped liquid return <= 2.5 m/s |
| N13 | BPA draw to P-108 (draw sump) | 16" | 150# | 22.51 | 289 | 573 | 0.7 | gravity draw / pump suction <= 0.9 m/s (self-venting) |
| N6 | Kero draw to C-102 | 12" | 150# | 32.41 | 128 | 591 | 0.5 | gravity draw to side stripper <= 0.6 m/s |
| N7 | Vapour return from C-102 | 8" | 150# | 32.92 | 2,250 | 3.70 | 19.4 | vapour return rho.v2 <= 4000 Pa |
| N10 | Diesel draw to C-103 | 12" | 150# | 24.64 | 157 | 573 | 0.6 | gravity draw to side stripper <= 0.6 m/s |
| N11 | Vapour return from C-103 | 8" | 150# | 25.15 | 2,621 | 3.75 | 22.6 | vapour return rho.v2 <= 4000 Pa |
| N14 | Ago draw to C-104 | 10" | 150# | 18.09 | 79 | 636 | 0.4 | gravity draw to side stripper <= 0.6 m/s |
| N15 | Vapour return from C-104 | 6" | 150# | 18.60 | 1,382 | 3.97 | 20.6 | vapour return rho.v2 <= 4000 Pa |
| N16 | Stripping steam (from H-101 SS coil) | 10" | 150# | 5.77 | 4,886 | 1.56 | 26.7 | stripping steam <= 35 m/s |
| N17 | Atm. residue to P-112 | 16" | 150# | -1.03 | 365 | 704 | 0.9 | pump suction (bottoms) <= 1.0 m/s |
| N18 | Vent / steam-out | 3" | 150# | 40.50 | - | - | - | - |
| N19 | PSV-1001 relief (4 x T orifice) | 4 x 8" | 150# | 40.50 | - | - | - | - |
| N20A/B | LT / LG bridle (bottom sump) | 2 x 3" | 150# | 0.30 | - | - | - | - |
| N21 | Wash-zone overflash / slop connection (spare) | 4" | 150# | 16.26 | - | - | - | - |
| M1 | Manway 24" (davit) | 24" | 150# | 39.50 | - | - | - | - |
| M2 | Manway 24" (davit) | 24" | 150# | 33.48 | - | - | - | - |
| M3 | Manway 24" (davit) | 24" | 150# | 27.54 | - | - | - | - |
| M4 | Manway 24" (davit) | 24" | 150# | 20.38 | - | - | - | - |
| M5 | Manway 24" (davit) | 24" | 150# | 13.31 | - | - | - | - |
| M6 | Manway 24" (davit) | 24" | 150# | 7.89 | - | - | - | - |
| M7 | Manway 24" (davit) | 24" | 150# | 5.02 | - | - | - | - |

### C-201 - Vacuum column (wet, packed)

| Mark | Service | Size | Rating | z from BTL (m) | Flow (m3/h act.) | rho (kg/m3) | v (m/s) | Criterion |
|---|---|---|---|---|---|---|---|---|
| N1 | Feed - transfer line from H-201 (tangential to vapour horn) | 66" | 150# | 12.89 | 464,525 | 0.56 | 59.8 | vacuum transfer line <= 70 m/s (rho_m.v2 << 6000 Pa) |
| N2 | Overhead vapour to J-201 / E-202 | 48" | 150# | 36.00 | 229,101 | 0.01 | 56.3 | vacuum vapour <= 60 m/s |
| N3 | LVGO PA return (+ LVGO reflux) | 6" | 150# | 35.30 | 96 | 860 | 1.4 | pumped liquid return <= 2.5 m/s |
| N4 | LVGO total draw to P-201 | 12" | 150# | 30.35 | 226 | 739 | 0.9 | gravity draw / pump suction <= 0.9 m/s (self-venting) |
| N5 | LVGO internal reflux to bed 2 | 4" | 150# | 26.89 | 45 | 760 | 1.5 | pumped liquid return <= 2.5 m/s |
| N6 | HVGO total draw to P-202 | 16" | 150# | 22.09 | 374 | 708 | 0.9 | gravity draw / pump suction <= 0.9 m/s (self-venting) |
| N7 | HVGO PA return | 8" | 150# | 22.09 | 204 | 790 | 1.8 | pumped liquid return <= 2.5 m/s |
| N8 | Wash oil (HVGO) to bed 4 | 2" | 150# | 17.19 | 16 | 790 | 2.1 | pumped liquid return <= 2.5 m/s |
| N9 | Slop wax draw to P-203 | 3" | 150# | 14.34 | 11 | 714 | 0.6 | gravity draw / pump suction <= 0.9 m/s (self-venting) |
| N10 | Stripping steam | 6" | 150# | 4.74 | 1,498 | 1.86 | 22.3 | stripping steam <= 35 m/s |
| N11 | VR quench return (from E-201 outlet) | 3" | 150# | 3.75 | 30 | 905 | 1.7 | pumped liquid return <= 2.5 m/s |
| N12 | Vacuum residue to P-204 | 10" | 150# | -0.75 | 179 | 757 | 1.0 | pump suction (bottoms) <= 1.0 m/s |
| N13 | PSV-2001 relief (R) | 6" | 150# | 36.00 | - | - | - | - |
| N14A/B | LT / LG bridle (boot) | 2 x 3" | 150# | 0.30 | - | - | - | - |
| N15 | Vent / steam-out / N2 purge | 4" | 150# | 36.00 | - | - | - | - |
| M1 | Manway 24" | 24" | 150# | 31.55 | - | - | - | - |
| M2 | Manway 24" | 24" | 150# | 23.29 | - | - | - | - |
| M3 | Manway 24" | 24" | 150# | 17.49 | - | - | - | - |
| M4 | Manway 24" (36" in flash zone) | 36" | 150# | 11.69 | - | - | - | - |
| M5 | Manway 24" | 24" | 150# | 4.40 | - | - | - | - |

### C-102 - Kero side stripper

| Mark | Service | Size | Rating | z from BTL (m) | Flow (m3/h act.) | rho (kg/m3) | v (m/s) | Criterion |
|---|---|---|---|---|---|---|---|---|
| N1 | Kero feed from C-101 tray 10 | 12" | 150# | 8.00 | 128 | 591 | 0.5 | gravity draw to side stripper <= 0.6 m/s |
| N2 | Vapour return to C-101 | 8" | 150# | 9.20 | 2,250 | 3.70 | 19.4 | vapour return rho.v2 <= 4000 Pa |
| N3 | Stripping steam | 4" | 150# | 4.05 | 944 | 1.56 | 31.9 | stripping steam <= 35 m/s |
| N4 | Bottoms to P-109 | 8" | 150# | -0.42 | 114 | 603 | 1.0 | pump suction (bottoms) <= 1.0 m/s |
| N5A/B | LT / LG bridle | 2 x 2" | 150# | 0.20 | - | - | - | - |
| N6 | Vent / steam-out / PSV-1009 (common) | 3" | 150# | 9.20 | - | - | - | - |
| M1 | Manway 24" | 24" | 150# | 8.45 | - | - | - | - |
| M2 | Manway 24" | 24" | 150# | 3.30 | - | - | - | - |

### C-103 - Diesel side stripper

| Mark | Service | Size | Rating | z from BTL (m) | Flow (m3/h act.) | rho (kg/m3) | v (m/s) | Criterion |
|---|---|---|---|---|---|---|---|---|
| N1 | Diesel feed from C-101 tray 22 | 12" | 150# | 8.00 | 157 | 573 | 0.6 | gravity draw to side stripper <= 0.6 m/s |
| N2 | Vapour return to C-101 | 8" | 150# | 9.20 | 2,621 | 3.75 | 22.6 | vapour return rho.v2 <= 4000 Pa |
| N3 | Stripping steam | 6" | 150# | 4.05 | 1,066 | 1.56 | 15.9 | stripping steam <= 35 m/s |
| N4 | Bottoms to P-110 | 10" | 150# | -0.47 | 140 | 584 | 0.8 | pump suction (bottoms) <= 1.0 m/s |
| N5A/B | LT / LG bridle | 2 x 2" | 150# | 0.20 | - | - | - | - |
| N6 | Vent / steam-out / PSV-1009 (common) | 3" | 150# | 9.20 | - | - | - | - |
| M1 | Manway 24" | 24" | 150# | 8.45 | - | - | - | - |
| M2 | Manway 24" | 24" | 150# | 3.30 | - | - | - | - |

### C-104 - Ago side stripper

| Mark | Service | Size | Rating | z from BTL (m) | Flow (m3/h act.) | rho (kg/m3) | v (m/s) | Criterion |
|---|---|---|---|---|---|---|---|---|
| N1 | Ago feed from C-101 tray 32 | 10" | 150# | 8.00 | 79 | 636 | 0.4 | gravity draw to side stripper <= 0.6 m/s |
| N2 | Vapour return to C-101 | 6" | 150# | 9.20 | 1,382 | 3.97 | 20.6 | vapour return rho.v2 <= 4000 Pa |
| N3 | Stripping steam | 3" | 150# | 4.05 | 575 | 1.56 | 33.5 | stripping steam <= 35 m/s |
| N4 | Bottoms to P-111 | 8" | 150# | -0.35 | 71 | 649 | 0.6 | pump suction (bottoms) <= 1.0 m/s |
| N5A/B | LT / LG bridle | 2 x 2" | 150# | 0.20 | - | - | - | - |
| N6 | Vent / steam-out / PSV-1009 (common) | 3" | 150# | 9.20 | - | - | - | - |
| M1 | Manway 24" | 24" | 150# | 8.45 | - | - | - | - |
| M2 | Manway 24" | 24" | 150# | 3.30 | - | - | - | - |

### C-105 - Naphtha stabiliser (debutaniser)

| Mark | Service | Size | Rating | z from BTL (m) | Flow (m3/h act.) | rho (kg/m3) | v (m/s) | Criterion |
|---|---|---|---|---|---|---|---|---|
| N1 | Feed (tray 13) | 8" | 300# | 8.98 | 187 | 614 | 1.6 | pumped liquid return <= 2.5 m/s |
| N2 | Overhead vapour to A-106 | 8" | 300# | 18.00 | 856 | 22 | 7.4 | vapour outlet rho.v2 <= 3000 Pa |
| N3 | Reflux | 3" | 300# | 16.35 | 23 | 530 | 1.3 | reflux / pumped liquid <= 2.0 m/s |
| N4 | Reboiler feed to E-116 (kettle) | 16" | 300# | -0.53 | 380 | 554 | 0.9 | gravity draw / pump suction <= 0.9 m/s (self-venting) |
| N5 | Reboiler return from E-116 (kettle) | 10" | 300# | 4.22 | 614 | 166 | 3.4 | reboiler vapour return rho.v2 <= 4000 Pa |
| N6 | Stabilised naphtha (bottoms) to E-114/C-106 | 12" | 300# | 0.30 | 196 | 554 | 0.7 | pump suction (bottoms) <= 1.0 m/s |
| N7 | PSV-1005 relief (R) | 6" | 300# | 18.00 | - | - | - | - |
| N8A/B | LT / LG bridle | 2 x 2" | 300# | 0.20 | - | - | - | - |
| N9 | Vent / steam-out | 2" | 300# | 18.00 | - | - | - | - |
| M1 | Manway 24" | 24" | 300# | 17.00 | - | - | - | - |
| M2 | Manway 24" | 24" | 300# | 8.98 | - | - | - | - |
| M3 | Manway 24" | 24" | 300# | 3.52 | - | - | - | - |

### C-106 - Naphtha splitter

| Mark | Service | Size | Rating | z from BTL (m) | Flow (m3/h act.) | rho (kg/m3) | v (m/s) | Criterion |
|---|---|---|---|---|---|---|---|---|
| N1 | Feed (tray 21) | 8" | 150# | 15.60 | 196 | 554 | 1.7 | pumped liquid return <= 2.5 m/s |
| N2 | Overhead vapour to A-107 | 20" | 150# | 29.50 | 14,876 | 5.72 | 22.0 | vapour outlet rho.v2 <= 3000 Pa |
| N3 | Reflux | 6" | 150# | 27.85 | 90 | 640 | 1.3 | reflux / pumped liquid <= 2.0 m/s |
| N4 | Reboiler feed to E-117 (thermosyphon) | 16" | 150# | -0.78 | 370 | 624 | 0.9 | gravity draw / pump suction <= 0.9 m/s (self-venting) |
| N5 | Reboiler return from E-117 (thermosyphon) | 20" | 150# | 4.13 | 11,154 | 6.89 | 21.5 | reboiler vapour return rho.v2 <= 4000 Pa |
| N6 | Bottoms to P-117A/B | 10" | 150# | 0.30 | 130 | 624 | 0.7 | pump suction (bottoms) <= 1.0 m/s |
| N7 | PSV-1007 relief (T) | 8" | 150# | 29.50 | - | - | - | - |
| N8A/B | LT / LG bridle | 2 x 2" | 150# | 0.20 | - | - | - | - |
| N9 | Vent / steam-out | 2" | 150# | 29.50 | - | - | - | - |
| M1 | Manway 24" | 24" | 150# | 28.50 | - | - | - | - |
| M2 | Manway 24" | 24" | 150# | 21.70 | - | - | - | - |
| M3 | Manway 24" | 24" | 150# | 15.61 | - | - | - | - |
| M4 | Manway 24" | 24" | 150# | 9.51 | - | - | - | - |
| M5 | Manway 24" | 24" | 150# | 3.43 | - | - | - | - |

## 12. Shell & tube exchangers and air coolers - mechanical summary

| Tag | TEMA size | Shells | m2/shell | Tubes/shell | Tube OD/L (mm) | Des. P sh/tu (barg) | Des. T | Shell matl. | Shell t | Channel t | Empty t/shell | Hydro t/shell |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-101 | 1200-6096 AES | 1 | 359 | 756 | 25.4 / 6096 | 30 / 20 | 185 | SA-516-70 | 20 | 14 | 18.9 | 27.2 |
| E-102 | 1300-6096 AES | 1 | 438 | 923 | 25.4 / 6096 | 30 / 20 | 240 | SA-516-70 | 20 | 16 | 22.4 | 32.0 |
| E-103 | 1250-6096 AES | 2 | 402 | 848 | 25.4 / 6096 | 30 / 20 | 255 | SA-516-70 | 20 | 14 | 20.7 | 29.6 |
| E-104 | 1200-6096 AES | 1 | 378 | 797 | 25.4 / 6096 | 30 / 20 | 235 | SA-516-70 | 20 | 14 | 19.5 | 27.7 |
| E-105 | 1300-6096 AES | 1 | 431 | 910 | 25.4 / 6096 | 30 / 20 | 285 | SA-516-70 | 22 | 16 | 22.7 | 32.3 |
| E-106 | 1350-6096 AES | 2 | 500 | 1055 | 25.4 / 6096 | 30 / 20 | 270 | SA-516-70 | 22 | 16 | 25.2 | 35.6 |
| E-107 | 1150-6096 AES | 1 | 324 | 683 | 25.4 / 6096 | 30 / 20 | 325 | SA-516-70 | 22 | 18 | 18.2 | 25.8 |
| E-108 | 1400-6096 AES | 4 | 549 | 1157 | 25.4 / 6096 | 30 / 20 | 345 | SA-387-11-2 | 25 | 18 | 28.2 | 39.3 |
| E-109 | 1000-6096 AES | 1 | 263 | 555 | 25.4 / 6096 | 30 / 20 | 365 | SA-387-11-2 | 20 | 16 | 14.5 | 20.2 |
| E-110 | 1300-6096 AES | 2 | 443 | 934 | 25.4 / 6096 | 30 / 20 | 345 | SA-387-11-2 | 22 | 18 | 23.2 | 32.9 |
| E-111 | 1400-6096 AES | 2 | 547 | 1154 | 25.4 / 6096 | 30 / 20 | 395 | SA-387-11-2 | 25 | 18 | 28.1 | 39.3 |
| E-113 | 1300-6096 AKT | 1 | 223 | 627 | 19.05 / 6096 | 13 / 20 | 290 | SA-516-70 | 14 | 12 | 10.3 | 20.2 |
| E-201 | 1950-6096 AKT | 1 | 648 | 1820 | 19.05 / 6096 | 6 / 20 | 310 | SA-516-70 | 16 | 14 | 24.2 | 46.4 |
| E-114 | 750-6096 AES | 1 | 117 | 248 | 25.4 / 6096 | 20 / 20 | 235 | SA-516-70 | 10 | 10 | 6.4 | 9.7 |
| E-115 | 900-6096 AEU | 2 | 370 | 1040 | 19.05 / 6096 | 3.5 / 7 | 90 | SA-516-70 | 12 | 12 | 9.0 | 13.5 |
| E-116 | 1200-6096 BKT | 1 | 190 | 535 | 19.05 / 6096 | 15 / 45 | 285 | SA-516-70 | 14 | 20 | 9.5 | 18.0 |
| E-117 | 750-6096 BXM | 1 | 225 | 632 | 19.05 / 6096 | 5 / 13 | 215 | SA-516-70 | 10 | 10 | 8.0 | 11.2 |
| E-118 | 600-6096 AEL | 1 | 84 | 177 | 25.4 / 6096 | 20 / 20 | 160 | SA-516-70 | 10 | 10 | 4.7 | 6.8 |
| E-202 | 1100-6096 AXS | 1 | 549 | 1543 | 19.05 / 6096 | 3.5 / 7 (FV) | 100 | SA-516-70 | 14 | 14 | 18.6 | 25.4 |
| E-203 | 500-6096 AXS | 1 | 79 | 222 | 19.05 / 6096 | 3.5 / 7 (FV) | 100 | SA-516-70 | 10 | 10 | 3.5 | 5.0 |
| E-204 | 400-4877 AXS | 1 | 30 | 107 | 19.05 / 4877 | 3.5 / 7 (FV) | 100 | SA-516-70 | 10 | 10 | 1.9 | 2.7 |

*Shell t = max(UG-27 with E = 0.85 + CA, TEMA R minimum). Bundle diameter from tube-count correlation (square pitch 1.25 OD for fouling crude; triangular for clean condensers).*

| Tag | Service | Bare area (m2) | Bays (data) | Rows req. | Bays @ 6 rows | Fans | Fan D (m) | Motor kW | Empty (t) |
|---|---|---|---|---|---|---|---|---|---|
| A-101 | Atm. overhead condenser | 1,667 | 2 | 10 | 4 | 4 | 4.5 | 90 | 102.7 |
| A-103 | Kero cooler | 184 | 1 | 3 | 1 | 2 | 4.5 | 11 | 23.8 |
| A-104 | Diesel cooler | 430 | 1 | 6 | 1 | 2 | 4.5 | 45 | 34.2 |
| A-105 | Ago cooler | 287 | 1 | 4 | 1 | 2 | 4.5 | 30 | 28.2 |
| A-106 | Stabiliser overhead condenser | 214 | 1 | 3 | 1 | 2 | 4.5 | 11 | 25.1 |
| A-107 | Splitter overhead condenser | 881 | 1 | 11 | 2 | 2 | 4.5 | 45 | 53.4 |
| A-108 | Heavy naphtha product cooler | 401 | 1 | 5 | 1 | 2 | 4.5 | 30 | 33.0 |
| A-201 | Lvgo cooler | 397 | 1 | 5 | 1 | 2 | 4.5 | 15 | 32.8 |
| A-202 | Hvgo Product cooler | 403 | 1 | 5 | 1 | 2 | 4.5 | 37 | 33.1 |

## 13. Process-data issues and holds

| # | Item | Issue / recommendation |
|---|---|---|
| 1 | C-201 | Top section ID 2.6 m is sized on vapour leaving the top of bed 1 (10 t/h). Vapour entering the bottom of bed 1 is ~ vapour leaving bed 2 (87 t/h), which needs ID ~4.8 m at Cs 0.11. Recommend process re-rate bed 1 at its bottom; GA drawn per equipment.json (hold). |
| 2 | H-101 | des_T 455 C in equipment.json is below the API 530 design metal temperature 510 C (estimated EOR TMT 494 C + 15 C). Use 510 C for coil design / datasheet. |
| 3 | H-201 | equipment.json L = 14.0 m cannot house 18.3 m horizontal radiant tubes; cabin incl. header boxes is 21.9 m long. Plot reservation must be >= 24 m (incl. tube-pulling at one end handled by crane). |
| 4 | H-201 | des_T 490 C in equipment.json is below the API 530 design metal temperature 575 C (estimated EOR TMT 559 C + 15 C). Use 575 C for coil design / datasheet. |
| 5 | H-101 | Radiant fraction 0.65 (basis.DESIGN) gives an estimated bridgewall temperature of 1044 C with APH; API 560 practice <= ~900-950 C. Suggest radiant fraction ~0.70 (more radiant surface) - vendor to optimise. |
| 6 | H-201 | 88 % efficiency is not achievable with process convection alone: charge enters at 349 C, so flue gas cannot be cooled below ~399 C (max. process convection 3.7 MW vs 5.1 MW assumed). ~1.4 MW must go to a utility coil (steam superheat / BFW) or an APH - none exists in equipment.json. Also vacuum-heater outlet tubes normally step up in size (6"->8"->10") - all tubes are 6" in the data. |
| 7 | P-112A/B | Rated dP 12 bar gives discharge ~13.9 barg but H&MB stream 19 (P-112 -> H-201) is at 19.0 barg: dP should be ~17 bar (head ~246 m). |
| 8 | P-206A/B | Rated flow 0.65 m3/h at 60 m is outside the centrifugal (API 610) range - use a positive-displacement / metering pump (API 674/675). |
| 9 | P-118 | Single pump without spare (desalter mud-wash/recycle) - confirm intermittent duty. |
| 10 | Stream 24 | HVGO product 'frm' is E-202 (ejector intercondenser); should be A-202 (HVGO product cooler). |
| 11 | Stream 20 | Destination 'C-102A-C' - strippers are tagged C-102/C-103/C-104. |
| 12 | A-101 | 1667 m2 bare in 2 bay(s) of 6 x 12 m needs 10 tube rows (>8, not practical); 4 bays at 6 rows required. Plot space / fan count to be revised. |
| 13 | A-107 | 881 m2 bare in 1 bay(s) of 6 x 12 m needs 11 tube rows (>8, not practical); 2 bays at 6 rows required. Plot space / fan count to be revised. |
| 14 | A-202 | Air temperature rise 35->85 C is unrealistically high (typ. 15-25 C); air flow and bundle size will increase. |
| 15 | X-104 | Area 'CDU' but service is VDU overhead (area 200) - sizing.py tests '"10" in tag'. |
| 16 | D-102 | moc states 6 mm CA but ca_mm = 3; mechanical design uses 6 mm. |
| 17 | E-116 | Tube-side HP steam header is superheated (400 C) but des_T = 285 C - design temperature must cover the steam supply (400 C) unless a desuperheater is added. |
| 18 | E-117 | Tube-side MP steam header is superheated (250 C) but des_T = 215 C - design temperature must cover the steam supply (250 C) unless a desuperheater is added. |
| 19 | PSV-1001 | 4 x T orifices for 'Reflux failure / blocked OH (total OH vapour)' (216 t/h, set 2.4 barg vs MAWP 3.5 barg). Raising set to MAWP and crediting unaffected pumparound duty (API 521 4.4.3) should reduce this. |
| 20 | PSV-1009 | One PSV protects C-102/103/104: requires no isolation between the vessels (locked-open valves) - confirm in P&ID. |
| 21 | E-1xx/2xx | Shell IDs from tube-count/bundle correlation exceed equipment.json 'D' for: E-113 1.30 vs 0.9, E-201 1.95 vs 1.2, E-116 1.20 vs 0.9 m (kettles include the enlarged shell). |
| 22 | C-101 | equipment.json weight_t 727 t (rule of thumb) vs calculated empty 353 t / operating 438 t - use data/mech.json. |
| 23 | C-201 | equipment.json weight_t 665 t (rule of thumb) vs calculated empty 294 t / operating 337 t - use data/mech.json. |
| 24 | Design P | Only C-201 (and ejector condensers) carry FV. Columns C-101..C-106 and drums D-101A, D-101B, D-102, D-103, D-104, D-106, D-201 are not full-vacuum capable as designed; refinery practice is FV for steam-out (or written steam-out procedure + vacuum breakers). Process to confirm. |
| 25 | C-101 | Stripping-section ID 4.14 m (= 0.6 x main ID) is not rounded; size string says 4.1 m. Hydraulically 2.5 m suffices; mechanical uses 4.14 m as given. |

## 14. Summary of results

| Tag | Service | Size (m) | Material | Shell t (mm) | Head t (mm) | Skirt (m / mm) | Empty (t) | Operating (t) | Hydrotest (t) |
|---|---|---|---|---|---|---|---|---|---|
| C-101 | Atmospheric crude fractionator | 6.9 / 4.14 x 40.5 | SA-516-70 | 16-20 | 16/12 | 6.5 / 20 | 353 | 438 | 1,629 |
| C-102 | Kero side stripper | 1.7 x 9.2 | SA-516-70 | 8 | 10/10 | 4 / 8 | 20 | 23 | 41 |
| C-103 | Diesel side stripper | 1.9 x 9.2 | SA-516-70 | 12 | 12/12 | 4.5 / 8 | 27 | 30 | 53 |
| C-104 | Ago side stripper | 1.4 x 9.2 | SA-516-70 | 10 | 12/12 | 3.5 / 8 | 18 | 20 | 32 |
| C-105 | Naphtha stabiliser (debutaniser) | 2.1 x 18 | SA-516-70 | 14 | 16/16 | 6 / 8 | 48 | 54 | 111 |
| C-106 | Naphtha splitter | 3.1 x 29.5 | SA-516-70 | 12 | 12/12 | 7.5 / 12 | 109 | 130 | 334 |
| C-201 | Vacuum column (wet, packed) | 6.6 / 3 / 2.6 x 36 | SA-516-70 | 18-25 | 18/18 | 6 / 18 | 294 | 337 | 1,043 |
| D-101A | Electrostatic desalter, 1st stage | 3.8 x 30 | SA-516-70 | 28 | 28 | saddles | 137 | 414 | 487 |
| D-101B | Electrostatic desalter, 2nd stage | 3.8 x 30 | SA-516-70 | 28 | 28 | saddles | 137 | 414 | 487 |
| D-102 | Atm. overhead reflux drum (3-phase) | 3.4 x 12 | SA-516-70 | 12 | 12 | saddles | 19 | 63 | 144 |
| D-103 | Fuel gas knock-out drum | 0.9 x 2.5 | SA-516-70 | 8 | 8 | legs | 1 | 2 | 3 |
| D-104 | Flare knock-out drum (unit) | 2.1 x 6.5 | SA-516-70 | 8 | 8 | saddles | 5 | 14 | 29 |
| D-105 | Stabiliser reflux drum | 1.7 x 5.5 | SA-516-70 | 16 | 16 | saddles | 6 | 11 | 20 |
| D-106 | Splitter reflux drum | 2.7 x 8.5 | SA-516-70 | 10 | 10 | saddles | 9 | 28 | 63 |
| D-201 | Ejector hotwell / sour water separator | 1.3 x 5.5 | SA-516-70 | 8 | 8 | saddles | 3 | 6 | 10 |
| D-202 | Vacuum off-gas knock-out drum | 0.6 x 2 | SA-516-70 | 8 | 8 | legs | 1 | 1 | 1 |
| H-101 | Atmospheric crude charge heater | 21.9 x 12.7 x 38 | A335 P9 tubes | 10.97 (tube) | - | - | 1,033 | 1,059 | 905 |
| H-201 | Vacuum heater | 21.9 x 5.4 x 32 | A335 P9 tubes | 10.97 (tube) | - | - | 328 | 337 | 347 |
