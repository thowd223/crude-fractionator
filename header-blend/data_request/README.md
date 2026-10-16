# Data request: fuel gas header composition study

Fill one CSV per table below. Each template holds one example row to show the format;
replace it. Column names can be adjusted if the historian export differs; tell us the mapping.

| File | What it holds | Why it is needed |
|---|---|---|
| `01_stream_register.csv` | One row per stream into the header: flow tag, meter type and design basis (MW, P, T, compensated or not), analyser tag or lab sample point, the unit's own fuel gas use tag, PFD/P&ID reference | Defines the mixing node; converts indicated flow to true kmol/h; ties each unit's production to its fuel use |
| `02_flow_history.csv` | Historian export, long format (timestamp, tag, value, quality), every flow tag in the register plus fuel use tags | Normal, min and max flow per unit while running |
| `03_analysis_history.csv` | Online GC and lab results per stream, mol%, one row per sample | Lean, normal and rich analysis per unit |
| `04_header_history.csv` | Header flow, pressure, temperature, analyser or calorimeter, NG import flow and analysis, any other make-up or flare gas recovery return | Validation: calculated blend against measured header |
| `05_unit_status_and_outages.csv` | Start/end of every shutdown, trip, hot standby and turnaround in the period, and amine-unit upsets | Exclude down periods from unit statistics; real outage periods to validate against |
| `06_scenarios.csv` | Outage cases the client wants studied, including units that always go down together | Scenario list for the range |
| `07_limits_and_basis.csv` | Burner design Wobbe and tolerance per consumer group, H2S permit limit, any H2 limit, NG import capacity, heating value standard and reference conditions | Pass/fail criteria and property basis |

## Period and resolution

- At least 12 months, preferably 24, so seasonal and catalyst-cycle effects show up.
- Hourly averages for flows; every available sample for analyses.
- Include at least one real outage of a major contributor if one occurred.

## Questions for the process engineer

1. Is the header normally short (NG import on pressure control) or long (excess to flare)? Does that change by season or operating mode?
2. Is make-up natural gas, LPG vaporisation, or something else? What is its analysis and capacity?
3. Are any flow meters not density-compensated? Orifice meters on fuel gas read wrong when MW changes.
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
