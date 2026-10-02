# 1 Basis
- AACE Class 4 (expected accuracy -30 % / +50 %), ISBL only, US Gulf Coast, 2026 USD (CEPCI 820, assumed).
- Purchased equipment: Towler & Sinnott correlations (CEPCI 532.9), with material factors per equipment
  metallurgy (5Cr 1.4, 9Cr 1.7, clad 1.6, Monel 1.9). Vessel shell weights come from the mechanical calculations
  (data/mech.json) where available.
- Installation: Towler fluids-processing factors (erection 0.3, piping 0.8, instrumentation
  0.3, electrical 0.2, civil 0.3, structures 0.2, lagging/paint 0.1).
- Excluded: Tankage, SWS, flare stack, CCR, main substation, OSBL racks; owner's costs, licence fees, land, escalation beyond 2026, catalyst/chemicals first fill.

# 2 Summary
| Item | USD million |
|---|---|
| Purchased equipment (2026 USGC) | 56.7 |
| Installed ISBL (Towler factors) | 167.8 |
| Design & engineering (25 %) | 42.0 |
| Contingency (20 %) | 42.0 |
| Total installed cost, ISBL | 251.7 |

Specific cost: **2,517 USD per BPSD** of capacity, ISBL. Check this against the owner's own
benchmark data for grassroots CDU/VDU units before using it for budgeting. The factored method tends to
under-estimate large, alloy-heavy refinery units.

# 3 Purchased equipment by type
| Type | USD million | Share |
|---|---|---|
| Fired heater | 19.24 | 34% |
| Column | 11.65 | 21% |
| Air cooler | 8.87 | 16% |
| Shell & tube | 7.17 | 13% |
| Desalter | 3.83 | 7% |
| Pump | 3.62 | 6% |
| Package | 0.74 | 1% |
| Drum | 0.62 | 1% |
| Ejector | 0.42 | 1% |
| Fan | 0.33 | 1% |
| Air preheater | 0.24 | 0% |

# 4 Equipment detail
| Tag | Service | Basis | Ce 2026 kUSD |
|---|---|---|---|
| C-101 | Atmospheric crude fractionator | shell 141 t, 41 trays | 3,566 |
| C-102 | Kero side stripper | shell 8 t, 6 trays | 143 |
| C-103 | Diesel side stripper | shell 13 t, 6 trays | 303 |
| C-104 | Ago side stripper | shell 9 t, 6 trays | 224 |
| C-105 | Naphtha stabiliser (debutaniser) | shell 22 t, 19 trays | 334 |
| C-106 | Naphtha splitter | shell 44 t, 38 trays | 718 |
| C-201 | Vacuum column (wet, packed) | shell 160 t, 20 trays, 308 m3 packing | 6,363 |
| H-101 | Atmospheric crude charge heater | 60.7 MW box | 14,455 |
| H-201 | Vacuum heater | 14.7 MW box | 4,788 |
| K-101A/B | H-101 forced-draft fan | 2 x 90 kW | 125 |
| K-102A/B | H-101 induced-draft fan | 2 x 200 kW | 208 |
| E-120 | H-101 cast-iron/glass-tube air preheater | 500 m2, 1 shell(s) | 236 |
| E-101 | Crude / Top pumparound | 359 m2, 1 shell(s) | 174 |
| E-102 | Crude / Kerosene product | 438 m2, 1 shell(s) | 208 |
| E-103 | Crude / LVGO pumparound/product | 804 m2, 2 shell(s) | 386 |
| E-104 | Crude / Diesel product | 378 m2, 1 shell(s) | 183 |
| E-105 | Crude / Vacuum residue | 431 m2, 1 shell(s) | 288 |
| E-106 | Crude / Middle (kero) pumparound | 1001 m2, 2 shell(s) | 661 |
| E-107 | Crude / Diesel product | 324 m2, 1 shell(s) | 224 |
| E-108 | Crude / HVGO pumparound/product | 2196 m2, 4 shell(s) | 1,755 |
| E-109 | Crude / AGO product | 263 m2, 1 shell(s) | 231 |
| E-110 | Crude / Bottom (diesel) pumparound | 886 m2, 2 shell(s) | 716 |
| E-111 | Crude / Vacuum residue | 1094 m2, 2 shell(s) | 875 |
| E-113 | BPA / MP steam generator (kettle) | 223 m2, 1 shell(s) | 120 |
| E-201 | VR / LP steam generator (kettle) | 84 m2, 1 shell(s) | 100 |
| E-114 | Stabiliser feed / bottoms | 86 m2, 1 shell(s) | 72 |
| E-115 | Atm. overhead trim condenser | 740 m2, 2 shell(s) | 358 |
| E-116 | Stabiliser reboiler (HP steam) | 242 m2, 1 shell(s) | 127 |
| E-117 | Splitter reboiler (MP steam) | 225 m2, 1 shell(s) | 121 |
| E-118 | Desalter wash water / brine | 84 m2, 1 shell(s) | 71 |
| E-202 | 1st-stage ejector intercondenser | 549 m2, 1 shell(s) | 335 |
| E-203 | 2nd-stage ejector intercondenser | 79 m2, 1 shell(s) | 90 |
| E-204 | Ejector aftercondenser | 30 m2, 1 shell(s) | 72 |
| A-101 | Atm. overhead condenser | 1667 m2 bare | 3,053 |
| A-103 | Kero cooler | 184 m2 bare | 388 |
| A-104 | Diesel cooler | 302 m2 bare | 589 |
| A-105 | Ago cooler | 287 m2 bare | 562 |
| A-106 | Stabiliser overhead condenser | 214 m2 bare | 439 |
| A-107 | Splitter overhead condenser | 881 m2 bare | 1,645 |
| A-108 | Heavy naphtha product cooler | 401 m2 bare | 756 |
| A-201 | Lvgo cooler | 397 m2 bare | 748 |
| A-202 | Hvgo Product cooler | 361 m2 bare | 688 |
| D-101A | Electrostatic desalter, 1st stage | shell 101 t | 1,917 |
| D-101B | Electrostatic desalter, 2nd stage | shell 101 t | 1,917 |
| D-102 | Atm. overhead reflux drum (3-phase) | shell 19 t | 219 |
| D-103 | Fuel gas knock-out drum | shell 1 t | 36 |
| D-105 | Stabiliser reflux drum | shell 6 t | 91 |
| D-106 | Splitter reflux drum | shell 8 t | 120 |
| D-201 | Ejector hotwell / sour water separator | shell 2 t | 49 |
| D-202 | Vacuum off-gas knock-out drum | shell 1 t | 31 |
| D-104 | Flare knock-out drum (unit) | shell 4 t | 73 |
| J-201 | Steam ejector (20 -> 130 mbar(a)) | 2 x 50 % train | 138 |
| J-202 | Steam ejector (120 -> 350 mbar(a)) | 2 x 50 % train | 138 |
| J-203 | Steam ejector (330 -> 1100 mbar(a)) | 2 x 50 % train | 138 |
| P-101A/B | Crude charge | 2 x 730 m3/h, 710 kW | 457 |
| P-102A/B | Desalted crude booster | 2 x 805 m3/h, 710 kW | 470 |
| P-103A/B | Atm. reflux | 2 x 159 m3/h, 55 kW | 114 |
| P-104A/B | Unstabilised naphtha | 2 x 180 m3/h, 160 kW | 171 |
| P-105A/B | Overhead sour water | 2 x 14 m3/h, 5.5 kW | 45 |
| P-106A/B | TPA pumparound | 2 x 293 m3/h, 110 kW | 164 |
| P-107A/B | MPA pumparound | 2 x 387 m3/h, 160 kW | 231 |
| P-108A/B | BPA pumparound | 2 x 318 m3/h, 132 kW | 205 |
| P-109A/B | Kero product | 2 x 122 m3/h, 55 kW | 125 |
| P-110A/B | Diesel product | 2 x 151 m3/h, 75 kW | 143 |
| P-111A/B | Ago product | 2 x 84 m3/h, 45 kW | 110 |
| P-112A/B | Atm. residue / vacuum heater charge | 2 x 398 m3/h, 315 kW | 290 |
| P-114A/B | Desalter wash water | 2 x 37 m3/h, 18.5 kW | 65 |
| P-115A/B | Stabiliser reflux / LPG | 2 x 39 m3/h, 18.5 kW | 66 |
| P-116A/B | Splitter reflux / LN | 2 x 146 m3/h, 55 kW | 112 |
| P-117A/B | Heavy naphtha product | 2 x 142 m3/h, 45 kW | 104 |
| P-118 | Desalter mud-wash / recycle | 1 x 19 m3/h, 7.5 kW | 24 |
| P-201A/B | LVGO pumparound / product | 2 x 198 m3/h, 110 kW | 171 |
| P-202A/B | HVGO pumparound / product | 2 x 391 m3/h, 200 kW | 248 |
| P-203A/B | Slop wax | 2 x 12 m3/h, 5.5 kW | 55 |
| P-204A/B | Vacuum residue (incl. quench) | 2 x 196 m3/h, 132 kW | 182 |
| P-205A/B | Hotwell sour water | 2 x 13 m3/h, 3.7 kW | 41 |
| P-206A/B | Hotwell slop oil | 2 x 1 m3/h, 0.75 kW | 31 |
| X-101 | Demulsifier injection package | vendor package | 185 |
| X-102 | Caustic injection package (desalted crude) | vendor package | 185 |
| X-103 | Neutraliser / filming amine package (atm OH) | vendor package | 185 |
| X-104 | Corrosion inhibitor package (VDU OH) | vendor package | 185 |

# 5 Accuracy and next steps
The heaters, the column shells and internals, and the hot exchanger bank account for more than 60 % of
equipment cost. Vendor budget quotes for H-101, H-201, C-101, C-201 and the desalters should be obtained to
move the estimate to Class 3.
