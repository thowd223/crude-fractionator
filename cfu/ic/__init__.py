"""Instrumentation & control deliverables (deliverables/04-instrumentation, data/io_list.json).

build() order: control-scheme diagrams -> C&E -> I/O list (needs data/instruments.json) -> architecture
(I/O counts) -> loop diagrams -> valve sizing -> reports.
"""
from __future__ import annotations


def build():
    from . import arch, ce, csd, cvsizing, iolist, loops_ld, report
    from .common import OUT
    OUT.mkdir(parents=True, exist_ok=True)
    csd.build()
    ce.build()
    io = iolist.build()
    arch.build()
    loops_ld.build()
    cvsizing.write_xlsx(cvsizing.valves(), OUT / "CFU-000-IC-CAL-001_Control-Valve-Sizing.xlsx")
    report.build(io)
    from ..drawing.sheet import merge_pdfs
    merge_pdfs(sorted(csd.DIR.glob("*.pdf")), OUT / "CFU-000-IC-CSD-ALL_Control-Scheme-Diagrams.pdf")
    if (OUT / "loop-diagrams").exists():
        merge_pdfs(sorted((OUT / "loop-diagrams").glob("*.pdf")), OUT / "CFU-100-IC-LD-ALL_Loop-Diagrams.pdf")
