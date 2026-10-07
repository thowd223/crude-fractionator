# 1 Purpose
This document maps the engineering activities of the CDU/VDU design: the order they run in, what each one needs
from upstream, and what it affects downstream. Use it to plan the remaining work and to judge the impact of a
change. It covers the 45 activities that produce this package and the activities still needed
before the design can be used for construction.

How to read it:
- An activity's **needs** are the activities whose results it uses. It can start when they have issued.
- A **wave** is a step in the sequence: wave 1 needs nothing, wave 2 needs only wave 1 results, and so on.
  Activities in the same wave can run in parallel.
- An **iteration loop** is a later result that revises an earlier activity (for example, vendor data revising
  the mechanical calculations). Loops are why FEED takes more than one pass.
- **Downstream** means every activity reachable through the needs links. If an activity changes, all its
  downstream activities must be re-checked.

The network drawing is CFU-000-PM-DEP-002. The workbook has the full sequence, link list, design structure
matrix (DSM), change-impact table, to-do list and code check. An interactive version is in the portal
(dependencies.html).

# 2 Summary
| Item | Value |
|---|---|
| Activities | 45 (29 issued, 4 issued but provisional, 12 not started) |
| Sequence waves | 13 |
| Input links | 129 |
| Iteration loops | 15 |
| Deliverables mapped to activities | 104 |
| Data reads traced in the build | 62 (62 upstream) |
| Code-check issues | 0 |

# 3 Design sequence
| Wave | ID | Activity | Discipline | Status | Needs |
|---|---|---|---|---|---|
| 1 | PRJ-01 | Design basis (BOD) | Project | Issued (FEED) | - |
| 2 | PRJ-02 | Crude assay characterisation | Process | Issued, provisional | PRJ-01 |
| 3 | PRC-00 | Rigorous simulation and model calibration | Process | Not started | PRJ-02 |
| 4 | PRC-01 | Heat and material balance | Process | Issued, provisional | PRJ-01, PRJ-02, PRC-00 |
| 5 | PRC-02 | Process equipment sizing | Process | Issued (FEED) | PRC-01 |
| 5 | PRC-05 | Block flow diagram | Process | Issued (FEED) | PRC-01 |
| 5 | PIP-01 | Piping material classes | Piping | Issued (FEED) | PRJ-01, PRC-01 |
| 6 | PRC-03 | Relief load and PSV sizing (unit) | Process | Issued (FEED) | PRC-01, PRC-02 |
| 6 | PRC-04 | Control loops and SIF definition | Process | Issued (FEED) | PRC-01, PRC-02 |
| 6 | LAY-01 | Plot plan and equipment layout | Layout | Issued (FEED) | PRC-02, PRC-01, PRJ-01 |
| 6 | ELE-01 | Electrical load list | Electrical | Issued (FEED) | PRC-02 |
| 7 | PRC-06 | Process flow diagrams | Process | Issued (FEED) | PRC-01, PRC-02, PRC-04 |
| 7 | PRC-07 | Process design report | Process | Issued (FEED) | PRC-01, PRC-02, PRC-03 |
| 7 | SAF-02 | Global flare load study | Safety | Not started | PRC-03 |
| 7 | MEC-01 | Mechanical design calculations | Mechanical | Issued (FEED) | PRC-02, PRC-01, PRC-03 |
| 7 | LAY-02 | Sections and 3D layout model | Layout | Issued (FEED) | LAY-01, PRC-02 |
| 7 | ICS-01 | Control philosophy and schemes | I&C | Issued (FEED) | PRC-04, PRC-01, PRC-02 |
| 7 | ELE-02 | Hazardous area classification | Electrical | Issued (FEED) | LAY-01, PRC-02, PRC-04 |
| 7 | ELE-03 | Electrical sizing, single-line diagrams | Electrical | Issued (FEED) | ELE-01 |
| 8 | PRC-08 | P&IDs, line list, instrument index | Process | Issued (FEED) | PRC-02, PRC-03, PRC-04, PRC-06, PIP-01, LAY-01 |
| 8 | MEC-02 | Equipment datasheets | Mechanical | Issued (FEED) | MEC-01, PRC-02, PRC-03 |
| 8 | MEC-03 | Equipment GA drawings | Mechanical | Issued (FEED) | MEC-01 |
| 8 | ELE-04 | Cable schedule | Electrical | Issued (FEED) | ELE-01, ELE-03, LAY-01, ELE-02 |
| 8 | CST-01 | Class 4 cost estimate | Cost | Issued (FEED) | PRC-02, MEC-01 |
| 9 | SAF-01 | Preliminary HAZOP | Safety | Issued (FEED) | PRC-08, PRC-04, PRC-03 |
| 9 | VEN-01 | Vendor enquiries and vendor data | Mechanical | Not started | MEC-02 |
| 9 | PIP-02 | Piping routing and 3D model | Piping | Issued (FEED) | PRC-08, LAY-01, PRC-03, MEC-01 |
| 9 | ICS-04 | Control valve sizing | I&C | Issued (FEED) | PRC-01, PRC-02, PRC-04, PRC-08 |
| 9 | ICS-05 | I/O list | I&C | Issued (FEED) | PRC-08, PRC-04, PRC-02, LAY-01 |
| 10 | SAF-04 | Siting study, QRA, F&G mapping | Safety | Not started | LAY-01, SAF-01, ELE-02 |
| 10 | PIP-03 | Pipe stress and supports (screening) | Piping | Issued, provisional | PIP-02, MEC-01 |
| 10 | PIP-04 | Isometrics and piping MTO | Piping | Issued (FEED) | PIP-02, PIP-01 |
| 10 | ICS-02 | SIF list and SIL determination (LOPA) | I&C | Issued, provisional | PRC-04, SAF-01 |
| 10 | ICS-06 | Loop diagrams | I&C | Issued (FEED) | ICS-05 |
| 10 | ICS-07 | ICS architecture | I&C | Issued (FEED) | ICS-05, ELE-03 |
| 10 | ELE-05 | Power system studies and protection | Electrical | Not started | ELE-03, VEN-01 |
| 11 | SAF-03 | Formal HAZOP and LOPA workshop | Safety | Not started | PRC-08, SAF-01, ICS-02 |
| 11 | PIP-05 | Detailed pipe stress (CAESAR II) | Piping | Not started | PIP-03, VEN-01 |
| 11 | CIV-01 | Geotechnical, civil and structural design | Civil | Not started | LAY-01, MEC-01, PIP-03 |
| 11 | ICS-03 | Cause and effect matrix | I&C | Issued (FEED) | PRC-04, PRC-03, PRC-02, ICS-02 |
| 12 | PRJ-03 | Document register and portal | Project | Issued (FEED) | CST-01, SAF-01, PIP-04, ICS-06, ICS-07, ELE-04, MEC-03, LAY-02, PRC-05, PRC-07, ICS-01, ICS-03, ICS-04, MEC-02, PIP-03 |
| 12 | LAY-03 | 3D model reviews and constructability | Layout | Not started | PIP-02, LAY-02, CIV-01 |
| 12 | ICS-08 | SIL verification and SRS | I&C | Not started | ICS-02, SAF-03, VEN-01 |
| 12 | CST-02 | Class 3 cost estimate | Cost | Not started | CST-01, VEN-01, PIP-04, ELE-04, CIV-01 |
| 13 | PRJ-04 | PE review, seal and IFC issue | Project | Not started | PRJ-03, SAF-03, ICS-08, PIP-05, ELE-05, CST-02, LAY-03, SAF-04, SAF-02 |

# 4 Inputs and impacts by activity
For each activity: what it needs (and what flows across each link), what it needs from outside the design team,
and what it feeds. Downstream counts are the activities and deliverables to re-check if it changes.

**PRJ-01 Design basis (BOD)** (Project, issued (feed))

- External inputs: Owner capacity, crude slate, product specs, turndown; Site, climate and utility conditions; Codes, standards and owner specifications
- Issues: CFU-000-PR-BOD-001
- Feeds: PRJ-02, PRC-01, PIP-01, LAY-01; 44 downstream activities, 103 downstream deliverables
- Note: Every other activity reads the basis; a change here re-opens the whole package.

**PRJ-02 Crude assay characterisation** (Process, issued, provisional)

- Needs: PRJ-01 (crude slate, design and check crudes)
- External inputs: Full laboratory assay (TBP, gravity, sulphur, salts, metals, acidity)
- Feeds: PRC-00, PRC-01; 43 downstream activities, 103 downstream deliverables
- Note: Uses a published Arab Light assay with pseudo-components, not a lab assay.

**PRC-00 Rigorous simulation and model calibration** (Process, not started)

- Needs: PRJ-02 (lab assay pseudo-components)
- External inputs: Simulator licence (HYSYS / Petro-SIM / Pro-II); Licensor or owner operating data
- Feeds: PRC-01; 42 downstream activities, 103 downstream deliverables
- Note: Replaces the ideal-VLE shortcut model; expect 5-10 C changes in draw temperatures.

**PRC-01 Heat and material balance** (Process, issued, provisional)

- Needs: PRJ-01 (capacity, product specs, utility conditions); PRJ-02 (pseudo-components); PRC-00 (calibrated cut points and efficiencies)
- Owns data: data/streams.json, data/process_results.json
- Issues: CFU-000-PR-HMB-001
- Feeds: PRC-02, PRC-05, PIP-01, PRC-03, PRC-04, LAY-01, PRC-06, PRC-07, MEC-01, ICS-01, ICS-04; 41 downstream activities, 102 downstream deliverables

**PRC-02 Process equipment sizing** (Process, issued (feed))

- Needs: PRC-01 (flows, duties, column vapour/liquid loads)
- Owns data: data/equipment.json
- Issues: CFU-000-ME-LST-001
- Feeds: PRC-03, PRC-04, LAY-01, ELE-01, PRC-06, PRC-07, MEC-01, LAY-02, ICS-01, ELE-02, PRC-08, MEC-02, CST-01, ICS-04, ICS-05, ICS-03; 38 downstream activities, 99 downstream deliverables
- Revised by: MEC-01 (mechanical holds re-rate sizing (C-201 bed-1 diameter, heater box length)); PIP-02 (routed lengths update pump and line hydraulics)
- Note: Equipment list is the hub: mechanical, layout, electrical, I&C and cost all read it.

**PRC-05 Block flow diagram** (Process, issued (feed))

- Needs: PRC-01 (unit yields)
- Issues: CFU-000-PR-BFD-001
- Feeds: PRJ-03; 2 downstream activities, 3 downstream deliverables

**PIP-01 Piping material classes** (Piping, issued (feed))

- Needs: PRJ-01 (codes, corrosion basis); PRC-01 (design T/P, sulphur and acid corrosion)
- Issues: CFU-000-PI-SPC-001
- Feeds: PRC-08, PIP-04; 20 downstream activities, 50 downstream deliverables
- Note: Defined in CONVENTIONS.md; summary issued with the P&IDs.

**PRC-03 Relief load and PSV sizing (unit)** (Process, issued (feed))

- Needs: PRC-01 (relief compositions and rates); PRC-02 (design pressures, wetted areas)
- Owns data: data/psv.json
- Feeds: PRC-07, SAF-02, MEC-01, PRC-08, MEC-02, SAF-01, PIP-02, ICS-03; 28 downstream activities, 69 downstream deliverables
- Revised by: SAF-02 (flare back-pressure changes PSV type and size)

**PRC-04 Control loops and SIF definition** (Process, issued (feed))

- Needs: PRC-01 (operating points); PRC-02 (equipment and instrument ranges)
- Owns data: data/control_loops.json
- Feeds: PRC-06, ICS-01, ELE-02, PRC-08, SAF-01, ICS-04, ICS-05, ICS-02, ICS-03; 24 downstream activities, 69 downstream deliverables

**LAY-01 Plot plan and equipment layout** (Layout, issued (feed))

- Needs: PRC-02 (equipment list and footprints); PRC-01 (hazard inventory, heater duties); PRJ-01 (site, spacing standards)
- Owns data: data/layout.json
- Issues: CFU-000-PL-PLT-001
- Feeds: LAY-02, ELE-02, PRC-08, ELE-04, PIP-02, ICS-05, SAF-04, CIV-01; 23 downstream activities, 58 downstream deliverables
- Revised by: MEC-01 (calculated dimensions and weights update footprints and spacing); PIP-02 (rack width and clashes move equipment); SAF-04 (siting study moves occupied buildings and equipment); VEN-01 (vendor package footprints)

**ELE-01 Electrical load list** (Electrical, issued (feed))

- Needs: PRC-02 (motor ratings, absorbed power)
- Issues: CFU-000-EL-LDL-001
- Feeds: ELE-03, ELE-04; 7 downstream activities, 10 downstream deliverables
- Revised by: ICS-07 (ICS cabinet and UPS loads added to the load list); VEN-01 (certified motor ratings)

**PRC-06 Process flow diagrams** (Process, issued (feed))

- Needs: PRC-01 (stream table); PRC-02 (equipment data); PRC-04 (principal control loops)
- Issues: CFU-000-PR-PFD-ALL, CFU-100-PR-PFD-001, CFU-100-PR-PFD-002, CFU-100-PR-PFD-003, CFU-100-PR-PFD-004, CFU-200-PR-PFD-005, CFU-200-PR-PFD-006
- Feeds: PRC-08; 20 downstream activities, 50 downstream deliverables

**PRC-07 Process design report** (Process, issued (feed))

- Needs: PRC-01 (H&MB); PRC-02 (sizing results); PRC-03 (relief summary)
- Issues: CFU-000-PR-RPT-001
- Feeds: PRJ-03; 2 downstream activities, 3 downstream deliverables

**SAF-02 Global flare load study** (Safety, not started)

- Needs: PRC-03 (unit relief loads)
- External inputs: Refinery flare network model, other units' loads
- Feeds: PRJ-04; 1 downstream activities, 0 downstream deliverables
- Note: Governing case (C-101 reflux failure, about 220 t/h) needs power and cooling-water failure cases.

**MEC-01 Mechanical design calculations** (Mechanical, issued (feed))

- Needs: PRC-02 (design P/T, dimensions, internals); PRC-01 (nozzle flows); PRC-03 (PSV set points)
- Owns data: data/mech.json
- Issues: CFU-000-ME-CAL-001
- Feeds: MEC-02, MEC-03, CST-01, PIP-02, PIP-03, CIV-01; 15 downstream activities, 37 downstream deliverables
- Revised by: VEN-01 (certified vendor dimensions, weights and nozzles)

**LAY-02 Sections and 3D layout model** (Layout, issued (feed))

- Needs: LAY-01 (equipment positions, structures); PRC-02 (equipment heights)
- Issues: CFU-000-PL-3DM-001, CFU-000-PL-ELV-001, CFU-000-PL-ELV-002, CFU-000-PL-ELV-003
- Feeds: PRJ-03, LAY-03; 3 downstream activities, 3 downstream deliverables

**ICS-01 Control philosophy and schemes** (I&C, issued (feed))

- Needs: PRC-04 (loops and SIFs); PRC-01 (operating points); PRC-02 (equipment)
- Issues: CFU-000-IC-CSD-006, CFU-000-IC-CSD-ALL, CFU-000-IC-RPT-001, CFU-100-IC-CSD-001, CFU-100-IC-CSD-002, CFU-100-IC-CSD-003, CFU-100-IC-CSD-004, CFU-200-IC-CSD-005
- Feeds: PRJ-03; 2 downstream activities, 3 downstream deliverables

**ELE-02 Hazardous area classification** (Electrical, issued (feed))

- Needs: LAY-01 (release-source positions); PRC-02 (fluids and conditions); PRC-04 (analysers and vents)
- Issues: CFU-000-EL-HAC-001, CFU-000-EL-HAC-002, CFU-000-EL-HAC-003
- Feeds: ELE-04, SAF-04; 5 downstream activities, 4 downstream deliverables

**ELE-03 Electrical sizing, single-line diagrams** (Electrical, issued (feed))

- Needs: ELE-01 (loads and demand)
- Owns data: data/electrical.json
- Issues: CFU-000-EL-CAL-001, CFU-000-EL-SLD-001, CFU-000-EL-SLD-002, CFU-000-EL-SLD-003, CFU-000-EL-SLD-004
- Feeds: ELE-04, ICS-07, ELE-05; 6 downstream activities, 5 downstream deliverables
- Revised by: ELE-04 (actual cable impedances re-run the motor-starting voltage-dip check)

**PRC-08 P&IDs, line list, instrument index** (Process, issued (feed))

- Needs: PRC-02 (equipment and design conditions); PRC-03 (PSV tags and sizes); PRC-04 (control loops and SIFs); PRC-06 (PFD topology); PIP-01 (piping classes); LAY-01 (fire and gas detector locations)
- Owns data: data/lines.json, data/instruments.json
- Issues: CFU-000-IC-IDX-001, CFU-000-PI-LL-001, CFU-000-PR-PID-000, CFU-000-PR-PID-ALL, CFU-100-PR-PID-001, CFU-100-PR-PID-002, CFU-100-PR-PID-003, CFU-100-PR-PID-004, CFU-100-PR-PID-005, CFU-100-PR-PID-006, CFU-100-PR-PID-007, CFU-100-PR-PID-008, CFU-100-PR-PID-009, CFU-100-PR-PID-010, CFU-100-PR-PID-011, CFU-200-PR-PID-012, CFU-200-PR-PID-013, CFU-200-PR-PID-014, CFU-200-PR-PID-015, CFU-900-PR-PID-016
- Feeds: SAF-01, PIP-02, ICS-04, ICS-05, SAF-03; 19 downstream activities, 30 downstream deliverables
- Revised by: ICS-04 (control valve sizes and reducers shown on the P&IDs); SAF-01 (HAZOP recommendations revise the P&IDs); SAF-03 (formal HAZOP actions revise the P&IDs)
- Note: Line list and instrument index feed piping, I&C and electrical; P&ID revisions ripple widely.

**MEC-02 Equipment datasheets** (Mechanical, issued (feed))

- Needs: MEC-01 (thicknesses, weights, nozzles); PRC-02 (process data); PRC-03 (PSV data)
- Issues: CFU-000-ME-DS-000, CFU-000-ME-DS-001, CFU-000-ME-DS-002, CFU-000-ME-DS-003, CFU-000-ME-DS-004, CFU-000-ME-DS-005, CFU-000-ME-DS-006, CFU-000-ME-DS-007
- Feeds: VEN-01, PRJ-03; 7 downstream activities, 3 downstream deliverables

**MEC-03 Equipment GA drawings** (Mechanical, issued (feed))

- Needs: MEC-01 (geometry, nozzle schedule)
- Issues: CFU-100-ME-GA-001, CFU-100-ME-GA-002, CFU-100-ME-GA-003, CFU-100-ME-GA-005, CFU-100-ME-GA-007, CFU-100-ME-GA-008, CFU-200-ME-GA-004, CFU-200-ME-GA-006
- Feeds: PRJ-03; 2 downstream activities, 3 downstream deliverables

**ELE-04 Cable schedule** (Electrical, issued (feed))

- Needs: ELE-01 (loads); ELE-03 (feeders); LAY-01 (routes); ELE-02 (zone ratings)
- Issues: CFU-000-EL-CBL-001
- Feeds: PRJ-03, CST-02; 3 downstream activities, 3 downstream deliverables

**CST-01 Class 4 cost estimate** (Cost, issued (feed))

- Needs: PRC-02 (equipment list); MEC-01 (shell weights)
- Issues: CFU-000-PM-EST-001
- Feeds: PRJ-03, CST-02; 3 downstream activities, 3 downstream deliverables

**SAF-01 Preliminary HAZOP** (Safety, issued (feed))

- Needs: PRC-08 (P&IDs); PRC-04 (SIFs); PRC-03 (relief devices)
- Issues: CFU-000-PR-RPT-002
- Feeds: SAF-04, ICS-02, SAF-03, PRJ-03; 7 downstream activities, 5 downstream deliverables

**VEN-01 Vendor enquiries and vendor data** (Mechanical, not started)

- Needs: MEC-02 (datasheets for enquiry)
- External inputs: Vendor quotations and certified data (heaters, desalters, packing, pumps, ejectors, air coolers)
- Feeds: ELE-05, PIP-05, ICS-08, CST-02; 5 downstream activities, 0 downstream deliverables
- Note: Vendor data revises weights, nozzles, motor ratings and I/O; plan for one full update cycle.

**PIP-02 Piping routing and 3D model** (Piping, issued (feed))

- Needs: PRC-08 (line list, in-line instruments); LAY-01 (nozzle positions, pipe rack); PRC-03 (PSV inlet/outlet); MEC-01 (nozzle sizes, weights)
- Owns data: data/routing.json
- Issues: CFU-000-PI-3DM-002
- Feeds: PIP-03, PIP-04, LAY-03; 8 downstream activities, 19 downstream deliverables

**ICS-04 Control valve sizing** (I&C, issued (feed))

- Needs: PRC-01 (flows, densities); PRC-02 (pump curves); PRC-04 (valve tags); PRC-08 (line sizes)
- Issues: CFU-000-IC-CAL-001
- Feeds: PRJ-03; 2 downstream activities, 3 downstream deliverables

**ICS-05 I/O list** (I&C, issued (feed))

- Needs: PRC-08 (instrument index); PRC-04 (loops and SIFs); PRC-02 (motor drivers); LAY-01 (junction-box zones)
- Owns data: data/io_list.json
- Issues: CFU-000-IC-IOL-001
- Feeds: ICS-06, ICS-07; 4 downstream activities, 8 downstream deliverables
- Revised by: VEN-01 (vendor package I/O)

**SAF-04 Siting study, QRA, F&G mapping** (Safety, not started)

- Needs: LAY-01 (plot plan); SAF-01 (major hazards); ELE-02 (release sources)
- External inputs: Occupied building list, meteorology
- Feeds: PRJ-04; 1 downstream activities, 0 downstream deliverables
- Note: API 752/753 siting, QRA, fire and gas mapping and fireproofing; may move buildings or equipment.

**PIP-03 Pipe stress and supports (screening)** (Piping, issued, provisional)

- Needs: PIP-02 (routed geometry); MEC-01 (nozzle allowables)
- Issues: CFU-000-PI-RPT-001
- Feeds: PIP-05, CIV-01, PRJ-03; 6 downstream activities, 3 downstream deliverables
- Note: Screening only; CAESAR II analysis is PIP-05.

**PIP-04 Isometrics and piping MTO** (Piping, issued (feed))

- Needs: PIP-02 (routed geometry); PIP-01 (piping classes)
- Issues: CFU-000-PI-ISO-000, CFU-000-PI-MTO-001, CFU-100-PI-ISO-001, CFU-100-PI-ISO-002, CFU-100-PI-ISO-003, CFU-100-PI-ISO-004, CFU-100-PI-ISO-005, CFU-100-PI-ISO-006, CFU-100-PI-ISO-007, CFU-100-PI-ISO-008, CFU-100-PI-ISO-009, CFU-100-PI-ISO-010, CFU-100-PI-ISO-011, CFU-100-PI-ISO-012, CFU-200-PI-ISO-001
- Feeds: PRJ-03, CST-02; 3 downstream activities, 3 downstream deliverables

**ICS-02 SIF list and SIL determination (LOPA)** (I&C, issued, provisional)

- Needs: PRC-04 (SIF definitions); SAF-01 (hazard scenarios)
- Issues: CFU-000-IC-RPT-002
- Feeds: SAF-03, ICS-03, ICS-08; 5 downstream activities, 4 downstream deliverables
- Note: LOPA frequencies are FEED judgements pending SAF-03.

**ICS-06 Loop diagrams** (I&C, issued (feed))

- Needs: ICS-05 (terminations, cabinets)
- Issues: CFU-100-IC-LD-001, CFU-100-IC-LD-002, CFU-100-IC-LD-003, CFU-100-IC-LD-ALL
- Feeds: PRJ-03; 2 downstream activities, 3 downstream deliverables

**ICS-07 ICS architecture** (I&C, issued (feed))

- Needs: ICS-05 (I/O counts); ELE-03 (UPS feeds)
- Issues: CFU-000-IC-BLK-001
- Feeds: PRJ-03; 2 downstream activities, 3 downstream deliverables

**ELE-05 Power system studies and protection** (Electrical, not started)

- Needs: ELE-03 (SLD); VEN-01 (motor and transformer data)
- External inputs: Utility short-circuit data; ETAP or equivalent
- Feeds: PRJ-04; 1 downstream activities, 0 downstream deliverables
- Note: Load flow, short circuit, motor starting, arc flash, relay coordination.

**SAF-03 Formal HAZOP and LOPA workshop** (Safety, not started)

- Needs: PRC-08 (IFD P&IDs); SAF-01 (preliminary findings); ICS-02 (draft SIL targets)
- External inputs: Multidisciplinary team incl. owner operations
- Feeds: ICS-08, PRJ-04; 2 downstream activities, 0 downstream deliverables

**PIP-05 Detailed pipe stress (CAESAR II)** (Piping, not started)

- Needs: PIP-03 (critical line list); VEN-01 (certified nozzle allowables)
- External inputs: CAESAR II or equivalent
- Feeds: PRJ-04; 1 downstream activities, 0 downstream deliverables
- Note: Includes nozzle-load agreement with equipment vendors.

**CIV-01 Geotechnical, civil and structural design** (Civil, not started)

- Needs: LAY-01 (plot plan); MEC-01 (operating and test weights); PIP-03 (support loads)
- External inputs: Geotechnical survey; Topographic survey
- Feeds: LAY-03, CST-02; 3 downstream activities, 0 downstream deliverables
- Note: No civil deliverables in this package: foundations, pipe rack and structures are still to do.

**ICS-03 Cause and effect matrix** (I&C, issued (feed))

- Needs: PRC-04 (SIFs); PRC-03 (relief devices); PRC-02 (equipment); ICS-02 (SIL targets)
- Issues: CFU-000-IC-CE-001
- Feeds: PRJ-03; 2 downstream activities, 3 downstream deliverables

**PRJ-03 Document register and portal** (Project, issued (feed))

- Needs: CST-01 (estimate); SAF-01 (HAZOP); PIP-04 (isometrics); ICS-06 (loop diagrams); ICS-07 (architecture); ELE-04 (cables); MEC-03 (GAs); LAY-02 (3D model); PRC-05 (BFD); PRC-07 (process report); ICS-01 (control philosophy); ICS-03 (C&E); ICS-04 (CV sizing); MEC-02 (datasheets); PIP-03 (stress study)
- Issues: CFU-000-PM-DEP-001, CFU-000-PM-DEP-002, CFU-000-PM-REG-001
- Feeds: PRJ-04; 1 downstream activities, 0 downstream deliverables

**LAY-03 3D model reviews and constructability** (Layout, not started)

- Needs: PIP-02 (routed model); LAY-02 (layout model); CIV-01 (structures)
- External inputs: Owner operations and maintenance reviewers
- Feeds: PRJ-04; 1 downstream activities, 0 downstream deliverables
- Note: 30/60/90 % model reviews.

**ICS-08 SIL verification and SRS** (I&C, not started)

- Needs: ICS-02 (SIL targets); SAF-03 (validated LOPA); VEN-01 (device failure data)
- Feeds: PRJ-04; 1 downstream activities, 0 downstream deliverables
- Note: PFDavg calculations and the safety requirements specification (IEC 61511).

**CST-02 Class 3 cost estimate** (Cost, not started)

- Needs: CST-01 (estimate structure); VEN-01 (budget quotes); PIP-04 (piping MTO); ELE-04 (cable quantities); CIV-01 (civil quantities)
- Feeds: PRJ-04; 1 downstream activities, 0 downstream deliverables

**PRJ-04 PE review, seal and IFC issue** (Project, not started)

- Needs: PRJ-03 (complete document set); SAF-03 (closed HAZOP actions); ICS-08 (SIL verification); PIP-05 (stress sign-off); ELE-05 (studies); CST-02 (Class 3 estimate); LAY-03 (model review); SAF-04 (siting study); SAF-02 (flare study)
- External inputs: Licensed Professional Engineer in responsible charge
- Feeds: nothing (end of chain); 0 downstream activities, 0 downstream deliverables
- Note: Nothing in this package is sealed; this is the gate before any use for construction.

# 5 Iteration loops
| From | Revises | What changes |
|---|---|---|
| MEC-01 | PRC-02 | mechanical holds re-rate sizing (C-201 bed-1 diameter, heater box length) |
| MEC-01 | LAY-01 | calculated dimensions and weights update footprints and spacing |
| PIP-02 | PRC-02 | routed lengths update pump and line hydraulics |
| PIP-02 | LAY-01 | rack width and clashes move equipment |
| ICS-04 | PRC-08 | control valve sizes and reducers shown on the P&IDs |
| SAF-01 | PRC-08 | HAZOP recommendations revise the P&IDs |
| ELE-04 | ELE-03 | actual cable impedances re-run the motor-starting voltage-dip check |
| ICS-07 | ELE-01 | ICS cabinet and UPS loads added to the load list |
| SAF-02 | PRC-03 | flare back-pressure changes PSV type and size |
| SAF-03 | PRC-08 | formal HAZOP actions revise the P&IDs |
| SAF-04 | LAY-01 | siting study moves occupied buildings and equipment |
| VEN-01 | MEC-01 | certified vendor dimensions, weights and nozzles |
| VEN-01 | LAY-01 | vendor package footprints |
| VEN-01 | ELE-01 | certified motor ratings |
| VEN-01 | ICS-05 | vendor package I/O |

Plan each loop as a formal update: issue the upstream activity, collect the later results, then re-issue.
The vendor-data loop (VEN-01) and the HAZOP loops (SAF-01, SAF-03) usually set the FEED schedule.

# 6 Change impact
The activities whose change reaches the most deliverables. Freeze these first.

| ID | Activity | Downstream activities | Downstream deliverables |
|---|---|---|---|
| PRC-00 | Rigorous simulation and model calibration | 42 | 103 |
| PRJ-01 | Design basis (BOD) | 44 | 103 |
| PRJ-02 | Crude assay characterisation | 43 | 103 |
| PRC-01 | Heat and material balance | 41 | 102 |
| PRC-02 | Process equipment sizing | 38 | 99 |
| PRC-03 | Relief load and PSV sizing (unit) | 28 | 69 |
| PRC-04 | Control loops and SIF definition | 24 | 69 |
| LAY-01 | Plot plan and equipment layout | 23 | 58 |
| PIP-01 | Piping material classes | 20 | 50 |
| PRC-06 | Process flow diagrams | 20 | 50 |
| MEC-01 | Mechanical design calculations | 15 | 37 |
| PRC-08 | P&IDs, line list, instrument index | 19 | 30 |
| PIP-02 | Piping routing and 3D model | 8 | 19 |
| ELE-01 | Electrical load list | 7 | 10 |

# 7 What still needs to be done
In sequence order. "Ready" means nothing it needs is still not started. "Re-opens" lists the issued activities
that must be re-checked when it completes.

| Order | ID | Activity | Status | Ready | Re-opens |
|---|---|---|---|---|---|
| 1 | PRJ-02 | Crude assay characterisation | Issued, provisional | yes | 31 issued activities |
| 2 | PRC-00 | Rigorous simulation and model calibration | Not started | yes | 31 issued activities |
| 3 | PRC-01 | Heat and material balance | Issued, provisional | after PRC-00 | 30 issued activities |
| 4 | SAF-02 | Global flare load study | Not started | yes | 0 issued activities |
| 5 | VEN-01 | Vendor enquiries and vendor data | Not started | yes | 0 issued activities |
| 6 | SAF-04 | Siting study, QRA, F&G mapping | Not started | yes | 0 issued activities |
| 7 | PIP-03 | Pipe stress and supports (screening) | Issued, provisional | yes | 1 issued activities |
| 8 | ICS-02 | SIF list and SIL determination (LOPA) | Issued, provisional | yes | 2 issued activities |
| 9 | ELE-05 | Power system studies and protection | Not started | after VEN-01 | 0 issued activities |
| 10 | SAF-03 | Formal HAZOP and LOPA workshop | Not started | yes | 0 issued activities |
| 11 | PIP-05 | Detailed pipe stress (CAESAR II) | Not started | after VEN-01 | 0 issued activities |
| 12 | CIV-01 | Geotechnical, civil and structural design | Not started | yes | 0 issued activities |
| 13 | LAY-03 | 3D model reviews and constructability | Not started | after CIV-01 | 0 issued activities |
| 14 | ICS-08 | SIL verification and SRS | Not started | after SAF-03, VEN-01 | 0 issued activities |
| 15 | CST-02 | Class 3 cost estimate | Not started | after VEN-01, CIV-01 | 0 issued activities |
| 16 | PRJ-04 | PE review, seal and IFC issue | Not started | after SAF-03, ICS-08, PIP-05, ELE-05, CST-02, LAY-03, SAF-04, SAF-02 | 0 issued activities |

The provisional items (assay, H&MB, stress screening, SIL determination) sit at the start of long chains:
replacing the shortcut process model (PRC-00, PRC-01) re-opens 41 of the
45 activities. Nothing in this package is reviewed or sealed by a licensed engineer; PRJ-04 is the
gate before any use for procurement or construction.

# 8 Check against the code
The build was run with file access recorded (`python -m cfu.wrapup.depmap --trace`, data/dataflow.json).
Each read of a data file was compared with this map:
- upstream: 62

Iterations found in the code (a module reads a file written later in the build, so it uses the previous revision):

- none

Issues:

- none: every traced read is covered by the map

# 9 Limits
- The map covers the activities in this FEED package and the main ones still needed. Detailed design adds more
  (structural steel, instrument installation details, procurement, construction planning).
- Links are finish-to-start for clarity. Real schedules overlap activities with holds and early releases.
- The code check covers data files only. Shared constants imported from cfu/basis.py (PRJ-01) reach every module.
