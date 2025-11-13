from __future__ import annotations

from pathlib import Path
import sys

# Robust imports regardless of cwd
BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "src"))

from patito.parser import parse_text  # type: ignore
from entrega3.translator_pilas import TranslatorPilas


def gen_quads(src: str) -> list[str]:
    tree = parse_text(src)
    tr = TranslatorPilas()
    tr.visit(tree)
    return tr.result().to_lines()


def test_parentheses_precedence_assign_and_print():
    src = (
        "program P;\n"
        "var x: int;\n"
        "main { x = (1 + 2) * 3; print(x); } end\n"
    )
    lines = gen_quads(src)
    assert lines == [
        "PLUS\t1\t2\tt1",
        "MUL\tt1\t3\tt2",
        "ASSIGN\tt2\tNone\tx",
        "PRINT\tx\tNone\tNone",
    ]


def test_unary_minus_and_plus_chain():
    src = (
        "program P;\n"
        "var x: int;\n"
        "main { x = -1 + 2; print(x); } end\n"
    )
    lines = gen_quads(src)
    assert lines == [
        "MINUS\t0\t1\tt1",
        "PLUS\tt1\t2\tt2",
        "ASSIGN\tt2\tNone\tx",
        "PRINT\tx\tNone\tNone",
    ]


def test_relational_gt_in_print():
    src = (
        "program P;\n"
        "main { print(3 * 2 > 5); } end\n"
    )
    lines = gen_quads(src)
    assert lines == [
        "MUL\t3\t2\tt1",
        "CMP_GT\tt1\t5\tt2",
        "PRINT\tt2\tNone\tNone",
    ]


def test_mixed_prints_with_strings_and_expr():
    src = (
        "program P;\n"
        "var a: int;\n"
        "main { a = 5; print(\"A=\", a); print((1 + 2) * (3 - 1)); } end\n"
    )
    lines = gen_quads(src)
    assert lines == [
        "ASSIGN\t5\tNone\ta",
        "PRINT\t\"A=\"\tNone\tNone",
        "PRINT\ta\tNone\tNone",
        "PLUS\t1\t2\tt1",
        "MINUS\t3\t1\tt2",
        "MUL\tt1\tt2\tt3",
        "PRINT\tt3\tNone\tNone",
    ]


def test_two_relations_two_prints():
    src = (
        "program P;\n"
        "main { print(1 < 2, 4 > 3); } end\n"
    )
    lines = gen_quads(src)
    assert lines == [
        "CMP_LT\t1\t2\tt1",
        "PRINT\tt1\tNone\tNone",
        "CMP_GT\t4\t3\tt2",
        "PRINT\tt2\tNone\tNone",
    ]
