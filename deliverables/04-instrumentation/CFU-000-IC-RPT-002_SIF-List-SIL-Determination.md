# 1. Purpose

This report lists the safety instrumented functions (SIFs) of the CDU / VDU, summarises the SIL determination by layer of protection analysis (LOPA), and documents the trip set-point basis used in the cause & effect matrix CFU-000-IC-CE-001. It is the FEED input to the Safety Requirements Specification (SRS, IEC 61511-1 clause 10).

# 2. Method

- Scenarios from the preliminary HAZOP (CFU-000-PR-RPT-002) and the SIF list in `cfu/control_loops.py`.

- Tolerable / target mitigated event likelihood (TMEL) by consequence category: C5 multiple fatalities 1e-6 /yr, C4 single fatality 1e-5 /yr, C3 serious injury / major environmental or asset 1e-4 /yr, C2 1e-3 /yr.

- Initiating event frequencies and IPL PFDs are CCPS typical values: BPCS loop failure 0.1 /yr; operator response to an independent alarm with >= 10 min available 0.1; PSV 0.01. Conditional modifiers (ignition, occupancy) are applied explicitly.

- Required risk reduction RRF = (IEF x prod(IPL PFD) x prod(CM)) / TMEL; SIL 1: 10 < RRF <= 100, SIL 2: 100 < RRF <= 1000, SIL 3: 1000 < RRF <= 10000.

- Manual ESD (SIF-901) is assigned SIL 2 by company practice (no LOPA scenario).

# 3. SIF list

| SIF | Function | Initiators | Voting | Final elements | SIL | Response | Proof test |
|---|---|---|---|---|---|---|---|
| SIF-101 | H-101 low-low pass flow (any pass) -> trip fuel | FT-1011..1018 (2oo3 each pass) | 2oo3 | XV-1021/1022 FG SSOV, XV-1026 pilot | SIL 2 | 2 s | 12 months |
| SIF-102 | H-101 low-low fuel gas pressure -> trip fuel | PT-1027A/B/C 2oo3 | 2oo3 | XV-1021/1022 | SIL 1 | 2 s | 24 months |
| SIF-103 | H-101 high-high fuel gas pressure -> trip fuel | PT-1027A/B/C 2oo3 | 2oo3 | XV-1021/1022 | SIL 1 | 2 s | 24 months |
| SIF-104 | H-101 loss of flame (all burners) -> trip fuel | BS-1028 (scanners) | per burner / all | XV-1021/1022/1026 | SIL 2 | 4 s (FFRT) | 12 months |
| SIF-105 | H-101 high-high arch pressure / loss of ID fan -> trip | PT-1029A/B/C | 2oo3 | XV-1021/1022 | SIL 1 | 3 s | 24 months |
| SIF-106 | H-101 high-high COT -> trip fuel | TT-1020A/B/C 2oo3 | 2oo3 | XV-1021/1022 | SIL 1 | 5 s | 24 months |
| SIF-107 | D-101A/B low-low interface (grid short) -> trip transformers | LT-1007B / LT-1008B | 1oo1 | Desalter transformer CB | SIL 1 | 5 s | 24 months |
| SIF-108 | C-101 high-high bottom level -> stop P-101 / close FV-1001 | LT-1082B | 1oo1 | XV-1001 + P-101 trip | SIL 1 | 10 s | 24 months |
| SIF-109 | D-105 low-low level -> close LPG product XV (gas blow-by to LPG treating) | LT-1092B | 1oo1 | XV-1093 | SIL 1 | 5 s | 24 months |
| SIF-110 | C-105 high-high pressure -> cut reboiler steam | PT-1091B | 1oo1 | XV-1096 | SIL 1 | 5 s | 24 months |
| SIF-201 | H-201 low-low pass flow -> trip fuel | FT-2001..2004 | 2oo3 | XV-2006A/B | SIL 2 | 2 s | 12 months |
| SIF-202 | H-201 low-low FG pressure / flame failure -> trip | PT-2009A/B/C, BS-2008 | per burner / all | XV-2006A/B | SIL 1 | 4 s (FFRT) | 24 months |
| SIF-203 | C-201 high-high bottom level -> trip FV-1083 / P-112 | LT-2024B | 1oo1 | XV-1083 | SIL 1 | 10 s | 24 months |
| SIF-204 | Pump P-112/P-204 hot-pump emergency isolation (fire) | Manual HS / fire detection | 1oo2 | EIV-1121/EIV-2041 (ROSOV) | SIL 1 | 30 s (valve) | 24 months |
| SIF-901 | Unit emergency shutdown (ESD-1, manual) | HS-9000 (CCR + field) | 1oo2 | All unit trip valves, heater trips | SIL 2 | 2 s | 12 months |



# 4. LOPA / SIL determination

**4.1 Scenarios and initiating events**

| SIF | Hazard scenario | Initiating event (IEF /yr) | Consequence (TMEL /yr) |
|---|---|---|---|
| SIF-101 | Loss of pass flow (FV fails closed, coking, charge loss) -> tube overheating / rupture, firebox fire | BPCS loop failure / charge pump trip (0.1) | C4 single fatality (1e-05) |
| SIF-102 | Flame-out on low FG pressure -> fuel accumulation, re-ignition explosion | PV-1021 fails closed / FG supply loss (0.1) | C4 single fatality (1e-05) |
| SIF-103 | High FG pressure -> flame lift-off / unstable flame -> flame-out, explosion | PV-1021 fails open (0.1) | C4 single fatality (1e-05) |
| SIF-104 | Loss of flame with fuel flowing -> firebox explosion | Burner instability / air-fuel upset (0.1) | C4 single fatality (1e-05) |
| SIF-105 | Positive firebox pressure (ID fan trip / damper closed) -> flue gas / flame release | ID fan trip or damper failure (0.2) | C3 serious injury (1e-04) |
| SIF-106 | High COT -> coking / tube overheating, transfer-line overpressure | TIC-1020 / PIC-1021 failure (0.1) | C3 serious injury / major asset (1e-04) |
| SIF-107 | Low interface -> water on electrodes, grid short / arcing, vapour generation, fire | LIC-1007/1008 failure (0.1) | C3 serious injury (1e-04) |
| SIF-108 | C-101 overfill -> liquid into overhead / PSV liquid relief, flare carry-over | LIC-1082 / FV-1083 failure, P-112 trip (0.1) | C3 major environmental (1e-04) |
| SIF-109 | D-105 loss of level -> gas blow-by into LPG treating / rundown, overpressure | LIC-1092 / FV-1093 fails open (0.1) | C3 serious injury (1e-04) |
| SIF-110 | C-105 overpressure on reboiler upset / loss of cooling -> PSV-1005 lift, LPG release | FIC-1096 failure / A-106 fan loss (0.2) | C3 serious injury (1e-04) |
| SIF-201 | H-201 loss of pass flow -> coking, tube rupture, fire | FIC-2001..2004 failure / P-112 trip (0.1) | C4 single fatality (1e-05) |
| SIF-202 | H-201 low FG pressure / flame failure -> fuel accumulation, explosion | PV-2006 failure / burner instability (0.1) | C4 single fatality (1e-05) |
| SIF-203 | C-201 overfill -> liquid into flash zone / wash bed, loss of vacuum, overpressure | LIC-2024 / FV-2025 failure, P-204 trip (0.1) | C3 major asset (1e-04) |
| SIF-204 | Fire at hot pump (> AIT) -> escalation; isolate inventory of C-101 / C-201 bottoms | Pump seal failure with ignition (0.01) | C4 single fatality (1e-05) |
| SIF-901 | Major emergency - unit-wide isolation (manual ESD) | Operator-initiated (escalation) (-) | C4 single fatality (1e-05) |



**4.2 Independent protection layers, conditional modifiers and required risk reduction**

| SIF | IPLs (PFD) | Conditional modifiers | MEL w/o SIF | RRF | SIL (LOPA) | SIL (SRS) |
|---|---|---|---|---|---|---|
| SIF-101 | Low-flow alarm FAL + operator (>= 10 min) (0.1) | Occupancy (heater area) (0.25) | 2.5e-03 | 250 | SIL 2 | SIL 2 |
| SIF-102 | Low-pressure alarm + operator (0.1) | Probability of delayed ignition (0.1); Occupancy (0.25) | 2.5e-04 | 25 | SIL 1 | SIL 1 |
| SIF-103 | High-pressure alarm + operator (0.1) | Probability of flame-out given HH (0.1); Occupancy (0.25) | 2.5e-04 | 25 | SIL 1 | SIL 1 |
| SIF-104 | Operator observation (no credit - too fast) (1) | Probability of explosive accumulation (0.1); Probability of ignition (0.5); Occupancy (0.25) | 1.3e-03 | 125 | SIL 2 | SIL 2 |
| SIF-105 | Draft alarm + operator (0.1) | Occupancy (platform) (0.1) | 2.0e-03 | 20 | SIL 1 | SIL 1 |
| SIF-106 | High-temperature alarm + operator (0.1) | Probability of tube rupture (0.5) | 5.0e-03 | 50 | SIL 1 | SIL 1 |
| SIF-107 | Interface alarm + operator (0.1) | Probability of ignition (0.3) | 3.0e-03 | 30 | SIL 1 | SIL 1 |
| SIF-108 | High-level alarm + operator (0.1) | Probability PSV relieves liquid (0.5) | 5.0e-03 | 50 | SIL 1 | SIL 1 |
| SIF-109 | Low-level alarm + operator (0.1) | Probability of downstream LOPC (0.3) | 3.0e-03 | 30 | SIL 1 | SIL 1 |
| SIF-110 | PSV-1005 (sized for case) (0.01) | Probability of ignition of flare release (1) | 2.0e-03 | 20 | SIL 1 | SIL 1 |
| SIF-201 | Low-flow alarm + operator (0.1) | Occupancy (0.25) | 2.5e-03 | 250 | SIL 2 | SIL 2 |
| SIF-202 | Alarm + operator (0.1) | Probability of delayed ignition (0.1); Occupancy (0.25) | 2.5e-04 | 25 | SIL 1 | SIL 1 |
| SIF-203 | High-level alarm + operator (0.1) | Probability of damage (0.5) | 5.0e-03 | 50 | SIL 1 | SIL 1 |
| SIF-204 | Fire-fighting (OSBL response) (1) | Probability of escalation within 15 min (0.1); Occupancy (0.5) | 5.0e-04 | 50 | SIL 1 | SIL 1 |
| SIF-901 | - | - | - | - | SIL 2 (company standard, manual ESD - LOPA n/a) | SIL 2 |



**Result:** 15 SIFs assessed; 15 LOPA results are consistent with the SIL in the SIF list. SIL distribution: SIL 1: 11, SIL 2: 4. No SIL 3 function is required; the logic solver is nevertheless SIL 3 capable to allow future changes without hardware replacement.

# 5. Trip set-point basis

- Pass flow LL = 40 % of design pass flow (below the 50 % turndown minimum with 10 % margin).

- COT HH = design COT + 15 °C (H-101) / + 12 °C (H-201); high alarm at + 8 °C (+ 6 °C).

- Burner FG pressure LL / HH per burner vendor stability curve (FEED: 0.15 / 2.2 barg with 2.0 barg max normal at design firing).

- Arch pressure HH = +2.5 mmH2O (normal -2.5 mmH2O draft).

- Vessel pressure HH = min(94 % of PSV set, set - 0.5 bar) - keeps >= 6 % margin to PSV lift.

- Level HH = 85 % of transmitter span (above HLA at 75 %); LL = 15 % (below LLA at 25 %).

| Initiator | SIF | Description | Voting | Normal | Trip | Response |
|---|---|---|---|---|---|---|
| FZLL-1011 | SIF-101 | H-101 pass 1 flow low-low | 2oo3 | 71.1 t/h | 28.5 t/h | 2 s |
| FZLL-1012 | SIF-101 | H-101 pass 2 flow low-low | 2oo3 | 71.1 t/h | 28.5 t/h | 2 s |
| FZLL-1013 | SIF-101 | H-101 pass 3 flow low-low | 2oo3 | 71.1 t/h | 28.5 t/h | 2 s |
| FZLL-1014 | SIF-101 | H-101 pass 4 flow low-low | 2oo3 | 71.1 t/h | 28.5 t/h | 2 s |
| FZLL-1015 | SIF-101 | H-101 pass 5 flow low-low | 2oo3 | 71.1 t/h | 28.5 t/h | 2 s |
| FZLL-1016 | SIF-101 | H-101 pass 6 flow low-low | 2oo3 | 71.1 t/h | 28.5 t/h | 2 s |
| FZLL-1017 | SIF-101 | H-101 pass 7 flow low-low | 2oo3 | 71.1 t/h | 28.5 t/h | 2 s |
| FZLL-1018 | SIF-101 | H-101 pass 8 flow low-low | 2oo3 | 71.1 t/h | 28.5 t/h | 2 s |
| PZLL-1027 | SIF-102 | H-101 burner FG pressure low-low | 2oo3 | 1.0-2.0 barg | 0.15 barg | 2 s |
| PZHH-1027 | SIF-103 | H-101 burner FG pressure high-high | 2oo3 | 1.0-2.0 barg | 2.2 barg | 2 s |
| BZLL-1028 | SIF-104 | H-101 loss of flame (all burners) | per burner / all | flame on | flame off | 4 s (FFRT) |
| PZHH-1029 | SIF-105 | H-101 arch pressure high-high / ID fan loss | 2oo3 | -2.5 mmH2O | +2.5 mmH2O | 3 s |
| TZHH-1020 | SIF-106 | H-101 COT high-high | 2oo3 | 366 °C | 381 °C | 5 s |
| LZLL-1007 | SIF-107 | D-101A interface low-low (grid short) | 1oo1 | 50 % | 15 % | 5 s |
| LZLL-1008 | SIF-107 | D-101B interface low-low (grid short) | 1oo1 | 50 % | 15 % | 5 s |
| LZHH-1082 | SIF-108 | C-101 bottom level high-high | 1oo1 | 50 % | 85 % | 10 s |
| LZLL-1092 | SIF-109 | D-105 level low-low (gas blow-by to LPG) | 1oo1 | 50 % | 15 % | 5 s |
| PZHH-1091 | SIF-110 | C-105 pressure high-high | 1oo1 | 10.8 barg | 12.2 barg | 5 s |
| FZLL-2001 | SIF-201 | H-201 pass 1 flow low-low | 2oo3 | 64.5 t/h | 25.8 t/h | 2 s |
| FZLL-2002 | SIF-201 | H-201 pass 2 flow low-low | 2oo3 | 64.5 t/h | 25.8 t/h | 2 s |
| FZLL-2003 | SIF-201 | H-201 pass 3 flow low-low | 2oo3 | 64.5 t/h | 25.8 t/h | 2 s |
| FZLL-2004 | SIF-201 | H-201 pass 4 flow low-low | 2oo3 | 64.5 t/h | 25.8 t/h | 2 s |
| PZLL-2009 | SIF-202 | H-201 burner FG pressure low-low | 2oo3 | 1.0-2.0 barg | 0.15 barg | 2 s |
| BZLL-2008 | SIF-202 | H-201 loss of flame (all burners) | per burner / all | flame on | flame off | 4 s (FFRT) |
| LZHH-2024 | SIF-203 | C-201 bottom level high-high | 1oo1 | 50 % | 85 % | 10 s |
| HS-1121 | SIF-204 | P-112 area fire - manual / F&G confirmed | 1oo2 | - | - | 30 s (valve) |
| HS-2041 | SIF-204 | P-204 area fire - manual / F&G confirmed | 1oo2 | - | - | 30 s (valve) |
| HS-9000 | SIF-901 | Unit ESD-1 push-button | 1oo2 | - | - | 2 s |



# 6. SRS requirements (FEED)

- SIS sensors, logic solver and final elements independent of the BPCS (separate taps, transmitters, cables, JBs and cabinets); BPCS valves are not credited as SIS final elements.

- 2oo3 voting for continuous analogue initiators on heaters (degrade to 2oo2 on fault, 1oo1 trip on two faults); 1oo1 for SIL 1 level / pressure functions with BPCS-transmitter comparison alarm.

- De-energise to trip for all SIFs; line monitoring on SOV outputs; fail-safe on loss of power or air.

- Bypasses for maintenance only via key-switch with time limit and CCR alarm; operational overrides (start-up) auto-reset.

- Proof-test intervals: SIL 2 12 months (partial-stroke tests of SSOVs every 3 months), SIL 1 24 months; PFDavg to be verified with vendor data (IEC 61508 certified devices or prior use).

- Response times per SIF (table above) include sensor, logic solver and final element closure; SSOV closure <= 2 s, ROSOV <= 30 s.

- BMS: NFPA 85 / 86 and API 556 sequences (purge, pilot proving, flame supervision, safety time 4 s).

# 7. F&G executive actions

Confirmed gas (2ooN at 50 % LEL) or confirmed fire per fire zone initiate the actions shown in the C&E matrix: beacons / PAGA, isolation of fuel to the heaters in the heater zone, ROSOV closure for the hot pumps P-112 / P-204 in their zones and the signal to the OSBL fire-water pumps. F&G is a SIL 2 system; performance targets (coverage, detector voting) from the F&G mapping study.