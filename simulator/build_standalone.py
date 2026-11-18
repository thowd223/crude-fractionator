"""Bundle the simulator into one self-contained HTML file for sharing outside Claude.

    python simulator/build_standalone.py

Writes simulator/dist/CDU-LIVE.html: the page, every script, the design data, the 3D plant model and three.js
(vendored in simulator/vendor/, MIT licence) in a single file that opens offline in any modern browser.
Fonts load from Google Fonts when online and fall back to system fonts offline. The AI advisor needs Claude, so
in this file it shows as unavailable; everything else works.
"""
from __future__ import annotations

import re
from pathlib import Path

SIM = Path(__file__).resolve().parent
OUT = SIM / "dist" / "CDU-LIVE.html"
VENDOR = {
    "three.min.js": SIM / "vendor" / "three-r128" / "three.min.js",
    "GLTFLoader.js": SIM / "vendor" / "three-r128" / "GLTFLoader.js",
    "OrbitControls.js": SIM / "vendor" / "three-r128" / "OrbitControls.js",
}
# What the claude.ai page skeleton normally supplies (see index.html, which is written for that skeleton).
RESET = ("html,body{margin:0}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
         "img{max-width:100%}[hidden]{display:none!important}")


def inline_script(code: str, name: str) -> str:
    code = code.replace("</script", "<\\/script")  # keep the HTML parser from ending the block early
    return f"<script>/* {name} */\n{code}\n</script>"


def main():
    page = (SIM / "index.html").read_text(encoding="utf-8")

    def repl(m: re.Match) -> str:
        src = m.group(1)
        base = src.rsplit("/", 1)[-1]
        if src.startswith("http"):
            if base not in VENDOR:
                raise SystemExit(f"no vendored copy for {src}")
            return inline_script(VENDOR[base].read_text(encoding="utf-8"), f"{base} (three.js r128, MIT licence)")
        out = inline_script((SIM / src).read_text(encoding="utf-8"), src)
        if src == "data/plant-data.js":  # the 3D model normally loads on demand; ship it in the same file
            out += "\n" + inline_script((SIM / "data" / "plant-model.js").read_text(encoding="utf-8"), "data/plant-model.js")
        return out

    body, n = re.subn(r'<script src="([^"]+)"></script>', repl, page)
    if n < 10:
        raise SystemExit(f"expected at least 10 script tags, found {n}")
    head_end = body.index("</style>") + len("</style>")
    head, rest = body[:head_end], body[head_end:]
    html = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
            f"<style>{RESET}</style>\n{head}\n</head>\n<body>\n{rest}\n</body>\n</html>\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB, {n} scripts inlined)")


if __name__ == "__main__":
    main()
