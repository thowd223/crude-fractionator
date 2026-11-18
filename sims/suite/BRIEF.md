# One Plant, Four Lenses: suite brief (shared by all four tools)

The suite is four interactive single-page tools for an oil, gas and chemicals EPC firm, each aimed at one audience.
All four are driven by the same project: the 100,000 BPSD Arab Light CDU/VDU FEED package in this repository
(`data/*.json`, `deliverables/`, `cfu/`). That shared source is the point of the demo: one model of the plant, four views of it.

| Tool | Folder | Audience | Accent token |
|---|---|---|---|
| Ripple: change-impact explorer | `sims/ripple/` | Engineering | teal |
| Big Lift: heavy lift + 4D build | `sims/biglift/` | Construction | safety orange |
| P80: cost & schedule risk room | `sims/p80/` | Executive management | violet |
| Your Unit: plant walkthrough + value | `sims/yourunit/` | Clients | green |

## File contract (each tool)

- Source: `sims/<tool>/<tool>.html`, an **HTML fragment**. No `<!doctype>`, `<html>`, `<head>` or `<body>` tags.
  Start with `<title>`, then `<meta name="claude:viewport-fit-sides" content="cover">`, the Google Fonts `<link>`, `<style>`,
  the markup, and the scripts. `python sims/suite/build.py` wraps fragments into full pages in `sims/suite/`
  (`index.html` = landing, plus `ripple.html`, `biglift.html`, `p80.html`, `yourunit.html`), which is what gets published.
- Put a small "← One Plant, Four Lenses" link to `index.html` in the header (id `suiteHome`).
- Data: embed what the page needs inline as a JS constant between the markers `/*DATA:BEGIN*/` and `/*DATA:END*/`.
  Also provide `sims/<tool>/extract.py`, which regenerates that block from `data/*.json` (and other repo files) and rewrites it in place,
  so the numbers are traceable to the package. Keep the embedded data compact (well under 300 KB).
- Single file otherwise: inline CSS and JS. External scripts only from `https://cdnjs.cloudflare.com` (exact version,
  e.g. `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`). Stylesheets only from Google Fonts. No other network calls,
  no fetch of external URLs, no iframes, no `alert/confirm/prompt`, no `window.print`, no download links.
- The page is wrapped in a skeleton that has charset + viewport meta and `[hidden]{display:none!important}`. Add that `[hidden]` rule yourself too.

## Visual system (shared)

Fonts (one Google Fonts link):
`https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap`

- `--f-display: "Archivo", "Arial Narrow", sans-serif` for headings and big numbers (use with restraint)
- `--f-body: "IBM Plex Sans", system-ui, sans-serif`
- `--f-mono: "IBM Plex Mono", ui-monospace, Menlo, monospace` for tags, units and tabular figures (`font-variant-numeric: tabular-nums`)

Tokens. Both themes are required. Use exactly this structure, then add your tool's accent:

```css
:root{
  --bg:#f3f5f6; --surface:#ffffff; --surface2:#eceff1; --line:#d4dbe0; --ink:#13202a; --dim:#5a6a76; --faint:#8e9ca6;
  --good:#1d8a4e; --warn:#b7791f; --bad:#c83a32;
  --teal:#0e7c8b; --orange:#d35f0b; --violet:#5b3fc4; --green:#1f8a4c;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#0b1015; --surface:#121a21; --surface2:#18222b; --line:#26333e; --ink:#dde6ec; --dim:#8a9ba7; --faint:#5d6e7a;
  --good:#4fd18a; --warn:#f0b54a; --bad:#ff6b5f;
  --teal:#3cc4d4; --orange:#ff8a2b; --violet:#a08bff; --green:#52d58e; color-scheme:dark } }
:root[data-theme="dark"]{ /* same dark values repeated */ }
body{background:var(--bg);color:var(--ink)}
```

Set `--accent` to your tool's colour (for example `--accent: var(--teal)`). Canvas and WebGL colours must also come from these tokens:
read them with `getComputedStyle` and re-read on a `prefers-color-scheme` change.
The look is a precise engineering instrument rather than a marketing page. Use a dense but calm layout, thin rules, mono tags, and
one accent colour. Round corners at 4–6 px at most. No gradients on chrome, no emoji, no glassmorphism.
Equipment tags (C-101, H-101…) always in mono.

## Layout & quality rules

- Desktop first (a 1600×900 demo screen), but it must work at 390 px wide: no horizontal page scroll, at least a 16 px side gutter
  written as `padding-left:max(16px, env(safe-area-inset-left,0px))` and the same for the right.
- The page must look complete and alive on load: realistic working state, no empty shells, no "click to start" walls.
  (An optional guided "tour" button is welcome.)
- Respect `prefers-reduced-motion`. Give keyboard focus a visible state. Give every form control an `id` and a label.
- Copy: plain, specific, the way a senior engineer talks. Avoid filler, avoid "not X but Y" and "worth noting".
  Use real units (barg, °C, t, MW, kg/h, m³/h, USD M) and real terms of art.
- No real company, product or brand names, such as crane manufacturers, licensors or operators. Use generic descriptions
  ("1,350 t crawler crane, superlift").
- Clearly label anything synthetic or assumed (for example "illustrative risk ranges, set by the user").
- Each tool reads `?tour` / `#tour` and runs its guided tour if present. This is optional but nice for demos.

## Verification (each tool, before reporting done)

Use Playwright (`require('playwright')` works globally via `NODE_PATH=$(npm root -g)`; Chromium is pre-installed; do not install Playwright).
Run `python sims/suite/build.py`, open `sims/suite/<tool>.html`, and confirm all of the following:
1. No console errors or page errors.
2. Screenshots at 1600×900 (dark and light, via `colorScheme`) and at 390×844 look right. Inspect them yourself.
3. `document.documentElement.scrollWidth <= innerWidth` at 390 px.
4. The key numbers trace to the repository data. State a few spot checks in your report.

Only touch files in your own `sims/<tool>/` folder. Do not commit, push or publish. Report: what you built, how it uses the data,
spot-check numbers, screenshots paths, known limitations.
