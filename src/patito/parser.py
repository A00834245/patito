# ANTLR4-based parser for Patito language
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple

try:
    from antlr4 import CommonTokenStream, InputStream
    from antlr4.error.ErrorListener import ErrorListener
    from antlr4.tree.Trees import Trees
except Exception as e:  # pragma: no cover
    raise ImportError(
        "antlr4 runtime not found. Install with: pip install antlr4-python3-runtime"
    ) from e

_BASE_PKGS = (
    "patito",
    "patito.antlr",
    "patito.grammar",
    "patito.generated",
    "patito.gen",
)


def _import_symbol(module_candidates: Tuple[str, ...], symbol: str):
    last_err: Optional[Exception] = None
    for mod in module_candidates:
        try:
            m = importlib.import_module(mod)
            if hasattr(m, symbol):
                return getattr(m, symbol)
        except ModuleNotFoundError as e:
            last_err = e
            continue
        except Exception as e:  
            last_err = e
            continue
    try:
        m = importlib.import_module(symbol)
        return getattr(m, symbol)
    except Exception as e:  
        last_err = e
    raise ImportError(
        f"Could not import {symbol}. Ensure ANTLR has generated Python targets and that they are on PYTHONPATH.\n"
        f"Tried modules: {', '.join(module_candidates)}"
    ) from last_err

PatitoLexer = _import_symbol(tuple(f"{b}.PatitoLexer" for b in _BASE_PKGS), "PatitoLexer")
PatitoParser = _import_symbol(tuple(f"{b}.PatitoParser" for b in _BASE_PKGS), "PatitoParser")

# Try multiple optional visitor/listener class names
try:
    PatitoVisitor = _import_symbol(
        tuple(f"{b}.PatitoVisitor" for b in _BASE_PKGS), "PatitoVisitor"
    )
except Exception:  # pragma: no cover
    PatitoVisitor = None  # type: ignore

try:
    PatitoParserVisitor = _import_symbol(
        tuple(f"{b}.PatitoParserVisitor" for b in _BASE_PKGS), "PatitoParserVisitor"
    )
except Exception:  # pragma: no cover
    PatitoParserVisitor = None  # type: ignore

try:
    PatitoListener = _import_symbol(
        tuple(f"{b}.PatitoListener" for b in _BASE_PKGS), "PatitoListener"
    )
except Exception:  # pragma: no cover
    PatitoListener = None  # type: ignore

try:
    PatitoParserListener = _import_symbol(
        tuple(f"{b}.PatitoParserListener" for b in _BASE_PKGS), "PatitoParserListener"
    )
except Exception:  # pragma: no cover
    PatitoParserListener = None  # type: ignore


@dataclass
class SyntaxIssue:
    line: int
    column: int
    message: str
    offending: Optional[str] = None

    def format(self) -> str:
        base = f"line {self.line}, column {self.column}: {self.message}"
        if self.offending:
            base += f" (offending: {self.offending!r})"
        return base


class PatitoErrorListener(ErrorListener):
    def __init__(self) -> None:
        super().__init__()
        self.issues: list[SyntaxIssue] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):  
        text = None
        try:
            text = getattr(offendingSymbol, "text", None)
        except Exception:
            text = None
        self.issues.append(SyntaxIssue(int(line), int(column), str(msg), text))


def _detect_start_rule(parser_obj: Any) -> str:
    candidates = (
        "programa",
        "program",
        "start",
        "main",
        "prog",
        "programa_p",  
    )
    for name in candidates:
        if hasattr(parser_obj, name) and callable(getattr(parser_obj, name)):
            return name
    try:
        rules = getattr(parser_obj, "ruleNames", None)
        if rules and len(rules) > 0:
            first = rules[0]
            if hasattr(parser_obj, first):
                return first
    except Exception:
        pass
    raise RuntimeError("Unable to determine start rule for Patito.")


def parse_text(text: str, print_tree: bool = False, start_rule: Optional[str] = None):
    input_stream = InputStream(text)
    lexer = PatitoLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = PatitoParser(token_stream)

    parser.removeErrorListeners()
    err_listener = PatitoErrorListener()
    parser.addErrorListener(err_listener)

    entry = start_rule or _detect_start_rule(parser)
    tree = getattr(parser, entry)()

    if err_listener.issues:
        msg = "\n".join(issue.format() for issue in err_listener.issues)
        raise SyntaxError(msg)

    if print_tree:
        print(tree_to_string(tree, parser))

    return tree


def parse_file(path: str, print_tree: bool = False, start_rule: Optional[str] = None):
    with open(path, "r", encoding="utf-8") as f:
        return parse_text(f.read(), print_tree=print_tree, start_rule=start_rule)


def tree_to_string(tree: Any, parser: Optional[Any] = None) -> str:
    try:
        return Trees.toStringTree(tree, None, parser)
    except Exception:
        try:
            return tree.toStringTree(recog=parser)
        except Exception:
            return str(tree)
