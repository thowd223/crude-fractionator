"""Wrap kick.html (an HTML fragment, as published to claude.ai) into a standalone index.html.

    python sims/kick/make_standalone.py
"""
from pathlib import Path

HERE = Path(__file__).parent
HEAD = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')

if __name__ == "__main__":
    body = (HERE / "kick.html").read_text(encoding="utf-8")
    (HERE / "index.html").write_text(HEAD + body + "\n</html>\n", encoding="utf-8")
    print("wrote", HERE / "index.html")
