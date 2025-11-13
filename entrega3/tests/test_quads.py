from __future__ import annotations

import os
import sys
from pathlib import Path

# Make imports robust regardless of current working directory
BASE = Path(__file__).resolve().parents[2]  # repo root
sys.path.insert(0, str(BASE))              # so 'entrega3' package resolves
sys.path.insert(0, str(BASE / "src"))     # so 'patito' (under src) resolves

from patito.parser import parse_text  # type: ignore
from entrega3.translator_pilas import TranslatorPilas


def gen_quads(src: str) -> list[str]:
    tree = parse_text(src)
    tr = TranslatorPilas()
    tr.visit(tree)
    return tr.result().to_lines()


def test_arithmetic_precedence():
    src = (
        "program P;\n"
        "var a: int;\n"
        "main { a = 1 + 2 * 3; } end\n"
    )
    lines = gen_quads(src)
    assert lines == [
        "MUL\t2\t3\tt1",
        "PLUS\t1\tt1\tt2",
        "ASSIGN\tt2\tNone\ta",
    ]


def test_relational_and_print_single():
    src = (
        "program P;\n"
        "main { print(1 + 2 < 5); } end\n"
    )
    lines = gen_quads(src)
    assert lines == [
        "PLUS\t1\t2\tt1",
        "CMP_LT\tt1\t5\tt2",
        "PRINT\tt2\tNone\tNone",
    ]


def test_assign_and_print_mixed_args():
    src = (
        "program P;\n"
        "var a: int;\n"
        "main { a = 5; print(\"x:\", a, 7 - 2); } end\n"
    )
    lines = gen_quads(src)
    assert lines == [
        "ASSIGN\t5\tNone\ta",
        "PRINT\t\"x:\"\tNone\tNone",
        "PRINT\ta\tNone\tNone",
        "MINUS\t7\t2\tt1",
        "PRINT\tt1\tNone\tNone",
    ]
