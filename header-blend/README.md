# Fuel Gas Header Blender (proof of concept)

Standalone demo, separate from the crude-fractionator model; it uses none of that project's
data. All 15 units in `example_units.json` are ILLUSTRATIVE values, not plant data.

## What it does

- **Composition range**: for every outage scenario, the lowest and highest header composition
  and fuel properties (H2, CH4, C2s, olefins, C3s, C4+, inerts, H2S, MW, LHV, HHV, Wobbe, NG
  make-up, surplus to flare), with each running unit anywhere in its flow range and any blend
  of its lean / normal / rich analysis. Shows which scenario drives each extreme and opens that
  exact case.
- **Single case**: switch units on/off, set flow and analysis, see the header result and heat
  balance (NG make-up when short, flare when long).

## Files

| File | Purpose |
|---|---|
| `index.html` | The page (UI only) |
| `model.js` | Calculation engine and range solver; runs in browser and Node |
| `example_units.json` | Illustrative unit data, scenarios, limits, component properties |
| `make_example_data.py` | Regenerates `example_units.json` |
| `verify.py` | Independent Python check of model.js (needs Node). `python3 verify.py` |
| `search_cli.js` | Runs the range solver from the command line (used by verify.py) |
| `serve.py` | Local web server for the page |
| `data_request/` | CSV templates and questions for the client's historical data |

## Run locally

The page loads its data with `fetch`, so serve the folder rather than opening the file:

    cd header-blend && python3 serve.py   # then open http://localhost:8000

`serve.py` adds the doctype and viewport wrapper that the claude.ai artifact host adds when
the page is published.

## Method in brief

Ideal-gas molar mixing; header heat held at demand (NG make-up when short, flare when long).
Every property except Wobbe is solved exactly as a linear-fractional program (Dinkelbach's
method, one-constraint LP via its dual). Wobbe is bounded from both sides: on each side of the
heat balance the reachable (HHV, MW) pairs form a convex set, which is enclosed between an
inner polygon of reachable cases and an outer polygon of exact support lines until the two
agree within 1e-9 relative. The reported Wobbe min/max are reachable cases and the outer value
is a proven bound; a scenario that does not reach that agreement is flagged on the page.

The range is a bound over the **input envelope** (each unit anywhere in its stated flow range
and any blend of its stated analyses, all at once), not a physical worst case: flows and
analyses outside the stated ranges are not covered. Full basis, assumptions and verification
results are on the page under "Technical basis for engineering review".

## Replacing the example data

When the historical data arrives (see `data_request/README.md`), it is reduced to the same
JSON shape: per unit, flow min / normal / max, any number of named analyses ("normal"
required), and fuel use. A different number of units, scenarios or analyses needs no code
changes; the data is checked on load (unknown unit ids in a scenario, missing "normal"
analysis, wrong number of components, missing, negative or all-zero analyses, flows that are
not numbers or out of order, negative fuel use, a make-up gas with no heating value, and a
base fuel demand that is not positive, which would allow an empty header). New components (butenes, CO, O2)
need a property row in the JSON and a group mapping in `model.js` / `index.html`.
