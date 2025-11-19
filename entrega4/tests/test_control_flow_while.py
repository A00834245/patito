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


def test_while_flow():
    src = (
        "program P;\n"
        "var a: int;\n"
        "main { while (a < 3) do { a = a + 1; }; } end\n"
    )
    ops = gen_opcodes(src)
    # LABEL start, CMP_LT, GOTOF end, PLUS, ASSIGN, GOTO start, LABEL end
    assert ops == [
        'LABEL', 'CMP_LT', 'GOTOF', 'PLUS', 'ASSIGN', 'GOTO', 'LABEL'
    ]

