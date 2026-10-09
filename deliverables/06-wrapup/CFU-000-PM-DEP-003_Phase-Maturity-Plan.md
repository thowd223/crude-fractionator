# 1 Purpose
This plan extends the design dependency map (CFU-000-PM-DEP-001) across the four phases of execution: FEL 1
(appraise), FEL 2 (select), FEL 3 (define / FEED) and detailed design. Most activities run in every phase. What
changes is how mature each one must be at each gate, so the plan is a matrix of target maturity by activity and
gate, plus the maturity each link needs.

Use it to:
- see what each gate requires, and what is still short;
- plan each phase as the steps that take activities from one level to the next, in the order the links allow;
- check that the gate targets are consistent (no gate asks for a result whose inputs are not mature enough).

# 2 Maturity scale
| Level | Name | Meaning |
|---|---|---|
| 0 | Not started | — |
| 1 | Concept | Sketches, factored or assumed data, option lists |
| 2 | Preliminary | Issued for review (rev A); enough to estimate and screen |
| 3 | Defined | Issued for design, HAZOP or purchase; the frozen basis for the next phase |
| 4 | Final | Issued for construction, approved or certified; one-off studies and decisions when complete |

# 3 Phases and gates
| Phase | Gate | Estimate | Purpose | Activities needed |
|---|---|---|---|---|
| FEL 1 · Appraise | Gate 1 · opportunity confirmed | Class 5 | Confirm there is a business case and a technically feasible concept worth developing. | 13 |
| FEL 2 · Select | Gate 2 · concept selected | Class 4 | Compare the alternatives and select one configuration, technology and site to take forward. | 34 |
| FEL 3 · Define (FEED) | Gate 3 · final investment decision | Class 3 | Define the selected concept well enough to fund it: HAZOP'd P&IDs, datasheets, long-lead orders. | 54 |
| Detailed design | Gate 4 · issued for construction | Class 2 | Complete the design with certified vendor data and issue everything needed to build. | 61 |

The plan has 61 activities (45 from the dependency map, 16 that
only appear once the phases are modelled), 178 input links, 15 iteration loops and
244 maturity steps.

# 4 Target matrix
Target level at each gate. "Now" is the level this package has reached.

| ID | Activity | Discipline | FEL 1 | FEL 2 | FEL 3 | DD | Now |
|---|---|---|---|---|---|---|---|
| FEL-01 | Business case, capacity and product slate | Project | 3 | 4 | 4 | 4 | 4* |
| PRJ-01 | Design basis (BOD) | Project | 2 | 3 | 4 | 4 | 4 |
| PRJ-03 | Document register and portal | Project | 1 | 2 | 3 | 4 | 3 |
| PRJ-05 | Execution plan and contracting strategy | Project | 1 | 2 | 4 | 4 | 0 |
| SEL-04 | Permitting and environmental basis | Project | · | 2 | 3 | 4 | 0 |
| PRJ-04 | PE review, seal and IFC issue | Project | · | · | · | 4 | 0 |
| FEL-02 | Configuration options and screening | Process | 4 | 4 | 4 | 4 | 4* |
| PRC-01 | Heat and material balance | Process | 1 | 2 | 3 | 4 | 2 |
| PRC-02 | Process equipment sizing | Process | 1 | 2 | 3 | 4 | 3 |
| PRC-05 | Block flow diagram | Process | 1 | 3 | 4 | 4 | 4 |
| PRC-06 | Process flow diagrams | Process | 1 | 2 | 3 | 4 | 3 |
| PRJ-02 | Crude assay characterisation | Process | 1 | 2 | 4 | 4 | 2 |
| PRC-00 | Rigorous simulation and model calibration | Process | · | 1 | 4 | 4 | 0 |
| PRC-03 | Relief load and PSV sizing (unit) | Process | · | 1 | 3 | 4 | 3 |
| PRC-04 | Control loops and SIF definition | Process | · | 1 | 3 | 4 | 3 |
| PRC-07 | Process design report | Process | · | 1 | 4 | 4 | 4 |
| PRC-08 | P&IDs, line list, instrument index | Process | · | 1 | 3 | 4 | 3 |
| SEL-01 | Alternatives evaluation and select decision | Process | · | 4 | 4 | 4 | 4* |
| SEL-02 | Technology and licensor selection | Process | · | 4 | 4 | 4 | 4* |
| SEL-03 | Utility and offsite basis | Process | · | 2 | 3 | 4 | 2 |
| SAF-02 | Global flare load study | Safety | · | 1 | 3 | 4 | 0 |
| SAF-01 | Preliminary HAZOP | Safety | · | · | 4 | 4 | 4 |
| SAF-04 | Siting study, QRA, F&G mapping | Safety | · | · | 4 | 4 | 0 |
| SAF-03 | Formal HAZOP and LOPA workshop | Safety | · | · | · | 4 | 0 |
| MEC-01 | Mechanical design calculations | Mechanical | · | 1 | 3 | 4 | 3 |
| MEC-02 | Equipment datasheets | Mechanical | · | 1 | 3 | 4 | 3 |
| MEC-03 | Equipment GA drawings | Mechanical | · | · | 2 | 4 | 2 |
| VEN-01 | Vendor enquiries and vendor data | Mechanical | · | · | 2 | 4 | 0 |
| PRO-01 | Requisitions and technical bid evaluations | Procurement | · | · | 3 | 4 | 0 |
| FEL-03 | Site screening and selection | Layout | 2 | 4 | 4 | 4 | 4* |
| LAY-01 | Plot plan and equipment layout | Layout | 1 | 2 | 3 | 4 | 3 |
| LAY-02 | Sections and 3D layout model | Layout | · | 1 | 3 | 4 | 3 |
| LAY-03 | 3D model reviews and constructability | Layout | · | · | 2 | 4 | 0 |
| PIP-01 | Piping material classes | Piping | · | 1 | 3 | 4 | 3 |
| PIP-02 | Piping routing and 3D model | Piping | · | · | 2 | 4 | 2 |
| PIP-03 | Pipe stress and supports (screening) | Piping | · | · | 2 | 4 | 1 |
| PIP-04 | Isometrics and piping MTO | Piping | · | · | 2 | 4 | 2 |
| PIP-05 | Detailed pipe stress (CAESAR II) | Piping | · | · | 1 | 4 | 0 |
| CIV-01 | Geotechnical, civil and structural design | Civil | · | 1 | 2 | 4 | 0 |
| CIV-02 | Foundation and structural steel detailing | Civil | · | · | · | 4 | 0 |
| ICS-01 | Control philosophy and schemes | I&C | · | 1 | 3 | 4 | 3 |
| ICS-07 | ICS architecture | I&C | · | 1 | 3 | 4 | 3 |
| ICS-02 | SIF list and SIL determination (LOPA) | I&C | · | · | 2 | 4 | 1 |
| ICS-03 | Cause and effect matrix | I&C | · | · | 2 | 4 | 2 |
| ICS-04 | Control valve sizing | I&C | · | · | 2 | 4 | 2 |
| ICS-05 | I/O list | I&C | · | · | 2 | 4 | 2 |
| ICS-06 | Loop diagrams | I&C | · | · | 1 | 4 | 1 |
| ICS-08 | SIL verification and SRS | I&C | · | · | · | 4 | 0 |
| ICS-09 | Instrument installation design | I&C | · | · | · | 4 | 0 |
| ELE-01 | Electrical load list | Electrical | · | 1 | 3 | 4 | 3 |
| ELE-03 | Electrical sizing, single-line diagrams | Electrical | · | 1 | 3 | 4 | 3 |
| ELE-02 | Hazardous area classification | Electrical | · | · | 3 | 4 | 3 |
| ELE-04 | Cable schedule | Electrical | · | · | 2 | 4 | 2 |
| ELE-05 | Power system studies and protection | Electrical | · | · | 1 | 4 | 0 |
| ELE-06 | Electrical layouts | Electrical | · | · | · | 4 | 0 |
| CON-01 | Constructability, modularisation and path of construction | Construction | · | 1 | 3 | 4 | 0 |
| CON-02 | Work packaging and system boundaries | Construction | · | · | 1 | 4 | 0 |
| FEL-04 | Class 5 estimate and economics | Cost | 4 | 4 | 4 | 4 | 4* |
| CST-01 | Class 4 cost estimate | Cost | · | 4 | 4 | 4 | 4 |
| CST-02 | Class 3 cost estimate | Cost | · | · | 4 | 4 | 0 |
| CST-03 | Control estimate | Cost | · | · | · | 4 | 0 |

\* assumed: decided in the design basis rather than developed in this package.

# 5 Link maturity rules
- By default, taking an activity to level L needs each of its inputs at level L.
- Studies, estimates and HAZOPs need early inputs only. Their cap: FEL-02 2, FEL-03 2, FEL-04 1, SEL-01 2, SEL-02 2, PRC-05 2, PRC-07 3, SAF-01 2, SAF-03 3, SAF-04 2, VEN-01 3, CST-01 2, CST-02 2, CST-03 3.
- Single-link exceptions:
  - PRC-00 → PRC-01: at level 1 needs nothing, at level 2 needs 1 (calibrated cut points and efficiencies)
  - SEL-01 → PRC-01: at level 1 needs nothing, at level 2 needs nothing (selected configuration)
  - SEL-01 → CST-01: at level 4 needs 4 (selected scope)
  - SEL-02 → SEL-01: at level 4 needs 4 (selected technology)
  - SEL-01 → PRJ-05: at level 1 needs nothing (selected scope)
  - PRC-04 → PRC-06: at level 1 needs nothing, at level 2 needs 1 (principal control loops)
  - PIP-03 → CIV-01: at level 1 needs nothing (support loads)
  - ICS-05 → ICS-07: at level 1 needs nothing, at level 3 needs 2 (I/O counts)
  - MEC-01 → CST-01: at level 4 needs 1 (shell weights)
- Iteration loops become forward links between levels, so the plan has no cycles:
  - PRC-02 reaches level 3 after MEC-01 reaches level 2 (mechanical holds re-rate sizing (C-201 bed-1 diameter, heater box length))
  - LAY-01 reaches level 3 after MEC-01 reaches level 2 (calculated dimensions and weights update footprints and spacing)
  - PRC-02 reaches level 4 after PIP-02 reaches level 3 (routed lengths update pump and line hydraulics)
  - LAY-01 reaches level 4 after PIP-02 reaches level 3 (rack width and clashes move equipment)
  - PRC-08 reaches level 4 after ICS-04 reaches level 3 (control valve sizes and reducers shown on the P&IDs)
  - PRC-08 reaches level 3 after SAF-01 reaches level 4 (HAZOP recommendations revise the P&IDs)
  - ELE-03 reaches level 4 after ELE-04 reaches level 3 (actual cable impedances re-run the motor-starting voltage-dip check)
  - ELE-01 reaches level 4 after ICS-07 reaches level 3 (ICS cabinet and UPS loads added to the load list)
  - PRC-03 reaches level 4 after SAF-02 reaches level 3 (flare back-pressure changes PSV type and size)
  - PRC-08 reaches level 4 after SAF-03 reaches level 4 (formal HAZOP actions revise the P&IDs)
  - LAY-01 reaches level 3 after SAF-04 reaches level 4 (siting study moves occupied buildings and equipment)
  - MEC-01 reaches level 4 after VEN-01 reaches level 4 (certified vendor dimensions, weights and nozzles)
  - LAY-01 reaches level 4 after VEN-01 reaches level 4 (vendor package footprints)
  - ELE-01 reaches level 4 after VEN-01 reaches level 4 (certified motor ratings)
  - ICS-05 reaches level 4 after VEN-01 reaches level 4 (vendor package I/O)

# 6 Gate readiness of this package
| Gate | Needed | Met | Assumed | Short |
|---|---|---|---|---|
| Gate 1 · opportunity confirmed | 13 | 8 | 4 | 1 |
| Gate 2 · concept selected | 34 | 22 | 6 | 6 |
| Gate 3 · final investment decision | 54 | 29 | 6 | 19 |
| Gate 4 · issued for construction | 61 | 5 | 6 | 50 |

**Gate 1 · opportunity confirmed: short**

- PRJ-05 Execution plan and contracting strategy: at 0 not started, needs 1 concept

**Gate 2 · concept selected: short**

- PRJ-05 Execution plan and contracting strategy: at 0 not started, needs 2 preliminary
- SEL-04 Permitting and environmental basis: at 0 not started, needs 2 preliminary
- PRC-00 Rigorous simulation and model calibration: at 0 not started, needs 1 concept
- SAF-02 Global flare load study: at 0 not started, needs 1 concept
- CIV-01 Geotechnical, civil and structural design: at 0 not started, needs 1 concept
- CON-01 Constructability, modularisation and path of construction: at 0 not started, needs 1 concept

**Gate 3 · final investment decision: short**

- PRJ-05 Execution plan and contracting strategy: at 0 not started, needs 4 final
- SEL-04 Permitting and environmental basis: at 0 not started, needs 3 defined
- PRC-01 Heat and material balance: at 2 preliminary, needs 3 defined
- PRJ-02 Crude assay characterisation: at 2 preliminary, needs 4 final
- PRC-00 Rigorous simulation and model calibration: at 0 not started, needs 4 final
- SEL-03 Utility and offsite basis: at 2 preliminary, needs 3 defined
- SAF-02 Global flare load study: at 0 not started, needs 3 defined
- SAF-04 Siting study, QRA, F&G mapping: at 0 not started, needs 4 final
- VEN-01 Vendor enquiries and vendor data: at 0 not started, needs 2 preliminary
- PRO-01 Requisitions and technical bid evaluations: at 0 not started, needs 3 defined
- LAY-03 3D model reviews and constructability: at 0 not started, needs 2 preliminary
- PIP-03 Pipe stress and supports (screening): at 1 concept, needs 2 preliminary
- PIP-05 Detailed pipe stress (CAESAR II): at 0 not started, needs 1 concept
- CIV-01 Geotechnical, civil and structural design: at 0 not started, needs 2 preliminary
- ICS-02 SIF list and SIL determination (LOPA): at 1 concept, needs 2 preliminary
- ELE-05 Power system studies and protection: at 0 not started, needs 1 concept
- CON-01 Constructability, modularisation and path of construction: at 0 not started, needs 3 defined
- CON-02 Work packaging and system boundaries: at 0 not started, needs 1 concept
- CST-02 Class 3 cost estimate: at 0 not started, needs 4 final

# 7 Steps by phase
Each step takes an activity to a level. Steps are in network order; "ready" means every input is already at the level the step needs.

## FEL 1 · Appraise
23 steps: 22 done, 1 ready, 0 blocked.

| Order | ID | Activity | To level | Today | Waiting on |
|---|---|---|---|---|---|
| 1 | FEL-01 | Business case, capacity and product slate | 1 Concept | done | - |
| 1 | PRJ-03 | Document register and portal | 1 Concept | done | - |
| 2 | FEL-01 | Business case, capacity and product slate | 2 Preliminary | done | - |
| 2 | FEL-03 | Site screening and selection | 1 Concept | done | - |
| 2 | PRJ-01 | Design basis (BOD) | 1 Concept | done | - |
| 2 | PRJ-05 | Execution plan and contracting strategy | 1 Concept | ready | - |
| 3 | FEL-01 | Business case, capacity and product slate | 3 Defined | done | - |
| 3 | FEL-02 | Configuration options and screening | 1 Concept | done | - |
| 3 | FEL-03 | Site screening and selection | 2 Preliminary | done | - |
| 3 | PRJ-01 | Design basis (BOD) | 2 Preliminary | done | - |
| 3 | PRJ-02 | Crude assay characterisation | 1 Concept | done | - |
| 4 | FEL-02 | Configuration options and screening | 2 Preliminary | done | - |
| 4 | PRC-01 | Heat and material balance | 1 Concept | done | - |
| 5 | FEL-02 | Configuration options and screening | 3 Defined | done | - |
| 5 | PRC-02 | Process equipment sizing | 1 Concept | done | - |
| 5 | PRC-05 | Block flow diagram | 1 Concept | done | - |
| 6 | FEL-02 | Configuration options and screening | 4 Final | done | - |
| 6 | LAY-01 | Plot plan and equipment layout | 1 Concept | done | - |
| 6 | PRC-06 | Process flow diagrams | 1 Concept | done | - |
| 7 | FEL-04 | Class 5 estimate and economics | 1 Concept | done | - |
| 8 | FEL-04 | Class 5 estimate and economics | 2 Preliminary | done | - |
| 9 | FEL-04 | Class 5 estimate and economics | 3 Defined | done | - |
| 10 | FEL-04 | Class 5 estimate and economics | 4 Final | done | - |

## FEL 2 · Select
45 steps: 38 done, 4 ready, 3 blocked.

| Order | ID | Activity | To level | Today | Waiting on |
|---|---|---|---|---|---|
| 2 | PRJ-03 | Document register and portal | 2 Preliminary | done | - |
| 4 | FEL-01 | Business case, capacity and product slate | 4 Final | done | - |
| 4 | FEL-03 | Site screening and selection | 3 Defined | done | - |
| 4 | PRC-00 | Rigorous simulation and model calibration | 1 Concept | ready | - |
| 4 | PRJ-01 | Design basis (BOD) | 3 Defined | done | - |
| 4 | PRJ-02 | Crude assay characterisation | 2 Preliminary | done | - |
| 4 | SEL-02 | Technology and licensor selection | 1 Concept | done | - |
| 5 | FEL-03 | Site screening and selection | 4 Final | done | - |
| 5 | PIP-01 | Piping material classes | 1 Concept | done | - |
| 5 | PRC-01 | Heat and material balance | 2 Preliminary | done | PRC-00 at 1 |
| 5 | SEL-01 | Alternatives evaluation and select decision | 1 Concept | done | - |
| 5 | SEL-02 | Technology and licensor selection | 2 Preliminary | done | - |
| 5 | SEL-03 | Utility and offsite basis | 1 Concept | done | - |
| 6 | ELE-01 | Electrical load list | 1 Concept | done | - |
| 6 | PRC-02 | Process equipment sizing | 2 Preliminary | done | - |
| 6 | PRC-03 | Relief load and PSV sizing (unit) | 1 Concept | done | - |
| 6 | PRC-04 | Control loops and SIF definition | 1 Concept | done | - |
| 6 | PRC-05 | Block flow diagram | 2 Preliminary | done | - |
| 6 | SEL-01 | Alternatives evaluation and select decision | 2 Preliminary | done | - |
| 6 | SEL-02 | Technology and licensor selection | 3 Defined | done | - |
| 6 | SEL-03 | Utility and offsite basis | 2 Preliminary | done | - |
| 7 | ELE-03 | Electrical sizing, single-line diagrams | 1 Concept | done | - |
| 7 | ICS-01 | Control philosophy and schemes | 1 Concept | done | - |
| 7 | LAY-01 | Plot plan and equipment layout | 2 Preliminary | done | - |
| 7 | LAY-02 | Sections and 3D layout model | 1 Concept | done | - |
| 7 | MEC-01 | Mechanical design calculations | 1 Concept | done | - |
| 7 | PRC-05 | Block flow diagram | 3 Defined | done | - |
| 7 | PRC-06 | Process flow diagrams | 2 Preliminary | done | - |
| 7 | PRC-07 | Process design report | 1 Concept | done | - |
| 7 | PRC-08 | P&IDs, line list, instrument index | 1 Concept | done | - |
| 7 | PRJ-05 | Execution plan and contracting strategy | 2 Preliminary | blocked | PRJ-05 at 1 |
| 7 | SAF-02 | Global flare load study | 1 Concept | ready | - |
| 7 | SEL-01 | Alternatives evaluation and select decision | 3 Defined | done | - |
| 7 | SEL-02 | Technology and licensor selection | 4 Final | done | - |
| 7 | SEL-04 | Permitting and environmental basis | 1 Concept | ready | - |
| 8 | CIV-01 | Geotechnical, civil and structural design | 1 Concept | ready | - |
| 8 | CON-01 | Constructability, modularisation and path of construction | 1 Concept | blocked | PRJ-05 at 1 |
| 8 | CST-01 | Class 4 cost estimate | 1 Concept | done | - |
| 8 | ICS-07 | ICS architecture | 1 Concept | done | - |
| 8 | MEC-02 | Equipment datasheets | 1 Concept | done | - |
| 8 | SEL-01 | Alternatives evaluation and select decision | 4 Final | done | - |
| 8 | SEL-04 | Permitting and environmental basis | 2 Preliminary | blocked | SEL-04 at 1 |
| 9 | CST-01 | Class 4 cost estimate | 2 Preliminary | done | - |
| 10 | CST-01 | Class 4 cost estimate | 3 Defined | done | - |
| 11 | CST-01 | Class 4 cost estimate | 4 Final | done | - |

## FEL 3 · Define (FEED)
90 steps: 55 done, 4 ready, 31 blocked.

| Order | ID | Activity | To level | Today | Waiting on |
|---|---|---|---|---|---|
| 3 | PRJ-03 | Document register and portal | 3 Defined | done | - |
| 5 | PRC-00 | Rigorous simulation and model calibration | 2 Preliminary | blocked | PRC-00 at 1 |
| 5 | PRJ-01 | Design basis (BOD) | 4 Final | done | - |
| 5 | PRJ-02 | Crude assay characterisation | 3 Defined | ready | - |
| 6 | PIP-01 | Piping material classes | 2 Preliminary | done | - |
| 6 | PRC-00 | Rigorous simulation and model calibration | 3 Defined | blocked | PRJ-02 at 3, PRC-00 at 2 |
| 6 | PRJ-02 | Crude assay characterisation | 4 Final | blocked | PRJ-02 at 3 |
| 7 | ELE-01 | Electrical load list | 2 Preliminary | done | - |
| 7 | ELE-02 | Hazardous area classification | 1 Concept | done | - |
| 7 | PRC-00 | Rigorous simulation and model calibration | 4 Final | blocked | PRJ-02 at 4, PRC-00 at 3 |
| 7 | PRC-03 | Relief load and PSV sizing (unit) | 2 Preliminary | done | - |
| 7 | PRC-04 | Control loops and SIF definition | 2 Preliminary | done | - |
| 8 | ELE-02 | Hazardous area classification | 2 Preliminary | done | - |
| 8 | ELE-03 | Electrical sizing, single-line diagrams | 2 Preliminary | done | - |
| 8 | ELE-04 | Cable schedule | 1 Concept | done | - |
| 8 | ICS-01 | Control philosophy and schemes | 2 Preliminary | done | - |
| 8 | ICS-04 | Control valve sizing | 1 Concept | done | - |
| 8 | ICS-05 | I/O list | 1 Concept | done | - |
| 8 | LAY-02 | Sections and 3D layout model | 2 Preliminary | done | - |
| 8 | MEC-01 | Mechanical design calculations | 2 Preliminary | done | - |
| 8 | MEC-03 | Equipment GA drawings | 1 Concept | done | - |
| 8 | PIP-02 | Piping routing and 3D model | 1 Concept | done | - |
| 8 | PRC-01 | Heat and material balance | 3 Defined | blocked | PRJ-02 at 3, PRC-00 at 3 |
| 8 | PRC-05 | Block flow diagram | 4 Final | done | - |
| 8 | PRC-07 | Process design report | 2 Preliminary | done | - |
| 8 | PRC-08 | P&IDs, line list, instrument index | 2 Preliminary | done | - |
| 8 | PRJ-05 | Execution plan and contracting strategy | 3 Defined | blocked | PRJ-05 at 2 |
| 8 | SAF-01 | Preliminary HAZOP | 1 Concept | done | - |
| 8 | SAF-02 | Global flare load study | 2 Preliminary | blocked | SAF-02 at 1 |
| 9 | CON-01 | Constructability, modularisation and path of construction | 2 Preliminary | blocked | PRJ-05 at 2, CON-01 at 1 |
| 9 | ELE-04 | Cable schedule | 2 Preliminary | done | - |
| 9 | ICS-02 | SIF list and SIL determination (LOPA) | 1 Concept | done | - |
| 9 | ICS-04 | Control valve sizing | 2 Preliminary | done | - |
| 9 | ICS-05 | I/O list | 2 Preliminary | done | - |
| 9 | ICS-06 | Loop diagrams | 1 Concept | done | - |
| 9 | LAY-03 | 3D model reviews and constructability | 1 Concept | blocked | CIV-01 at 1 |
| 9 | MEC-02 | Equipment datasheets | 2 Preliminary | done | - |
| 9 | MEC-03 | Equipment GA drawings | 2 Preliminary | done | - |
| 9 | PIP-01 | Piping material classes | 3 Defined | done | PRC-01 at 3 |
| 9 | PIP-02 | Piping routing and 3D model | 2 Preliminary | done | - |
| 9 | PIP-03 | Pipe stress and supports (screening) | 1 Concept | done | - |
| 9 | PIP-04 | Isometrics and piping MTO | 1 Concept | done | - |
| 9 | PRC-02 | Process equipment sizing | 3 Defined | done | PRC-01 at 3 |
| 9 | PRJ-05 | Execution plan and contracting strategy | 4 Final | blocked | PRJ-05 at 3 |
| 9 | PRO-01 | Requisitions and technical bid evaluations | 1 Concept | blocked | PRJ-05 at 1 |
| 9 | SAF-01 | Preliminary HAZOP | 2 Preliminary | done | - |
| 9 | SAF-04 | Siting study, QRA, F&G mapping | 1 Concept | ready | - |
| 9 | SEL-03 | Utility and offsite basis | 3 Defined | blocked | PRC-01 at 3 |
| 10 | CON-02 | Work packaging and system boundaries | 1 Concept | blocked | CON-01 at 1 |
| 10 | ELE-01 | Electrical load list | 3 Defined | done | - |
| 10 | ICS-02 | SIF list and SIL determination (LOPA) | 2 Preliminary | ready | - |
| 10 | ICS-03 | Cause and effect matrix | 1 Concept | done | - |
| 10 | ICS-07 | ICS architecture | 2 Preliminary | done | - |
| 10 | PIP-03 | Pipe stress and supports (screening) | 2 Preliminary | ready | - |
| 10 | PIP-04 | Isometrics and piping MTO | 2 Preliminary | done | - |
| 10 | PRC-03 | Relief load and PSV sizing (unit) | 3 Defined | done | PRC-01 at 3 |
| 10 | PRC-04 | Control loops and SIF definition | 3 Defined | done | PRC-01 at 3 |
| 10 | PRO-01 | Requisitions and technical bid evaluations | 2 Preliminary | blocked | PRJ-05 at 2, PRO-01 at 1 |
| 10 | SAF-01 | Preliminary HAZOP | 3 Defined | done | - |
| 10 | SAF-04 | Siting study, QRA, F&G mapping | 2 Preliminary | blocked | SAF-04 at 1 |
| 10 | VEN-01 | Vendor enquiries and vendor data | 1 Concept | blocked | PRO-01 at 1 |
| 11 | CIV-01 | Geotechnical, civil and structural design | 2 Preliminary | blocked | PIP-03 at 2, CIV-01 at 1 |
| 11 | CST-02 | Class 3 cost estimate | 1 Concept | blocked | VEN-01 at 1, CIV-01 at 1 |
| 11 | ELE-03 | Electrical sizing, single-line diagrams | 3 Defined | done | - |
| 11 | ELE-05 | Power system studies and protection | 1 Concept | blocked | VEN-01 at 1 |
| 11 | ICS-01 | Control philosophy and schemes | 3 Defined | done | PRC-01 at 3 |
| 11 | ICS-03 | Cause and effect matrix | 2 Preliminary | done | ICS-02 at 2 |
| 11 | MEC-01 | Mechanical design calculations | 3 Defined | done | PRC-01 at 3 |
| 11 | PIP-05 | Detailed pipe stress (CAESAR II) | 1 Concept | blocked | VEN-01 at 1 |
| 11 | PRC-06 | Process flow diagrams | 3 Defined | done | PRC-01 at 3 |
| 11 | PRC-07 | Process design report | 3 Defined | done | PRC-01 at 3 |
| 11 | SAF-01 | Preliminary HAZOP | 4 Final | done | - |
| 11 | SAF-02 | Global flare load study | 3 Defined | blocked | SAF-02 at 2 |
| 11 | SAF-04 | Siting study, QRA, F&G mapping | 3 Defined | blocked | SAF-04 at 2 |
| 11 | VEN-01 | Vendor enquiries and vendor data | 2 Preliminary | blocked | PRO-01 at 2, VEN-01 at 1 |
| 12 | CST-02 | Class 3 cost estimate | 2 Preliminary | blocked | VEN-01 at 2, CIV-01 at 2, CST-02 at 1 |
| 12 | ICS-07 | ICS architecture | 3 Defined | done | - |
| 12 | LAY-03 | 3D model reviews and constructability | 2 Preliminary | blocked | CIV-01 at 2, LAY-03 at 1 |
| 12 | MEC-02 | Equipment datasheets | 3 Defined | done | - |
| 12 | PRC-07 | Process design report | 4 Final | done | PRC-01 at 3 |
| 12 | SAF-04 | Siting study, QRA, F&G mapping | 4 Final | blocked | SAF-04 at 3 |
| 13 | CST-02 | Class 3 cost estimate | 3 Defined | blocked | VEN-01 at 2, CIV-01 at 2, CST-02 at 2 |
| 13 | LAY-01 | Plot plan and equipment layout | 3 Defined | done | PRC-01 at 3, SAF-04 at 4 |
| 13 | PRO-01 | Requisitions and technical bid evaluations | 3 Defined | blocked | PRJ-05 at 3, PRO-01 at 2 |
| 14 | CST-02 | Class 3 cost estimate | 4 Final | blocked | VEN-01 at 2, CIV-01 at 2, CST-02 at 3 |
| 14 | ELE-02 | Hazardous area classification | 3 Defined | done | - |
| 14 | LAY-02 | Sections and 3D layout model | 3 Defined | done | - |
| 14 | PRC-08 | P&IDs, line list, instrument index | 3 Defined | done | - |
| 14 | SEL-04 | Permitting and environmental basis | 3 Defined | blocked | PRC-01 at 3, SEL-04 at 2 |
| 15 | CON-01 | Constructability, modularisation and path of construction | 3 Defined | blocked | PRJ-05 at 3, CON-01 at 2 |

## Detailed design
86 steps: 0 done, 7 ready, 79 blocked.

| Order | ID | Activity | To level | Today | Waiting on |
|---|---|---|---|---|---|
| 9 | ELE-06 | Electrical layouts | 1 Concept | ready | - |
| 9 | PRC-01 | Heat and material balance | 4 Final | blocked | PRJ-02 at 4, PRC-00 at 4, PRC-01 at 3 |
| 10 | ELE-06 | Electrical layouts | 2 Preliminary | blocked | ELE-06 at 1 |
| 10 | ICS-06 | Loop diagrams | 2 Preliminary | ready | - |
| 10 | PIP-01 | Piping material classes | 4 Final | blocked | PRC-01 at 4 |
| 10 | SAF-03 | Formal HAZOP and LOPA workshop | 1 Concept | ready | - |
| 10 | SEL-03 | Utility and offsite basis | 4 Final | blocked | PRC-01 at 4, SEL-03 at 3 |
| 11 | CON-02 | Work packaging and system boundaries | 2 Preliminary | blocked | CON-01 at 2, CON-02 at 1 |
| 11 | ICS-02 | SIF list and SIL determination (LOPA) | 3 Defined | blocked | ICS-02 at 2 |
| 11 | ICS-08 | SIL verification and SRS | 1 Concept | blocked | SAF-03 at 1, VEN-01 at 1 |
| 11 | ICS-09 | Instrument installation design | 1 Concept | blocked | VEN-01 at 1 |
| 11 | SAF-03 | Formal HAZOP and LOPA workshop | 2 Preliminary | blocked | ICS-02 at 2, SAF-03 at 1 |
| 12 | CIV-02 | Foundation and structural steel detailing | 1 Concept | blocked | CIV-01 at 1, VEN-01 at 1, PIP-05 at 1 |
| 12 | CST-03 | Control estimate | 1 Concept | blocked | CST-02 at 1, PRO-01 at 1, CIV-01 at 1 |
| 12 | ELE-05 | Power system studies and protection | 2 Preliminary | blocked | VEN-01 at 2, ELE-05 at 1 |
| 12 | ICS-03 | Cause and effect matrix | 3 Defined | blocked | ICS-02 at 3 |
| 12 | ICS-08 | SIL verification and SRS | 2 Preliminary | blocked | ICS-02 at 2, SAF-03 at 2, VEN-01 at 2, ICS-08 at 1 |
| 12 | ICS-09 | Instrument installation design | 2 Preliminary | blocked | VEN-01 at 2, ICS-09 at 1 |
| 12 | MEC-03 | Equipment GA drawings | 3 Defined | ready | - |
| 12 | PIP-05 | Detailed pipe stress (CAESAR II) | 2 Preliminary | blocked | PIP-03 at 2, VEN-01 at 2, PIP-05 at 1 |
| 13 | CIV-02 | Foundation and structural steel detailing | 2 Preliminary | blocked | CIV-01 at 2, VEN-01 at 2, PIP-05 at 2, CIV-02 at 1 |
| 13 | CST-03 | Control estimate | 2 Preliminary | blocked | CST-02 at 2, PRO-01 at 2, CIV-01 at 2, CST-03 at 1 |
| 13 | PRJ-04 | PE review, seal and IFC issue | 1 Concept | blocked | SAF-03 at 1, ICS-08 at 1, PIP-05 at 1, ELE-05 at 1, CST-02 at 1, LAY-03 at 1, SAF-04 at 1, SAF-02 at 1, CIV-02 at 1, ICS-09 at 1, ELE-06 at 1, CON-02 at 1, PRO-01 at 1 |
| 14 | PRJ-04 | PE review, seal and IFC issue | 2 Preliminary | blocked | SAF-03 at 2, ICS-08 at 2, PIP-05 at 2, ELE-05 at 2, CST-02 at 2, LAY-03 at 2, SAF-04 at 2, SAF-02 at 2, CIV-02 at 2, ICS-09 at 2, ELE-06 at 2, CON-02 at 2, PRO-01 at 2, PRJ-04 at 1 |
| 14 | VEN-01 | Vendor enquiries and vendor data | 3 Defined | blocked | PRO-01 at 3, VEN-01 at 2 |
| 15 | ELE-04 | Cable schedule | 3 Defined | ready | - |
| 15 | ELE-05 | Power system studies and protection | 3 Defined | blocked | VEN-01 at 3, ELE-05 at 2 |
| 15 | ICS-04 | Control valve sizing | 3 Defined | blocked | PRC-01 at 3 |
| 15 | ICS-05 | I/O list | 3 Defined | ready | - |
| 15 | PIP-02 | Piping routing and 3D model | 3 Defined | ready | - |
| 15 | SAF-03 | Formal HAZOP and LOPA workshop | 3 Defined | blocked | ICS-02 at 3, SAF-03 at 2 |
| 15 | VEN-01 | Vendor enquiries and vendor data | 4 Final | blocked | PRO-01 at 3, VEN-01 at 3 |
| 16 | ELE-06 | Electrical layouts | 3 Defined | blocked | ELE-04 at 3, PIP-02 at 3, ELE-06 at 2 |
| 16 | ICS-06 | Loop diagrams | 3 Defined | blocked | ICS-05 at 3, ICS-06 at 2 |
| 16 | ICS-08 | SIL verification and SRS | 3 Defined | blocked | ICS-02 at 3, SAF-03 at 3, VEN-01 at 3, ICS-08 at 2 |
| 16 | ICS-09 | Instrument installation design | 3 Defined | blocked | ICS-05 at 3, PIP-02 at 3, VEN-01 at 3, ICS-09 at 2 |
| 16 | PIP-03 | Pipe stress and supports (screening) | 3 Defined | blocked | PIP-02 at 3, PIP-03 at 2 |
| 16 | PIP-04 | Isometrics and piping MTO | 3 Defined | blocked | PIP-02 at 3 |
| 16 | PRC-02 | Process equipment sizing | 4 Final | blocked | PRC-01 at 4, PIP-02 at 3 |
| 16 | SAF-03 | Formal HAZOP and LOPA workshop | 4 Final | blocked | ICS-02 at 3, SAF-03 at 3 |
| 17 | CIV-01 | Geotechnical, civil and structural design | 3 Defined | blocked | PIP-03 at 3, CIV-01 at 2 |
| 17 | CON-02 | Work packaging and system boundaries | 3 Defined | blocked | CON-01 at 3, PIP-04 at 3, CON-02 at 2 |
| 17 | ELE-01 | Electrical load list | 4 Final | blocked | PRC-02 at 4, VEN-01 at 4 |
| 17 | LAY-01 | Plot plan and equipment layout | 4 Final | blocked | PRC-02 at 4, PRC-01 at 4, PIP-02 at 3, SAF-04 at 4, VEN-01 at 4 |
| 17 | PIP-05 | Detailed pipe stress (CAESAR II) | 3 Defined | blocked | PIP-03 at 3, VEN-01 at 3, PIP-05 at 2 |
| 17 | PRC-03 | Relief load and PSV sizing (unit) | 4 Final | blocked | PRC-01 at 4, PRC-02 at 4, SAF-02 at 3 |
| 17 | PRC-04 | Control loops and SIF definition | 4 Final | blocked | PRC-01 at 4, PRC-02 at 4 |
| 18 | CIV-02 | Foundation and structural steel detailing | 3 Defined | blocked | CIV-01 at 3, VEN-01 at 3, PIP-05 at 3, CIV-02 at 2 |
| 18 | CST-03 | Control estimate | 3 Defined | blocked | CST-02 at 3, PRO-01 at 3, PIP-04 at 3, CIV-01 at 3, CST-03 at 2 |
| 18 | ELE-02 | Hazardous area classification | 4 Final | blocked | LAY-01 at 4, PRC-02 at 4, PRC-04 at 4 |
| 18 | ELE-03 | Electrical sizing, single-line diagrams | 4 Final | blocked | ELE-01 at 4, ELE-04 at 3 |
| 18 | ICS-01 | Control philosophy and schemes | 4 Final | blocked | PRC-04 at 4, PRC-01 at 4, PRC-02 at 4 |
| 18 | ICS-02 | SIF list and SIL determination (LOPA) | 4 Final | blocked | PRC-04 at 4, ICS-02 at 3 |
| 18 | LAY-02 | Sections and 3D layout model | 4 Final | blocked | LAY-01 at 4, PRC-02 at 4 |
| 18 | LAY-03 | 3D model reviews and constructability | 3 Defined | blocked | PIP-02 at 3, CIV-01 at 3, LAY-03 at 2 |
| 18 | MEC-01 | Mechanical design calculations | 4 Final | blocked | PRC-02 at 4, PRC-01 at 4, PRC-03 at 4, VEN-01 at 4 |
| 18 | PRC-06 | Process flow diagrams | 4 Final | blocked | PRC-01 at 4, PRC-02 at 4, PRC-04 at 4 |
| 18 | SAF-02 | Global flare load study | 4 Final | blocked | PRC-03 at 4, SAF-02 at 3 |
| 18 | SEL-04 | Permitting and environmental basis | 4 Final | blocked | PRC-01 at 4, LAY-01 at 4, SEL-04 at 3 |
| 19 | CON-01 | Constructability, modularisation and path of construction | 4 Final | blocked | LAY-01 at 4, LAY-02 at 4, PRJ-05 at 4, CON-01 at 3 |
| 19 | CST-03 | Control estimate | 4 Final | blocked | CST-02 at 3, PRO-01 at 3, PIP-04 at 3, CIV-01 at 3, CST-03 at 3 |
| 19 | ELE-04 | Cable schedule | 4 Final | blocked | ELE-01 at 4, ELE-03 at 4, LAY-01 at 4, ELE-02 at 4, ELE-04 at 3 |
| 19 | ELE-05 | Power system studies and protection | 4 Final | blocked | ELE-03 at 4, VEN-01 at 4, ELE-05 at 3 |
| 19 | ICS-03 | Cause and effect matrix | 4 Final | blocked | PRC-04 at 4, PRC-03 at 4, PRC-02 at 4, ICS-02 at 4, ICS-03 at 3 |
| 19 | ICS-08 | SIL verification and SRS | 4 Final | blocked | ICS-02 at 4, SAF-03 at 4, VEN-01 at 4, ICS-08 at 3 |
| 19 | MEC-02 | Equipment datasheets | 4 Final | blocked | MEC-01 at 4, PRC-02 at 4, PRC-03 at 4 |
| 19 | MEC-03 | Equipment GA drawings | 4 Final | blocked | MEC-01 at 4, MEC-03 at 3 |
| 19 | PRC-08 | P&IDs, line list, instrument index | 4 Final | blocked | PRC-02 at 4, PRC-03 at 4, PRC-04 at 4, PRC-06 at 4, PIP-01 at 4, LAY-01 at 4, ICS-04 at 3, SAF-03 at 4 |
| 19 | PRJ-04 | PE review, seal and IFC issue | 3 Defined | blocked | SAF-03 at 3, ICS-08 at 3, PIP-05 at 3, ELE-05 at 3, CST-02 at 3, LAY-03 at 3, SAF-04 at 3, SAF-02 at 3, CIV-02 at 3, ICS-09 at 3, ELE-06 at 3, CON-02 at 3, PRO-01 at 3, PRJ-04 at 2 |
| 20 | ICS-04 | Control valve sizing | 4 Final | blocked | PRC-01 at 4, PRC-02 at 4, PRC-04 at 4, PRC-08 at 4, ICS-04 at 3 |
| 20 | ICS-05 | I/O list | 4 Final | blocked | PRC-08 at 4, PRC-04 at 4, PRC-02 at 4, LAY-01 at 4, VEN-01 at 4, ICS-05 at 3 |
| 20 | PIP-02 | Piping routing and 3D model | 4 Final | blocked | PRC-08 at 4, LAY-01 at 4, PRC-03 at 4, MEC-01 at 4, PIP-02 at 3 |
| 20 | PRO-01 | Requisitions and technical bid evaluations | 4 Final | blocked | MEC-02 at 4, PRJ-05 at 4, PRO-01 at 3 |
| 21 | ELE-06 | Electrical layouts | 4 Final | blocked | ELE-04 at 4, LAY-02 at 4, PIP-02 at 4, ELE-06 at 3 |
| 21 | ICS-06 | Loop diagrams | 4 Final | blocked | ICS-05 at 4, ICS-06 at 3 |
| 21 | ICS-07 | ICS architecture | 4 Final | blocked | ICS-05 at 4, ELE-03 at 4 |
| 21 | ICS-09 | Instrument installation design | 4 Final | blocked | ICS-05 at 4, PIP-02 at 4, VEN-01 at 4, ICS-09 at 3 |
| 21 | PIP-03 | Pipe stress and supports (screening) | 4 Final | blocked | PIP-02 at 4, MEC-01 at 4, PIP-03 at 3 |
| 21 | PIP-04 | Isometrics and piping MTO | 4 Final | blocked | PIP-02 at 4, PIP-01 at 4, PIP-04 at 3 |
| 22 | CIV-01 | Geotechnical, civil and structural design | 4 Final | blocked | LAY-01 at 4, MEC-01 at 4, PIP-03 at 4, CIV-01 at 3 |
| 22 | CON-02 | Work packaging and system boundaries | 4 Final | blocked | CON-01 at 4, PRC-08 at 4, PIP-04 at 4, CON-02 at 3 |
| 22 | PIP-05 | Detailed pipe stress (CAESAR II) | 4 Final | blocked | PIP-03 at 4, VEN-01 at 4, PIP-05 at 3 |
| 22 | PRJ-03 | Document register and portal | 4 Final | blocked | PIP-04 at 4, ICS-06 at 4, ICS-07 at 4, ELE-04 at 4, MEC-03 at 4, LAY-02 at 4, ICS-01 at 4, ICS-03 at 4, ICS-04 at 4, MEC-02 at 4, PIP-03 at 4 |
| 23 | CIV-02 | Foundation and structural steel detailing | 4 Final | blocked | CIV-01 at 4, VEN-01 at 4, PIP-05 at 4, CIV-02 at 3 |
| 23 | LAY-03 | 3D model reviews and constructability | 4 Final | blocked | PIP-02 at 4, LAY-02 at 4, CIV-01 at 4, LAY-03 at 3 |
| 24 | PRJ-04 | PE review, seal and IFC issue | 4 Final | blocked | PRJ-03 at 4, SAF-03 at 4, ICS-08 at 4, PIP-05 at 4, ELE-05 at 4, CST-02 at 4, LAY-03 at 4, SAF-04 at 4, SAF-02 at 4, CIV-02 at 4, ICS-09 at 4, ELE-06 at 4, CON-02 at 4, PRO-01 at 4, PRJ-04 at 3 |

# 8 Consistency check
- none: every gate target is supported by its inputs at the same gate, and the step network has no cycles

# 9 Limits
- Targets are typical values for a refinery process unit and should be agreed with the owner's gate criteria
  (for example CII PDRI or IPA FEL index) before use.
- One level per activity: an activity whose deliverables mature at different rates (for example equipment
  datasheets for long-lead and bulk items) is shown at the level of most of its deliverables.
- "Achieved" is taken from the package status: issued = the FEL 3 target, provisional = the FEL 2 target.
- Construction, commissioning and handover phases are not modelled.
