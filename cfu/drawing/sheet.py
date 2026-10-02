"""Common drawing sheet: ISO A-size frame, zone grid, title block, revision block (SVG, mm units).

Every drawing in the package uses this so title blocks, numbering and revisions are uniform.

    sh = Sheet("A1", "PROCESS FLOW DIAGRAM", "CRUDE PREHEAT & DESALTING", "CFU-100-PR-PFD-001")
    g = sh.g                      # svgwrite group in drawing-area coordinates (mm, origin top-left)
    g.add(sh.dwg.line(...))
    sh.save(Path("deliverables/01-process/pfd/CFU-100-PR-PFD-001"))   # writes .svg and .pdf
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import svgwrite

from .. import basis

SIZES = {"A0": (1189, 841), "A1": (841, 594), "A2": (594, 420), "A3": (420, 297), "A4L": (297, 210)}
FONT = "DejaVu Sans, Arial, sans-serif"
INK = "#000000"
REV_DATE = _dt.date(2026, 10, 2).isoformat()


class Sheet:
    def __init__(self, size: str, title1: str, title2: str, dwg_no: str, sheet: str = "1 OF 1",
                 rev: str | None = None, scale: str = "NTS", notes: list[str] | None = None,
                 revisions: list[tuple[str, str, str]] | None = None, discipline: str = "PROCESS"):
        self.W, self.H = SIZES[size]
        self.size = size
        self.dwg_no = dwg_no
        self.dwg = svgwrite.Drawing(size=(f"{self.W}mm", f"{self.H}mm"), viewBox=f"0 0 {self.W} {self.H}",
                                    profile="full", debug=False)
        self.dwg.add(self.dwg.rect((0, 0), (self.W, self.H), fill="white"))
        self.m = 10 if size in ("A0", "A1", "A2") else 7      # margin
        self.tb_w, self.tb_h = (180, 62)
        self.rev = rev or basis.PROJECT["rev"]
        self._frame()
        self._title_block(title1, title2, sheet, scale, discipline)
        self._revisions(revisions or [(self.rev, REV_DATE, basis.PROJECT["rev_desc"])])
        if notes:
            self.notes(notes)
        # drawing group (clip-free; caller keeps inside self.area)
        self.g = self.dwg.g(font_family=FONT, fill="none", stroke=INK, stroke_width=0.35)
        self.dwg.add(self.g)

    # usable drawing area (x0, y0, x1, y1) excluding title block column
    @property
    def area(self):
        return (self.m + 5, self.m + 5, self.W - self.m - 5, self.H - self.m - self.tb_h - 5)

    def _frame(self):
        d, m = self.dwg, self.m
        d.add(d.rect((m, m), (self.W - 2 * m, self.H - 2 * m), fill="none", stroke=INK, stroke_width=0.7))
        # zone markers
        nx, ny = (8, 6) if self.size in ("A0", "A1") else (6, 4)
        g = d.g(font_family=FONT, font_size=3.0, fill=INK)
        for i in range(nx):
            x = m + (self.W - 2 * m) * (i + 0.5) / nx
            g.add(d.text(str(i + 1), insert=(x, m - 2.5), text_anchor="middle"))
            g.add(d.text(str(i + 1), insert=(x, self.H - m + 5), text_anchor="middle"))
            xb = m + (self.W - 2 * m) * i / nx
            if i:
                d.add(d.line((xb, m - 4), (xb, m), stroke=INK, stroke_width=0.25))
                d.add(d.line((xb, self.H - m), (xb, self.H - m + 4), stroke=INK, stroke_width=0.25))
        for j in range(ny):
            y = m + (self.H - 2 * m) * (j + 0.5) / ny
            ch = "ABCDEFGH"[j]
            g.add(d.text(ch, insert=(m - 5, y + 1), text_anchor="middle"))
            g.add(d.text(ch, insert=(self.W - m + 5, y + 1), text_anchor="middle"))
        d.add(g)

    def _title_block(self, t1, t2, sheet, scale, disc):
        d = self.dwg
        w, h = self.tb_w, self.tb_h
        x0, y0 = self.W - self.m - w, self.H - self.m - h
        g = d.g(font_family=FONT, fill=INK, stroke="none")
        box = d.g(fill="none", stroke=INK, stroke_width=0.5)
        box.add(d.rect((x0, y0), (w, h)))
        rows = [0, 10, 22, 36, 46, h]
        for r in rows[1:-1]:
            box.add(d.line((x0, y0 + r), (x0 + w, y0 + r)))
        P = basis.PROJECT
        fs = 2.6 if w >= 180 else 2.3
        g.add(d.text(P["client"].upper(), insert=(x0 + 3, y0 + 4.5), font_size=fs))
        g.add(d.text(P["name"].upper(), insert=(x0 + 3, y0 + 8.3), font_size=fs + 0.3, font_weight="bold"))
        g.add(d.text(t1.upper(), insert=(x0 + w / 2, y0 + 15.5), font_size=4.2, font_weight="bold", text_anchor="middle"))
        g.add(d.text(t2.upper(), insert=(x0 + w / 2, y0 + 20.3), font_size=3.2, text_anchor="middle"))
        # mid row: discipline / stage / scale / sheet
        cols = [0, 45, 90, 130, w]
        for c in cols[1:-1]:
            box.add(d.line((x0 + c, y0 + 22), (x0 + c, y0 + 36)))
        labels = [("DISCIPLINE", disc), ("STAGE", P["stage"]), ("SCALE", scale), ("SHEET", sheet)]
        for (lbl, val), c0, c1 in zip(labels, cols[:-1], cols[1:]):
            g.add(d.text(lbl, insert=(x0 + c0 + 1.5, y0 + 25.5), font_size=2.0))
            g.add(d.text(val, insert=(x0 + (c0 + c1) / 2, y0 + 32.5), font_size=3.3, text_anchor="middle"))
        # drawn/checked row
        cols2 = [0, 45, 90, 135, w]
        for c in cols2[1:-1]:
            box.add(d.line((x0 + c, y0 + 36), (x0 + c, y0 + 46)))
        for (lbl, val), c0 in zip([("DRAWN", "CLAUDE CODE"), ("CHECKED", "-"), ("APPROVED", "-"), ("DATE", REV_DATE)],
                                  cols2[:-1]):
            g.add(d.text(lbl, insert=(x0 + c0 + 1.5, y0 + 39), font_size=2.0))
            g.add(d.text(val, insert=(x0 + c0 + 1.5, y0 + 44), font_size=2.8))
        box.add(d.line((x0 + w - 25, y0 + 46), (x0 + w - 25, y0 + h)))
        g.add(d.text("DRAWING NUMBER", insert=(x0 + 1.5, y0 + 49), font_size=2.0))
        g.add(d.text(self.dwg_no, insert=(x0 + (w - 25) / 2, y0 + h - 4), font_size=5.0, font_weight="bold",
                     text_anchor="middle"))
        g.add(d.text("REV", insert=(x0 + w - 23.5, y0 + 49), font_size=2.0))
        g.add(d.text(self.rev, insert=(x0 + w - 12.5, y0 + h - 4), font_size=6.0, font_weight="bold",
                     text_anchor="middle"))
        d.add(box)
        d.add(g)
        self._tb = (x0, y0)

    def _revisions(self, revs):
        d = self.dwg
        x0, y0 = self._tb
        w = self.tb_w
        rh = 5
        n = len(revs) + 1
        top = y0 - rh * n
        box = d.g(fill="none", stroke=INK, stroke_width=0.35)
        g = d.g(font_family=FONT, font_size=2.4, fill=INK, stroke="none")
        box.add(d.rect((x0, top), (w, rh * n)))
        for i in range(1, n):
            box.add(d.line((x0, top + rh * i), (x0 + w, top + rh * i)))
        for c in (12, 40):
            box.add(d.line((x0 + c, top), (x0 + c, top + rh * n)))
        for i, (r, dt, desc) in enumerate(list(revs) + [("REV", "DATE", "DESCRIPTION")]):
            yy = top + rh * (n - i) - 1.5
            g.add(d.text(r, insert=(x0 + 2, yy)))
            g.add(d.text(dt, insert=(x0 + 14, yy)))
            g.add(d.text(desc, insert=(x0 + 42, yy)))
        d.add(box)
        d.add(g)
        self._notes_bottom = top - 3

    def notes(self, notes: list[str], title="NOTES"):
        d = self.dwg
        x0 = self._tb[0]
        lh = 3.6
        y = self._notes_bottom - lh * (len(notes) + 1)
        g = d.g(font_family=FONT, font_size=2.5, fill=INK)
        g.add(d.text(title, insert=(x0, y), font_weight="bold", font_size=3.0))
        for i, n in enumerate(notes):
            g.add(d.text(f"{i + 1}. {n}", insert=(x0, y + lh * (i + 1))))
        d.add(g)
        self._notes_bottom = y - 3

    # ------------------------------------------------------------------
    def text(self, s, x, y, size=2.5, anchor="start", bold=False, color=INK, rotate=None, g=None, italic=False):
        t = self.dwg.text(s, insert=(x, y), font_size=size, text_anchor=anchor, fill=color, stroke="none",
                          font_weight="bold" if bold else "normal", font_family=FONT,
                          font_style="italic" if italic else "normal")
        if rotate:
            t.rotate(rotate, center=(x, y))
        (g or self.g).add(t)
        return t

    def save(self, stem: Path, pdf: bool = True):
        stem = Path(stem)
        stem.parent.mkdir(parents=True, exist_ok=True)
        svg = stem.with_suffix(".svg")
        self.dwg.saveas(svg, pretty=False)
        if pdf:
            import cairosvg
            cairosvg.svg2pdf(url=str(svg), write_to=str(stem.with_suffix(".pdf")))
        return svg


def merge_pdfs(paths, out):
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in paths:
        w.append(str(p))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        w.write(f)
