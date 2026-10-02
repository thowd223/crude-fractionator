# Project conventions (all disciplines)

This file is the contract between all deliverable generators. Read it before adding anything.

## Repository layout
```
cfu/                     Python package - single source of truth
  basis.py               Basis of design constants
  assay.py, thermo.py    Crude characterisation + thermo
  hmb.py                 Heat & material balance (Model)
  sizing.py              Equipment sizing
  control_loops.py       Master control-loop list + SIFs
  export.py              JSON + workbook export
  drawing/sheet.py       Common A-size sheet frame / title block (USE IT for every drawing)
  drawing/*.py           One module per drawing family
  <discipline>/          Discipline generator sub-packages (pid, layout, piping, ic, elec, mech)
data/                    Generated master data (JSON) - read by downstream generators
deliverables/
  00-basis/  01-process/  02-equipment/  03-layout-piping/  04-instrumentation/  05-electrical/  06-wrapup/
build.py                 Regenerates everything:  python build.py
```
Each generator module exposes `build()` and is registered in `build.py`. Generators must be
deterministic and read inputs only from `data/*.json` or the `cfu` package (never hand-typed
duplicates of process numbers).

## Document numbering
`CFU-<area>-<disc>-<type>-<seq>` e.g. `CFU-100-PR-PID-003`
* area: `000` general, `100` CDU (desalting, preheat, H-101, C-101..C-106), `200` VDU, `900` unit utilities
* disc: `PR` process, `ME` mechanical, `PI` piping, `PL` plant layout, `IC` instrumentation/control,
  `EL` electrical, `PM` project management
* type: `BFD PFD PID HMB LST DS CAL GA PLT ELV 3DM ISO LL IDX IOL CE LD SLD HAC LDL CBL RPT REG EST`
Files: `<docno>_<Short-Title>.<ext>`; drawings saved as `.svg` + `.pdf` via `Sheet.save()`.
Rev A = "Issued for review (FEED)", date 2026-10-02, drawn "CLAUDE CODE".

## Units
SI. Temperature C, pressure bar(g) (bar(a) or mbar(a) for vacuum, stated), flow kg/h or m3/h,
lengths mm on drawings / m on layouts, power kW, duty MW. Pipe sizes NPS inches (e.g. `24"`).

## Equipment tags (from data/equipment.json - do not invent new numbers without adding them there)
C- columns, D- drums/desalters, E- shell&tube, A- air coolers, H- heaters, P- pumps (A/B = 2x100%),
J- ejectors, K- fans, X- packages. 1xx = CDU, 2xx = VDU.

## Stream numbers
H&MB stream numbers 1-34 (data/streams.json) shown in diamonds on BFD/PFD.

## Line numbering
`<NPS>"-<fluid>-<area>-<seq3>-<class>-<insul>` e.g. `24"-P-100-012-B2-H`
* fluid: `P` process HC, `PG` process gas/vapour, `SW` sour water, `WW` wash water/brine, `LS/MS/HS` steam,
  `CD` condensate, `BFW`, `CWS/CWR` cooling water, `FG` fuel gas, `FL` flare, `BD` blowdown/drain,
  `IA` instrument air, `N` nitrogen, `CH` chemical
* insul: `H` heat conservation, `P` personnel protection, `ST` steam traced, `N` none, `C` cold
* Piping classes (summary owned by the piping deliverable):

| Class | Rating | Material | CA | Service / limit |
|---|---|---|---|---|
| A1 | 150# | CS (A106-B) | 3 mm | HC <= 230 C, general |
| A2 | 150# | CS, HIC-resistant, PWHT | 6 mm | Sour water, OH vapour/condensate, wash water/brine |
| B1 | 300# | CS (A106-B) | 3 mm | HC <= 260 C, pump discharges |
| B2 | 300# | 5Cr-1/2Mo (A335 P5) | 3 mm | Sulfidic HC 260-400 C (hot crude, AR, BPA, HVGO, VR) |
| B3 | 300# | 9Cr-1Mo (A335 P9) | 3 mm | Heater outlets / transfer lines (H-101, H-201) |
| C1 | 600# | CS, killed | 3 mm | LPG / stabiliser, P-101/P-102 discharge > 300# |
| S1 | 150# | CS | 1.5 mm | LP/MP steam, condensate |
| S2 | 600# | 1.25Cr (A335 P11) | 1.5 mm | HP steam 41 barg / 400 C |
| U1 | 150# | CS, cement-lined if CW | 1.5 mm | Cooling water, utility water, BFW (300# BFW -> B1) |
| U2 | 150# | SS304 / galvanised | 0 | Instrument air, nitrogen |
| V1 | 150# | 5Cr-1/2Mo | 3 mm | Vacuum vapour lines (C-201 OH, transfer line large bore -> B3 for > 400 C) |
| A3 | 300# | CS, HIC-resistant, PWHT | 6 mm | Wash water / brine / sour water above 150# rating (desalter pressure) |
| S3 | 300# | CS (A106-B) | 1.5 mm | MP steam 10.3 barg / 250-290 C design (exceeds S1) |
| F1 | 150# | CS, killed, impact-tested | 3 mm | Flare / relief headers, -29 to 350 C |

## Instrument tags
ISA-5.1. `<letters>-<loop>` loop = area digit + 3 digits (1xxx CDU, 2xxx VDU, 9xxx utilities).
Principal control loops are fixed in `cfu/control_loops.py` (`LOOPS`, `SIFS`) - reuse those tags.
Additional instruments (PI, TI, LG, PSV, XV, etc.) take free numbers inside the same loop ranges.
PSV tags from data/psv.json (PSV-1001...). SIS initiators carry suffix A/B/C.

## Plot plan frame (fixed so layout, electrical and piping agree)
* Unit plot 230 m (x, east) x 150 m (y, north), origin = SW corner, grade EL 100.000 m.
* Prevailing wind from SSE. Fired heaters on the south side, upwind of hydrocarbon equipment.
* Main pipe rack: E-W, centred on y = 75 m, width 10 m, 3 tiers (EL 106.0/108.5/111.0); tie-in to OSBL
  rack at west edge x = 0.
* Substation SS-100: x 10-40, y 5-20 (non-classified). Field auxiliary room / satellite instrument
  house FAR-100: x 45-65, y 5-17. Central control room is OSBL (fibre link).
* Road around unit: 6 m wide, 3 m inside plot boundary, except along the south-west where it runs north of SS-100/FAR-100 (y 22-28); fire-water ring main OSBL. Rack tier 1 EL 106.0 gives 5.35 m clear at road crossings (maintenance roads only).
* Area blocks (guidance): x 0-70 desalting + preheat exchangers; x 70-150 C-101/strippers/OH system
  north of rack; heaters H-101, H-201 in band y 20-50 x 80-185; x 150-230 VDU north of rack;
  light ends (C-105/C-106) north-west, >= 30 m from heaters (LPG spacing).

## Coordination rule
Agents never edit another discipline's folder or `data/` files they don't own. Owned outputs:
* process (Phase 0): `data/streams.json, equipment.json, psv.json, process_results.json`
* P&ID / PFD: `data/lines.json`, `data/instruments.json`
* layout: `data/layout.json`
* electrical: `data/electrical.json`
* I&C: `data/io_list.json`
