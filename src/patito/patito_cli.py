from __future__ import annotations

import sys
from typing import Optional

from .parser import parse_text
from .translator import Translator
from .ir_runtime import run as run_ir


def _read_source_from_argv_or_stdin(argv: list[str], start_index: int) -> str:
    # If a path is provided and not '-', read file; otherwise read stdin
    if len(argv) > start_index and argv[start_index] != "-":
        path = argv[start_index]
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    # If no file arg and stdin is a tty (no pipe), show usage
    if len(argv) <= start_index and sys.stdin.isatty():
        print("Usage: python -m patito.patito_cli [--run] <file.pat> | - (reads stdin)", file=sys.stderr)
        sys.exit(2)
    return sys.stdin.read()


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv) if argv is None else argv
    run_mode = False
    args = argv[1:]
    if args and args[0] == "--run":
        run_mode = True
        args = args[1:]
    try:
        src = _read_source_from_argv_or_stdin([argv[0]] + args, 1)
        tree = parse_text(src)
        tr = Translator()
        result = tr.visit(tree)
        if run_mode:
            out = run_ir(result.quads)
            for line in out:
                print(line)
        else:
            for q in result.quads:
                print(f"{q.op}\t{q.arg1}\t{q.arg2}\t{q.res}")
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
