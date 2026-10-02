"""Minimal Markdown -> PDF renderer (reportlab) for engineering reports.

Supports: # / ## / ### headings, paragraphs, '- ' bullets, pipe tables, ![caption](image.png), **bold**,
`code`, and a document control header. Markdown is written alongside the PDF so both are deliverables.
"""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from . import basis

_ss = getSampleStyleSheet()
ST = {
    "h1": ParagraphStyle("h1", parent=_ss["Heading1"], fontSize=15, spaceBefore=10, spaceAfter=6,
                         textColor=colors.HexColor("#1F3864")),
    "h2": ParagraphStyle("h2", parent=_ss["Heading2"], fontSize=12.5, spaceBefore=8, spaceAfter=4,
                         textColor=colors.HexColor("#1F3864")),
    "h3": ParagraphStyle("h3", parent=_ss["Heading3"], fontSize=11, spaceBefore=6, spaceAfter=3),
    "p": ParagraphStyle("p", parent=_ss["BodyText"], fontSize=9.5, leading=12.5),
    "li": ParagraphStyle("li", parent=_ss["BodyText"], fontSize=9.5, leading=12.5, leftIndent=12, bulletIndent=3),
    "td": ParagraphStyle("td", parent=_ss["BodyText"], fontSize=7.8, leading=9.4),
    "th": ParagraphStyle("th", parent=_ss["BodyText"], fontSize=7.8, leading=9.4, textColor=colors.white,
                         fontName="Helvetica-Bold"),
    "cap": ParagraphStyle("cap", parent=_ss["BodyText"], fontSize=8.5, textColor=colors.HexColor("#444444"),
                          alignment=1),
}


def _inline(s: str) -> str:
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", s)
    return s


def md_to_flow(md: str, base: Path):
    flow = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.strip() == "\\pagebreak":
            flow.append(PageBreak())
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)", ln)
        if m:
            flow.append(Paragraph(_inline(m.group(2)), ST["h" + str(len(m.group(1)))]))
            i += 1
            continue
        m = re.match(r"^!\[(.*?)\]\((.*?)\)", ln.strip())
        if m:
            p = (base / m.group(2)).resolve()
            from PIL import Image as PI
            w, h = PI.open(p).size
            W = min(170 * mm, 115 * mm * w / h)
            flow.append(KeepTogether([Image(str(p), width=W, height=W * h / w), Paragraph(_inline(m.group(1)),
                                                                                      ST["cap"])]))
            flow.append(Spacer(1, 4))
            i += 1
            continue
        if ln.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.match(r"^:?-{2,}:?$", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            data = [[Paragraph(_inline(c), ST["th" if r == 0 else "td"]) for c in row] for r, row in enumerate(rows)]
            ncol = max(len(r) for r in rows)
            t = Table(data, repeatRows=1, colWidths=[170 * mm / ncol] * ncol if ncol > 4 else None)
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
                                   ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#999999")),
                                   ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3FA")]),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
            flow += [t, Spacer(1, 6)]
            continue
        if re.match(r"^\s*[-*]\s+", ln):
            flow.append(Paragraph(_inline(re.sub(r"^\s*[-*]\s+", "", ln)), ST["li"], bulletText="•"))
            i += 1
            continue
        para = [ln.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||!\[|\s*[-*]\s)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        flow.append(Paragraph(_inline(" ".join(para)), ST["p"]))
    return flow


def render(md: str, out_stem: Path, docno: str, title: str):
    """Write <stem>.md and <stem>.pdf."""
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    out_stem.with_suffix(".md").write_text(md)
    P = basis.PROJECT

    def deco(c, doc):
        c.saveState()
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(18 * mm, 287 * mm, f"{P['name']}  |  {title}")
        c.drawRightString(192 * mm, 287 * mm, f"{docno}  Rev {P['rev']}")
        c.line(18 * mm, 285.5 * mm, 192 * mm, 285.5 * mm)
        c.drawString(18 * mm, 10 * mm, f"{P['stage']} - {P['rev_desc']}  |  Prepared by Claude Code")
        c.drawRightString(192 * mm, 10 * mm, f"Page {doc.page}")
        c.restoreState()

    doc = SimpleDocTemplate(str(out_stem.with_suffix(".pdf")), pagesize=A4, leftMargin=18 * mm,
                            rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=16 * mm, title=title)
    cover = [Spacer(1, 40 * mm), Paragraph(P["client"].upper(), ST["h3"]), Paragraph(P["name"], ST["h1"]),
             Spacer(1, 6 * mm), Paragraph(title, ParagraphStyle("t", parent=ST["h1"], fontSize=20, leading=24)),
             Spacer(1, 10 * mm)]
    ctl = Table([["Document No.", docno], ["Revision", P["rev"]], ["Status", P["rev_desc"]],
                 ["Date", "2026-10-02"], ["Prepared", "Claude Code"], ["Checked / Approved", "- / -"]],
                colWidths=[45 * mm, 100 * mm])
    ctl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 9),
                             ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#D9E1F2"))]))
    cover += [ctl, PageBreak()]
    doc.build(cover + md_to_flow(md, out_stem.parent), onFirstPage=deco, onLaterPages=deco)
