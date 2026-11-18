# Ripple Change Tracer

An interactive demonstration for an EPC audience (refining, midstream, chemicals). It traces one
project change across a 43-item register in nine disciplines, shows how cost and schedule grow with
the stage at which the change is found, and presents the same trace for engineering, construction,
executives and the client.

- `index.html` is the whole page, written as an Artifact body (no `<html>`/`<head>` wrapper).
- The project (Calder Point Refinery, Unit 24 DHT Revamp), tags and figures are fictional. Nothing
  comes from the rest of this repository.
- Four traces are prepared in the `SC` array. "Trace with Claude" and "Ask Claude" use the Artifact
  `sample` capability and only work when the page is opened in Claude.
- Cost model (`calc`): engineering hours × $165/hr × stage multiplier, plus material deltas, plus
  rework tiers that switch on once an item is bought, fabricated or installed.

To add a scenario, append an object to `SC` using the `I(node, via, order, note, hrs, mat, tiers)` helper.
