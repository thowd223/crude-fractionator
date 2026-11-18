"""Assemble the 'One Plant, Four Lenses' suite into full standalone pages in sims/suite/.

Each tool is authored as an HTML fragment (sims/<tool>/<tool>.html) so it can also be published as a claude.ai
artifact. This wraps every fragment in a document skeleton and writes the flat suite folder:

    python sims/suite/build.py
"""
from pathlib import Path

SIMS = Path(__file__).resolve().parent.parent
OUT = SIMS / "suite"
PAGES = {"index": SIMS / "suite" / "landing.html",
         "ripple": SIMS / "ripple" / "ripple.html",
         "biglift": SIMS / "biglift" / "biglift.html",
         "p80": SIMS / "p80" / "p80.html",
         "yourunit": SIMS / "yourunit" / "yourunit.html",
         "kick": SIMS / "kick" / "kick.html"}
HEAD = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>[hidden]{display:none!important}body{margin:0}</style>\n')


def wrap(fragment: str) -> str:
    return HEAD + fragment + "\n</html>\n"


if __name__ == "__main__":
    for name, src in PAGES.items():
        if not src.exists():
            print(f"skip {name}: {src.relative_to(SIMS)} not built yet")
            continue
        (OUT / f"{name}.html").write_text(wrap(src.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"wrote suite/{name}.html")
