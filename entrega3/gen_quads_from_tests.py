from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure local packages are importable when running directly
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))        # entrega3 package
sys.path.insert(0, str(BASE / "src"))  # patito under src

from patito.parser import parse_text  # type: ignore
from entrega3.translator_pilas import TranslatorPilas


SAMPLES: dict[str, str] = {
    # Matches the programs covered by entrega3/tests/test_quads_programs.py
    "parentheses_precedence_assign_and_print": (
        "program P;\n"
        "var x: int;\n"
        "main { x = (1 + 2) * 3; print(x); } end\n"
    ),
    "unary_minus_and_plus_chain": (
        "program P;\n"
        "var x: int;\n"
        "main { x = -1 + 2; print(x); } end\n"
    ),
    "relational_gt_in_print": (
        "program P;\n"
        "main { print(3 * 2 > 5); } end\n"
    ),
    "mixed_prints_with_strings_and_expr": (
        "program P;\n"
        "var a: int;\n"
        "main { a = 5; print(\"A=\", a); print((1 + 2) * (3 - 1)); } end\n"
    ),
    "two_relations_two_prints": (
        "program P;\n"
        "main { print(1 < 2, 4 > 3); } end\n"
    ),
}


def gen_quads(src: str) -> list[str]:
    tree = parse_text(src, print_tree=False)
    tr = TranslatorPilas()
    tr.visit(tree)
    return tr.result().to_lines()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Generate quads from built-in sample programs")
    p.add_argument("--only", choices=sorted(SAMPLES.keys()), help="Run only the specified sample")
    p.add_argument("--list", action="store_true", help="List available sample names and exit")
    p.add_argument("--show-sources", action="store_true", help="Print program sources before their quads")
    args = p.parse_args(argv)

    if args.list:
        for name in sorted(SAMPLES.keys()):
            print(name)
        return 0

    names = [args.only] if args.only else sorted(SAMPLES.keys())
    for i, name in enumerate(names, 1):
        src = SAMPLES[name]
        print(f"=== {i}. {name} ===")
        if args.show_sources:
            print("--- source ---")
            print(src.rstrip())
            print("--- quads ---")
        for line in gen_quads(src):
            print(line)
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
