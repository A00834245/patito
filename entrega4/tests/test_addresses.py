from __future__ import annotations

from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "src"))

from patito.parser import parse_text  # type: ignore
from entrega4.translator_mem import TranslatorMem

# Address ranges
G_INT = range(1000, 2000)
C_INT = range(14000, 15000)
T_INT = range(20000, 21000)


def gen_lines(src: str) -> list[list[str]]:
    tree = parse_text(src)
    tr = TranslatorMem()
    tr.visit(tree)
    return [ln.split('\t') for ln in tr.result().to_lines()]


def as_ints(tokens: list[str]) -> list[int]:
    out = []
    for t in tokens[1:]:  # skip opcode
        try:
            if t is not None and t != 'None' and t != '':
                out.append(int(t))
        except Exception:
            pass
    return out


def test_address_ranges_basic():
    src = (
        "program P;\n"
        "var a: int;\n"
        "main { a = 1 + 2 * 3; print(a); } end\n"
    )
    lines = gen_lines(src)
    # ASSIGN line -> dest is global int
    assign = next(l for l in lines if l[0] == 'ASSIGN')
    ints = as_ints(assign)
    assert any(v in G_INT for v in ints)
    # constants exist
    all_ints = [v for l in lines for v in as_ints(l)]
    assert len([v for v in all_ints if v in C_INT]) >= 3
    # temps exist
    assert len([v for v in all_ints if v in T_INT]) >= 1

