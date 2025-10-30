# FUTURE: CLI tool to parse Patito source files and print the generated AST for debugging/demos.
from __future__ import annotations

import sys
from typing import Optional

from .parser import parse_text
from .patito_ast import PatitoASTVisitor


def _read_source_from_argv_or_stdin(argv: list[str]) -> str:
    # If a path is provided and not '-', read file; otherwise read stdin
    if len(argv) > 1 and argv[1] != "-":
        path = argv[1]
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    # If no file arg and stdin is a tty (no pipe), show usage
    if len(argv) == 1 and sys.stdin.isatty():
        print("Usage: python -m patito.patito_cli <file.pat> | - (reads stdin)", file=sys.stderr)
        sys.exit(2)
    return sys.stdin.read()


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv) if argv is None else argv
    try:
        src = _read_source_from_argv_or_stdin(argv)
        tree = parse_text(src)
        ast = PatitoASTVisitor().visit(tree)
        print(ast)
        return 0
    except SyntaxError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        # Unhandled error; still show message and non-zero exit
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
