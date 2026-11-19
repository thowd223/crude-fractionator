"""Operations and construction training generated from the design data."""
from __future__ import annotations


def build():
    from . import board, loto
    loto.build()
    board.build()
