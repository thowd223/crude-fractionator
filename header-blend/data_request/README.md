# Data request: fuel gas header composition study

Fill one CSV per table below. Each template holds one example row to show the format;
replace it. Column names can be adjusted if the historian export differs; tell us the mapping.

| File | What it holds | Why it is needed |
|---|---|---|
| `01_stream_register.csv` | One row per tag, with its role: unit off-gas, unit fuel use, unit throughput, NG and other make-up, flare gas recovery return, each offsite consumer, header spill to flare, header analyser. For each meter: standard conditions of its units, wet/dry, how it is compensated and from which inputs, design MW/P/T, operating P/T tags. For each analysed stream: analyser or sample point and analyser lag. For fuel use: what the tag measures | Defines the mixing node and every flow in and out of it; converts indicated flow to true kmol/h; ties each unit's production to its fuel use |
| `02_flow_history.csv` | Historian export, long format (timestamp, tag, value, quality), every tag in the register | Normal, min and max flow per stream while running; demand of each consumer |
| `03_analysis_history.csv` | Online GC and lab results per stream (units, make-up, flare gas recovery), mol%, one row per sample, with sample time and result time | Lean, normal and rich analysis per stream |
| `04_header_history.csv` | Header flow, pressure, temperature and analyser or calorimeter; NG import, other make-up, flare gas recovery return, spill to flare and offsite fuel demand | Validation: calculated blend against measured header |
| `05_unit_status_and_outages.csv` | Start/end of every shutdown, trip, hot standby, reduced-rate period and turnaround, with the actual rate and any firing that continued; amine-unit upsets | Exclude down periods from unit statistics; real outage periods to validate against |
| `06_scenarios.csv` | Cases the client wants studied: units down, units at a stated reduced rate, units on hot standby with their remaining firing, changes in offsite demand | Scenario list for the range |
| `07_limits_and_basis.csv` | Burner design Wobbe and tolerance per consumer group, H2S permit limit, any H2 limit, NG import capacity, heating value standard and reference conditions, fuel-use basis, historian time and averaging conventions, bad-data handling | Pass/fail criteria, property basis and how to line up the data |

## Period and resolution

- At least 12 months, preferably 24, so seasonal and catalyst-cycle effects show up.
- Hourly averages for flows; every available sample for analyses.
- Include at least one real outage of a major contributor if one occurred.

## Basis the data must state

- **Meters.** Give the standard (base) temperature and absolute pressure the flow units refer to, wet or dry, and how each meter is compensated (none, live P/T, live P/T/MW, fixed design MW) and from which tags. Orifice meters on fuel gas read wrong when MW changes; without this the flows cannot be corrected.
- **Fuel use.** The model works in **net (LHV) heat input**, GJ/h. Say whether each fuel-use figure is gas volume, net heat input, gross heat input or absorbed process duty. Gas volume is converted with the gas analysis; absorbed duty needs the furnace efficiency.
- **Time.** Time zone and DST convention, averaging interval, whether a timestamp marks the start or the end of its interval, and how bad or missing values appear in the export. For lab samples, the time the gas was drawn, not the time the result was reported; for online GCs, the analyser lag.

## Questions for the process engineer

1. Is the header normally short (NG import on pressure control) or long (excess to flare)? Does that change by season or operating mode?
2. Is make-up natural gas, LPG vaporisation, or something else? What is its analysis and capacity?
3. Which flow meters are not density-compensated, or compensated with a fixed design MW? (Also captured per meter in `01_stream_register.csv`.)
4. Which consumers are on this header besides the 15 units (boilers, offsites, flare pilots)?
5. Are there components beyond the list in `03_analysis_history.csv` (CO, O2, NH3, mercaptans, COS, H2O)?
6. Which burners are most sensitive to Wobbe or H2 swings, and what are their design values and limits?
7. When the header is long, what happens: flare, curtail production, back out swing fuels (fuel oil, LPG vaporiser)? Is there flare gas recovery returning gas to the header?
8. When a unit trips, do its heaters go to hot standby on minimum fire, or out completely?
9. Does each unit's fuel use scale with its throughput, and which tag gives the throughput?
10. Which amine units treat which streams, and how often do they upset?

## How the data will be used

- For each unit, running periods only (from file 05): flow min / normal / max as the 5th / 50th / 95th percentile, after density compensation.
- Lean / normal / rich analysis: samples at the 5th / 50th / 95th percentile of molecular weight, plus engineer-selected samples such as the highest-H2S and highest-H2 sample on record, so H2S and H2 extremes are not tied to MW. The model takes any number of named analyses per unit.
- Components: the model currently carries H2, CH4, C2H4, C2H6, C3H6, C3H8, C4 (as n-butane), C5+ (as n-pentane), N2, CO2, H2S. iC4/nC4/butenes are lumped to C4 for now; CO, O2 or other components need a property row and group mapping added in the code.
- Unit fuel use: median while running.
- Validation: replay the history hour by hour through the model and compare with the header analyser before any outage case is reported.
- Reduced-rate and hot-standby cases: the current model handles units fully down (no gas made, no fuel burned). Cases from `06_scenarios.csv` with a reduced rate or remaining firing need a small extension (scaled flow range and residual fuel use per unit); the rates and firing asked for above are what it needs.

## What the results will and will not show

The range is the lowest and highest value over the **input envelope**: each unit anywhere between its P5 and P95 flow and any blend of its selected analyses, all at once. It is a bound for that envelope, not a physical worst case. Flows outside P5–P95 and analyses outside the selected samples are excluded on purpose, so a rare real event can fall outside the range. The replay against history shows how often that happens, and the envelope can be widened (for example P1–P99) where it matters.
