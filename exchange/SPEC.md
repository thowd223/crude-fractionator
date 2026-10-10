# Discipline task and information exchange register: data specification

The register lists every detailed engineering task each discipline performs on an onshore process-plant project
(terminals, fractionation, refining units), from FEL 1 through detailed design, plus the procurement,
construction and completions work that consumes engineering data. It also lists every **information item**
those tasks produce and every **exchange**: an item sent from the task that owns it to a task that uses it,
including what is taken from it, which system it moves between, and how it moves today.

It is generic: it must not be specific to one unit or one project. Use typical tag, document and data names.

## Files

One JSON file per discipline in `exchange/data/<CODE>.json`. The build (`exchange/build.py`) merges them,
checks every reference and generates the register workbook and the interactive page.

## Disciplines (codes)

| Code | Discipline | Covers |
|---|---|---|
| PROC | Process | Simulation, H&MB, PFDs, P&IDs (process content), line list process data, process datasheets, relief and flare hydraulics, utility balances, control and operating philosophy |
| SAFE | Process safety and environmental | HAZID, HAZOP, LOPA, SIL determination input, QRA, facility siting, fire and gas mapping, environmental studies, emissions, permits |
| FIRE | Fire protection | Fire protection philosophy, fire water demand and network, fire zones and fireproofing, fixed fire protection systems, fire pump and fire equipment datasheets, requisitions and vendor data |
| MECH | Mechanical | Static equipment (vessels, columns, tanks, exchangers, heaters), rotating equipment, packages, mechanical datasheets and calculations, technical bid evaluation, vendor data review |
| PIPE | Piping | Plot plan and layout, 3D model, piping materials (classes, valve and specialty items, MTO), stress, supports, isometrics, tie-ins, hydrotest |
| CIVL | Civil and structural | Survey, geotechnical, grading and drainage, roads, foundations, structures, pipe racks, buildings, HVAC, architecture |
| INST | Instrumentation and control | Instrument index, datasheets, control valves, PSV datasheets (if I&C owned), loops, I/O, control and safety systems, F&G system, C&E, wiring, installation, analyzers, telecom |
| ELEC | Electrical | Load list, single-lines, power studies, equipment specs, cable schedule, raceway, grounding, lighting, heat tracing, cathodic protection, hazardous area drawings |
| PROJ | Project management, controls and document control | Execution plan, schedule, estimate, change control, interface management, document control, deliverables register, gate reviews |
| SCM | Procurement and materials | Requisition processing, bidding, PO award, expediting, inspection, logistics, site material receipt and issue |
| CONS | Construction | Constructability, path of construction, AWP (CWP/IWP), field engineering, RFIs, field changes, as-builts |
| COMM | Completions and commissioning | Systemization, ITRs, punch, turnover, pre-commissioning, commissioning, handover |
| VEND | Vendors and fabricators (external) | Quotations, vendor drawings and data, certified data, fabrication, test certificates, data books |
| OWNR | Owner and operations (external) | Business case, design basis inputs, standards, reviews and approvals, operations input, handover acceptance |

## Systems (use these exact names in `system`)

The client's stack. Use "Excel / Word" where a task uses no specific system.

| System | Used for | Status today |
|---|---|---|
| HYSYS | Process simulation (AspenTech) | In use |
| HTRI | Exchanger thermal design (Mechanical) | In use |
| Flare / relief tool | Relief and flare hydraulics (e.g. Aspen Flare System Analyzer) | Assumed; confirm |
| SPID | Smart P&ID (Octave, formerly Hexagon) | In use |
| SI | Smart Instrumentation (Octave) | In use |
| SPEL | Smart Electrical (Octave) | In use |
| S3D | Smart 3D (Octave) | In use |
| SPF | SmartPlant Foundation (Octave) integration and tag hub | In use, only partly working |
| CAESAR II | Pipe stress | In use |
| Tekla | Structural steel modelling and fabrication | In use |
| ETAP | Power system studies | In use |
| Mechanical calc tool | Vessel / tank / heater calculations (PV Elite, COMPRESS, or equal) | Assumed; confirm |
| PHA tool | HAZOP / LOPA recording (PHA-Pro or equal) | Assumed; confirm |
| Document Locator | Document control (ColumbiaSoft) | In use |
| Purchasing DB | In-house SQL database: MRs, POs, PO lines, expediting | In use |
| Jovix | Site material management | In use |
| P6 | Schedule | In use |
| iConstruct | AWP and model-based construction (Navisworks based) | In use |
| Procore | Field management: RFIs, submittals, daily logs | In use |
| Smart Completions | Systemization, ITRs, punch, turnover | In use |
| DCS / SIS config | Control and safety system configuration (vendor tools) | External / vendor |
| Excel / Word | Spreadsheets and documents with no system of record | In use |

Integration state today (use it to choose `method`):
- HYSYS to SPID, SI, datasheets: no link. Stream data is copied by hand into the line list, P&ID data and datasheets.
- SPID and S3D: rough correlation through SPF (P&ID-to-model check, partial).
- SPID and SI: not linked. Instrument tags are created in both and correlated by hand.
- SPEL: not linked to SPID or SI. Loads and cables are keyed in by hand.
- S3D to CAESAR II: file export of stress lines. CAESAR II results go back by hand (support changes, markups).
- S3D and Tekla: model file exchange (reference models), not data-linked.
- S3D isometrics and MTO to Purchasing DB: spreadsheet export, re-keyed or imported by hand.
- Purchasing DB to Jovix: PO and PO-line data passed for receiving.
- S3D and Tekla models to iConstruct: through Navisworks; Jovix status into iConstruct for material availability.
- Tags into Smart Completions: spreadsheet loads from engineering lists.
- Documents of all kinds move through Document Locator (transmittals, comments).

## Ownership agreed with the client

- Materials selection and corrosion allowances: Process and Mechanical jointly; Mechanical issues.
- Exchanger thermal design: Mechanical, in HTRI. Process does preliminary sizing only.
- Fire pumps and fixed fire protection: Fire protection.
- Relief valves: Process sizes them, I&C specifies and quotes them, the vendor does the final sizing, and
  I&C and Process align the final sizing with the vendor before purchase.

## Phases

`FEL1`, `FEL2`, `FEL3`, `DD` (detailed design), `CON` (construction), `COM` (commissioning and handover).

## Maturity levels (for `level` on inputs)

0 not started, 1 concept, 2 preliminary (IFR / rev A), 3 defined (IFD / issued for HAZOP or purchase), 4 final (IFC / approved / certified).

## Schema

```json
{
  "discipline": "PIPE",
  "tasks": [
    {
      "id": "PIPE-T010",
      "name": "Route lines in the 3D model",
      "phases": ["FEL3", "DD"],
      "system": "S3D",
      "activity": "PIP-02",
      "description": "One sentence: what the task does.",
      "produces": ["PIPE-I020"],
      "consumes": [
        {"item": "PROC-I030", "use": "line number, size, spec, fluid, design P/T, insulation",
         "method": "integrated", "level": 3}
      ]
    }
  ],
  "items": [
    {
      "id": "PIPE-I020",
      "name": "Routed piping model",
      "system": "S3D",
      "form": "model",
      "content": "What it contains: the attributes or data others take from it.",
      "owner_task": "PIPE-T010"
    }
  ]
}
```

Rules:
- IDs: tasks `<CODE>-T###`, items `<CODE>-I###`, numbered in rough work order, unique.
- `system`: one name from the systems table (the system the task works in or the item lives in).
- `activity`: the closest activity from the activity list below (the summary-level map). Required.
- `form`: one of `data` (rows or attributes in a system or list), `document` (report, specification, datasheet),
  `drawing`, `model` (3D or calculation model), `decision` (an agreed basis, approval or resolution).
- Each item has exactly one owner task in the same discipline, and that task lists it in `produces`.
- `consumes` references any discipline's items by ID.
- Information a task needs that no item carries yet goes in a top-level `gaps` array of the file
  (`{"task", "from", "info", "method", "level"}`) until the owning discipline adds the item. The build lists
  open gaps, unused items and tasks without inputs as warnings.
  - `use`: what the consuming task takes from the item, specific enough to check (attributes, values).
  - `method` today: `integrated` (system-to-system, live or by publish/retrieve), `file` (export/import of a
    file), `manual` (read the document or list and re-enter by hand), `review` (read and comment or approve,
    no data transferred), `meeting` (workshop or coordination meeting).
  - `level`: the maturity the item must have before the task can use it.
- Detail: engineering disciplines 25 to 45 tasks; project-side disciplines 15 to 30. A task is one piece of work
  one person or a small team does and issues (for example "Size control valves", "Prepare instrument
  datasheets", "Run the motor-starting study"), not a whole deliverable family.
- Items are the actual information that moves: a list, a set of attributes, a drawing, a model, a markup, a
  decision. Break a document up when different parts go to different people (for example "Stream data" and
  "Equipment process duties" rather than "H&MB").
- Include the return flows: comments, markups, holds, clash reports, vendor data, RFIs, field changes, as-built
  redlines, HAZOP actions, and so on.

## Activity list (summary level, for `activity`)

- FEL-01: Business case, capacity and product slate
- PRJ-01: Design basis (BOD)
- PRJ-03: Document register and portal
- PRJ-05: Execution plan and contracting strategy
- SEL-04: Permitting and environmental basis
- PRJ-04: PE review, seal and IFC issue
- FEL-02: Configuration options and screening
- PRC-01: Heat and material balance
- PRC-02: Process equipment sizing
- PRC-05: Block flow diagram
- PRC-06: Process flow diagrams
- PRJ-02: Crude assay characterisation
- PRC-00: Rigorous simulation and model calibration
- PRC-03: Relief load and PSV sizing (unit)
- PRC-04: Control loops and SIF definition
- PRC-07: Process design report
- PRC-08: P&IDs, line list, instrument index
- SEL-01: Alternatives evaluation and select decision
- SEL-02: Technology and licensor selection
- SEL-03: Utility and offsite basis
- SAF-02: Global flare load study
- SAF-01: Preliminary HAZOP
- SAF-04: Siting study, QRA, F&G mapping
- SAF-03: Formal HAZOP and LOPA workshop
- MEC-01: Mechanical design calculations
- MEC-02: Equipment datasheets
- MEC-03: Equipment GA drawings
- VEN-01: Vendor enquiries and vendor data
- PRO-01: Requisitions and technical bid evaluations
- FEL-03: Site screening and selection
- LAY-01: Plot plan and equipment layout
- LAY-02: Sections and 3D layout model
- LAY-03: 3D model reviews and constructability
- PIP-01: Piping material classes
- PIP-02: Piping routing and 3D model
- PIP-03: Pipe stress and supports (screening)
- PIP-04: Isometrics and piping MTO
- PIP-05: Detailed pipe stress (CAESAR II)
- CIV-01: Geotechnical, civil and structural design
- CIV-02: Foundation and structural steel detailing
- ICS-01: Control philosophy and schemes
- ICS-07: ICS architecture
- ICS-02: SIF list and SIL determination (LOPA)
- ICS-03: Cause and effect matrix
- ICS-04: Control valve sizing
- ICS-05: I/O list
- ICS-06: Loop diagrams
- ICS-08: SIL verification and SRS
- ICS-09: Instrument installation design
- ELE-01: Electrical load list
- ELE-03: Electrical sizing, single-line diagrams
- ELE-02: Hazardous area classification
- ELE-04: Cable schedule
- ELE-05: Power system studies and protection
- ELE-06: Electrical layouts
- CON-01: Constructability, modularisation and path of construction
- CON-02: Work packaging and system boundaries
- FEL-04: Class 5 estimate and economics
- CST-01: Class 4 cost estimate
- CST-02: Class 3 cost estimate
- CST-03: Control estimate
