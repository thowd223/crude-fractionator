# Dependency map for a live project: approach

How to extend the design dependency map (`cfu/wrapup/depmap.py`, CFU-000-PM-DEP-001/002)
to a real project where the deliverable list is not known up front: isometrics not yet
numbered or split into sheets, plan drawings not yet defined, wiring not yet laid out.

Core idea: draw the links between **engineering objects** (lines, tags, equipment,
cables, plot areas), not between document numbers. The objects become known before
their documents are numbered. Documents are then generated from those objects.

## 1. Three levels of detail

| Level | What it holds | How it is made | Rough size |
|---|---|---|---|
| **L1 Design steps** | Wave-level activities (simulation, P&IDs, stress, cable sizing) like `activities.py` | Written by hand at kickoff from a template of past projects | 50–200 |
| **L2 Deliverable types** | Piping iso, instrument loop diagram, motor datasheet, area plot plan, wiring diagram | Template library. Each type states which object kind it comes from and what it needs | 100–300 |
| **L3 Instances** | ISO-1001-01 sh 2, loop diagram for FIC-101, wiring diagram for JB-12 | **Generated** from the design data, never typed in by hand | Thousands |

Only L1 and L2 are maintained by hand. L3 is rebuilt from the design databases every night.

## 2. Make the objects the backbone

The design's registers list the objects before the documents are numbered:

- **Line list** (from the P&IDs). Rule: every line in a stress-relevant class or ≥ 2 in
  gets an iso. Each new line gets an iso placeholder automatically. Real sheet numbers
  replace it once the 3D model issues them.
- **Instrument index**. Each loop needs a loop diagram, a datasheet, an I/O assignment,
  and a SIL check if it is a safety function.
- **Equipment list**. Each item needs a datasheet, vendor data, a foundation, and a
  motor if it has a driver.
- **Cable schedule / junction box list**. Each cable or junction box needs a wiring
  diagram and termination schedule. A cable can't be sized until its route length is
  known, which comes from layout.
- **Plot areas / grid zones**. Each area needs plan drawings and steel and foundation
  drawings. Sheets are split later.

Links are written against object kinds. For example, "iso of line X needs line X at the
P&ID revision, routing in the model, the stress result and the pipe class". When line X
appears, that link appears with it.

## 3. Forecast what isn't known yet

For a type whose objects don't exist yet, create **placeholder quantities** from
benchmark ratios. Examples:

- isos ≈ 1.3 × line count;
- wiring diagrams ≈ 1 per 8 cables;
- plan sheets per 1,000 m² of plot.

Placeholders carry the same links, so planning and impact analysis work from day one.
They are replaced as real objects arrive, and the gap between forecast and actual is
itself a progress measure. This is rolling-wave planning: stay coarse where the design
is unknown and get finer as it firms up.

## 4. Give each link a required maturity and a consumed revision

- **Required maturity:** "Line sizing needs the heat and material balance at
  *preliminary*, but isos need the P&ID at *IFD*." This tells you what can start early
  and at what risk.
- **Consumed revision:** record which revision of each input a deliverable was built
  on. This is the real-world version of the build trace (`depmap.py --trace`). If the
  P&ID moves from Rev B to Rev C and the iso was built on B, the link is flagged
  **suspect**.

The suspect list from a change is the engineering change / MOC impact list, at the level
of individual documents and objects. It comes out automatically instead of from memory.

## 5. Where the data comes from

Don't build a new database of record. Read from the project's existing systems,
through exports or APIs:

| Data | Typical source |
|---|---|
| P&IDs, line list | SmartPlant P&ID / AVEVA Diagrams / Plant 3D |
| Routing, isos, sheet counts | E3D / S3D / Plant 3D |
| Instruments | SPI / INtools, or the instrument index spreadsheet |
| Electrical | SPEL / ETAP / cable schedule |
| Document numbers, revisions, status | Document control (Aconex, Documentum, SharePoint register) |
| Holds | HAZOP action log, vendor data tracker, holds register |

A nightly script pulls these sources, applies the L2 rules to create the L3 instances,
and compares consumed revisions with current ones. Storage can be Postgres tables (nodes
and edges) or Neo4j. Spreadsheets will do for a pilot.

The script publishes:

- **Ready to start:** every input is at the required maturity.
- **Blocked:** a list of what is missing, each with an owner.
- **Suspect:** items whose inputs changed since they were built.
- **Change impact:** what a proposed change would affect, for ECN / MOC review.
- **Forecast vs actual** document counts.
- **Schedule logic:** L1/L2 links drive the planner's logic in P6 instead of being
  drawn by hand.

## 6. Mapping from this repo

| Live-project piece | Existing piece here |
|---|---|
| L1 template | `cfu/wrapup/activities.py` |
| L2 rules | Document-prefix mapping (`doc_map` in `depmap.py`) |
| Consumed-revision staleness check | Build trace (`python -m cfu.wrapup.depmap --trace`) |
| **New:** object layer | To build: generate instances from `data/lines.json`, `instruments.json`, `io_list.json`, `electrical.json` |

## 7. Proposed prototype (not yet built)

1. Generate L3 instances: per-line iso placeholders, per-loop diagrams,
   per-junction-box wiring diagrams, each with its links.
2. Add required maturity and consumed revision to every link.
3. Add a **Suspect** view to `portal/dependencies.html`. For example, change one stream
   on the heat and material balance and see exactly which isos and datasheets go stale.
