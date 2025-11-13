from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict

# Ensure local packages are importable when running directly
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))            # entrega3 package
sys.path.insert(0, str(BASE / "src"))   # patito under src

from patito.parser import parse_text  # type: ignore
from entrega3.translator_pilas import TranslatorPilas


def _samples() -> Dict[str, str]:
    """Collect all sample programs we want to render into quads.

    Includes:
    - The example file under entrega3/programs/example.pat (if present)
    - The minimal unit-test programs from entrega3/tests/test_quads.py
    - The program-style tests from entrega3/tests/test_quads_programs.py
    """
    srcs: Dict[str, str] = {}

    # From example file
    example_path = BASE / "entrega3" / "programs" / "example.pat"
    if example_path.exists():
        srcs["example_file_program"] = example_path.read_text(encoding="utf-8")

    # From entrega3/tests/test_quads.py
    srcs["test_arithmetic_precedence"] = (
        "program P;\n"
        "var a: int;\n"
        "main { a = 1 + 2 * 3; } end\n"
    )
    srcs["test_relational_and_print_single"] = (
        "program P;\n"
        "main { print(1 + 2 < 5); } end\n"
    )
    srcs["test_assign_and_print_mixed_args"] = (
        "program P;\n"
        "var a: int;\n"
        "main { a = 5; print(\"x:\", a, 7 - 2); } end\n"
    )

    # From entrega3/tests/test_quads_programs.py
    srcs["parentheses_precedence_assign_and_print"] = (
        "program P;\n"
        "var x: int;\n"
        "main { x = (1 + 2) * 3; print(x); } end\n"
    )
    srcs["unary_minus_and_plus_chain"] = (
        "program P;\n"
        "var x: int;\n"
        "main { x = -1 + 2; print(x); } end\n"
    )
    srcs["relational_gt_in_print"] = (
        "program P;\n"
        "main { print(3 * 2 > 5); } end\n"
    )
    srcs["mixed_prints_with_strings_and_expr"] = (
        "program P;\n"
        "var a: int;\n"
        "main { a = 5; print(\"A=\", a); print((1 + 2) * (3 - 1)); } end\n"
    )
    srcs["two_relations_two_prints"] = (
        "program P;\n"
        "main { print(1 < 2, 4 > 3); } end\n"
    )

    return srcs


def gen_quads(src: str) -> list[str]:
    tree = parse_text(src, print_tree=False)
    tr = TranslatorPilas()
    tr.visit(tree)
    return tr.result().to_lines()


def run_pytest_quiet() -> str:
    """Run pytest -q and return combined output (stdout+stderr)."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=str(BASE),
            capture_output=True,
            text=True,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return out
    except Exception as e:
        return f"[pytest failed to run: {e}]\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Run tests and generate a quads report for multiple programs")
    p.add_argument("--out", default=str(BASE / "entrega3" / "tests" / "quads_report.txt"), help="Output file path")
    p.add_argument("--no-pytest", action="store_true", help="Skip running pytest before generating report")
    p.add_argument("--show-sources", action="store_true", help="Include program sources in the report")
    args = p.parse_args(argv)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Quads Report\n\n")

        if not args.no_pytest:
            f.write("## Pytest summary\n\n")
            f.write("````\n")
            f.write(run_pytest_quiet())
            f.write("````\n\n")

        f.write("## Program quads\n\n")
        samples = _samples()
        for i, name in enumerate(sorted(samples.keys()), 1):
            src = samples[name]
            f.write(f"### {i}. {name}\n\n")
            if args.show_sources:
                f.write("```patito\n")
                f.write(src.rstrip("\n"))
                f.write("\n```\n\n")
            f.write("```text\n")
            for line in gen_quads(src):
                f.write(line + "\n")
            f.write("```\n\n")

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
