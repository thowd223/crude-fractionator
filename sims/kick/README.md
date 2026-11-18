# KICK: well-control simulator

A single-file interactive drilling simulator for demos and training. Open `index.html` in any modern browser; it needs no build step and no server.

You take the brake on an 8½″ hole section of an offshore well. Pore pressure ramps up through a transition shale toward a gas sand that kicked on the offset well. Read the warning signs (rising gas, falling d-exponent, drilling break, flow out, pit gain), shut the well in, and circulate the kick out through the choke with the Wait & Weight or Driller's Method. Do it without fracturing the casing shoe.

## What is modelled

| Area | Model |
|---|---|
| Hydrostatics | 0.052 × MW × TVD, with separate original and kill mud columns in the string and annulus |
| Friction | Power-law annular and string/bit pressure losses vs. pump rate and mud weight (ECD, SPP, SCR) |
| Influx | Darcy-like inflow from the exposed sand, proportional to underbalance and exposed thickness |
| Gas | Boyle's-law slugs that expand as they rise, migrate at about 1,000 ft/hr when shut in, and merge or disperse |
| Closed well | Wellbore compressibility; casing pressure is solved from the volume balance each step |
| Choke | Orifice flow for mud and for gas; gas reaching the choke drops pressure fast |
| Shoe | Losses start when shoe pressure exceeds the 15.0 ppg leak-off; an underground blowout follows after 30 bbl |
| Kill sheet | KMW, ICP, FCP, strokes to bit, bottoms-up strokes, MAASP and influx gradient, from the recorded SIDPP/SICP |
| Auto-choke | PI controller on drill pipe pressure (schedule) or casing pressure (pump start-up and shutdown) |
| Mud log | ROP, lagged gas units and corrected d-exponent against a normal compaction trend |

Outcomes: well killed, section TD reached cleanly (weight up early), surface blowout, or shoe breakdown. A debrief scores kick size, reaction time, peak shoe and casing pressure, how closely drill pipe pressure tracked the schedule, and any secondary influx.

It is a training and demonstration aid with simplified physics, not an engineering tool.

## Files

- `kick.html`: the page as an HTML fragment. This is the source and the version published as a claude.ai artifact.
- `index.html`: the standalone page. Regenerate it with `python sims/kick/make_standalone.py` after editing `kick.html`.

`window.__kick.run(seconds)` advances the simulation headless, which is useful for scripted checks.
