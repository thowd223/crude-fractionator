# Integration priorities

Ranked from the 663 manual hand-offs between systems in the interface register. 645 of them (97%) fall in the 22 candidates below; 145 are a person reading a document to do their own work, which no integration removes. Scoring is described in `exchange/rank.py`. Ease ratings are assumptions to confirm with IT and the tool owners.

| Rank | Wave | ID | Integration | Systems | Hand-offs | Value | Ease | Priority | Prerequisite |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | INT-15 | Deliverables, numbering and progress | Document Locator ↔ P6 ↔ discipline lists | 42 | 77 | easy | 77 | Document numbering rule |
| 2 | 1 | INT-14 | Procurement status to the schedule | Purchasing DB ↔ P6 | 26 | 53 | easy | 53 | MR/PO to P6 activity code |
| 3 | 1 | INT-01 | Simulation to process data | HYSYS → datasheets, line list, SI, HTRI | 26 | 48 | easy | 48 | Stream-to-line numbering rule |
| 4 | 1 | INT-16 | Model to construction work packages | S3D, SPEL, SI → iConstruct, Procore | 43 | 57 | medium | 43 | CWA/CWP coding on model objects |
| 5 | 1 | INT-02 | Line list as one record | SPID line data ↔ line sizing ↔ S3D, SI, CAESAR II | 31 | 56 | medium | 42 | Agreed line numbering and line-list ownership by column |
| 6 | 2 | INT-11 | Requisitions into purchasing | Document Locator / Excel → Purchasing DB | 46 | 42 | easy | 42 | Requisition line template |
| 7 | 2 | INT-17 | Systemization and completions | SPID, SI, S3D → Smart Completions ↔ P6 | 41 | 52 | medium | 39 | Tag crosswalk; system codes on tags |
| 8 | 2 | INT-12 | Material take-off into purchasing | S3D / Excel MTOs → Purchasing DB | 14 | 38 | easy | 38 | Commodity code to purchasing ident map |
| 9 | 2 | INT-21 | Design basis values | Basis documents → calcs and design tools | 55 | 38 | easy | 38 | None |
| 10 | 2 | INT-06 | Equipment register | Process and mechanical datasheets → S3D, SI, SPEL, HTRI, calc tools | 49 | 49 | medium | 37 | Equipment class library (CFIHOS subset) |
| 11 | 2 | INT-13 | Receipt to site | Purchasing DB / vendors → Jovix → Procore, iConstruct | 17 | 37 | easy | 37 | PO line to Jovix item mapping |
| 12 | 2 | INT-10 | Safety lifecycle to design | PHA tool → SPID, SI, DCS/SIS | 30 | 48 | medium | 36 | Tag crosswalk; SIF numbering |
| 13 | 3 | INT-03 | P&ID tags into the instrument index | SPID → SI | 28 | 46 | medium | 34 | Tag crosswalk (harvest step 3) |
| 14 | 3 | INT-07 | Electrical loads and studies | Motor and package data → SPEL ↔ ETAP | 40 | 32 | easy | 32 | Load list template for other disciplines |
| 15 | 3 | INT-18 | Structural interfaces | S3D ↔ Tekla, loads and civil data | 64 | 33 | medium | 25 | Support and foundation mark numbering |
| 16 | 3 | INT-22 | Vendor data into engineering | Certified vendor documents → engineering tools | 28 | 42 | hard | 21 | CFIHOS vendor data requirements in POs; Equipment class library |
| 17 | 3 | INT-09 | Relief and flare data | Relief tool ↔ SI, CAESAR II, equipment data | 15 | 27 | medium | 20 | Tag crosswalk (PSV tags) |
| 18 | 3 | INT-05 | Piping specs to the model, SI and purchasing | Piping class spec → S3D, SI, Purchasing DB | 9 | 20 | easy | 20 | Commodity code to purchasing ident map |
| 19 | 3 | INT-04 | In-line instrument and routing data to the model | SI ↔ S3D | 10 | 23 | medium | 17 | Tag crosswalk |
| 20 | 3 | INT-19 | Pipe stress interfaces | S3D ↔ CAESAR II ↔ equipment | 10 | 21 | medium | 16 | Equipment class library (via INT-06) |
| 21 | 3 | INT-08 | I&C–electrical signals | SPEL ↔ SI | 9 | 16 | easy | 16 | Tag crosswalk |
| 22 | 3 | INT-20 | As-built and field changes | Procore → SPID, S3D, SI, SPEL, Tekla | 12 | 21 | hard | 10 | Tag crosswalk; Document numbering rule |

## Candidates

### 1. INT-15 Deliverables, numbering and progress (wave 1)

Deliverable lists, document numbers, WBS and cost codes, schedule dates and progress re-keyed between Document Locator, P6 and discipline workbooks.

- **Systems:** Document Locator ↔ P6 ↔ discipline lists
- **Manual hand-offs:** 42 (effort 422.0, 244 downstream tasks, 31% late-stage)
- **Ease:** easy. Both systems take structured imports; numbering is a rule, not a document.
- **Approach:** One deliverables register keyed by document number feeds Document Locator and P6; progress comes from document status, not workbooks.
- **Prerequisite:** Document numbering rule
- **Items:** PROJ-I060, PROJ-I140, PROJ-I030, PROJ-I040, PROJ-I050, PROJ-I070, VEND-I060, PROJ-I310, PROJ-I130, PROJ-I180, OWNR-I284, PROJ-I340, PROJ-I280, PROJ-I230, SCM-I010, SCM-I360, CIVL-I901, CIVL-I902, ELEC-I901, ELEC-I902, INST-I901, INST-I902, MECH-I901, MECH-I902, PIPE-I901, PIPE-I902, PROC-I901, PROC-I902

### 2. INT-14 Procurement status to the schedule (wave 1)

Need dates, PO dates, vendor print status and delivery forecasts copied between the purchasing database and P6.

- **Systems:** Purchasing DB ↔ P6
- **Manual hand-offs:** 26 (effort 199.0, 220 downstream tasks, 56% late-stage)
- **Ease:** easy. P6 has a documented API and the purchasing database is yours.
- **Approach:** Link each MR and PO to its P6 activity; push forecasts to P6 and pull need dates back nightly.
- **Prerequisite:** MR/PO to P6 activity code
- **Items:** SCM-I130, SCM-I140, SCM-I170, SCM-I200, PROJ-I150, CONS-I140, CONS-I090, VEND-I160, VEND-I310, MECH-I560, SCM-I340, CONS-I190, OWNR-I160

### 3. INT-01 Simulation to process data (wave 1)

Stream, case and duty data copied from HYSYS into datasheets, the line list, SI process data and HTRI inputs.

- **Systems:** HYSYS → datasheets, line list, SI, HTRI
- **Manual hand-offs:** 26 (effort 153.6, 351 downstream tasks, 0% late-stage)
- **Ease:** easy. HYSYS exposes stream data through its spreadsheet and automation interface; the targets take tabular imports.
- **Approach:** Publish a tagged stream table from each HYSYS case revision and load it into datasheet templates and SI process data, keyed by stream and line number.
- **Prerequisite:** Stream-to-line numbering rule
- **Items:** PROC-I110, PROC-I030, PROC-I060, PROC-I155, PROC-I315, PROC-I160, PROC-I220

### 4. INT-16 Model to construction work packages (wave 1)

IFC isometrics, supports, cable and instrument schedules, steel and CWP scope moved by hand into iConstruct and Procore.

- **Systems:** S3D, SPEL, SI → iConstruct, Procore
- **Manual hand-offs:** 43 (effort 208.5, 221 downstream tasks, 66% late-stage)
- **Ease:** medium. iConstruct reads S3D directly; SPEL, SI and Tekla content needs CWA/CWP codes assigned first.
- **Approach:** Assign CWA/CWP codes in each authoring tool and let iConstruct read model and schedule data by code; IFC release status comes from Document Locator.
- **Prerequisite:** CWA/CWP coding on model objects
- **Items:** PIPE-I400, PIPE-I300, PIPE-I390, PIPE-I480, PIPE-I540, ELEC-I320, ELEC-I322, ELEC-I360, ELEC-I272, INST-I300, INST-I310, INST-I320, INST-I330, CIVL-I240, CIVL-I190, CIVL-I340, CONS-I050, CONS-I060, CONS-I170, CONS-I200, CONS-I270, PROJ-I320, COMM-I050, OWNR-I120, CONS-I040

### 5. INT-02 Line list as one record (wave 1)

Line sizes, process conditions, design pressure and temperature and piping class copied between SPID, the line-sizing workbook, S3D, SI and stress.

- **Systems:** SPID line data ↔ line sizing ↔ S3D, SI, CAESAR II
- **Manual hand-offs:** 31 (effort 243.8, 311 downstream tasks, 2% late-stage)
- **Ease:** medium. Line data sits in SPID and in workbooks at once; one home has to be chosen before anything can be linked.
- **Approach:** Make one line list the record (SPID line properties or the registry), with Process and Piping each owning their columns; S3D, SI and CAESAR II read from it.
- **Prerequisite:** Agreed line numbering and line-list ownership by column
- **Items:** PROC-I190, PROC-I210, PIPE-I160, PROC-I130, PROC-I111, PIPE-I220, PIPE-I210

### 6. INT-11 Requisitions into purchasing (wave 2)

Requisition headers and lines, bidders, bid bulletins, awards and POs typed from documents into the purchasing database.

- **Systems:** Document Locator / Excel → Purchasing DB
- **Manual hand-offs:** 46 (effort 106.3, 213 downstream tasks, 55% late-stage)
- **Ease:** easy. The purchasing database is in-house SQL, so you control its import.
- **Approach:** Issue each requisition with a structured header and line file alongside the PDF; the purchasing database imports it and returns the MR number.
- **Prerequisite:** Requisition line template
- **Items:** MECH-I350, MECH-I390, MECH-I400, ELEC-I130, ELEC-I140, ELEC-I150, ELEC-I160, ELEC-I170, CIVL-I307, CIVL-I310, CIVL-I050, PIPE-I430, SCM-I030, SCM-I050, SCM-I060, SCM-I070, SCM-I080, SCM-I110, SCM-I120, SCM-I150, OWNR-I060, PROJ-I020, PROJ-I210, VEND-I020, VEND-I030, VEND-I040, VEND-I324, OWNR-I285

### 7. INT-17 Systemization and completions (wave 2)

System boundaries, tag-to-system assignments, ITR requirements, test packs, punch and turnover status keyed into Smart Completions and back.

- **Systems:** SPID, SI, S3D → Smart Completions ↔ P6
- **Manual hand-offs:** 41 (effort 210.0, 155 downstream tasks, 69% late-stage)
- **Ease:** medium. Smart Completions imports tag registers; the system-to-tag link has to exist in the design tools first.
- **Approach:** Assign system and subsystem codes to tags in SPID; load the full tag register with those codes into Smart Completions from the tag crosswalk.
- **Prerequisite:** Tag crosswalk; system codes on tags
- **Items:** COMM-I020, COMM-I030, COMM-I040, COMM-I140, COMM-I150, COMM-I250, COMM-I270, INST-I260, INST-I380, INST-I410, MECH-I570, ELEC-I400, CONS-I280, CONS-I290, CONS-I300, PIPE-I500, CONS-I350, VEND-I270, OWNR-I210, SAFE-I330, INST-I420, PROC-I375, COMM-I240

### 8. INT-12 Material take-off into purchasing (wave 2)

Piping, instrument, steel and spares quantities re-typed from MTO workbooks into purchasing.

- **Systems:** S3D / Excel MTOs → Purchasing DB
- **Manual hand-offs:** 14 (effort 107.7, 101 downstream tasks, 82% late-stage)
- **Ease:** easy. S3D produces MTO reports by ident; the database is yours.
- **Approach:** Load MTOs by ident and revision into the purchasing database and compute the delta to buy, applying the surplus policy.
- **Prerequisite:** Commodity code to purchasing ident map
- **Items:** PIPE-I420, INST-I340, CIVL-I248, CIVL-I200, PROJ-I373, COMM-I110, COMM-I120, MECH-I510, VEND-I260, SCM-I350, CIVL-I070, ELEC-I050, PROJ-I080

### 9. INT-21 Design basis values (wave 2)

Site conditions, design criteria, assays and philosophies read from basis documents and re-typed into every calculation.

- **Systems:** Basis documents → calcs and design tools
- **Manual hand-offs:** 55 (effort 64.9, 353 downstream tasks, 4% late-stage)
- **Ease:** easy. No tool link is needed: the values only have to be published once as data.
- **Approach:** Publish each basis as a governed parameter table (site data, criteria, cases) that calculations reference instead of copying.
- **Prerequisite:** None
- **Items:** CIVL-I030, CIVL-I020, CIVL-I390, CIVL-I010, CIVL-I065, PROC-I010, OWNR-I030, OWNR-I050, MECH-I030, MECH-I040, PIPE-I030, PROC-I095, PROC-I120, SAFE-I240, SAFE-I062, FIRE-I192, FIRE-I200, FIRE-I220, PROC-I280, ELEC-I010, ELEC-I012, PROJ-I371, VEND-I321, VEND-I322

### 10. INT-06 Equipment register (wave 2)

Equipment tags, duties, sizes, nozzles and outline data copied from Excel datasheets and lists into the model, SI, SPEL and design tools.

- **Systems:** Process and mechanical datasheets → S3D, SI, SPEL, HTRI, calc tools
- **Manual hand-offs:** 49 (effort 160.7, 343 downstream tasks, 6% late-stage)
- **Ease:** medium. Equipment data lives in Excel datasheets; it needs a structured equipment register before it can be shared.
- **Approach:** Hold equipment attributes in one register keyed by tag (CFIHOS equipment classes); datasheets, S3D, SI and SPEL read from it.
- **Prerequisite:** Equipment class library (CFIHOS subset)
- **Items:** MECH-I080, MECH-I170, MECH-I290, MECH-I300, MECH-I420, MECH-I590, PROC-I170, PROC-I171, PROC-I175, PROC-I176, MECH-I140, FIRE-I230, MECH-I220, MECH-I240, MECH-I250, MECH-I090, MECH-I100, MECH-I150, MECH-I130

### 11. INT-13 Receipt to site (wave 2)

Shipping notices, packing lists, MTRs, receipts, issues and shortages keyed between purchasing, vendors, Jovix and the field tools.

- **Systems:** Purchasing DB / vendors → Jovix → Procore, iConstruct
- **Manual hand-offs:** 17 (effort 90.3, 71 downstream tasks, 100% late-stage)
- **Ease:** easy. Jovix takes PO and shipment imports; field tools need only status by IWP.
- **Approach:** Load PO lines and shipping notices into Jovix from the purchasing database; publish availability and shortages to iConstruct by IWP.
- **Prerequisite:** PO line to Jovix item mapping
- **Items:** SCM-I250, VEND-I220, VEND-I170, SCM-I270, SCM-I300, SCM-I310, SCM-I320, SCM-I330, VEND-I325, MECH-I530, VEND-I290, CONS-I020, PIPE-I410, VEND-I200

### 12. INT-10 Safety lifecycle to design (wave 2)

HAZOP actions, SIL targets, SIFs, trips and cause-and-effects carried by hand from the PHA tool and Word into SPID, SI and the DCS/SIS.

- **Systems:** PHA tool → SPID, SI, DCS/SIS
- **Manual hand-offs:** 30 (effort 137.7, 272 downstream tasks, 43% late-stage)
- **Ease:** medium. PHA records are structured; the cause-and-effect and SRS are Word or Excel documents.
- **Approach:** Keep the SIF and trip list as data keyed by instrument tag, linked to HAZOP/LOPA scenario IDs; generate cause-and-effects from it.
- **Prerequisite:** Tag crosswalk; SIF numbering
- **Items:** SAFE-I152, SAFE-I160, SAFE-I162, SAFE-I280, SAFE-I170, INST-I210, INST-I220, INST-I240, INST-I241, PROC-I235, INST-I170, VEND-I280, SAFE-I180, PROC-I230, PROC-I240

### 13. INT-03 P&ID tags into the instrument index (wave 3)

Instrument tags, loops and control valve data re-typed from issued P&IDs into SI, SI sizes back onto the P&IDs, and SI data re-typed into requisition and vendor documents.

- **Systems:** SPID → SI
- **Manual hand-offs:** 28 (effort 155.0, 316 downstream tasks, 5% late-stage)
- **Ease:** medium. Both are Octave tools, but the SPF publish/retrieve link works poorly today; a direct tag compare works without SPF.
- **Approach:** Compare SPID and SI tag lists on every P&ID issue; report new, deleted and changed tags for I&C to accept, instead of re-reading drawings.
- **Prerequisite:** Tag crosswalk (harvest step 3)
- **Items:** PROC-I200, PROC-I340, PROC-I341, INST-I050, INST-I071, INST-I060, INST-I070, INST-I080, INST-I110, INST-I261

### 14. INT-07 Electrical loads and studies (wave 3)

Motor ratings, load lists, certified electrical data and study results moved between Mechanical, vendors, SPEL and ETAP.

- **Systems:** Motor and package data → SPEL ↔ ETAP
- **Manual hand-offs:** 40 (effort 138.7, 137 downstream tasks, 22% late-stage)
- **Ease:** easy. ETAP has an established data exchange with SPEL; the load list is already structured in SPEL.
- **Approach:** Use SPEL as the load record and run the SPEL–ETAP exchange for loads, ratings and study results; collect other disciplines' loads on one template.
- **Prerequisite:** Load list template for other disciplines
- **Items:** MECH-I330, MECH-I440, VEND-I120, ELEC-I192, ELEC-I202, ELEC-I110, ELEC-I220, ELEC-I230, ELEC-I240, ELEC-I252, ELEC-I030, ELEC-I090, ELEC-I120, CIVL-I305, INST-I280, INST-I161, INST-I351, INST-I350, MECH-I210

### 15. INT-18 Structural interfaces (wave 3)

Rack and structure configuration, support loads, equipment loads and underground data passed between S3D, Tekla and civil calcs.

- **Systems:** S3D ↔ Tekla, loads and civil data
- **Manual hand-offs:** 64 (effort 106.2, 205 downstream tasks, 16% late-stage)
- **Ease:** medium. S3D and Tekla exchange steel models; loads are still calc reports.
- **Approach:** Exchange steel between S3D and Tekla by model import; publish support and equipment loads as tables keyed by support and foundation mark.
- **Prerequisite:** Support and foundation mark numbering
- **Items:** CIVL-I210, CIVL-I220, CIVL-I135, CIVL-I130, CIVL-I155, CIVL-I150, CIVL-I140, CIVL-I100, CIVL-I110, PIPE-I260, PIPE-I310, MECH-I430, VEND-I080, CIVL-I060, CIVL-I040, PIPE-I040, PIPE-I070, PIPE-I060, CONS-I240, CIVL-I270, CIVL-I120, CIVL-I170, CIVL-I195, CIVL-I160, CIVL-I165

### 16. INT-22 Vendor data into engineering (wave 3)

Certified drawings, loads, nameplate data and IOMs read from vendor PDFs and re-typed into engineering tools and the asset register.

- **Systems:** Certified vendor documents → engineering tools
- **Manual hand-offs:** 28 (effort 57.9, 256 downstream tasks, 69% late-stage)
- **Ease:** hard. It depends on vendors returning structured data, which only the purchase order can require.
- **Approach:** Require CFIHOS vendor data sheets (Excel by tag) in every PO and load them to the equipment register on receipt.
- **Prerequisite:** CFIHOS vendor data requirements in POs; Equipment class library
- **Items:** VEND-I140, MECH-I450, VEND-I230, VEND-I240, VEND-I070, VEND-I250, MECH-I490, MECH-I500, OWNR-I200, OWNR-I180

### 17. INT-09 Relief and flare data (wave 3)

Relief loads, PSV datasheets, flare back-pressures and final valve sizing re-entered between the relief tool, SI, stress and datasheets.

- **Systems:** Relief tool ↔ SI, CAESAR II, equipment data
- **Manual hand-offs:** 15 (effort 49.7, 244 downstream tasks, 4% late-stage)
- **Ease:** medium. The relief tool output is tabular; PSV tags already exist in SI.
- **Approach:** Publish the relief load summary by PSV tag into SI; return the agreed vendor sizing to the relief and flare model.
- **Prerequisite:** Tag crosswalk (PSV tags)
- **Items:** PROC-I250, PROC-I251, PROC-I260, PROC-I261, INST-I145

### 18. INT-05 Piping specs to the model, SI and purchasing (wave 3)

Piping class ratings, materials and commodity codes re-entered into the S3D catalogue, SI and purchasing.

- **Systems:** Piping class spec → S3D, SI, Purchasing DB
- **Manual hand-offs:** 9 (effort 42.6, 111 downstream tasks, 30% late-stage)
- **Ease:** easy. The S3D spec is already structured; the work is mapping commodity codes to purchasing idents once.
- **Approach:** Treat the S3D spec as the record and publish class and commodity tables to SI and the purchasing database.
- **Prerequisite:** Commodity code to purchasing ident map
- **Items:** PIPE-I110, PIPE-I120, PIPE-I130, PIPE-I140

### 19. INT-04 In-line instrument and routing data to the model (wave 3)

In-line instrument dimensions, flow-element straight runs, junction boxes and tray routing passed between SI and S3D by hand.

- **Systems:** SI ↔ S3D
- **Manual hand-offs:** 10 (effort 40.0, 173 downstream tasks, 17% late-stage)
- **Ease:** medium. S3D and SI share tag numbers but no live link; dimensional tables export from SI cleanly.
- **Approach:** Export SI dimensional data by tag for S3D placement; return routed lengths and junction box locations to SI.
- **Prerequisite:** Tag crosswalk
- **Items:** INST-I072, INST-I091, INST-I151, INST-I291, ELEC-I330, PIPE-I180, INST-I115, INST-I290

### 20. INT-19 Pipe stress interfaces (wave 3)

Nozzle allowables, thermal growth, stress markups and results passed by hand between equipment data, CAESAR II and the model.

- **Systems:** S3D ↔ CAESAR II ↔ equipment
- **Manual hand-offs:** 10 (effort 19.9, 157 downstream tasks, 25% late-stage)
- **Ease:** medium. S3D-to-CAESAR II export exists; nozzle data comes from datasheets.
- **Approach:** Export stress lines from S3D to CAESAR II; carry nozzle allowables from the equipment register.
- **Prerequisite:** Equipment class library (via INT-06)
- **Items:** MECH-I280, MECH-I600, MECH-I480, PIPE-I230, PIPE-I270, PIPE-I240, VEND-I090

### 21. INT-08 I&C–electrical signals (wave 3)

MCC and switchgear signals, interlock schematics, heat tracing alarms and area classification passed between SPEL and SI.

- **Systems:** SPEL ↔ SI
- **Manual hand-offs:** 9 (effort 42.0, 129 downstream tasks, 0% late-stage)
- **Ease:** easy. Same vendor, same tag conventions; the signal list is structured on both sides.
- **Approach:** Exchange the MCC/switchgear interface signal list by tag between SPEL and SI on each issue.
- **Prerequisite:** Tag crosswalk
- **Items:** ELEC-I340, ELEC-I350, ELEC-I304, ELEC-I072, ELEC-I070, ELEC-I060

### 22. INT-20 As-built and field changes (wave 3)

Redlines, RFIs, field changes and dispositions read from Procore and re-drawn in each design tool.

- **Systems:** Procore → SPID, S3D, SI, SPEL, Tekla
- **Manual hand-offs:** 12 (effort 25.3, 73 downstream tasks, 61% late-stage)
- **Ease:** hard. The edits are drawing judgements; what can be linked is the tag and document reference, not the change itself.
- **Approach:** Tag each RFI, field change and redline with document number and tags so that each design tool sees open changes against its objects.
- **Prerequisite:** Tag crosswalk; Document numbering rule
- **Items:** CONS-I330, CONS-I210, CONS-I220, CONS-I230, CIVL-I360, CIVL-I365, PROC-I320
