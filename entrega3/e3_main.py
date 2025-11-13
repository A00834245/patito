from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure local 'src' is importable
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE))

from patito.parser import parse_text  # type: ignore
from entrega3.translator_pilas import TranslatorPilas


def run_on_text(src: str) -> int:
    tree = parse_text(src, print_tree=False)
    tr = TranslatorPilas()
    tr.visit(tree)
    for line in tr.result().to_lines():
        print(line)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Entrega3: print IR quad queue for Patito")
    p.add_argument("file", nargs="?", help="Path to .pat source. If omitted, read from stdin")
    args = p.parse_args(argv)

    if args.file:
        src_path = Path(args.file)
        src = src_path.read_text(encoding="utf-8")
        return run_on_text(src)
    else:
        src = sys.stdin.read()
        return run_on_text(src)


if __name__ == "__main__":
    raise SystemExit(main())
