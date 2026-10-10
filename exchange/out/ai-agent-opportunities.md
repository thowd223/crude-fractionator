# AI agent opportunities

430 of 462 tasks have work an agent could take on. Weighted by recurring effort, agents could take about 25% of the task work, with people keeping every judgement, approval and signature. Scoring is described in `exchange/agents.py`; readiness and shares are assumptions to confirm.

| Rank | Wave | ID | Agent | Does | Tasks | Disciplines | Value | Readiness | Priority | Prerequisite |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | AG-04 | Datasheet drafter | draft, transfer | 57 | 8 | 89 | needs a prerequisite | 67 | Stream-to-line numbering rule; datasheet templates |
| 2 | 1 | AG-06 | Specification and standards assistant | answer, check | 64 | 13 | 64 | ready now | 64 | None |
| 3 | 1 | AG-02 | Vendor document reviewer | review, extract | 56 | 13 | 61 | ready now | 61 | None |
| 4 | 1 | AG-11 | Document control agent | check, monitor | 28 | 13 | 52 | ready now | 52 | Document numbering rule |
| 5 | 1 | AG-18 | Coordination and interface manager | record, monitor | 40 | 11 | 52 | ready now | 52 | None |
| 6 | 2 | AG-12 | Progress and schedule analyst | monitor, draft | 23 | 10 | 45 | ready now | 45 | None |
| 7 | 2 | AG-05 | Requisition and bid evaluation assistant | draft, review | 26 | 9 | 41 | ready now | 41 | Requisition line template |
| 8 | 2 | AG-07 | Design basis and calculation input checker | check, transfer | 44 | 9 | 41 | ready now | 41 | None |
| 9 | 2 | AG-01 | Drawing and P&ID reader | extract | 22 | 11 | 35 | ready now | 35 | None (it feeds the tag crosswalk) |
| 10 | 2 | AG-17 | Completions assistant | draft, check | 31 | 11 | 46 | needs a prerequisite | 34 | Tag crosswalk; system codes on tags |
| 11 | 2 | AG-13 | Estimate and quantity assistant | draft, check | 19 | 7 | 31 | ready now | 31 | None |
| 12 | 2 | AG-03 | Cross-system consistency checker | check | 41 | 7 | 38 | needs a prerequisite | 28 | Tag crosswalk |
| 13 | 3 | AG-08 | Safety study scribe and action tracker | record, monitor | 15 | 7 | 27 | ready now | 27 | None |
| 14 | 3 | AG-10 | Expediting agent | monitor, transfer | 16 | 8 | 29 | needs a prerequisite | 22 | MR/PO to P6 activity code |
| 15 | 3 | AG-16 | RFI, query and field change assistant | answer, draft | 17 | 8 | 22 | ready now | 22 | None |
| 16 | 3 | AG-20 | Model and drawing checker | check, review | 17 | 9 | 21 | needs a prerequisite | 16 | Agreed line list (INT-02) |
| 17 | 3 | AG-19 | Change impact tracer | check, monitor | 10 | 7 | 15 | ready now | 15 | None |
| 18 | 3 | AG-14 | Material reconciliation agent | check, monitor | 16 | 6 | 19 | needs a prerequisite | 14 | Commodity code to purchasing ident map |
| 19 | 3 | AG-09 | Safety instrumented logic drafter | draft, check | 13 | 6 | 16 | needs a prerequisite | 12 | Tag crosswalk; SIF numbering |
| 20 | 3 | AG-15 | Work package builder | draft, check | 7 | 3 | 10 | needs a prerequisite | 8 | CWA/CWP coding on model objects |

## By discipline

| Discipline | Tasks | With an agent | Share of work agents could take |
|---|---|---|---|
| OWNR Owner and operations | 24 | 17 | 8% |
| PROJ Project and controls | 26 | 25 | 36% |
| PROC Process | 48 | 48 | 26% |
| SAFE Process safety and environmental | 36 | 32 | 21% |
| FIRE Fire protection | 6 | 6 | 20% |
| MECH Mechanical | 45 | 45 | 32% |
| PIPE Piping | 45 | 40 | 21% |
| CIVL Civil and structural | 39 | 32 | 14% |
| INST Instrumentation and control | 46 | 46 | 31% |
| ELEC Electrical | 45 | 43 | 26% |
| SCM Procurement and materials | 28 | 27 | 28% |
| VEND Vendors and fabricators | 21 | 17 | 7% |
| CONS Construction | 28 | 27 | 24% |
| COMM Completions and commissioning | 25 | 25 | 28% |

## Agents

### 1. AG-04 Datasheet drafter (wave 1)

Fills process, mechanical, instrument and electrical datasheets from HYSYS cases, SI, the line list and the equipment register, and marks what changed since the last revision.

- **Reads:** HYSYS, SI, SPEL, Excel / Word. **Writes:** draft datasheets
- **Highest autonomy:** 2. **Person:** The engineer checks every datasheet and issues it under their name.
- **Guardrails:** Values it could not source are left blank and flagged, never assumed.
- **Readiness:** needs a prerequisite. Needs HYSYS stream export and datasheet templates.
- **Prerequisite:** Stream-to-line numbering rule; datasheet templates
- **Work:** 57 tasks in CIVL, ELEC, FIRE, INST, MECH, PIPE, PROC, SAFE; 295 manual, review or meeting hand-offs touched; 0 hand-offs no integration removes
  - CIVL-T300 Design building HVAC: Drafts HVAC equipment datasheets from heat load results and room data (draft, share 1, autonomy 2)
  - ELEC-T060 Prepare hazardous area release source list: Fills fluid data from PROC-I285 and gas group and T-class from SAFE-I035 per source (draft, share 1, autonomy 2)
  - ELEC-T090 Develop electrical load list in SPEL: Loads consumer tags, ratings, duty and voltage from MECH, INST, CIVL and vendor lists into SPEL (transfer, share 3, autonomy 2)
  - ELEC-T130 Specify MV switchgear: Fills MV switchgear datasheets with ratings, fault duties and area class from ELEC-I110, ELEC-I220, ELEC-I072 (draft, share 2, autonomy 2)
  - ELEC-T140 Specify power transformers: Fills power transformer datasheets with ratings, fault duties and area class from ELEC-I110, ELEC-I220, ELEC-I072 (draft, share 2, autonomy 2)
  - ELEC-T150 Specify LV switchgear, MCCs and E-houses: Fills LV switchgear, MCC and E-house datasheets with ratings, fault duties and area class from ELEC-I110, ELEC-I220, ELEC-I072 (draft, share 2, autonomy 2)
  - ELEC-T160 Specify VFDs and harmonic mitigation: Fills VFD datasheets with ratings, fault duties and area class from ELEC-I110, ELEC-I220, ELEC-I072 and MECH-I330 (draft, share 2, autonomy 2)
  - ELEC-T170 Specify UPS, DC systems and emergency generator: Fills UPS, DC and generator datasheets with ratings, fault duties and area class from ELEC-I110, ELEC-I220, ELEC-I072 and INST-I280 (draft, share 2, autonomy 2)
  - ELEC-T210 Build ETAP model and run load flow study: Carries SPEL loads and certified transformer data ELEC-I192 into ETAP input tables for approval (transfer, share 1, autonomy 2)
  - ELEC-T260 Perform arc flash study: Drafts equipment labels from approved study results and the OWNR-I060 labeling standard (draft, share 1, autonomy 2)
  - ELEC-T300 Design electric heat tracing: Compiles circuit list and loads from vendor design software output and PROC-I210 tracing requirements (draft, share 1, autonomy 2)
  - FIRE-T230 Prepare fire pump and fire protection equipment datasheets and requisitions: Fills fire pump, driver and skid datasheets from demand calc and NFPA 20 templates; flags unsourced fields (draft, share 2, autonomy 2)
  - INST-T060 Enter instrument process data: Carries HYSYS stream data PROC-I110 and per-tag ranges PROC-I220 into SI process data sheets (transfer, share 3, autonomy 2)
  - INST-T070 Size control valves: Loads flow cases and allowable dP from PROC-I220 and line class into SI sizing inputs, flagging gaps (transfer, share 1, autonomy 2)
  - INST-T080 Size on/off and emergency shutdown valves and actuators: Loads closure times, fail positions and SIF final element requirements from PROC-I235 and INST-I220 into SI (transfer, share 1, autonomy 2)
  - INST-T090 Calculate flow elements and thermowells: Carries flow cases from INST-I060 and pipe ID from PIPE-I160 schedules into SI calculation inputs (transfer, share 1, autonomy 2)
  - INST-T100 Specify relief valves from the process sizing: Fills PSV datasheets from PROC-I250/I251 relief cases: rate, set and back pressure, fluid properties, orifice (draft, share 2, autonomy 2)
  - INST-T110 Prepare instrument datasheets: Fills SI datasheets from process data, valve sizing results, area classification and piping class materials (draft, share 3, autonomy 2)
  - INST-T160 Specify analyzers and analyzer shelters: Drafts analyzer datasheets from PROC-I390 requirements and PROC-I110 stream compositions (draft, share 1, autonomy 2)
  - INST-T250 Rationalize alarms and build master alarm database: Pre-loads the alarm database with INST-I050 tags and PROC-I220 set points before sessions (transfer, share 1, autonomy 2)
  - INST-T260 Develop I/O list and assign I/O: Carries per-motor signals from the SPEL ELEC-I340 export into the SI I/O list for approval (transfer, share 1, autonomy 2)
  - INST-T280 Compile instrument utility loads: Drafts power, UPS and instrument air consumer lists from SI instrument types and locations (draft, share 2, autonomy 2)
  - INST-T300 Prepare hook-up drawings and assign typicals: Assigns each SI tag to a hook-up typical by type, connection and service flags; compiles BOMs (draft, share 2, autonomy 2)
  - INST-T380 Prepare system configuration data for vendors: Exports tags, ranges, alarms and I/O from SI and the alarm database into vendor configuration templates (transfer, share 2, autonomy 2)
  - MECH-T010 Prepare mechanical input to FEL 1 equipment list and configuration screening: Tabulates equipment from each HYSYS screening case into the block-level equipment list template (draft, share 1, autonomy 2)
  - MECH-T030 Select equipment materials and corrosion allowances with Process: Drafts the materials selection table by equipment tag from the corrosion basis and stream data (draft, share 1, autonomy 2)
  - MECH-T040 Define rotating equipment sparing and driver selection: Lists rotating machines with duty, power and sparing basis from the equipment list and sparing philosophy (draft, share 1, autonomy 2)
  - MECH-T060 Maintain mechanical equipment list: Carries updated datasheet and certified vendor attributes into the equipment list for approval (transfer, share 2, autonomy 2)
  - MECH-T070 Perform shell-and-tube exchanger thermal and hydraulic design: Transfers HYSYS stream data and fouling factors into the thermal rating input files (transfer, share 1, autonomy 2)
  - MECH-T080 Perform air-cooled exchanger thermal design: Loads process data and design ambient from the basis into the air cooler rating inputs (transfer, share 1, autonomy 2)
  - MECH-T090 Design and specify fired heaters: Fills the API 560 datasheet from heater design results and process data, flagging unsourced values (draft, share 2, autonomy 2)
  - MECH-T110 Specify column and vessel internals: Drafts internals specification sheets from tray or packing vendor data and vessel calc dimensions (draft, share 1, autonomy 2)
  - MECH-T130 Prepare mechanical datasheets for vessels and columns: Fills vessel and column mechanical datasheets from process datasheets, vessel calcs and nozzle schedules (draft, share 3, autonomy 2)
  - MECH-T140 Prepare mechanical datasheets for exchangers: Fills TEMA and API 661 datasheets from thermal rating outputs and the materials selection table (draft, share 3, autonomy 2)
  - MECH-T150 Prepare rotating equipment datasheets: Fills pump and compressor API datasheets from process datasheets and electrical motor data (draft, share 2, autonomy 2)
  - MECH-T160 Prepare package specifications and scope split: Drafts package utility demand and interface tables from process, I&C and electrical inputs (draft, share 1, autonomy 2)
  - MECH-T170 Select seal, flush and lube oil systems: Drafts the seal plan schedule per pump from rotating datasheets and fluid properties (draft, share 1, autonomy 2)
  - MECH-T190 Prepare nozzle orientations and allowable nozzle loads: Tabulates allowable nozzle loads per nozzle from datasheets and the project nozzle load table (draft, share 1, autonomy 2)
  - MECH-T230 Issue motor and driver electrical data: Carries motor power, voltage, starting method and VFD needs from rotating datasheets to the electrical load list (transfer, share 2, autonomy 2)
  - MECH-T440 Issue as-built equipment data for handover: Updates datasheets and the equipment register with certified as-built vendor values, flagging changes (transfer, share 2, autonomy 2)
  - PIPE-T110 Prepare valve specifications and datasheets: Drafts valve datasheets per valve code from piping classes and process valve requirements (draft, share 2, autonomy 2)
  - PIPE-T120 Prepare specialty item list and datasheets: Drafts specialty item datasheets from process data and piping classes (draft, share 1, autonomy 2)
  - PIPE-T140 Add piping data to the line list: Fills class, test pressure, NDE, PWHT, paint and insulation per line from classes and fabrication specs (transfer, share 3, autonomy 2)
  - PIPE-T190 Issue as-routed line data for hydraulic checks: Carries as-routed lengths, fittings and elevations from S3D reports into process hydraulic check templates (transfer, share 2, autonomy 2)
  - PROC-T030 Run screening simulations and prepare BFDs and screening equipment list: Builds the screening equipment list and BFD tables from each HYSYS case (draft, share 2, autonomy 2)
  - PROC-T110 Prepare heat and material balance: Extracts stream tables per design case from HYSYS into the H&MB template, marking changes since last revision (draft, share 2, autonomy 2)
  - PROC-T160 Prepare equipment list process data: Carries duty, size and design conditions from sizing sheets into equipment list process columns (transfer, share 3, autonomy 2)
  - PROC-T170 Prepare static equipment process datasheets: Fills vessel, column and tank process datasheets from sizing, design conditions and H&MB; flags unsourced fields (draft, share 3, autonomy 2)
  - PROC-T175 Prepare heat transfer equipment process datasheets: Fills exchanger, air cooler and heater process datasheets from duty estimates and H&MB; flags unsourced fields (draft, share 3, autonomy 2)
  - PROC-T180 Prepare rotating equipment process datasheets: Fills pump, compressor and blower process datasheets from duty calcs and stream properties (draft, share 3, autonomy 2)
  - PROC-T185 Prepare package process specifications: Drafts package process specifications from utility basis and consumption lists (draft, share 2, autonomy 2)
  - PROC-T210 Prepare line list and tie-in process data: Populates line list process conditions from H&MB, design conditions and line sizing per SPID line (transfer, share 3, autonomy 2)
  - PROC-T220 Prepare instrument process data: Fills instrument process data per SI tag from the H&MB; flags tags without stream mapping (transfer, share 3, autonomy 2)
  - PROC-T270 Prepare utility, chemical and catalyst consumption lists and balances: Compiles per-consumer utility, chemical and catalyst tables from equipment list, electrical load list and vendor data (draft, share 2, autonomy 2)
  - PROC-T280 Prepare process input to environmental and safety studies: Compiles release-source compositions, inventories and effluent summaries from H&MB and vessel sizing (draft, share 2, autonomy 2)
  - SAFE-T035 Compile hazardous materials inventory and properties: Compiles hazardous material inventories and properties by area from H&MB, vessel sizes and SDS data (draft, share 2, autonomy 2)
  - SAFE-T060 Develop emissions inventory: Compiles source-by-source emission tables from heater datasheets, tank data and fugitive component counts (draft, share 2, autonomy 2)

### 2. AG-06 Specification and standards assistant (wave 1)

Answers questions on project specs, owner standards, codes and the design basis with citations, and checks drafts against them for deviations.

- **Reads:** Document Locator. **Writes:** answers, deviation lists
- **Highest autonomy:** 1. **Person:** The engineer decides; the agent only points to the clause.
- **Guardrails:** Answers only from the indexed project record and cites document, revision and clause.
- **Readiness:** ready now. Needs an index of the spec library only.
- **Prerequisite:** None
- **Work:** 64 tasks in CIVL, COMM, CONS, ELEC, FIRE, INST, MECH, OWNR, PIPE, PROC, PROJ, SAFE, SCM; 368 manual, review or meeting hand-offs touched; 35 hand-offs no integration removes
  - CIVL-T010 Assess candidate sites for civil constraints: Answers site questions from flood maps, surveys and soil reports with citations (answer, share 1, autonomy 1)
  - CIVL-T020 Prepare civil and structural design basis: Cites code editions and owner standards for each civil and structural design criterion (answer, share 1, autonomy 1)
  - CIVL-T260 Define structural fireproofing extent: Cites fireproofing standards and fire scenario envelopes for the members in question (answer, share 1, autonomy 1)
  - CIVL-T270 Develop building space programme and layouts: Cites owner building standards and room size requirements for each building (answer, share 1, autonomy 1)
  - CIVL-T290 Prepare architectural drawings: Checks door, finish and fire rating schedules against owner standards; lists deviations (check, share 1, autonomy 1)
  - COMM-T010 Prepare completions and commissioning execution plan: Checks the draft plan against owner completions requirements and contract definitions of MC, RFSU and handover (check, share 1, autonomy 1)
  - COMM-T050 Define ITR library and ITR matrix by tag type: Cites owner and discipline inspection requirements by tag type for each check sheet (answer, share 1, autonomy 1)
  - COMM-T080 Write pre-commissioning procedures: Answers spec requirements for flushing velocity, leak test media and inerting criteria with citations (answer, share 1, autonomy 1)
  - CONS-T010 Compile constructability input and lessons learned: Searches lessons-learned registers, site and contractor documents and lists cited constructability requirements by area (answer, share 2, autonomy 1)
  - CONS-T020 Prepare site logistics, laydown and temporary facilities plan: Answers site data, owner rules and safety separation distances for laydown planning with cited clauses (answer, share 1, autonomy 1)
  - CONS-T090 Review IFR drawings for constructability: Checks IFR drawings against construction specs and tolerance clauses and lists deviations with citations (check, share 1, autonomy 1)
  - ELEC-T010 Prepare electrical design basis and philosophy: Checks draft basis against OWNR-I060 owner standards and NEC, NFPA 70E, API RP 540 clauses (check, share 1, autonomy 1)
  - ELEC-T130 Specify MV switchgear: Checks the MV switchgear specification against OWNR-I060 owner standards and approved vendors; lists deviations (check, share 1, autonomy 1)
  - ELEC-T140 Specify power transformers: Checks the power transformer specification against OWNR-I060 owner standards and approved vendors; lists deviations (check, share 1, autonomy 1)
  - ELEC-T150 Specify LV switchgear, MCCs and E-houses: Checks the LV switchgear, MCC and E-house specification against OWNR-I060 owner standards and approved vendors; lists deviations (check, share 1, autonomy 1)
  - ELEC-T160 Specify VFDs and harmonic mitigation: Checks the VFD specification against OWNR-I060 owner standards and approved vendors; lists deviations (check, share 1, autonomy 1)
  - ELEC-T170 Specify UPS, DC systems and emergency generator: Checks the UPS, DC and generator specification against OWNR-I060 owner standards and approved vendors; lists deviations (check, share 1, autonomy 1)
  - ELEC-T310 Design cathodic protection: Answers NACE/AMPP and owner CP requirements from the spec library with citations (answer, share 1, autonomy 1)
  - FIRE-T045 Prepare fire protection and F&G philosophy: Checks draft philosophy against SHE basis, owner standards and NFPA clauses; lists gaps (check, share 1, autonomy 1)
  - FIRE-T220 Specify fixed fire protection systems: Cites NFPA and owner requirements by area for deluge, water spray, foam and clean agent (answer, share 1, autonomy 1)
  - INST-T010 Define preliminary control and safety concept: Answers from OWNR-I130/I060 owner automation standards and approved system vendors, citing clauses (answer, share 1, autonomy 1)
  - INST-T030 Develop ICS architecture and control/rack room requirements: Cites OWNR-I130 platform, historian and control room integration standards for the architecture (answer, share 1, autonomy 1)
  - INST-T040 Write I&C design basis and general instrument specifications: Checks draft I&C basis and general specs against OWNR-I060/I180 standards and codes; lists deviations (check, share 2, autonomy 1)
  - INST-T160 Specify analyzers and analyzer shelters: Cites SAFE-I062/I072 permit conditions for CEMS and flare monitoring requirements (answer, share 1, autonomy 1)
  - INST-T170 Write control narratives and functional design specifications: Checks draft narratives against PROC-I230/I240 control philosophy and operating modes; lists gaps (check, share 1, autonomy 1)
  - INST-T180 Prepare DCS specification: Checks the DCS specification against OWNR-I130 standards and INST-I030 architecture; lists deviations (check, share 1, autonomy 1)
  - INST-T190 Prepare SIS specification: Checks the SIS specification against the SRS and owner standards; lists deviations with citations (check, share 1, autonomy 1)
  - INST-T350 Design telecom, CCTV and security systems: Answers from owner telecom standards and SAFE-I370 security assessment with citations (answer, share 1, autonomy 1)
  - MECH-T020 Develop mechanical design basis: Cites owner standards, code editions and design basis clauses for each mechanical design rule (answer, share 1, autonomy 1)
  - MECH-T030 Select equipment materials and corrosion allowances with Process: Cites corrosion basis, owner materials standards and code clauses for each service (answer, share 1, autonomy 1)
  - MECH-T090 Design and specify fired heaters: Checks the heater datasheet against API 560 and the project heater specification; lists deviations (check, share 1, autonomy 1)
  - MECH-T160 Prepare package specifications and scope split: Checks package specifications against owner standards and interface requirements; lists missing clauses (check, share 1, autonomy 1)
  - MECH-T170 Select seal, flush and lube oil systems: Cites API 682, API 614 and owner seal-plan rules for each pump and compressor service (answer, share 1, autonomy 1)
  - MECH-T240 Prepare mechanical technical specifications: Checks draft specifications against owner standards and current code editions; lists deviations and gaps (check, share 1, autonomy 1)
  - OWNR-T040 Issue owner standards and specifications: Indexes received owner standards and answers clause questions from the project team with citations (answer, share 1, autonomy 1)
  - OWNR-T060 Set risk tolerance criteria: Answers project questions on the risk matrix and LOPA target frequencies with citations (answer, share 1, autonomy 1)
  - OWNR-T190 Write operating procedures and train operators: Answers procedure writers' questions from control narratives, C&Es and vendor IOMs with citations (answer, share 1, autonomy 1)
  - PIPE-T010 Prepare block plot plan options: Cites owner spacing standards and siting study distances for each block layout option (answer, share 1, autonomy 1)
  - PIPE-T030 Write piping layout design basis: Cites owner layout standards, spacing tables and constructability rules for each design basis section (answer, share 1, autonomy 1)
  - PIPE-T040 Develop plot plan and equipment layout: Checks plot plan spacing against owner standards and the siting study; lists deviations (check, share 1, autonomy 1)
  - PIPE-T090 Develop piping material classes: Checks piping classes against ASME B31.3, B16.5 ratings and owner standards; lists deviations (check, share 1, autonomy 1)
  - PIPE-T130 Prepare piping fabrication, erection and inspection specifications: Checks fabrication, NDE and testing specifications against ASME B31.3 and owner standards; lists gaps (check, share 1, autonomy 1)
  - PROC-T010 Prepare process design basis: Checks draft basis against owner standards and BOD for missing or conflicting requirements (check, share 1, autonomy 1)
  - PROC-T095 Define process layout requirements: Cites owner layout, spacing and access clauses relevant to each process layout requirement (answer, share 1, autonomy 1)
  - PROC-T135 Define corrosion basis and agree materials selection with Mechanical: Cites owner corrosion standards and NACE/API clauses applicable to the identified corrosive species (answer, share 1, autonomy 1)
  - PROC-T185 Prepare package process specifications: Checks package specifications against owner standards and the design basis (check, share 1, autonomy 1)
  - PROC-T230 Prepare control and operating philosophy and control narratives: Checks control narratives against the control philosophy and owner operating standards, citing clauses (check, share 1, autonomy 1)
  - PROC-T290 Prepare process description and design report: Pulls cited basis, case and decision references from design basis, H&MB and HAZID records (answer, share 1, autonomy 1)
  - PROC-T350 Prepare operating manual process input: Answers drafters' questions from control narratives, trip schedule and vendor manuals with citations (answer, share 1, autonomy 1)
  - PROC-T365 Prepare start-up, shutdown and emergency procedures: Pulls cited limits, trip actions and vendor start-up steps from manuals, C&E and narratives (answer, share 1, autonomy 1)
  - PROJ-T010 Prepare the project execution plan: Checks the draft execution plan against contract and owner procedures and lists missing required sections (check, share 1, autonomy 1)
  - SAFE-T010 Compile environmental baseline and site constraints: Answers from owner site reports and existing permits: receptors, limits and attainment status with citations (answer, share 1, autonomy 1)
  - SAFE-T040 Prepare SHE design basis and risk criteria: Checks draft SHE basis against owner standards and cited codes for missing requirements (check, share 1, autonomy 1)
  - SAFE-T070 Prepare air permit application: Checks the application against regulatory checklist, emissions inventory and datasheets for gaps (check, share 1, autonomy 1)
  - SAFE-T080 Prepare water, stormwater and spill permit data: Cites NPDES, pretreatment and SPCC requirements and pulls tank volumes for containment checks (answer, share 1, autonomy 1)
  - SAFE-T140 Review relief and depressuring scenarios: Lists HAZOP overpressure causes and fire zones without a matching relief scenario, citing documents (check, share 1, autonomy 1)
  - SAFE-T210 Specify emergency isolation valve requirements: Cites owner and API criteria for EIV need against inventory and fire zone data (answer, share 1, autonomy 1)
  - SAFE-T230 Lay out safety equipment and escape routes: Cites code and owner requirements for shower, eyewash, egress and muster distances (answer, share 1, autonomy 1)
  - SAFE-T255 Review hazardous area classification: Checks HAC release sources and gas groups against hazmat inventory and API RP 505 clauses (check, share 1, autonomy 1)
  - SAFE-T300 Prepare RMP hazard assessment and registration data: Checks RMP registration data against hazmat inventory, Part 68 thresholds and requirements (check, share 1, autonomy 1)
  - SAFE-T310 Provide emergency response planning input: Compiles cited scenarios, zones, alarms and muster data from siting, F&G and layout studies (answer, share 1, autonomy 1)
  - SAFE-T320 Prepare construction environmental compliance plan: Extracts permit conditions from issued permits and maps each to a construction requirement with citations (answer, share 2, autonomy 1)
  - SCM-T020 Prepare bidders lists and prequalify vendors: Answers which approved-vendor-list entries cover each package, citing the list revision (answer, share 1, autonomy 1)
  - SCM-T060 Manage bid clarifications and bid bulletins: Answers technical bidder questions already settled by the specs, citing the clause (answer, share 1, autonomy 1)

### 3. AG-02 Vendor document reviewer (wave 1)

Checks vendor drawings, data and calculations against the datasheet, requisition and specifications; drafts review comments and pulls certified values (weights, loads, nozzles, motor data) into registers.

- **Reads:** Document Locator, Purchasing DB. **Writes:** draft comment sheets, staging tables
- **Highest autonomy:** 2. **Person:** The responsible engineer sets the review code and signs the comments.
- **Guardrails:** Comments cite the clause they rely on; it never returns a review code to a vendor itself.
- **Readiness:** ready now. Reads documents only.
- **Prerequisite:** None
- **Work:** 56 tasks in CIVL, COMM, CONS, ELEC, FIRE, INST, MECH, OWNR, PIPE, PROC, SAFE, SCM, VEND; 241 manual, review or meeting hand-offs touched; 27 hand-offs no integration removes
  - CIVL-T030 Specify and manage the topographic survey: Checks survey deliverables against the scope for coverage, grid, benchmarks and format (review, share 1, autonomy 2)
  - CIVL-T050 Set foundation design parameters from the geotechnical report: Extracts borehole logs, SPT/CPT results and lab test values from the geotechnical report into tables (extract, share 2, autonomy 2)
  - CIVL-T320 Review vendor and fabricator drawings: Checks vendor load and anchor data and steel shop drawings against design drawings; drafts comments (review, share 2, autonomy 2)
  - COMM-T080 Write pre-commissioning procedures: Pulls vendor flushing, cleaning, drying and preservation requirements from vendor manuals into a requirement table (extract, share 1, autonomy 2)
  - COMM-T090 Write commissioning and function test procedures: Extracts vendor run-in and function test requirements from vendor manuals into a test requirement table (extract, share 1, autonomy 2)
  - COMM-T100 Define commissioning spares, consumables and first fills: Pulls lubricant, chemical, catalyst, filter and first-fill quantities from vendor data and lists them by system (extract, share 2, autonomy 2)
  - COMM-T110 Define vendor commissioning support requirements: Extracts vendor representative scope and man-day allowances from purchase orders per package (extract, share 1, autonomy 2)
  - COMM-T250 Support performance test run: Extracts guarantee values and test conditions from vendor and licensor data into the comparison table (extract, share 1, autonomy 2)
  - CONS-T040 Prepare heavy lift and crane study: Pulls certified lift weights, centres of gravity and lifting lug data from vendor drawings into the lift register (extract, share 1, autonomy 2)
  - CONS-T190 Survey, set out and verify foundations: Pulls anchor bolt patterns and baseplate dimensions from certified vendor drawings into the setting-out check list (extract, share 1, autonomy 2)
  - ELEC-T080 Size substations and electrical buildings: Pulls switchgear, MCC, VFD and UPS dimensions, weights and heat losses from VEND-I020 (extract, share 1, autonomy 2)
  - ELEC-T190 Review electrical vendor drawings and data: Checks vendor GA, schematics and datasheets against specs; drafts comments; extracts certified impedances and weights (review, share 2, autonomy 2)
  - ELEC-T200 Review motor and package electrical data: Checks MECH-I440 motor datasheets against ELEC-I012 requirements; extracts kW, FLA, LRC and PF (review, share 2, autonomy 2)
  - ELEC-T230 Run motor-starting study: Extracts speed-torque curves, inertia and LRC from MECH-I440 certified motor and driven-equipment data (extract, share 1, autonomy 2)
  - ELEC-T240 Run harmonic analysis: Extracts VFD harmonic spectra and front-end type from VEND-I140 certified data (extract, share 1, autonomy 2)
  - ELEC-T250 Perform protective relay coordination study: Extracts relay models, CT ratios, trip units and fuse curves from VEND-I140 certified documents (extract, share 1, autonomy 2)
  - ELEC-T400 Witness factory acceptance tests: Checks VEND-I150 FAT procedures against specification acceptance criteria and witness points (review, share 1, autonomy 2)
  - FIRE-T240 Review fire protection vendor data: Checks fire pump curves, skid drawings and listings against datasheets and NFPA 20; drafts comments (review, share 2, autonomy 2)
  - INST-T145 Align final relief valve sizing with Process and vendor: Compares vendor final orifice, model and rating VEND-I020 with PROC-I255 acceptance and the TBE (review, share 1, autonomy 2)
  - INST-T150 Review instrument vendor data: Checks instrument vendor drawings against SI datasheets; drafts comments; extracts certified dimensions and weights (review, share 2, autonomy 2)
  - INST-T230 Verify SIL achievement: Extracts failure rates, SFF and SIL capability from VEND-I140 FMEDA reports and SIL certificates (extract, share 1, autonomy 2)
  - INST-T270 Integrate vendor package controls: Reviews package P&IDs, I/O lists and narratives VEND-I100/I110 against I&C requirements; drafts comments (review, share 2, autonomy 2)
  - INST-T280 Compile instrument utility loads: Pulls analyzer, cabinet and panel power from VEND-I120/I020 vendor data (extract, share 1, autonomy 2)
  - MECH-T050 Obtain budget quotations and equipment cost data: Pulls price, weight and delivery from vendor budget quotations into the equipment cost sheet (extract, share 2, autonomy 2)
  - MECH-T200 Prepare equipment outline drawings, footprints and maintenance envelopes: Pulls dimensions, footprints and removal envelopes from vendor outline drawings into the layout table (extract, share 2, autonomy 2)
  - MECH-T210 Compile equipment weights and foundation loads: Pulls empty, operating and test weights and loads from vessel calcs and vendor drawings into the load register (extract, share 3, autonomy 2)
  - MECH-T220 Prepare equipment lifting data: Extracts lifting weights and centres of gravity from vendor lifting drawings into the heavy-lift list (extract, share 1, autonomy 2)
  - MECH-T300 Review vendor drawings and data: Checks vendor drawings and calcs against datasheet and requisition, drafting cited comments; collates discipline comments (review, share 2, autonomy 2)
  - MECH-T310 Release certified vendor data to other disciplines: Pulls certified weights, loads, nozzle and motor data from certified vendor documents into release registers (extract, share 2, autonomy 2)
  - MECH-T340 Review rotordynamic, torsional and pulsation studies: Checks vendor rotordynamic and pulsation reports against API acceptance criteria and drafts cited comments (review, share 1, autonomy 2)
  - MECH-T350 Review and approve inspection and test plans: Checks vendor ITPs against specification test and NDE requirements; drafts comments on missing points (review, share 2, autonomy 2)
  - MECH-T360 Witness shop tests and factory acceptance tests: Checks FAT and shop test records against ITP acceptance criteria and drafts the test report punch (review, share 1, autonomy 2)
  - MECH-T370 Review spare parts recommendations: Checks vendor spare parts lists for completeness and drafts interchangeability tables per owner spares policy (review, share 2, autonomy 2)
  - MECH-T380 Review manufacturer's data books: Checks data books against VDRL and specifications for missing certificates, code stamps and manuals (review, share 3, autonomy 2)
  - MECH-T390 Define equipment preservation and storage requirements: Extracts storage and preservation requirements from vendor manuals into the equipment preservation schedule (extract, share 2, autonomy 2)
  - OWNR-T160 Define spare parts philosophy and approve spares: Consolidates vendor SPIRs into a spares list grouped by philosophy category for owner selection (extract, share 1, autonomy 2)
  - PIPE-T240 Specify and requisition spring and engineered supports: Checks vendor spring hanger data against datasheet loads and travel; drafts comments (review, share 1, autonomy 2)
  - PIPE-T310 Incorporate vendor data and manage piping holds: Pulls certified nozzle sizes, ratings and positions from vendor drawings for model update (extract, share 1, autonomy 2)
  - PIPE-T360 Review valve and specialty item vendor data: Checks valve vendor drawings, test certificates and data books against datasheets; drafts comments (review, share 2, autonomy 2)
  - PROC-T255 Review vendor relief valve sizing: Checks vendor orifice, rated capacity and back-pressure limits against each relief case; drafts comments (review, share 2, autonomy 2)
  - PROC-T310 Review vendor data against process duties: Checks vendor drawings and performance data against process datasheets; drafts comments citing datasheet fields (review, share 2, autonomy 2)
  - PROC-T315 Reconcile simulation with certified vendor data: Extracts certified performance curves and data from vendor documents into simulation input tables (extract, share 1, autonomy 2)
  - SAFE-T240 Perform noise study: Extracts vendor sound power and pressure data into the noise model input table (extract, share 1, autonomy 2)
  - SAFE-T270 Review vendor packages and bids for SHE compliance: Checks vendor bids and data for noise, emission guarantees, fire-safe valves and safety devices; drafts comments (review, share 2, autonomy 2)
  - SCM-T150 Coordinate inspection and test plans: Reviews vendor ITPs against requisition inspection requirements and drafts comments with proposed hold points (review, share 2, autonomy 2)
  - SCM-T160 Carry out shop inspection and release: Checks certificates and MTRs against specification and PO requirements before release (review, share 1, autonomy 2)
  - SCM-T170 Prepare the logistics plan: Extracts shipping dimensions and weights from certified vendor drawings into the oversize move list (extract, share 1, autonomy 2)
  - SCM-T200 Receive materials at site in Jovix: Extracts heat numbers from MTRs and packing lists into staging for Jovix (extract, share 1, autonomy 2)
  - SCM-T270 Procure commissioning and operating spares: Extracts vendor SPIR lines into a consolidated spares list for owner selection (extract, share 2, autonomy 2)
  - VEND-T050 Prepare GA and outline drawings for review: Checks received GAs against datasheet nozzles, weights and loads and drafts review comments (review, share 1, autonomy 2)
  - VEND-T060 Prepare vendor design calculations: Checks design conditions, materials and allowances in vendor calcs against the datasheet and drafts comments (review, share 1, autonomy 2)
  - VEND-T080 Prepare package electrical data: Pulls motor ratings and electrical loads from vendor datasheets into load list staging tables (extract, share 1, autonomy 2)
  - VEND-T090 Incorporate comments and issue certified final data: Checks the certified issue incorporates every prior review comment and flags unresolved ones (review, share 1, autonomy 2)
  - VEND-T110 Procure raw materials and issue MTRs: Extracts heat numbers, grades and test values from MTRs and flags values outside specification (extract, share 1, autonomy 2)
  - VEND-T170 Prepare nameplate and as-built data: Extracts nameplate data, serial numbers and as-built weights into asset data staging tables (extract, share 1, autonomy 2)
  - VEND-T190 Prepare IOM manuals and spare parts lists: Extracts SPIR spare parts and interchangeability data into staging for spares processing (extract, share 1, autonomy 2)

### 4. AG-11 Document control agent (wave 1)

Checks transmittals, numbering, title blocks and revision status, keeps the deliverables register in step with P6 and Document Locator, and lists overdue reviews.

- **Reads:** Document Locator, P6. **Writes:** register updates, overdue lists
- **Highest autonomy:** 3. **Person:** Document control approves register changes.
- **Guardrails:** Never issues or supersedes a document.
- **Readiness:** ready now. Document Locator metadata and P6 exports.
- **Prerequisite:** Document numbering rule
- **Work:** 28 tasks in CIVL, COMM, CONS, ELEC, INST, MECH, OWNR, PIPE, PROC, PROJ, SAFE, SCM, VEND; 169 manual, review or meeting hand-offs touched; 11 hand-offs no integration removes
  - CIVL-T005 Plan, measure and report discipline deliverables: Keeps the civil deliverables register in step with P6 and Document Locator; lists overdue reviews (monitor, share 1, autonomy 3)
  - CIVL-T350 Check, seal and issue civil and structural IFC packages: Checks IFC package contents, numbering, title blocks and revisions against the register before sealing (check, share 1, autonomy 2)
  - COMM-T220 Compile system turnover packages: Checks as-built and vendor document revisions in the dossier against Document Locator status (check, share 1, autonomy 3)
  - CONS-T090 Review IFR drawings for constructability: Lists IFR drawings due for construction review and flags comments overdue against review deadlines (monitor, share 1, autonomy 3)
  - CONS-T260 Prepare as-built redlines: Checks redline transmittals cite correct drawing numbers and IFC revisions (check, share 1, autonomy 3)
  - ELEC-T005 Plan, measure and report discipline deliverables: Keeps the electrical deliverables list in step with the PROJ-I060 register and Document Locator revisions (check, share 1, autonomy 3)
  - ELEC-T390 Seal and issue electrical deliverables IFC: Checks title blocks, numbering and revisions of the IFC package against the PROJ-I060 register (check, share 1, autonomy 3)
  - INST-T005 Plan, measure and report discipline deliverables: Keeps the I&C deliverables list in step with the PROJ-I060 register and Document Locator revisions (check, share 1, autonomy 3)
  - MECH-T005 Plan, measure and report discipline deliverables: Keeps the mechanical deliverables register in step with P6 and Document Locator; lists overdue reviews (monitor, share 1, autonomy 3)
  - MECH-T250 Prepare requisition technical packages for bid: Checks every referenced document revision in the requisition is current in Document Locator (check, share 1, autonomy 3)
  - OWNR-T090 Review and comment on deliverables: Tracks owner review due dates, lists overdue comment sheets and chases returns (monitor, share 1, autonomy 3)
  - OWNR-T230 Accept final documentation: Checks handover documents and data books against the handover specification index before submission (check, share 1, autonomy 2)
  - PIPE-T005 Plan, measure and report discipline deliverables: Keeps the piping deliverables register in step with P6 and Document Locator; lists overdue reviews (monitor, share 1, autonomy 3)
  - PROC-T005 Plan, measure and report discipline deliverables: Keeps process deliverables register in step with P6 and Document Locator; lists overdue and held documents (monitor, share 2, autonomy 3)
  - PROC-T340 Update P&IDs to IFD and IFC: Checks revision status, title blocks and transmittals of the P&ID issue set (check, share 1, autonomy 3)
  - PROJ-T040 Set up document numbering and the Document Locator project: Checks Document Locator folders, type codes and workflows against the issued numbering procedure, listing mismatches (check, share 1, autonomy 2)
  - PROJ-T050 Compile and maintain the deliverables register: Collects discipline deliverables lists, checks numbers against the rule, keeps planned and actual dates in step with P6 (monitor, share 3, autonomy 3)
  - PROJ-T130 Measure engineering progress: Checks document statuses claimed for credit against issued revisions in Document Locator (check, share 1, autonomy 3)
  - PROJ-T170 Prepare gate review packages and record gate decisions: Checks every gate deliverable is issued at the required revision and lists gaps in the package (check, share 2, autonomy 2)
  - PROJ-T200 Issue documents by transmittal: Checks numbering, title block and metadata on each issue and builds transmittals from the distribution matrix (check, share 3, autonomy 3)
  - PROJ-T210 Run review cycles and consolidate comments: Routes documents per the review matrix, consolidates comment sheets, lists overdue reviews and chases reviewers (monitor, share 2, autonomy 3)
  - PROJ-T230 Track IFC issue and PE seal status: Checks each IFC document shows checked, approved and sealed status in Document Locator before release (check, share 2, autonomy 2)
  - PROJ-T260 Compile the final records and close out: Checks the final records index against the deliverables register and lists missing as-builts (check, share 2, autonomy 2)
  - SAFE-T290 Compile process safety information for PSM: Confirms each PSI document is the current issued revision in Document Locator (check, share 1, autonomy 2)
  - SCM-T120 Set up VDRL tracking: Checks VDRL document numbers against the project numbering rule (check, share 1, autonomy 3)
  - SCM-T130 Expedite vendor documents and route them for review: Lists vendor documents overdue in engineering review and reminds reviewers (monitor, share 1, autonomy 3)
  - SCM-T280 Close out purchase orders: Checks final documents and MDR received against the VDRL and lists gaps blocking closure (check, share 2, autonomy 2)
  - VEND-T040 Issue the vendor document schedule: Checks the vendor document schedule against the VDRL for missing documents, numbers and dates (check, share 1, autonomy 3)

### 5. AG-18 Coordination and interface manager (wave 1)

Records coordination meetings, model reviews and interface queries; tracks actions and inter-discipline holds; reminds owners before need dates.

- **Reads:** meeting notes, Document Locator, P6. **Writes:** minutes, action and hold lists
- **Highest autonomy:** 3. **Person:** Chairs approve minutes; owners close their actions.
- **Guardrails:** Records decisions, never makes them.
- **Readiness:** ready now. Meeting notes and transcripts only.
- **Prerequisite:** None
- **Work:** 40 tasks in CIVL, COMM, CONS, ELEC, INST, MECH, OWNR, PIPE, PROC, PROJ, SAFE; 196 manual, review or meeting hand-offs touched; 0 hand-offs no integration removes
  - CIVL-T070 Review plot plan for civil constraints: Logs civil comments per plot plan revision and tracks their incorporation (record, share 1, autonomy 3)
  - CIVL-T140 Coordinate underground services and prepare composite: Tracks underground conflicts found in the composite by owner until each is resolved (monitor, share 1, autonomy 3)
  - CIVL-T250 Coordinate embedments, sleeves and penetrations: Collects embedment and penetration requests from disciplines into one schedule; chases missing ones (monitor, share 2, autonomy 3)
  - CIVL-T330 Take part in 3D model reviews and clash resolution: Records structural review actions and clash assignments and tracks them to close (record, share 1, autonomy 3)
  - COMM-T140 Raise and manage punch lists: Reminds action-by parties of open punch items ahead of subsystem need dates (monitor, share 1, autonomy 3)
  - COMM-T230 Hand over systems to the owner: Records handover meetings, agreed punch exceptions and owner actions and tracks them to closure (record, share 1, autonomy 2)
  - CONS-T080 Review 3D model for constructability (30/60/90 % reviews): Records 30/60/90 % review comments and actions by area and tracks them to close-out (record, share 1, autonomy 3)
  - CONS-T160 Manage IWP constraints and release IWPs: Chases constraint owners before IWP need dates and logs constraint status changes (monitor, share 1, autonomy 3)
  - ELEC-T030 Coordinate utility interconnect and power supply: Records utility meetings and tracks interconnection application actions and dates (record, share 1, autonomy 2)
  - ELEC-T180 Evaluate electrical bids technically: Records clarification meetings and tracks open vendor clarifications (record, share 1, autonomy 2)
  - ELEC-T330 Route raceway, cable tray and duct banks in S3D: Records model review actions on electrical raceway and tracks closure (record, share 1, autonomy 3)
  - ELEC-T390 Seal and issue electrical deliverables IFC: Lists open OWNR-I110 comments, PIPE-I350 model actions and PIPE-I360 clashes before IFC (monitor, share 1, autonomy 2)
  - ELEC-T400 Witness factory acceptance tests: Records switchgear, MCC, VFD and UPS FAT punch and tracks it to closure (record, share 1, autonomy 2)
  - INST-T250 Rationalize alarms and build master alarm database: Records rationalization session outcomes: set points, priorities, consequences and open actions (record, share 2, autonomy 2)
  - INST-T290 Prepare instrument location plans and JB locations: Records I&C model review comments and tracks them to close-out (record, share 1, autonomy 3)
  - INST-T390 Review configuration and witness system FAT: Records FAT punch items and tracks them to closure (record, share 1, autonomy 2)
  - MECH-T290 Hold vendor kick-off meetings: Records kick-off minutes, open holds and data schedule commitments; tracks actions to close (record, share 2, autonomy 3)
  - MECH-T320 Close requisition holds: Tracks requisition and vendor data holds, reminds owners and flags holds blocking vendor dates (monitor, share 2, autonomy 3)
  - MECH-T400 Review 3D model for equipment access and maintenance: Records equipment access findings from model reviews and tracks them to close (record, share 1, autonomy 3)
  - MECH-T420 Coordinate vendor site representatives: Tracks vendor representative requests, dates and attendance against the construction schedule; reminds owners (monitor, share 2, autonomy 3)
  - OWNR-T080 Act as permit applicant: Tracks permit conditions passed back by the owner as actions on the owning disciplines (monitor, share 1, autonomy 2)
  - OWNR-T100 Provide operations and maintenance input: Records O&M requirements from workshops and tracks each to the owning discipline (record, share 1, autonomy 2)
  - OWNR-T120 Review the 3D model for operability and maintenance: Records model review comments by location and tracks each to the owning discipline's close-out (record, share 2, autonomy 2)
  - OWNR-T140 Provide tie-in and outage windows: Records agreed outage windows and reminds tie-in owners before cut-off dates (monitor, share 1, autonomy 2)
  - PIPE-T040 Develop plot plan and equipment layout: Records plot plan review comments and tracks each action to close (record, share 1, autonomy 3)
  - PIPE-T230 Resolve nozzle loads with mechanical and vendors: Tracks each exceeded nozzle load to agreement with mechanical and the vendor (monitor, share 1, autonomy 3)
  - PIPE-T260 Request civil and structural openings, platforms and foundations: Tracks piping requests for platforms, sleepers and penetrations until civil incorporates them (monitor, share 1, autonomy 3)
  - PIPE-T280 Run 30/60/90 model reviews: Records 30/60/90 review comments by area and owner and tracks each action to close-out (record, share 2, autonomy 3)
  - PIPE-T290 Detect and resolve clashes: Tracks clash assignments by owner and reports open clashes by area before each issue (monitor, share 1, autonomy 3)
  - PIPE-T310 Incorporate vendor data and manage piping holds: Maintains the piping hold list, reminding owners and flagging holds blocking isometric issue (monitor, share 2, autonomy 3)
  - PROC-T080 Prepare process input to select decision: Records the alternatives ranking workshop, scores and rationale; tracks follow-up actions (record, share 1, autonomy 2)
  - PROC-T375 Support commissioning, start-up and performance test: Records commissioning and performance test meetings; tracks process punch items and actions (record, share 1, autonomy 2)
  - PROJ-T070 Issue estimate quantity requests to disciplines: Sends QTO templates, basis and due dates to each discipline, tracks returns and chases late ones (monitor, share 3, autonomy 3)
  - PROJ-T160 Run change control: trends and change notices: Logs trends and change notices, tracks their approval status and reminds owners of open items (monitor, share 1, autonomy 3)
  - PROJ-T170 Prepare gate review packages and record gate decisions: Records gate decisions and conditions and tracks each condition to close-out (record, share 1, autonomy 2)
  - PROJ-T180 Maintain the risk register and contingency analysis: Records workshop risks and mitigations into the register and tracks mitigation actions with their owners (record, share 2, autonomy 2)
  - PROJ-T190 Run interface management: Keeps the interface register, reminds owners before need dates and chases interface agreements to closure (monitor, share 3, autonomy 3)
  - PROJ-T220 Maintain the hold list: Tracks each hold by cause, owner and target date, reminds owners and reports overdue releases (monitor, share 3, autonomy 3)
  - SAFE-T250 Review plot plan and 3D model for safety: Records safety model review comments and tracks them to close-out (record, share 1, autonomy 2)
  - SAFE-T350 Set up environmental startup compliance: Tracks startup notification, performance test and CEMS certification deadlines against permit conditions (monitor, share 1, autonomy 2)

### 6. AG-12 Progress and schedule analyst (wave 2)

Compiles progress from document status, quantities and installed counts, drafts the period report narrative and flags critical-path and need-date risks.

- **Reads:** P6, Document Locator, Purchasing DB, iConstruct, Smart Completions. **Writes:** draft progress reports
- **Highest autonomy:** 2. **Person:** Project controls validates and issues.
- **Guardrails:** Shows the source of every figure.
- **Readiness:** ready now. Exports only.
- **Prerequisite:** None
- **Work:** 23 tasks in CIVL, COMM, CONS, ELEC, INST, MECH, PIPE, PROC, PROJ, SCM; 89 manual, review or meeting hand-offs touched; 0 hand-offs no integration removes
  - CIVL-T005 Plan, measure and report discipline deliverables: Compiles civil deliverable progress from Document Locator status and P6; flags late deliverables and holds (monitor, share 2, autonomy 2)
  - COMM-T040 Set commissioning sequence and required subsystem turnover dates: Drafts the required turnover date table per subsystem and flags clashes with the construction path (draft, share 1, autonomy 2)
  - COMM-T130 Track test pack status by subsystem: Tracks test pack prepared, tested and reinstated status per subsystem and forecasts MC dates (monitor, share 3, autonomy 2)
  - COMM-T170 Execute loop checks: Reports loop check status and open defects by subsystem against the commissioning schedule (monitor, share 1, autonomy 2)
  - COMM-T240 Report completions progress: Compiles ITR, punch and certificate counts by system from Smart Completions and drafts the report narrative (draft, share 3, autonomy 2)
  - CONS-T050 Define path of construction: Drafts area sequence tables from the commissioning system order and plot plan areas for planner review (draft, share 1, autonomy 1)
  - CONS-T110 Develop construction schedule by CWP: Drafts CWP activity list tied to EWP and material delivery dates and flags need-date conflicts (draft, share 2, autonomy 2)
  - CONS-T120 Align EWPs and procurement packages to CWPs: Maps EWP and PO forecast dates to CWP need dates and lists every package that misses (monitor, share 3, autonomy 2)
  - CONS-T210 Track installed quantities and progress: Rolls daily installed quantities from IWP up to CWP and schedule and flags variance against plan (monitor, share 2, autonomy 2)
  - ELEC-T005 Plan, measure and report discipline deliverables: Compiles electrical deliverable progress from Document Locator status against PROJ-I140 planned dates; flags holds (monitor, share 2, autonomy 2)
  - INST-T005 Plan, measure and report discipline deliverables: Compiles I&C deliverable progress from Document Locator status against PROJ-I140 planned dates; flags holds (monitor, share 2, autonomy 2)
  - MECH-T005 Plan, measure and report discipline deliverables: Compiles mechanical deliverable progress from Document Locator status and P6; flags late deliverables and holds (monitor, share 2, autonomy 2)
  - PIPE-T005 Plan, measure and report discipline deliverables: Compiles piping deliverable progress from Document Locator status and P6; flags late deliverables and holds (monitor, share 2, autonomy 2)
  - PROC-T005 Plan, measure and report discipline deliverables: Computes earned progress by rules of credit from document status and drafts the period report narrative (draft, share 2, autonomy 2)
  - PROJ-T030 Set up the WBS, cost codes and P6 project structure: Drafts P6 activity code and cost code dictionaries from the approved WBS and area codes (draft, share 1, autonomy 2)
  - PROJ-T110 Build and baseline the integrated schedule in P6: Drafts engineering and procurement activity lists from the deliverables register and procurement plan for planner review (draft, share 1, autonomy 2)
  - PROJ-T120 Integrate procurement and vendor dates into the schedule: Flags vendor forecast dates that erode float or pass need dates on the critical path (monitor, share 1, autonomy 2)
  - PROJ-T130 Measure engineering progress: Computes deliverable progress by rules of credit from Document Locator status and drafts the earned value update (monitor, share 3, autonomy 2)
  - PROJ-T140 Update the schedule and analyse the critical path: Runs float and critical path comparison against last period and drafts the look-ahead and slippage list (monitor, share 2, autonomy 2)
  - PROJ-T150 Track cost and forecast at completion: Drafts cost report tables and narrative from commitment and actuals exports, citing the source of each figure (draft, share 1, autonomy 2)
  - PROJ-T240 Prepare monthly progress reports: Compiles progress, cost, schedule, change, procurement and HSE figures into the draft report with sourced narrative (draft, share 3, autonomy 2)
  - PROJ-T250 Load construction progress into P6: Compiles installed quantities and IWP completion from iConstruct into a P6 progress update for approval (draft, share 2, autonomy 2)
  - SCM-T010 Prepare the procurement plan and long-lead list: Drafts package need dates from P6 and flags items whose delivery durations make them long-lead (draft, share 1, autonomy 2)

### 7. AG-05 Requisition and bid evaluation assistant (wave 2)

Assembles requisition packages from datasheets and specs, compares vendor technical bids clause by clause, drafts TBE tables, clarifications and deviation lists.

- **Reads:** Document Locator, Purchasing DB, Excel / Word. **Writes:** draft MRs, draft TBEs
- **Highest autonomy:** 2. **Person:** The engineer recommends; Procurement awards.
- **Guardrails:** No commercial data in technical evaluations; never ranks bidders on its own.
- **Readiness:** ready now. Documents only.
- **Prerequisite:** Requisition line template
- **Work:** 26 tasks in CIVL, ELEC, FIRE, INST, MECH, PIPE, PROC, SCM, VEND; 154 manual, review or meeting hand-offs touched; 1 hand-offs no integration removes
  - CIVL-T040 Specify the geotechnical investigation: Drafts the geotechnical contractor scope from the borehole location plan and test schedule (draft, share 1, autonomy 2)
  - CIVL-T310 Prepare civil and structural requisitions and bid evaluations: Assembles civil, steel and HVAC technical scopes; drafts TBE tables comparing bids clause by clause (draft, share 2, autonomy 2)
  - ELEC-T130 Specify MV switchgear: Assembles the MV switchgear requisition package from datasheets, specification and VDRL (draft, share 1, autonomy 2)
  - ELEC-T140 Specify power transformers: Assembles the power transformer requisition package from datasheets, specification and VDRL (draft, share 1, autonomy 2)
  - ELEC-T150 Specify LV switchgear, MCCs and E-houses: Assembles the LV switchgear, MCC and E-house requisition package from datasheets, specification and VDRL (draft, share 1, autonomy 2)
  - ELEC-T160 Specify VFDs and harmonic mitigation: Assembles the VFD requisition package from datasheets, specification and VDRL (draft, share 1, autonomy 2)
  - ELEC-T170 Specify UPS, DC systems and emergency generator: Assembles the UPS, DC and generator requisition package from datasheets, specification and VDRL (draft, share 1, autonomy 2)
  - ELEC-T180 Evaluate electrical bids technically: Compares electrical offers with ELEC-I130 to I170 requirements; drafts TBE tables and deviation lists (review, share 2, autonomy 2)
  - FIRE-T230 Prepare fire pump and fire protection equipment datasheets and requisitions: Assembles fire protection requisition packages from datasheets and specifications (draft, share 2, autonomy 2)
  - INST-T130 Prepare instrument material requisitions: Assembles instrument MRs with SI and PSV datasheets, PROJ-I370 VDRL template and SCM-I030 bidder list (draft, share 2, autonomy 2)
  - INST-T140 Evaluate instrument bids technically: Compares vendor offers with MR datasheets clause by clause; drafts TBE tables, clarifications and deviations (review, share 2, autonomy 2)
  - MECH-T050 Obtain budget quotations and equipment cost data: Assembles budget enquiry packages from preliminary datasheets and the equipment list (draft, share 1, autonomy 2)
  - MECH-T250 Prepare requisition technical packages for bid: Assembles requisitions from datasheets, specifications, VDRL and scope; lists open holds per requisition (draft, share 3, autonomy 2)
  - MECH-T260 Issue technical queries and clarifications to bidders: Compares bids clause by clause with the requisition; drafts technical queries and deviation lists (review, share 2, autonomy 2)
  - MECH-T270 Prepare technical bid evaluations: Drafts TBE tables from clarified offers and TQ responses, collating other disciplines' comments (draft, share 2, autonomy 2)
  - MECH-T280 Prepare requisitions for purchase: Carries agreed TQ answers and accepted deviations from the clarified offer into the purchase requisition (draft, share 2, autonomy 2)
  - PIPE-T240 Specify and requisition spring and engineered supports: Assembles the spring hanger requisition from CAESAR II support data and drafts the TBE (draft, share 2, autonomy 2)
  - PIPE-T340 Produce MTO by ident and bulk requisitions: Assembles bulk requisitions from the net MTO and valve and specialty datasheets (draft, share 1, autonomy 2)
  - PIPE-T350 Evaluate piping bids: Compares bulk material and valve offers line by line with requisitions and drafts the TBE (review, share 2, autonomy 2)
  - PROC-T070 Evaluate technology and licensor process offers: Tabulates licensor offers on yields, utilities, catalyst and guarantees; drafts clarification questions (review, share 2, autonomy 2)
  - PROC-T305 Process input to technical bid evaluations: Compares vendor offers clause by clause with process datasheets; drafts deviation list and clarifications (review, share 2, autonomy 2)
  - SCM-T050 Issue RFQ packages: Assembles the RFQ package from the technical MR and standard terms and checks the attachment list (draft, share 2, autonomy 2)
  - SCM-T060 Manage bid clarifications and bid bulletins: Logs bidder questions and drafts bid bulletins from the engineers' answers (draft, share 2, autonomy 2)
  - SCM-T070 Receive bids and distribute technical portions: Builds the unpriced technical bid folder per bidder for TBE distribution (draft, share 1, autonomy 1)
  - SCM-T090 Prepare the bid tabulation and award recommendation: Compiles TBE results and deviation lists into the technical section of the bid tabulation (draft, share 1, autonomy 1)
  - VEND-T030 Answer bid clarifications: Checks vendor clarification responses against open TBE queries and lists unresolved items (review, share 1, autonomy 2)

### 8. AG-07 Design basis and calculation input checker (wave 2)

Holds the current design basis values (site data, criteria, cases), feeds them into calculations and flags calculations built on a superseded basis revision.

- **Reads:** Document Locator, Excel / Word, Mechanical calc tool. **Writes:** basis parameter table, calc input flags
- **Highest autonomy:** 3. **Person:** The calc originator and checker accept the inputs.
- **Guardrails:** Basis values change only through the owning discipline.
- **Readiness:** ready now. Documents and workbooks only.
- **Prerequisite:** None
- **Work:** 44 tasks in CIVL, ELEC, FIRE, INST, MECH, OWNR, PIPE, PROC, SAFE; 217 manual, review or meeting hand-offs touched; 41 hand-offs no integration removes
  - CIVL-T020 Prepare civil and structural design basis: Collects site wind, seismic, temperature and rainfall data from owner documents into the basis table (transfer, share 1, autonomy 3)
  - CIVL-T150 Design static equipment foundations: Checks foundation calcs use current certified vendor loads and soil parameters; flags superseded inputs (check, share 1, autonomy 2)
  - CIVL-T160 Design rotating equipment foundations with dynamic analysis: Checks dynamic foundation calcs use current certified machine data and soil parameters (check, share 1, autonomy 2)
  - CIVL-T170 Design tank foundations: Checks tank foundation calcs use current tank loads and soil parameters; flags superseded inputs (check, share 1, autonomy 2)
  - CIVL-T180 Design piles and prepare piling layout: Checks pile designs use current foundation loads and geotechnical parameters (check, share 1, autonomy 2)
  - CIVL-T200 Analyse and design pipe racks: Checks rack analysis loads against current piping, cable and air cooler load data (check, share 1, autonomy 2)
  - CIVL-T210 Analyse and design process structures and platforms: Checks structure analysis loads against current equipment, piping and cable load data (check, share 1, autonomy 2)
  - CIVL-T280 Design blast-resistant and other buildings structurally: Checks building designs use current blast overpressure and wind/seismic basis values (check, share 1, autonomy 2)
  - ELEC-T010 Prepare electrical design basis and philosophy: Carries ambient, wind and seismic data from CIVL-I030 into basis tables (transfer, share 1, autonomy 2)
  - ELEC-T110 Size major electrical equipment: Flags sizing calculations built on a superseded load list or study revision (check, share 1, autonomy 3)
  - ELEC-T210 Build ETAP model and run load flow study: Flags study runs on a superseded load list or one-line revision (check, share 1, autonomy 3)
  - ELEC-T220 Run short-circuit study: Flags short-circuit runs using superseded or uncertified impedances (check, share 1, autonomy 3)
  - ELEC-T260 Perform arc flash study: Flags arc flash results based on superseded settings or fault currents (check, share 1, autonomy 2)
  - ELEC-T270 Design grounding system: Checks the ground grid study uses current CIVL-I390 soil resistivity and ELEC-I220 fault data (check, share 1, autonomy 3)
  - FIRE-T190 Calculate fire water demand: Checks demand calc inputs (fire zones, areas, rates) against current fire envelopes and NFPA 15 (check, share 1, autonomy 2)
  - INST-T040 Write I&C design basis and general instrument specifications: Carries ambient data from CIVL-I030 and area classification method from ELEC-I010 into basis tables (transfer, share 1, autonomy 2)
  - INST-T070 Size control valves: Flags control valve calculations built on superseded process data or line class revisions (check, share 1, autonomy 3)
  - INST-T080 Size on/off and emergency shutdown valves and actuators: Flags ESD valve sizing based on superseded trip, EIV or SIF requirement revisions (check, share 1, autonomy 2)
  - INST-T090 Calculate flow elements and thermowells: Flags flow element and thermowell calculations on superseded process or line data (check, share 1, autonomy 3)
  - MECH-T020 Develop mechanical design basis: Carries current site data and safety basis values into the mechanical design basis tables (transfer, share 1, autonomy 2)
  - MECH-T070 Perform shell-and-tube exchanger thermal and hydraulic design: Flags exchanger ratings built on superseded process data or design basis revisions (check, share 1, autonomy 3)
  - MECH-T080 Perform air-cooled exchanger thermal design: Checks air cooler designs use the current design ambient temperature and site elevation (check, share 1, autonomy 3)
  - MECH-T100 Perform vessel and column mechanical design calculations: Feeds design conditions, corrosion allowance and site wind/seismic data into vessel calcs; flags superseded inputs (check, share 1, autonomy 2)
  - MECH-T120 Design storage tanks: Feeds basis wind, seismic, soil and fire-case data into tank calcs; flags superseded inputs (check, share 1, autonomy 2)
  - OWNR-T020 Supply crude assays and feed cases: Loads received assay and feed case data into the design basis parameter table for process review (transfer, share 1, autonomy 2)
  - OWNR-T030 Supply site and existing facility data: Loads received climatic and survey values into the basis parameter table (transfer, share 1, autonomy 2)
  - OWNR-T050 Define owner design basis requirements: Carries owner design life, margins and utility conditions into the basis parameter table (transfer, share 1, autonomy 2)
  - PIPE-T220 Perform detailed stress analysis in CAESAR II: Checks CAESAR II inputs (design conditions, wind, seismic) against the line list and design basis (check, share 1, autonomy 2)
  - PROC-T010 Prepare process design basis: Compiles owner feed, product, ambient and battery-limit data into the basis parameter table with sources (transfer, share 2, autonomy 2)
  - PROC-T020 Characterise feed and set up assay in simulation: Transfers owner assay cuts and contaminant data into a sourced input table for the simulation (transfer, share 1, autonomy 2)
  - PROC-T060 Develop and simulate FEL2 alternatives: Checks each alternative's simulation uses the current basis feed, ambient and turndown cases (check, share 1, autonomy 2)
  - PROC-T090 Define utility and offsite basis: Checks utility supply conditions against owner site data and electrical inputs; flags superseded values (check, share 1, autonomy 2)
  - PROC-T100 Build and calibrate rigorous simulation: Compares model inputs with licensor and plant test data tables; flags mismatched or superseded values (check, share 1, autonomy 2)
  - PROC-T130 Set design pressures and temperatures: Flags design conditions built on superseded H&MB, pump shut-off or owner margin values (check, share 1, autonomy 2)
  - PROC-T140 Size vessels and columns: Feeds current H&MB flows and properties into vessel sizing workbooks; flags stale inputs (transfer, share 1, autonomy 2)
  - PROC-T150 Define rotating equipment process duties: Feeds H&MB flows and piping elevations into pump and compressor hydraulics sheets; flags superseded inputs (transfer, share 1, autonomy 2)
  - PROC-T155 Estimate exchanger duties and preliminary areas: Feeds H&MB stream data and design conditions into exchanger screening sheets; flags superseded inputs (transfer, share 1, autonomy 2)
  - PROC-T190 Size lines and run hydraulics: Loads H&MB stream data into the line sizing workbook; flags lines sized on superseded cases (transfer, share 1, autonomy 2)
  - PROC-T250 Calculate relief loads and size relief valves: Flags relief calcs built on superseded H&MB, design pressures or fire zone data (check, share 1, autonomy 2)
  - PROC-T260 Run flare and blowdown hydraulics: Checks flare model loads and inputs against the current relief load summary and isometric data (check, share 1, autonomy 2)
  - SAFE-T050 Run preliminary consequence modelling for layout spacing: Checks release cases use current inventory, fluid data and site meteorology from the basis (check, share 1, autonomy 2)
  - SAFE-T100 Perform facility siting study (API RP 752/753): Checks building occupancy, inventories and plot coordinates in siting models against current issues (check, share 1, autonomy 2)
  - SAFE-T120 Perform quantitative risk assessment: Checks QRA inputs (parts counts, inventories, isolation times, populations) against current issued sources (check, share 1, autonomy 2)
  - SAFE-T130 Check flare radiation, noise and dispersion: Checks flare radiation inputs match current flare loads, stack data and plot plan (check, share 1, autonomy 2)

### 9. AG-01 Drawing and P&ID reader (wave 2)

Reads P&IDs, PFDs, plot plans and vendor or licensor drawings (PDF or scan) and lists the tags, lines, connections, notes and holds they contain.

- **Reads:** Document Locator. **Writes:** staging tables for review
- **Highest autonomy:** 2. **Person:** The owning engineer accepts or corrects each extracted tag before it is loaded anywhere.
- **Guardrails:** Never writes into SPID, SI or S3D; every value carries its drawing number, revision and location on the sheet.
- **Readiness:** ready now. Works on issued PDFs today; no tool access needed.
- **Prerequisite:** None (it feeds the tag crosswalk)
- **Work:** 22 tasks in COMM, ELEC, FIRE, INST, MECH, OWNR, PIPE, PROC, PROJ, SAFE, VEND; 114 manual, review or meeting hand-offs touched; 3 hand-offs no integration removes
  - COMM-T020 Develop preliminary system list and start-up sequence: Lists equipment, units and utility streams from PFDs and utility diagrams as input to system definition (extract, share 1, autonomy 2)
  - COMM-T030 Mark system and subsystem boundaries on P&IDs: Extracts tags, valves and isolation points from P&IDs and single-lines along the marked boundaries (extract, share 1, autonomy 2)
  - ELEC-T060 Prepare hazardous area release source list: Lists release sources (seals, flanges, vents, drains, PSVs) from PROC-I201 P&IDs with locations (extract, share 2, autonomy 2)
  - ELEC-T100 Review P&IDs and assign electrical attributes: Lists motors, MOVs, heat tracing flags and electrical interlocks per PROC-I200 IFR P&ID (extract, share 2, autonomy 2)
  - ELEC-T280 Design lightning protection: Lists structure heights and building dimensions from MECH-I290 and civil drawings for NFPA 780 assessment (extract, share 1, autonomy 2)
  - FIRE-T200 Define fire scenario envelopes and fireproofing zones: Extracts structures, supports, cable routes and valves inside fire envelopes from plot plans (extract, share 1, autonomy 2)
  - INST-T020 Prepare factored instrument count and I&C estimate input: Lists instrument tags, control valves and analyzers from PROC-I200 P&IDs or PFDs for counting (extract, share 2, autonomy 2)
  - INST-T045 Review P&IDs for instrumentation and controls: Lists instruments, loops, fail positions and holds per PROC-I200/I340 P&ID revision for markup (extract, share 2, autonomy 2)
  - INST-T050 Build and maintain the instrument index in SI: Extracts tags, loops, service, line, equipment and P&ID number from PROC-I340 P&IDs into SI staging (extract, share 3, autonomy 2)
  - INST-T115 Define instrument connections on equipment and lines: Lists instrument nozzles, sizes and elevations from MECH-I170/I270 nozzle schedules and vessel drawings (extract, share 1, autonomy 2)
  - INST-T200 Specify fire and gas system and device list: Extracts detector tags, types, coordinates and zones from SAFE-I180 mapping study into SI staging (extract, share 2, autonomy 2)
  - INST-T260 Develop I/O list and assign I/O: Extracts package I/O and serial link maps from MECH-I450 vendor documents into staging (extract, share 1, autonomy 2)
  - INST-T270 Integrate vendor package controls: Extracts package interface signals from vendor P&IDs and I/O lists into the signal list (extract, share 1, autonomy 2)
  - MECH-T180 Provide mechanical input to P&IDs and HAZOP: Lists vents, drains, seal systems and package boundary tags from P&IDs for mechanical markup (extract, share 1, autonomy 2)
  - OWNR-T030 Supply site and existing facility data: Extracts tie-in points, capacities and coordinates from owner as-built drawings into staging tables (extract, share 1, autonomy 2)
  - PIPE-T120 Prepare specialty item list and datasheets: Lists special items with tags and sizes from P&IDs into the specialty item list (extract, share 2, autonomy 2)
  - PIPE-T380 Identify tie-ins and issue tie-in packages: Lists tie-in points with size and spec from marked-up P&IDs into the tie-in list (extract, share 1, autonomy 2)
  - PROC-T200 Develop P&IDs (process content): Extracts tags, connections and notes from vendor and licensor P&IDs for incorporation (extract, share 1, autonomy 2)
  - PROC-T250 Calculate relief loads and size relief valves: Extracts PSV tags, set pressures and protected equipment from P&IDs into the relief device register (extract, share 1, autonomy 2)
  - PROJ-T220 Maintain the hold list: Extracts HOLD clouds and notes from issued drawings to reconcile against the hold list (extract, share 1, autonomy 2)
  - SAFE-T350 Set up environmental startup compliance: Extracts valves, flanges and connectors from as-built P&IDs to draft the LDAR component inventory (extract, share 2, autonomy 2)
  - VEND-T070 Prepare package P&IDs, I/O and control narrative: Extracts tags, I/O points and DCS/SIS interface signals from received package P&IDs (extract, share 1, autonomy 2)

### 10. AG-17 Completions assistant (wave 2)

Builds system and subsystem tag registers, assigns ITRs by tag class, checks test packs and turnover dossiers for completeness and drafts punch summaries.

- **Reads:** SPID, SI, SPEL, S3D, Smart Completions, Document Locator. **Writes:** draft registers, completeness reports
- **Highest autonomy:** 2. **Person:** Completions engineers accept registers; turnover is signed by people.
- **Guardrails:** Never signs an ITR or accepts a system.
- **Readiness:** needs a prerequisite. Needs tag-to-system codes.
- **Prerequisite:** Tag crosswalk; system codes on tags
- **Work:** 31 tasks in COMM, CONS, ELEC, INST, MECH, OWNR, PIPE, PROC, PROJ, SAFE, VEND; 142 manual, review or meeting hand-offs touched; 2 hand-offs no integration removes
  - COMM-T030 Mark system and subsystem boundaries on P&IDs: Checks every P&ID tag falls in exactly one subsystem and lists gaps and overlaps (check, share 1, autonomy 2)
  - COMM-T050 Define ITR library and ITR matrix by tag type: Drafts the ITR matrix mapping A, B and C check sheets to discipline tag types (draft, share 2, autonomy 2)
  - COMM-T060 Build tag-to-subsystem register: Builds the tag-to-subsystem register from line, equipment, instrument and cable lists against marked boundaries (draft, share 3, autonomy 2)
  - COMM-T070 Load tags and assign ITRs in Smart Completions: Prepares the load sheet and generates ITRs per tag from the matrix; flags tags with no matrix match (draft, share 3, autonomy 2)
  - COMM-T140 Raise and manage punch lists: Drafts punch entries from walkdown notes with subsystem, category and action-by party; summarises open items (draft, share 2, autonomy 2)
  - COMM-T150 Accept subsystem turnover from construction: Checks turnover packages for complete A-ITRs, cleared A punch, test records and dossier before acceptance (check, share 2, autonomy 2)
  - COMM-T160 Execute pre-commissioning (B-ITRs): Checks recorded B-ITRs for missing values, out-of-tolerance results and missing vendor sign-offs (check, share 1, autonomy 2)
  - COMM-T190 Energise electrical systems: Lists missing prerequisite records per feeder: protection test results, ITRs and permit references (check, share 1, autonomy 1)
  - COMM-T200 Commission systems and confirm ready for start-up: Checks C-ITRs, test results and start-up punch per system and lists open RFSU items (check, share 1, autonomy 2)
  - COMM-T220 Compile system turnover packages: Assembles system dossiers from certificates, ITRs, test records, punch and vendor data and lists gaps (check, share 3, autonomy 2)
  - CONS-T220 Track welds and NDE: Checks the weld log against isos for missing welds, welder qualifications, NDE percentages and repair rates (check, share 2, autonomy 2)
  - CONS-T230 Prepare and execute pressure test packs: Assembles test pack contents: marked-up P&IDs and isos, test limits, blind list and test pressure tables (draft, share 2, autonomy 2)
  - CONS-T240 Complete construction ITRs (A sheets): Checks A-ITR records for missing fields, attachments and tag mismatches before signature (check, share 1, autonomy 2)
  - CONS-T250 Clear construction punch items: Drafts punch summaries by subsystem and crew listing outstanding construction items for planning (draft, share 1, autonomy 2)
  - CONS-T270 Walk down and certify mechanical completion by subsystem: Checks each subsystem for complete A-ITRs, cleared A punch and test packs; lists outstanding items before walkdown (check, share 1, autonomy 2)
  - CONS-T280 Compile construction quality dossier: Assembles weld, NDE, test, traceability and calibration records per subsystem and reports missing records (check, share 3, autonomy 2)
  - ELEC-T420 Define electrical systems and energization sequence: Builds electrical tag and cable lists by subsystem from SPEL exports in COMM-I040 format (draft, share 2, autonomy 2)
  - ELEC-T430 Support electrical testing, setting and energization: Checks NETA test records and B-ITRs are complete per tag before energization (check, share 1, autonomy 2)
  - INST-T410 Prepare instrument tag register for completions: Builds instrument, cable and JB register with subsystem codes from SI exports in COMM-I040 format (draft, share 3, autonomy 2)
  - INST-T420 Support loop checks and resolve I&C punch: Summarises loop check results and open I&C punch by subsystem (check, share 1, autonomy 2)
  - INST-T430 Support SAT, SIS validation and integrated testing: Checks SIF validation records are complete against the SRS and C&E test procedures (check, share 1, autonomy 2)
  - MECH-T430 Provide mechanical completion and pre-commissioning input: Drafts equipment check sheet assignments by tag class and checks punch lists for completeness (draft, share 2, autonomy 2)
  - OWNR-T200 Witness and accept commissioning tests: Checks ITRs and test records in each witness pack are complete before owner witnessing (check, share 1, autonomy 2)
  - OWNR-T210 Accept system handover: Checks turnover packages for completeness and drafts the retained punch summary for owner review (check, share 1, autonomy 2)
  - OWNR-T220 Load asset register and CMMS: Drafts CMMS asset load sheets from handover tag registers, flagging missing required attributes (draft, share 1, autonomy 2)
  - PIPE-T390 Define hydrotest and test pack boundaries: Drafts test pack boundaries from isos and line list grouped by test pressure, medium and system (draft, share 2, autonomy 2)
  - PROC-T360 Prepare process input to systemization and commissioning: Builds draft system and subsystem tag registers from SPID lines and equipment for process marking (draft, share 2, autonomy 2)
  - PROJ-T260 Compile the final records and close out: Checks vendor data books and turnover records for completeness against the handover requirements (check, share 1, autonomy 2)
  - SAFE-T290 Compile process safety information for PSM: Checks PSI dossier against OSHA 1910.119(d) list; lists missing relief, SIL, HAC and procedure records (check, share 3, autonomy 2)
  - SAFE-T340 Lead pre-startup safety review (PSSR): Checks system turnover dossiers and punch status for PSSR completeness (check, share 1, autonomy 2)
  - VEND-T180 Compile the MDR / data book: Checks the received data book against the MDR index and lists missing certificates and records (check, share 1, autonomy 2)

### 11. AG-13 Estimate and quantity assistant (wave 2)

Builds quantity takeoffs from the register, model reports and benchmarks, and checks estimate quantities against the latest MTOs.

- **Reads:** S3D, Excel / Word, P6. **Writes:** draft quantity sheets
- **Highest autonomy:** 2. **Person:** The estimator owns the estimate.
- **Guardrails:** Flags every factor or benchmark it applied.
- **Readiness:** ready now. Model reports and workbooks.
- **Prerequisite:** None
- **Work:** 19 tasks in CIVL, COMM, CONS, ELEC, INST, PIPE, PROJ; 101 manual, review or meeting hand-offs touched; 0 hand-offs no integration removes
  - CIVL-T060 Prepare civil and structural quantities for estimates: Builds civil and steel quantity sheets from plot plan, equipment list, Tekla reports and benchmarks, flagging factors (draft, share 2, autonomy 2)
  - CIVL-T240 Prepare structural steel MTO: Builds steel MTO by profile, grade and coating from Tekla reports; checks against the estimate (draft, share 3, autonomy 2)
  - COMM-T120 Plan temporary commissioning facilities: Drafts temporary spool, blind and strainer quantity lists from flushing circuits and isometric data (draft, share 1, autonomy 2)
  - CONS-T030 Evaluate modularisation and prefabrication strategy: Drafts quantity and field-hour comparison tables for stick-built versus rack and module options, flagging benchmarks used (draft, share 1, autonomy 2)
  - CONS-T100 Prepare construction execution plan and estimate input: Builds direct field-hour takeoffs from MTO quantities and installation norms, flagging every productivity factor applied (draft, share 2, autonomy 2)
  - ELEC-T020 Prepare preliminary electrical load estimate: Compiles connected and running loads from MECH-I050 drivers and PROC-I270, flagging every factor (draft, share 2, autonomy 2)
  - ELEC-T050 Prepare electrical cost estimate inputs: Builds quantity sheets from equipment ratings, motor list and VEND-I010 budget prices in PROJ-I080 template (draft, share 2, autonomy 2)
  - ELEC-T290 Design lighting and small power: Takes off fixtures and receptacles per area from layouts into lighting panel schedules (draft, share 1, autonomy 2)
  - ELEC-T370 Prepare electrical MTO and bulk requisitions: Totals cable, tray, conduit, lighting, grounding, tracing and CP materials with SCM-I060 codes (draft, share 2, autonomy 2)
  - INST-T020 Prepare factored instrument count and I&C estimate input: Builds I/O, valve and cabinet counts in the PROJ-I080 template, flagging every factor applied (draft, share 2, autonomy 2)
  - INST-T320 Prepare instrument cable schedule and tray loading: Takes off cable lengths from S3D route distances and counts cables per tray segment (draft, share 1, autonomy 2)
  - INST-T340 Prepare instrument bulk MTO: Totals cable, tubing, fittings and JBs from hook-up BOMs and cable schedule with SCM-I060 codes (draft, share 2, autonomy 2)
  - PIPE-T020 Estimate piping quantities for FEL1 estimate: Applies benchmark factors to equipment counts and run lengths to draft piping quantities per option (draft, share 2, autonomy 2)
  - PIPE-T060 Lay out pipe racks and assign tiers: Tabulates rack lines from the line list with sizes and weights to draft rack load estimates (draft, share 1, autonomy 2)
  - PIPE-T150 Prepare FEL3 piping MTO for the estimate: Combines S3D MTO reports with factored quantities for unrouted areas into the bulk MTO, flagging factors (draft, share 2, autonomy 2)
  - PROJ-T060 Prepare the Class 5 estimate: Drafts capacity-factored cost tables from benchmark data, flagging every factor and escalation applied (draft, share 1, autonomy 2)
  - PROJ-T080 Prepare the Class 4 estimate: Builds the equipment-factored quantity sheet from the equipment list and budget quotes, flagging each factor (draft, share 2, autonomy 2)
  - PROJ-T090 Prepare the Class 3 estimate: Checks estimate quantities against the latest discipline MTOs and vendor quotes and lists differences (check, share 2, autonomy 2)
  - PROJ-T100 Prepare the control estimate and budget: Maps approved estimate lines to WBS and cost codes into a draft control budget table (draft, share 1, autonomy 2)

### 12. AG-03 Cross-system consistency checker (wave 2)

Before each issue, compares the same tag or line across SPID, SI, S3D, SPEL, the line list and the equipment register, and lists every mismatch with both values.

- **Reads:** SPID, SI, S3D, SPEL, Excel / Word. **Writes:** discrepancy reports
- **Highest autonomy:** 3. **Person:** Each discipline lead clears their mismatches; the agent re-checks.
- **Guardrails:** Read-only on every tool; reports, never fixes.
- **Readiness:** needs a prerequisite. Needs read access to the tool databases or scheduled exports.
- **Prerequisite:** Tag crosswalk
- **Work:** 41 tasks in COMM, CONS, ELEC, INST, MECH, PIPE, PROC; 187 manual, review or meeting hand-offs touched; 8 hand-offs no integration removes
  - COMM-T060 Build tag-to-subsystem register: Compares register tags against SPID, SI and SPEL and lists missing or duplicate tags (check, share 1, autonomy 3)
  - COMM-T170 Execute loop checks: Compares loop check records against SI loop data and the DCS/SIS I/O list and lists mismatches (check, share 1, autonomy 2)
  - CONS-T130 Build construction model and attach CWP/IWP attributes: Compares iConstruct object tags against S3D, Tekla and Jovix idents and lists mismatches with both values (check, share 1, autonomy 3)
  - ELEC-T070 Prepare hazardous area classification drawings: Checks drawn extents cover every source on the ELEC-I060 release source list (check, share 1, autonomy 2)
  - ELEC-T090 Develop electrical load list in SPEL: Compares SPEL load list with P&ID motor tags and the equipment register (check, share 1, autonomy 3)
  - ELEC-T100 Review P&IDs and assign electrical attributes: Compares P&ID motor and MOV tags with the SPEL load list (check, share 1, autonomy 3)
  - ELEC-T120 Develop one-line diagrams in SPEL: Compares one-line loads and ratings with the SPEL load list and ELEC-I110 ratings (check, share 1, autonomy 3)
  - ELEC-T200 Review motor and package electrical data: Compares certified motor data with SPEL load list values (check, share 1, autonomy 3)
  - ELEC-T320 Size cables and build cable schedule in SPEL: Compares the cable schedule with SPEL loads and one-line feeders; lists missing or orphan cables (check, share 1, autonomy 3)
  - ELEC-T340 Define MCC and switchgear interface signals with I&C: Compares MCC/switchgear signal list with SI I/O list, INST-I240 motor trips and INST-I170 logic (check, share 2, autonomy 2)
  - ELEC-T440 Produce as-built electrical records: Checks as-left relay settings against the ELEC-I252 setting files (check, share 1, autonomy 3)
  - INST-T050 Build and maintain the instrument index in SI: Compares SI index with SPID tags after each P&ID revision; lists missing or mismatched tags (check, share 1, autonomy 3)
  - INST-T060 Enter instrument process data: Compares SI process data with process datasheets and line list after each process revision (check, share 1, autonomy 3)
  - INST-T100 Specify relief valves from the process sizing: Compares PSV datasheet values with the process relief summary and PIPE-I160 inlet/outlet classes (check, share 1, autonomy 2)
  - INST-T110 Prepare instrument datasheets: Checks datasheet Ex ratings and wetted materials against ELEC-I072 and PIPE-I110 (check, share 1, autonomy 3)
  - INST-T115 Define instrument connections on equipment and lines: Compares instrument connection list with mechanical nozzle schedules; flags missing or mismatched nozzles (check, share 1, autonomy 3)
  - INST-T200 Specify fire and gas system and device list: Checks F&G device Ex ratings in SI against ELEC-I072 area classification (check, share 1, autonomy 2)
  - INST-T240 Prepare cause and effect charts: Checks C&E tags against the SI index and ELEC-I340 motor trip signals (check, share 1, autonomy 2)
  - INST-T260 Develop I/O list and assign I/O: Checks the I/O list against the SI index, motor signals and package I/O (check, share 1, autonomy 3)
  - INST-T310 Design instrument wiring, marshalling and terminations: Checks SI terminations against VEND-I140 marshalling numbering and ELEC-I350 MCC relay terminals (check, share 1, autonomy 3)
  - INST-T320 Prepare instrument cable schedule and tray loading: Compares the cable schedule with SI wiring; lists missing or duplicate cables (check, share 1, autonomy 3)
  - INST-T330 Generate loop diagrams: Checks loop diagrams against VEND-I280 final I/O and INST-I151 certified wiring data before issue (check, share 1, autonomy 3)
  - INST-T380 Prepare system configuration data for vendors: Cross-checks the configuration export against SI, the alarm database and C&E; lists mismatches (check, share 2, autonomy 2)
  - INST-T440 Prepare as-built I&C database and drawings: Checks as-built SI against final vendor data and approved field changes (check, share 1, autonomy 3)
  - MECH-T060 Maintain mechanical equipment list: Compares equipment list attributes with datasheets, SPID and vendor data and lists mismatches (check, share 2, autonomy 3)
  - MECH-T130 Prepare mechanical datasheets for vessels and columns: Compares datasheet nozzles and design conditions with SPID, line list and instrument data (check, share 1, autonomy 3)
  - MECH-T190 Prepare nozzle orientations and allowable nozzle loads: Compares orientation drawings with piping requests and the vessel datasheet nozzle schedule (check, share 1, autonomy 3)
  - MECH-T210 Compile equipment weights and foundation loads: Checks the load register against vessel calcs and datasheets and lists weight differences (check, share 1, autonomy 3)
  - MECH-T330 Check piping loads against equipment nozzle allowables: Tabulates CAESAR II nozzle loads against vendor and code allowables and lists every exceedance (check, share 2, autonomy 2)
  - MECH-T440 Issue as-built equipment data for handover: Compares the as-built register with certified vendor data and owner handover requirements (check, share 1, autonomy 3)
  - PIPE-T080 Request equipment nozzle orientations and elevations: Compares requested nozzle orientations with vendor drawings and vessel datasheets; lists differences (check, share 1, autonomy 3)
  - PIPE-T100 Build S3D piping specification catalogue: Compares S3D catalogue entries with issued piping classes; lists mismatched commodity and valve codes (check, share 2, autonomy 3)
  - PIPE-T170 Check model against P&IDs: Compares SPID line numbers, sizes, specs and components with S3D and lists every mismatch (check, share 3, autonomy 3)
  - PIPE-T180 Position in-line instruments and instrument access: Compares in-line instrument tags in S3D with the instrument index and P&IDs (check, share 1, autonomy 3)
  - PROC-T120 Prepare process flow diagrams: Checks PFD stream numbers and equipment tags against the H&MB stream table and equipment list (check, share 1, autonomy 3)
  - PROC-T160 Prepare equipment list process data: Compares equipment list process data with sizing calcs and Mechanical's equipment register (check, share 1, autonomy 3)
  - PROC-T200 Develop P&IDs (process content): Compares SPID equipment and lines with equipment list, line sizing and instrument index (check, share 1, autonomy 3)
  - PROC-T210 Prepare line list and tie-in process data: Checks line list against SPID lines and piping classes (check, share 1, autonomy 3)
  - PROC-T325 Review instrument and control valve sizing: Compares process data used in SI valve, flow element and PSV sizing against current instrument process data (check, share 2, autonomy 2)
  - PROC-T340 Update P&IDs to IFD and IFC: Checks updated P&IDs against SI, line list and equipment register before issue (check, share 1, autonomy 3)
  - PROC-T385 Incorporate as-built redlines into P&IDs: Compares as-built P&IDs with line list and SI after redline incorporation (check, share 1, autonomy 3)

### 13. AG-08 Safety study scribe and action tracker (wave 3)

Drafts HAZOP, HAZID and LOPA worksheets from the session record, tracks every recommendation to close-out and checks that the close-out evidence exists.

- **Reads:** PHA tool, Document Locator, SPID. **Writes:** draft worksheets, action status
- **Highest autonomy:** 2. **Person:** The study leader and team own every entry; actions close only on the owner's sign-off.
- **Guardrails:** Never closes a safety action; never changes a risk ranking.
- **Readiness:** ready now. Works on session notes and the PHA export.
- **Prerequisite:** None
- **Work:** 15 tasks in COMM, INST, MECH, OWNR, PIPE, PROC, SAFE; 91 manual, review or meeting hand-offs touched; 0 hand-offs no integration removes
  - COMM-T200 Commission systems and confirm ready for start-up: Checks PSSR and safety study actions due before start-up have close-out evidence and lists gaps (monitor, share 1, autonomy 2)
  - INST-T045 Review P&IDs for instrumentation and controls: Checks each SAFE-I152 HAZOP recommendation on instruments appears on the P&ID markups (monitor, share 1, autonomy 2)
  - INST-T055 Close out HAZOP and LOPA actions on I&C design: Tracks SAFE-I152/I160 actions assigned to I&C and checks close-out evidence exists on IFD P&IDs (monitor, share 2, autonomy 2)
  - MECH-T180 Provide mechanical input to P&IDs and HAZOP: Tracks mechanical HAZOP actions to close-out and checks close-out evidence exists (monitor, share 2, autonomy 2)
  - OWNR-T130 Take part in HAZOP and accept actions: Checks close-out evidence exists before each action goes to owner sign-off and reports status (monitor, share 1, autonomy 2)
  - PIPE-T300 Respond to HAZOP and safety layout actions: Tracks layout-related HAZOP, siting and fire and gas actions; checks close-out evidence exists (monitor, share 2, autonomy 2)
  - PROC-T300 Participate in HAZOP and close process actions: Tracks process-owned HAZOP/LOPA actions and checks close-out evidence exists (monitor, share 1, autonomy 2)
  - PROC-T340 Update P&IDs to IFD and IFC: Checks every HAZOP markup is incorporated on the IFD and IFC P&IDs (monitor, share 1, autonomy 2)
  - SAFE-T020 Facilitate concept HAZID and ENVID: Drafts HAZID/ENVID worksheets from the session record and tracks every action to close-out (record, share 2, autonomy 2)
  - SAFE-T090 Facilitate preliminary (coarse) HAZOP: Drafts coarse HAZOP worksheets from session record and tracks recommendations to close-out (record, share 2, autonomy 2)
  - SAFE-T150 Facilitate formal HAZOP: Drafts node-by-node HAZOP worksheets from session record and PHA tool; tracks recommendations (record, share 2, autonomy 2)
  - SAFE-T160 Run LOPA and set SIL targets: Drafts LOPA worksheets from HAZOP scenarios and session notes (record, share 1, autonomy 2)
  - SAFE-T170 Track and close out PHA and study actions: Tracks HAZID, HAZOP, LOPA, siting and QRA actions; chases owners and checks close-out evidence exists (monitor, share 3, autonomy 2)
  - SAFE-T280 Facilitate vendor package and design change HAZOPs: Drafts vendor package and revalidation HAZOP worksheets from session record; tracks recommendations (record, share 2, autonomy 2)
  - SAFE-T340 Lead pre-startup safety review (PSSR): Checks PHA close-out evidence and PSSR checklist items exist; lists open items (monitor, share 2, autonomy 2)

### 14. AG-10 Expediting agent (wave 3)

Chases vendors for document returns and manufacturing progress, updates the purchasing database and warns when a forecast passes the P6 need date.

- **Reads:** Purchasing DB, P6, Document Locator, email. **Writes:** purchasing database status, vendor reminders
- **Highest autonomy:** 3. **Person:** The expeditor handles escalations and anything commercial.
- **Guardrails:** Sends only templated status requests; no commitments or commercial terms.
- **Readiness:** needs a prerequisite. Needs write access to status fields in the purchasing database and an email account.
- **Prerequisite:** MR/PO to P6 activity code
- **Work:** 16 tasks in COMM, CONS, ELEC, INST, MECH, PROJ, SCM, VEND; 81 manual, review or meeting hand-offs touched; 0 hand-offs no integration removes
  - COMM-T110 Define vendor commissioning support requirements: Requests and tracks vendor representative mobilisation dates against the commissioning schedule (monitor, share 1, autonomy 3)
  - CONS-T120 Align EWPs and procurement packages to CWPs: Sends templated forecast requests to vendors on POs flagged late against CWP need dates (monitor, share 1, autonomy 3)
  - ELEC-T190 Review electrical vendor drawings and data: Chases overdue electrical vendor documents against SCM-I160 VDRL dates (monitor, share 1, autonomy 3)
  - INST-T150 Review instrument vendor data: Chases overdue instrument vendor documents against SCM-I170 due dates (monitor, share 1, autonomy 3)
  - MECH-T300 Review vendor drawings and data: Chases overdue vendor submissions and resubmissions against the VDRL schedule (monitor, share 1, autonomy 3)
  - PROJ-T120 Integrate procurement and vendor dates into the schedule: Carries PO award, drawing return and forecast delivery dates from the Purchasing DB into a P6 update (transfer, share 3, autonomy 2)
  - SCM-T030 Register material requisitions in the Purchasing DB: Keys MR header and line data from Document Locator issues into the Purchasing DB for buyer approval (transfer, share 3, autonomy 2)
  - SCM-T100 Award the purchase order in the Purchasing DB: Prepares PO line entries from the conformed MR lines for the buyer to check and load (transfer, share 1, autonomy 1)
  - SCM-T120 Set up VDRL tracking: Loads VDRL documents, numbers and due dates per PO into the Purchasing DB for approval (transfer, share 3, autonomy 2)
  - SCM-T130 Expedite vendor documents and route them for review: Chases overdue vendor documents, updates receipt and return status and reports print status (monitor, share 3, autonomy 3)
  - SCM-T140 Expedite manufacturing and forecast deliveries: Requests milestone status, updates forecast ex-works dates and warns when forecasts pass P6 need dates (monitor, share 3, autonomy 3)
  - SCM-T180 Manage shipping and traffic: Tracks shipments against forecasts and sends templated shipping notices to site (monitor, share 1, autonomy 3)
  - SCM-T210 Raise OS&D reports: Tracks open OS&D reports and sends templated follow-ups to vendor and carrier (monitor, share 2, autonomy 2)
  - SCM-T260 Call off vendor site services: Tracks call-off requests, vendor representative dates and service days against the PO (monitor, share 1, autonomy 2)
  - VEND-T100 Prepare the ITP and manufacturing schedule: Loads vendor manufacturing milestones as the expediting baseline and checks them against need dates (monitor, share 1, autonomy 3)
  - VEND-T150 Report manufacturing progress: Reads vendor progress reports, updates forecasts and flags slipped milestones (monitor, share 1, autonomy 3)

### 15. AG-16 RFI, query and field change assistant (wave 3)

Answers RFIs and technical queries from the project record where the answer already exists, drafts responses for the engineer, routes changes to the owning discipline and tracks as-built redlines to closure.

- **Reads:** Procore, Document Locator, SPID, S3D. **Writes:** draft responses, routing
- **Highest autonomy:** 2. **Person:** The responsible engineer signs every response that changes design.
- **Guardrails:** Design changes always go to a person; cites the documents it relied on.
- **Readiness:** ready now. Procore and Document Locator read access.
- **Prerequisite:** None
- **Work:** 17 tasks in CIVL, COMM, CONS, ELEC, INST, MECH, PIPE, PROC; 70 manual, review or meeting hand-offs touched; 2 hand-offs no integration removes
  - CIVL-T360 Answer RFIs and disposition field changes and NCRs: Answers civil RFIs from IFC drawings and specs where answered; drafts others and routes NCRs (answer, share 2, autonomy 2)
  - CIVL-T380 Incorporate as-built civil and structural changes: Tracks civil field redlines to closure; lists drawings and Tekla areas awaiting as-built update (draft, share 1, autonomy 2)
  - COMM-T210 Raise commissioning technical queries: Answers commissioning queries already covered by design records with citations; drafts and routes the rest (answer, share 2, autonomy 2)
  - CONS-T170 Raise and manage RFIs: Answers RFIs already covered by the project record with citations; drafts and routes the rest, tracking closure (answer, share 2, autonomy 2)
  - CONS-T180 Raise field change requests: Drafts field change requests from RFI history and marked-up IFC drawings and routes them to the owning discipline (draft, share 1, autonomy 2)
  - CONS-T260 Prepare as-built redlines: Tracks redlines against approved field changes and RFIs and drafts transmittals listing affected drawings (draft, share 1, autonomy 2)
  - ELEC-T410 Answer RFIs and issue field changes: Answers electrical RFIs from IFC drawings, SPEL and vendor data where the answer exists; drafts responses (answer, share 2, autonomy 2)
  - ELEC-T440 Produce as-built electrical records: Lists each CONS-I330 redline with affected SPEL cables, terminations and drawings (draft, share 1, autonomy 2)
  - INST-T400 Answer construction RFIs and issue I&C field changes: Answers I&C RFIs from IFC loop, hook-up and location drawings where the answer exists; drafts responses (answer, share 2, autonomy 2)
  - INST-T420 Support loop checks and resolve I&C punch: Drafts responses to I&C punch items citing IFC loop diagrams (answer, share 1, autonomy 2)
  - INST-T440 Prepare as-built I&C database and drawings: Lists each CONS-I330 redline with affected SI tags and drawings for incorporation (draft, share 1, autonomy 2)
  - MECH-T410 Respond to field RFIs and equipment issues: Answers equipment RFIs from datasheets and vendor documents where answered; drafts others for the engineer (answer, share 2, autonomy 2)
  - PIPE-T420 Respond to piping RFIs and field changes: Answers piping RFIs from isos, specs and model where answered; drafts others; tracks field change isos (answer, share 2, autonomy 2)
  - PIPE-T440 Prepare as-built isometrics and model: Tracks field redlines to closure; lists isos and model areas still awaiting as-built update (draft, share 1, autonomy 2)
  - PROC-T320 Respond to technical queries, holds and change requests: Answers process TQs already settled in datasheets or H&MB with citations; routes the rest (answer, share 2, autonomy 2)
  - PROC-T370 Respond to field RFIs and review field changes: Answers RFIs already resolved in P&IDs, line list or datasheets with citations; routes field changes (answer, share 2, autonomy 2)
  - PROC-T385 Incorporate as-built redlines into P&IDs: Tracks field redlines and commissioning changes through P&ID incorporation to closure (draft, share 1, autonomy 2)

### 16. AG-20 Model and drawing checker (wave 3)

Checks model reports, isometrics and steel drawings against the line list, piping specs, standards and clash rules before review and issue.

- **Reads:** S3D, Tekla, Document Locator, Excel / Word. **Writes:** check reports
- **Highest autonomy:** 3. **Person:** The designer and checker clear findings; the checker still signs.
- **Guardrails:** Read-only on models.
- **Readiness:** needs a prerequisite. Needs scheduled model reports.
- **Prerequisite:** Agreed line list (INT-02)
- **Work:** 17 tasks in CIVL, CONS, ELEC, INST, MECH, PIPE, PROC, SAFE, VEND; 63 manual, review or meeting hand-offs touched; 15 hand-offs no integration removes
  - CIVL-T190 Prepare foundation plans and anchor bolt layouts: Checks anchor bolt plans against certified vendor base plate data and equipment coordinates; lists mismatches (check, share 1, autonomy 2)
  - CIVL-T220 Model structures in Tekla and share reference models: Checks Tekla model reports against design outputs and the S3D reference for missing members (check, share 1, autonomy 3)
  - CIVL-T230 Prepare steel GA drawings and connection design data: Checks steel GA and erection drawings against the Tekla model, standards and title block rules (check, share 2, autonomy 2)
  - CIVL-T350 Check, seal and issue civil and structural IFC packages: Checks package drawings against the Tekla model and standards before checker review (check, share 1, autonomy 2)
  - CONS-T080 Review 3D model for constructability (30/60/90 % reviews): Runs model reports against weld access, spool break and erection clearance rules and lists findings for reviewers (check, share 1, autonomy 2)
  - ELEC-T330 Route raceway, cable tray and duct banks in S3D: Checks S3D tray reports against segregation rules, PIPE-I070 rack levels and clash rules (check, share 1, autonomy 3)
  - ELEC-T360 Prepare electrical layouts and installation details: Checks layouts against ELEC-I192 certified dimensions, CIVL-I190 foundations and the tray model (check, share 1, autonomy 2)
  - INST-T290 Prepare instrument location plans and JB locations: Checks S3D instrument and JB placements against access rules and hazardous area boundaries (check, share 1, autonomy 2)
  - MECH-T400 Review 3D model for equipment access and maintenance: Checks model equipment against maintenance envelopes and access rules; lists infringements (check, share 1, autonomy 3)
  - PIPE-T200 Prepare stress-critical line list: Applies stress-criticality rules by size, temperature and service to the line list; drafts the categorisation (check, share 2, autonomy 2)
  - PIPE-T250 Design pipe supports: Checks S3D support placement reports against stress support output and standard support rules (check, share 1, autonomy 3)
  - PIPE-T320 Extract and check isometrics: Checks isometrics against line list, piping class, supports and hold list before issue (check, share 2, autonomy 3)
  - PIPE-T370 Produce piping GA and key plan drawings: Checks extracted GA drawings for key plan references and line labels against the line list (check, share 1, autonomy 3)
  - PIPE-T410 Review fabricator spool drawings: Checks fabricator spool drawings and weld maps against IFC isometrics; lists differences (review, share 2, autonomy 3)
  - PROC-T330 Review 3D model and isometrics for process requirements: Checks model reports and isometrics for slopes, pockets and elevations against process layout requirements (check, share 2, autonomy 2)
  - SAFE-T250 Review plot plan and 3D model for safety: Checks model reports for spacing, escape and access against siting and layout rules (check, share 1, autonomy 2)
  - VEND-T140 Detail and fabricate structural steel: Checks returned shop drawings against the Tekla model and issued steel drawings, listing differences (check, share 1, autonomy 2)

### 17. AG-19 Change impact tracer (wave 3)

When an item is revised, uses this register's exchanges to list every task, document and system downstream that relies on it, at the level it needs, and tells their owners.

- **Reads:** Document Locator, this register. **Writes:** impact notices
- **Highest autonomy:** 3. **Person:** Each notified owner decides whether to revise.
- **Guardrails:** Notifies; never revises.
- **Readiness:** ready now. Runs on this register plus Document Locator revision events.
- **Prerequisite:** None
- **Work:** 10 tasks in CONS, ELEC, MECH, PROC, PROJ, SAFE, SCM; 57 manual, review or meeting hand-offs touched; 7 hand-offs no integration removes
  - CONS-T180 Raise field change requests: Lists downstream documents, tasks and systems affected by each proposed field change (check, share 1, autonomy 3)
  - ELEC-T070 Prepare hazardous area classification drawings: Notifies instrument, telecom, lighting and vendor owners when classified extents are revised (monitor, share 1, autonomy 2)
  - MECH-T310 Release certified vendor data to other disciplines: Notifies piping, civil, electrical and I&C owners when certified vendor data is released or revised (monitor, share 1, autonomy 3)
  - PROC-T315 Reconcile simulation with certified vendor data: Lists datasheets and documents relying on the revised H&MB and notifies their owners (check, share 1, autonomy 3)
  - PROC-T320 Respond to technical queries, holds and change requests: Lists downstream tasks and documents affected by each change request or deviation (check, share 1, autonomy 3)
  - PROJ-T160 Run change control: trends and change notices: Lists downstream tasks, documents and systems affected by each trend to support impact estimating (check, share 1, autonomy 2)
  - PROJ-T190 Run interface management: Notifies interface owners when an exchanged item they rely on is revised (monitor, share 1, autonomy 3)
  - SAFE-T330 Perform MOC safety reviews of field and design changes: Lists safety studies, PSI items and HAZOP nodes relying on each changed item (check, share 1, autonomy 2)
  - SAFE-T360 Update safety studies to as-built and hand over: Lists study inputs changed by as-built redlines to scope siting, F&G and QRA revisions (check, share 1, autonomy 2)
  - SCM-T110 Process PO amendments: Lists PO lines affected by each MR revision with the quantity and specification differences (check, share 1, autonomy 2)

### 18. AG-14 Material reconciliation agent (wave 3)

Reconciles MTO, purchased, shipped, received and issued quantities by ident and CWP; forecasts shortages and surplus.

- **Reads:** Excel / Word, Purchasing DB, Jovix, S3D. **Writes:** reconciliation and shortage reports
- **Highest autonomy:** 3. **Person:** Materials manager acts on shortages; buyers place orders.
- **Guardrails:** Never orders material.
- **Readiness:** needs a prerequisite. Needs the ident map between MTO, purchasing and Jovix.
- **Prerequisite:** Commodity code to purchasing ident map
- **Work:** 16 tasks in CONS, ELEC, INST, PIPE, SCM, VEND; 33 manual, review or meeting hand-offs touched; 1 hand-offs no integration removes
  - CONS-T150 Check IWP material availability against Jovix: Compares each IWP bill of materials with Jovix warehouse and laydown status and reports shortages by ident (check, share 3, autonomy 3)
  - CONS-T200 Request and receive materials from the warehouse: Lists material to issue for released IWPs and tracks reported shortages, damage and surplus to closure (monitor, share 2, autonomy 2)
  - ELEC-T370 Prepare electrical MTO and bulk requisitions: Reconciles MTO revisions with purchased quantities and SCM-I330 surplus (check, share 1, autonomy 3)
  - INST-T340 Prepare instrument bulk MTO: Reconciles instrument bulk MTO revisions against purchased, received and issued quantities (check, share 1, autonomy 3)
  - PIPE-T340 Produce MTO by ident and bulk requisitions: Reconciles S3D MTO by ident against prior buys and surplus; lists net quantities (check, share 2, autonomy 3)
  - PIPE-T430 Reconcile piping material shortages and surplus: Reconciles MTO against received and issued quantities by ident; forecasts shortages and surplus (monitor, share 3, autonomy 3)
  - SCM-T040 Load piping bulk MTO into the Purchasing DB: Checks S3D MTO commodity codes map to purchasing idents and flags unmapped or changed lines (check, share 2, autonomy 2)
  - SCM-T190 Pass PO data to Jovix for receiving: Checks Jovix expected receipts match PO header, lines and idents after each transfer (check, share 2, autonomy 3)
  - SCM-T200 Receive materials at site in Jovix: Compares packing lists with PO lines and flags differences for the receiving clerk (check, share 1, autonomy 2)
  - SCM-T220 Manage the warehouse, laydown and preservation: Lists preservation tasks due by location from Jovix and flags overdue records (monitor, share 1, autonomy 3)
  - SCM-T230 Report material availability to AWP: Matches received stock against CWP/IWP bills of material and publishes availability and shortage lists (check, share 3, autonomy 3)
  - SCM-T240 Issue materials to construction: Checks pick tickets against IWP material lists and heat traceability records (check, share 1, autonomy 2)
  - SCM-T250 Reconcile materials and dispose of surplus: Reconciles ordered, received, issued and installed quantities by ident and CWP and forecasts surplus (check, share 3, autonomy 3)
  - SCM-T280 Close out purchase orders: Confirms delivered quantities match PO lines and lists open lines (check, share 1, autonomy 2)
  - VEND-T130 Fabricate pipe spools: Tracks spool status reports against the IFC isometric list and site need by CWP (monitor, share 1, autonomy 3)
  - VEND-T160 Pack, preserve and ship: Checks vendor packing lists against PO lines before shipment release (check, share 1, autonomy 2)

### 19. AG-09 Safety instrumented logic drafter (wave 3)

Drafts cause-and-effect charts, the SIF list and SRS tables from the trip schedule, LOPA and SI, and checks them against the P&IDs and the DCS/SIS configuration.

- **Reads:** PHA tool, SI, SPID, DCS / SIS config. **Writes:** draft C&Es, mismatch lists
- **Highest autonomy:** 2. **Person:** The I&C and process safety engineers check and approve every line.
- **Guardrails:** Safety-critical: always draft only, with independent human verification.
- **Readiness:** needs a prerequisite. Needs SI and PHA exports keyed by tag.
- **Prerequisite:** Tag crosswalk; SIF numbering
- **Work:** 13 tasks in COMM, ELEC, INST, PROC, SAFE, VEND; 65 manual, review or meeting hand-offs touched; 0 hand-offs no integration removes
  - COMM-T090 Write commissioning and function test procedures: Checks procedure test steps cover every C&E line and SIF in the SRS and lists omissions (check, share 1, autonomy 2)
  - COMM-T180 Execute C&E and SIF function tests: Checks recorded results against every C&E line and SRS requirement and lists untested or failed items (check, share 1, autonomy 2)
  - ELEC-T350 Prepare control and interlock schematics: Checks interlock schematics against INST-I240 C&E trip actions and INST-I210 SIF final elements (check, share 1, autonomy 2)
  - INST-T190 Prepare SIS specification: Cross-checks SIS I/O and SIF counts with INST-I261 and SAFE-I160 SIL targets (check, share 1, autonomy 2)
  - INST-T210 Define SIFs and input to SIL determination: Drafts SIF list rows from PROC-I235 trip schedule and SAFE-I160 LOPA; checks tags against P&IDs (draft, share 1, autonomy 2)
  - INST-T220 Write safety requirements specification: Drafts SRS tables per SIF: safe state, trip points, response time, bypasses from INST-I210, SAFE-I160, PROC-I235 (draft, share 2, autonomy 2)
  - INST-T230 Verify SIL achievement: Checks verified SIF architectures match the SRS and the selected device tags (check, share 1, autonomy 2)
  - INST-T240 Prepare cause and effect charts: Drafts shutdown and F&G C&E charts from PROC-I235 trips, SAFE-I182 zones and the SIF list (draft, share 2, autonomy 2)
  - INST-T390 Review configuration and witness system FAT: Checks configured SIS and F&G logic against INST-I240/I241 C&E charts; lists mismatches (check, share 1, autonomy 2)
  - PROC-T235 Define trips, interlocks and process input to SIF: Drafts trip schedule table from P&ID interlocks and SI tags; checks it against the P&IDs (draft, share 1, autonomy 2)
  - SAFE-T160 Run LOPA and set SIL targets: Drafts the SIF list with target SIL from LOPA results and SI tags (draft, share 1, autonomy 2)
  - SAFE-T260 Review cause and effect and SIL verification: Checks C&Es and SIL verification against LOPA targets, F&G actions and HAZOP recommendations; lists mismatches (check, share 2, autonomy 2)
  - VEND-T200 Configure and test the DCS/SIS: Checks configured cause-and-effect logic against approved C&E charts and lists mismatches before FAT (check, share 1, autonomy 2)

### 20. AG-15 Work package builder (wave 3)

Assembles CWP and IWP content (drawings, isos, materials, holds, permits), checks constraints are cleared and lists what blocks release.

- **Reads:** S3D, iConstruct, Jovix, Document Locator, P6, Procore. **Writes:** draft IWPs, constraint lists
- **Highest autonomy:** 2. **Person:** The work packager and superintendent release the package.
- **Guardrails:** Cannot release a package with an open constraint.
- **Readiness:** needs a prerequisite. Needs CWA/CWP codes on model objects.
- **Prerequisite:** CWA/CWP coding on model objects
- **Work:** 7 tasks in CIVL, CONS, PIPE; 38 manual, review or meeting hand-offs touched; 0 hand-offs no integration removes
  - CIVL-T340 Provide civil inputs to construction packaging: Drafts civil and steel CWP content lists from the model and construction sequence (draft, share 1, autonomy 2)
  - CONS-T070 Define CWPs, boundaries and sequence: Drafts discipline CWP scope lists from deliverable registers and CWA boundaries, with engineering and material need dates (draft, share 1, autonomy 2)
  - CONS-T130 Build construction model and attach CWP/IWP attributes: Checks every model object carries CWA, CWP and IWP codes and lists unassigned or conflicting objects (check, share 2, autonomy 2)
  - CONS-T140 Develop installation work packages (IWPs): Assembles IWP content per crew scope: isos, drawings, model views, materials and quantities from iConstruct (draft, share 3, autonomy 2)
  - CONS-T160 Manage IWP constraints and release IWPs: Checks each IWP for open holds, RFIs, materials, scaffolding and permits and lists what blocks release (check, share 2, autonomy 2)
  - PIPE-T330 Prepare spool lists and fabrication packages: Assembles fabrication packages from IFC isometrics, spool lists and weld data (draft, share 1, autonomy 2)
  - PIPE-T400 Issue model to AWP and construction model: Checks published model objects carry iso, spool and CWP attributes; lists gaps (check, share 1, autonomy 2)
