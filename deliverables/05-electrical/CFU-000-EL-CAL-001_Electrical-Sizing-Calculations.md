# CFU-000-EL-CAL-001 - Electrical System Sizing Calculations

Rev A - Issued for review (FEED). Unit: 100 kBPSD Crude & Vacuum Distillation Unit (100,000 BPSD). Generated from `cfu/elec` (load list, studies and cable schedule are computed from data/equipment.json; no hand-typed process data).

## 1. Purpose and scope

FEED-level sizing of the unit electrical distribution in substation SS-100: maximum demand, transformer ratings, short-circuit levels and switchgear ratings, largest-motor starting voltage dip, cable sizing method and results, UPS and DC battery sizing, and the basis for not providing an emergency diesel generator. Hazardous-area classification is deferred until the plot plan is final.

## 2. Basis and references

| Item | Value |
|---|---|
| Utility supply | 2 x 13.8 kV feeders from refinery main substation, 3-ph, 60 Hz |
| Utility fault level | 31.5 kA at 13.8 kV (753 MVA), X/R 15 (assumed) |
| Distribution voltages | 4.16 kV MV motors >= 200 kW; 480 V LV; 208Y/120 V lighting; 120 V UPS |
| System grounding | 13.8 kV per utility; 4.16 kV low-resistance 400 A / 10 s; 480 V high-resistance 5 A (alarm, continued operation); 208Y/120 V solidly grounded |
| Codes | NFPA 70 (NEC), IEEE 141, 242, 399, 485, 1100, IEEE C57.12.00/.10, C37.20.1/.2/.7, C37.2, IEC 60364-5-52, IEC 60502-2, IEC 60909 (peak factor), API RP 540 |
| Ambient | 35.0 C design, -5.0 C min, elevation 5 m |

## 3. System configuration

Secondary-selective (double-ended) arrangement at every level: two 13.8 kV incomers to SWG-101A/B with a normally-open tie; two 13.8/4.16 kV transformers TR-101/102 feeding SWG-102A/B (N.O. tie); two 4.16/0.48 kV transformers TR-103/104 feeding the 480 V switchgear/MCC-101A/B (N.O. tie). Ties are interlocked 2-out-of-3 so transformers are never paralleled; on loss of one source the incomer opens and the tie closes automatically (open transition). Every transformer therefore carries the full demand of both bus sections in the contingency case. Pump pairs (2 x 100 %) are split across the two bus sections. See CFU-000-EL-SLD-001..004.

## 4. Electrical load and maximum demand

Maximum demand MD = 1.0 x C + 0.3 x I + 0.1 x S (continuous / intermittent / standby), applied separately to kW and kvar (IEEE 141 practice). Motor input = absorbed kW / efficiency (/ 0.97 for VFDs). Detailed list: CFU-000-EL-LDL-001.

| Bus | Connected kW | C kW | I kW | S kW | MD kW | MD kvar | MD kVA | PF |
|---|---|---|---|---|---|---|---|---|
| MCC-101A | 1,769 | 1,084 | 127 | 559 | 1,178 | 643 | 1,342 | 0.88 |
| MCC-101B | 1,779 | 1,080 | 124 | 575 | 1,175 | 634 | 1,335 | 0.88 |
| SWG-102A | 1,903 | 985 | 0 | 918 | 1,077 | 528 | 1,199 | 0.90 |
| SWG-102B | 1,903 | 918 | 0 | 985 | 1,017 | 534 | 1,148 | 0.89 |
| SWG-102A incl. LV |  |  |  |  | 2,266 | 1,197 | 2,563 | 0.88 |
| SWG-102B incl. LV |  |  |  |  | 2,203 | 1,193 | 2,505 | 0.88 |
| **Unit total at 13.8 kV** |  |  |  |  | **4,505** | **2,533** | **5,168** | 0.87 |

LV transformer through-load includes 1 % active / 4 % reactive transformer losses; MV transformer 0.8 % / 6 %.

## 5. Transformer sizing

Criteria: (a) ONAN rating >= contingency maximum demand (both bus sections on one transformer, tie closed), with ONAN loading <= 95 %; (b) ONAF (fan-cooled, +25 % for <= 10 MVA per IEEE C57.12.10) >= 1.25 x MD, i.e. the 25 % future margin is available with forced cooling. Off-circuit taps +/-2 x 2.5 %.

| Transformer | Ratio | MD kVA | 1.25 x MD | Selected ONAN/ONAF kVA | ONAN load % | Z % | Secondary FLC (ONAF) A |
|---|---|---|---|---|---|---|---|
| TR-101 / TR-102 | 13.8/4.16 kV | 5,068 | 6,335 | 7,500 / 9,375 | 68 | 7.0 | 1,301 |
| TR-103 / TR-104 | 4.16/0.48 kV | 2,676 | 3,345 | 3,000 / 3,750 | 89 | 5.75 | 4,511 |
| LTR-101A | 480-208Y/120 V | 41 | 51 | 75 (dry, AN) | 54 | 4.0 |  |
| LTR-101B | 480-208Y/120 V | 41 | 51 | 75 (dry, AN) | 54 | 4.0 |  |

The 13.8/4.16 kV unit rating (7.5 MVA) is governed by the 95 % ONAN loading limit: the next smaller standard size (5 MVA) would be loaded to 101 % with no ONAN margin. The 480 V transformers are at the practical upper limit for 480 V unit substations (5000 A bus); see Section 11.

## 6. Short-circuit levels

Method: IEEE 141 / ANSI E/X hand calculation on a 100 MVA base, prefault voltage 1.0 pu. Sources: utility (753 MVA, X/R 15); running motors as subtransient sources - MV motors X" = 0.17 pu on motor kVA, LV motors grouped at 4 x FLC (X" = 0.25 pu); VFD-fed motors excluded. Peak ip = kappa x sqrt(2) x Ik", kappa = 1.02 + 0.98 e^(-3R/X) (IEC 60909).

| Element | Z (pu, 100 MVA) | X/R |
|---|---|---|
| Utility 13.8 kV | 0.1328 | 15 |
| TR-101/102 (7.5 MVA, 7.0 %) | 0.9333 | 14 |
| TR-103/104 (3 MVA, 5.75 %) | 1.9167 | 6 |

| Case | Bus | Ik" kA sym | X/R | ip kA peak |
|---|---|---|---|---|
| normal (tie open) - section A | 13.8 kV | 31.9 | 14.9 | 82.1 |
| normal (tie open) - section A | 4.16 kV | 14.4 | 13.7 | 36.9 |
| normal (tie open) - section A | 0.48 kV | 46.3 | 7.3 | 109.4 |
| normal (tie open) - section B | 13.8 kV | 31.9 | 14.9 | 82.2 |
| normal (tie open) - section B | 4.16 kV | 14.5 | 13.7 | 37.2 |
| normal (tie open) - section B | 0.48 kV | 46.5 | 7.3 | 109.9 |
| one transformer, tie closed | 13.8 kV | 32.2 | 14.9 | 83.0 |
| one transformer, tie closed | 4.16 kV | 15.9 | 13.4 | 40.5 |
| one transformer, tie closed | 0.48 kV | 52.4 | 7.1 | 123.3 |

| Equipment | Max. calculated Ik" kA | Selected rating (kA sym, >= 1.1 x calc.) | Bus continuous A |
|---|---|---|---|
| SWG-101 13.8 kV | 32.2 | 40 | 1200 |
| SWG-102 4.16 kV | 15.9 | 31.5 | 2000 |
| MCC-101 480 V | 52.4 | 65 | 5000 |

The 13.8 kV rating is set by the utility (31.5 kA) plus motor contribution; 40 kA switchgear is specified. Ratings assume the tie is never closed with both incomers in service (2-out-of-3 interlock).

## 7. Motor starting voltage dip

Largest DOL motor: P-101A (710 kW, 4.16 kV; P-101A/B and P-102A/B are identical 710 kW units). Locked-rotor 6.5 x FLC at PF 0.2 -> 5,373 kVA. Network: utility + one 13.8/4.16 kV transformer (ONAN impedance); pre-start bus load modelled as constant impedance with pre-start bus voltage 1.00 pu (tap setting); motor cable impedance included for the terminal voltage. Limits: 10 % at the 4.16 kV bus, 15 % at the motor terminals.

| Case | Pre-start load kVA | Bus dip % | Terminal dip % | Result |
|---|---|---|---|---|
| Normal: tie open, motor bus section on its own transformer | 1,845 | 5.3 | 5.8 | OK |
| Contingency: one 13.8/4.16 kV transformer feeding both sections, largest motor started last | 4,350 | 5.2 | 5.8 | OK |
| Contingency + one 13.8 kV incomer (utility fault level reduced to 20 kA assumed) | 4,350 | 5.6 | 6.1 | OK |

DOL starting of the 710 kW pumps is therefore acceptable; no soft-starter / autotransformer is required. Motor-acceleration time and pump torque margin to be confirmed with vendor curves (IEEE 399 dynamic study at detailed design). LV motors: bus dip on MCC-101A/B for each DOL start is computed in the cable schedule (largest 3.5 %).

## 8. Cable sizing

- Conductors: copper, XLPE 90 C, IEC 60228 metric sizes (mm2). LV 0.6/1 kV Cu/XLPE/SWA/PVC multicore with separate earth core (IEC 60364-5-54 sizing); 4.16 kV: 3.6/6 kV screened 3-core Cu/XLPE/CWS/SWA/PVC; 13.8 kV: 8.7/15 kV single-core in trefoil. Equivalent UL/NEC types (MC-HL / TC-ER) acceptable; NEC 310 ampacity check at detailed design.
- Ampacity: base values IEC 60364-5-52 Table B.52.12 method E (LV) / IEC 60502-2 Annex B (MV) at 30 C in air on ladder tray; derating 0.91 (40 C ambient incl. solar) x 0.8 (grouping) = 0.73. Required ampacity >= 1.25 x FLC for motors (NEC 430.22) and >= 1.25 x rated current for feeders (continuous load).
- Voltage drop: dV% = sqrt(3) I L (R cos(phi) + X sin(phi)) / V x 100 with R at 90 C. Running <= 5 %. Starting (DOL, 6.5 x FLC at PF 0.35 LV / 0.2 MV): bus dip + cable drop <= 15 % at motor terminals; bus dip <= 10 %.
- Short-circuit withstand: S >= sqrt(I^2 t) / k, k = 143 (Cu/XLPE 90->250 C). MV: prospective bus fault current with t = 0.25 s (motor feeders, instantaneous 50 element) / 0.5 s (incomers, transformer feeders). LV: let-through I^2t of current-limiting MCCB by rating (manufacturer typical, 65 kA class).
- Minimum sizes: LV power 4 mm2; 4.16 kV 35 mm2. Parallel LV runs >= 95 mm2.
- Route length = Manhattan distance from SS-100 reference point (25, 12.5) m to the consumer + 15 m riser/termination allowance (+10 m for air-cooler fan motors on top of the pipe rack), rounded up to 5 m. Coordinates source: data/layout.json (139 tagged items).
- 13.8 kV incomer route from the refinery main substation assumed 600 m (OSBL, to be confirmed by refinery electrical master plan).

**Worked example CBL-P-101A:** Crude charge pump A; design FLC 115 A; route 100 m (layout); required ampacity 143 A; selected 3C x 70 mm2 Cu/XLPE/CWS/SWA/PVC 3.6/6 kV; derated ampacity 186 A; VD running 0.17 %; VD starting (cable) 0.5 %; bus dip 5.3 % -> terminal 5.9 %; SC minimum 56 mm2.

**Worked example CBL-P-104A:** Unstabilised naphtha pump A; design FLC 233 A; route 140 m (layout); required ampacity 291 A; selected 3C x 185 + E95 mm2 Cu/XLPE/SWA/PVC 0.6/1 kV; derated ampacity 332 A; VD running 1.75 %; VD starting (cable) 9.0 %; bus dip 3.5 % -> terminal 12.5 %; SC minimum 17 mm2.

| Summary | Value |
|---|---|
| Number of cables | 117 |
| Total route length (m) | 16,975 |
| Max running VD % | 4.94 |
| Max terminal dip at start % | 15.0 |

## 9. UPS and battery sizing

| Step | Value |
|---|---|
| UPS consumers (DCS 22, SIS/BMS 14, F&G 6, telecom 8, analysers 6, misc. 4 kVA) | 60 kVA |
| Design load incl. 20 % future | 72 kVA |
| Rating (design load <= 80 % of rating) | 100 kVA each, 2 x 100 % dual-bus (UPS-101A -> UDB-101A, UPS-101B -> UDB-101B), each with own battery, static bypass and external maintenance bypass |
| Battery power = 72 kVA x 0.9 / 0.94 | 68.9 kW |
| Cells / nominal / float / end voltage | 192 x 2 V / 384 / 432 / 336 V (1.75 V/cell) |
| Max discharge current at end voltage | 205 A |
| Kt for 30 min to 1.75 V/cell (VRLA, 25 C) | 1.1 Ah/A |
| Capacity = I x Kt x aging 1.25 x design margin 1.10 x temperature 1.00 | 310 Ah |
| Selected battery (per UPS) | 350 Ah, 30 min |

UPS input (rectifier) load on each MCC section includes 50 % share of the consumers plus 5 kW battery recharge. 125 V DC switchgear control supply (IEEE 485 duty cycle):

| Section | Value |
|---|---|
| Duty cycle | L1 60 A 1 min (trip) / L2 15 A 120 min standing / L3 40 A 1 min (close) |
| Section 1 / 2 / 3 capacity (Ah) | 33.0 / 35.7 / 49.6 |
| Required = max x aging 1.25 x margin 1.10 | 68 Ah -> 75 Ah, 60 cells VRLA |
| Chargers | 2 x 100 %, 30 A each (standing load + recharge in 8 h) |

## 10. Emergency diesel generator - basis for omission

No emergency generator is provided. The unit is supplied by two independent 13.8 kV feeders, each able to carry the whole unit load, from the refinery main substation. On a total power failure the unit is designed to fail safe: the SIS is de-energise-to-trip, emergency isolation valves fail closed, the fired-heater BMS trips H-101/H-201 and snuffing steam is manual; there is no rotating equipment requiring post-trip power (no lube/seal-oil consoles - API 682 seals, ring-oil or rolling-bearing pumps; vacuum by steam ejectors). The essential loads (DCS, SIS/BMS, F&G, PAGA/telecom) are on the 2 x 100 % UPS with 30 min autonomy, which covers safe shutdown and operator response; escape lighting uses self-contained 90-min fittings. If the HAZOP identifies an essential motor load (e.g. an emergency cooling or flushing pump), it will be supplied from the refinery emergency power network rather than a dedicated unit generator.

## 11. Assumptions, holds and issues

- HOLD: utility X/R (15) and minimum fault level at 13.8 kV to be confirmed by the refinery power study; motor-start case 3 assumes 20 kA minimum.
- HOLD: 13.8 kV feeder route length from the refinery main substation assumed 600 m.
- The 480 V double-ended substation needs 3,000/3,750 kVA transformers and a 5000 A bus (52 kA calculated, 65 kA rated). This is at the practical limit for 480 V; recommended at detailed design to split LV into two double-ended substations (e.g. CDU / VDU+air coolers) of ~2000 kVA each, or to move the 160 kW pumps to 4.16 kV. Kept as one board here per the FEED key SLD.
- Long 480 V motor feeders: SS-100 is in the SW corner while the VDU pumps are ~170 m east, so the 15 % terminal-dip criterion governs (e.g. P-201B 150 mm2 at 260 m, P-107B 240 mm2 at 195 m, P-107A 240 mm2 at 195 m, P-201A 150 mm2 at 255 m). Moving the >= 110 kW LV pumps to 4.16 kV, or a satellite LV substation near the VDU, would reduce copper; to be reviewed with the plot plan.
- Allowance loads (lighting, HVAC, heat tracing, MOVs, welding, UPS, CP, analyser house) are FEED estimates and must be replaced by vendor / discipline data.
- Desalter transformer load factor (0.35) assumed; desalter vendor to confirm grid power.
- Cable lengths use equipment coordinates from data/layout.json (139 tagged items) with Manhattan routing from SS-100 plus allowances; actual tray/trench routes to be confirmed at detailed design (lengths regenerate automatically when the layout changes).
- Hazardous-area classification: CFU-000-EL-HAC-001/002/003 (Section 12); motor Ex protection per location in data/electrical.json (loads[].area_class).

## 12. Hazardous area classification and equipment protection

Classification CFU-000-EL-HAC-001/002 (schedule HAC-003) per API RP 505 / NFPA 70 Art. 505, point-source method, fluid categories per EI 15. Gas group IIA T3 generally, IIB in H2S / fuel-gas / off-gas services. 146 release sources: Atmospheric vent 1, Control-valve station 32, Ejector / condenser flanges 1, Exchanger flanges 25, Header box plugs / flanges 12, Pump seal 42, Sample point 14, Vessel flanges / instruments 19.

| Unclassified item | Clearance to nearest classified area (m) | Nearest source |
|---|---|---|
| H-101 | 10.3 | RS-132 Control valves FV-1011, FV-1012, FV-1013, FV-1014, |
| H-201 | 13.2 | RS-126 Control valves LV-9002 (D-103) |
| E-120 | 34.1 | RS-132 Control valves FV-1011, FV-1012, FV-1013, FV-1014, |
| SS-100 | 17.1 | RS-076 D-101B Electrostatic desalter, 2nd stage |
| FAR-100 | 20.1 | RS-076 D-101B Electrostatic desalter, 2nd stage |

| Equipment | Zone 1 | Zone 2 |
|---|---|---|
| LV motors (480 V) | Ex db or Ex eb (tE, stall relay), IIB T3 (Gb) | Ex ec (non-sparking), IIA/IIB T3 (Gc); AEx ec per NEC 505 |
| MV motors (4.16 kV) | Not located in Zone 1 (relocate) / Ex pxb | Ex ec with stator discharge risk assessment / pre-start purge, IIA T3 |
| VFD-fed motors | Ex db certified with the drive (converter duty) | Ex ec certified for converter duty; T-class verified with VFD |
| Instruments | Ex ia / ib (intrinsic safety), Ex db | Ex ia / ic, Ex db, Ex ec |
| Lighting fittings | Ex db / eb, IIB T3 | Ex ec / nR, IIA T3 (IIB in H2S areas) |
| Junction boxes / glands | Ex eb boxes; Ex db barrier glands for Ex d | Ex eb / ec boxes and glands |
| Heat tracing | Ex 60079-30-1, stabilised design <= T3 | Ex 60079-30-1, self-regulating, T3 |
| Desalter transformers | n/a (Zone 2 only) | Vendor package certified for Zone 2 (Ex o / ec), HV entry to vessel via Ex bushings |
| Welding / receptacles | Not permitted | Ex de interlocked receptacles; hot-work permit |
| Buildings SS-100 / FAR-100 | - | Non-classified; pressurised (NFPA 496 / IEC 60079-13), intakes in unclassified area, gas detection |
