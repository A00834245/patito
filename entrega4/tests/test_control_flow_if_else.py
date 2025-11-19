from __future__ import annotations

from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "src"))

from patito.parser import parse_text  # type: ignore
from entrega4.translator_mem import TranslatorMem


def gen_opcodes(src: str) -> list[str]:
    tree = parse_text(src)
    tr = TranslatorMem()
    tr.visit(tree)
    return [ln.split('\t')[0] for ln in tr.result().to_lines()]


def test_if_else_flow():
    src = (
        "program P;\n"
        "var a: int;\n"
        "main { if (1 < 2) { a = 1; } else { a = 2; }; } end\n"
    )
    ops = gen_opcodes(src)
    assert ops == [
        'CMP_LT', 'GOTOF', 'ASSIGN', 'GOTO', 'LABEL', 'ASSIGN', 'LABEL'
    ]

