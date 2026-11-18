# CDU LIVE: operator training simulator

A real-time, browser-based simulator of the 100 kBPSD CDU/VDU designed in this repository. Open
`simulator/index.html` in a browser (no server or build step needed; the 3D view loads three.js from a CDN).

## What it does

* **Console**: a live overview of the whole unit. Flows are coloured by temperature and animated by rate, the
  H-101 and H-201 fireboxes burn with the actual fired duty, C-101 is shaded by its tray temperature profile, and
  six status boards show firebox, tray loading, overhead corrosion, desalter, vacuum and crude data. Click any
  equipment for an explainer, its FEED datasheet and the handles that act on it.
* **Field 3D**: the project's plant model (`CFU-000-PL-3DM-001.glb`) with live tags over the equipment, glowing
  heaters, stack smoke scaled to firing, and equipment in alarm pulsing red.
* **Cuts & quality**: where every barrel goes (product distribution by boiling point, with the overlap caused by
  imperfect fractionation), TBP slicing, C-101 temperature profile, product specifications with giveaway, yields
  against design and a margin breakdown.
* **APC optimiser**: a real-time optimiser (`js/apc.js`) that every plant minute tests a one-step move of 17
  handles, plus paired draw moves, on the steady-state model and keeps those that raise margin without crossing
  one of 24 constraints (specs and equipment limits, each with a safety margin). It sheds to manual on a trip.
  The panel shows the benefit since switch-on (per day, per year, per barrel), the constraints it is pushing
  against and its recent moves. From the design point it finds about +$220k/day: the FEED case carries
  deliberate giveaway (diesel 50 °C inside its 95 % point, for example), so this is the upper end of what APC earns.
* **AI shift advisor** (`js/advisor.js`): Claude reads the live plant and answers questions about it. It has
  three page tools: `get_plant_state`, `what_if` (tests setpoint changes on the model without touching the
  plant) and `propose_moves` (shows an Apply card; nothing moves until the operator presses it). Alarm
  explanations offer "Ask the advisor". It runs through the artifact's `sample` capability, so it works when
  the page is opened at claude.ai and uses the viewer's own Claude account; opened as a local file, everything
  else works and the advisor says it is unavailable.
* **Learn**: concept cards, each with a one-click experiment, and an equipment index.
* **Scenarios**: a 12-stop guided tour ("Follow a barrel") and four scored missions: margin optimisation, a crude
  switch to a heavy sour blend, a charge pump trip in real time (beat SIF-101), and a loss of vacuum.

About 20 operator handles (charge rate, crude blend, COT, O2, top temperature, three draws, three pumparounds,
stripping steam, wash water, mix valve, demulsifier, neutraliser, vacuum heater, ejector steam), pumps, SIS resets
and ESD-1, all tagged with the loop numbers in `data/control_loops.json`. Twenty-five alarms each carry a plain
explanation of cause and effect. Product prices are editable.

## The model (`js/model.js`)

The crude is split into about 110 TBP pseudo-components (Watson K characterisation, sulfur and metals
distributions). Each tick the model calculates desalting, preheat recovery, H-101 duty and coil outlet temperature
(sensible + vaporisation), flash-zone vaporisation with stripping steam, cut points from the draw rates, overlap
widths from internal reflux (which depends on how heat is split between the condenser and the pumparounds),
side-stripper effects, tray loading, product TBP distributions and D86 conversion (Riazi-Daubert), flash point
(API), freeze and cloud point, vacuum-column lift (Maxwell-Bonnell AET), ejector stability and cracking, HVGO
metals and carbon, tube metal temperature and coking, overhead dew point and corrosion, and the unit margin.
First-order lags give realistic dynamics: heaters respond in about a minute, the column in tens of minutes,
analysers in about 15 minutes.

At start-up the model calibrates itself against the FEED heat and material balance in `data/*.json`, so the design
inputs reproduce the design point (CIT 274 °C, 66.9 MW fired against 67.4 MW in the H&MB, design cut points,
60 mbar vacuum flash zone, 17.5 MW on H-201). It is a training model: trends and trade-offs are right, absolute
values are at FEED accuracy. The three crudes besides Arab Light use representative assays, and prices are
illustrative.

## Files

| File | Contents |
|---|---|
| `index.html` | Page shell and styles |
| `js/model.js` | Process model and dynamic simulator |
| `js/content.js` | Equipment explainers, concepts, tour, missions, alarm definitions |
| `js/mimic.js` | Console SVG, built in code and bound to the model |
| `js/charts.js` | Analysis charts and trend sparklines |
| `js/field3d.js` | three.js field view |
| `js/apc.js` | APC optimiser: constraints, manipulated variables, move search |
| `js/advisor.js` | AI shift advisor: plant state, tools, chat panel |
| `js/app.js` | Simulation loop, operator panel, alarms, missions, tour, sound |
| `data/plant-data.js` | Generated: design point, layout, datasheets, loop tags |
| `data/plant-model.js` | Generated: 3D model (base64) |

## Sharing outside Claude

`dist/CDU-LIVE.html` is the whole simulator in one file (about 2 MB): page, scripts, design data, 3D model and
three.js. Send it by email, Teams or SharePoint; it opens offline in Chrome, Edge, Firefox or Safari by
double-clicking. Fonts come from Google Fonts when online and fall back to system fonts offline. The AI advisor
needs Claude, so in this file it shows as unavailable; everything else, APC and the 3D view included, works.
Rebuild it after any change:

```bash
python simulator/build_standalone.py
```

three.js r128 is vendored in `vendor/three-r128/` (MIT licence, file included) so the build needs no network.

Regenerate the data bundles after a rebuild of the design package:

```bash
python simulator/build_assets.py
```
