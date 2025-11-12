from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from antlr4 import TerminalNode, ParseTreeVisitor

# Import generated parser token types if available
try:  # pragma: no cover - exercised by runtime usage
    from .generated.PatitoParser import PatitoParser  # type: ignore
    try:
        from .generated.PatitoVisitor import PatitoVisitor as _BaseVisitor  # type: ignore
    except Exception:  # pragma: no cover
        _BaseVisitor = ParseTreeVisitor  # type: ignore
except Exception:  # pragma: no cover
    # Fallback: attempt non-generated relative names used by some ANTLR configs
    try:
        from .PatitoParser import PatitoParser  # type: ignore
        try:
            from .PatitoVisitor import PatitoVisitor as _BaseVisitor  # type: ignore
        except Exception:  # pragma: no cover
            _BaseVisitor = ParseTreeVisitor  # type: ignore
    except Exception:  # pragma: no cover
        PatitoParser = None  # type: ignore
        _BaseVisitor = ParseTreeVisitor  # type: ignore


@dataclass
class Quad:
    op: str
    arg1: Any = None
    arg2: Any = None
    res: Any = None


@dataclass
class Place:
    name: Any  # temp name, variable name, or immediate value
    type: str  # "int" | "float" | "string" | "bool"


@dataclass
class TranslationResult:
    quads: List[Quad]
    output: List[str]


class TranslationContext:
    def __init__(self) -> None:
        self.quads: List[Quad] = []
        self.output: List[str] = []
        self.temps = 0
        self.labels = 0
        self.symbols: dict[str, str] = {}  # name -> type

    def new_temp(self, ty: str) -> Place:
        self.temps += 1
        return Place(f"t{self.temps}", ty)

    def new_label(self) -> str:
        self.labels += 1
        return f"L{self.labels}"

    def emit(self, op: str, a1: Any = None, a2: Any = None, r: Any = None) -> None:
        self.quads.append(Quad(op, a1, a2, r))


def _to_place_immediate(tok: TerminalNode) -> Place:
    text = tok.getText()
    if tok.symbol.type == PatitoParser.INT_LIT:
        return Place(int(text), "int")
    if tok.symbol.type == PatitoParser.FLOAT_LIT:
        return Place(float(text), "float")
    # String literal retains quotes for printing; mark type string
    return Place(text, "string")


class Translator(_BaseVisitor):
    def __init__(self, ctx: Optional[TranslationContext] = None) -> None:
        super().__init__()
        self.ctx = ctx or TranslationContext()

    # ---------- Program ----------
    def visitStart(self, ctx):  # start: programa EOF
        self.visit(ctx.programa())
        return TranslationResult(self.ctx.quads, self.ctx.output)

    def visitPrograma(self, ctx):
        # PROGRAM ID SEMI programa_p programa_pp MAIN body END
        # Global vars (optional)
        p = self.visit(ctx.programa_p())
        _ = self.visit(ctx.programa_pp())
        self.visit(ctx.body())
        return None

    # ---------- Vars ----------
    def visitVars(self, ctx):
        return self.visit(ctx.vars_p())

    def visitVars_p(self, ctx):
        ids: List[str] = []
        # Collect identifiers until ':'
        for ch in ctx.getChildren():
            if isinstance(ch, TerminalNode):
                ttype = ch.symbol.type
                if ttype == PatitoParser.COLON:
                    break
                if ttype == PatitoParser.ID:
                    ids.append(ch.getText())
        ty = self.visit(ctx.type_())  # (type, name)
        ty_name = ty[1] if isinstance(ty, tuple) else str(ty)
        for name in ids:
            if name in self.ctx.symbols:
                # simple duplicate check; could raise semantic error
                pass
            self.ctx.symbols[name] = ty_name
        # Continue chains
        more = self.visit(ctx.vars_ppp())
        return more

    def visitVars_pp(self, ctx):
        return None

    def visitVars_ppp(self, ctx):
        if ctx.getChildCount() == 0:
            return None
        return self.visit(ctx.vars_p())

    def visitType(self, ctx):
        if ctx.INT_TYPE():
            return ("type", "int")
        if ctx.FLOAT_TYPE():
            return ("type", "float")
        return ("type", ctx.getText())

    # ---------- Body/Statements ----------
    def visitBody(self, ctx):
        return self.visit(ctx.body_p())

    def visitBody_p(self, ctx):
        if ctx.getChildCount() == 0:
            return None
        return self.visit(ctx.body_pp())

    def visitBody_pp(self, ctx):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.statement())
        return self.visit(ctx.body_pp())

    def visitStatement(self, ctx):
        if ctx.assign():
            return self.visit(ctx.assign())
        if ctx.condition():
            return self.visit(ctx.condition())
        if ctx.cycle():
            return self.visit(ctx.cycle())
        if ctx.fcall():
            return self.visit(ctx.fcall())
        if ctx.print_stmt():
            return self.visit(ctx.print_stmt())
        return None

    def visitAssign(self, ctx):
        name = ctx.ID().getText()
        expr = self.visit(ctx.expresion())  # Place
        self.ctx.emit("ASSIGN", expr.name, None, name)
        return None

    def visitPrint_stmt(self, ctx):
        args: List[Place] = []
        args.extend(self.visit(ctx.print_p()))
        args.extend(self.visit(ctx.print_pp()))
        for a in args:
            self.ctx.emit("PRINT", a.name, None, None)
        return None

    def visitPrint_p(self, ctx):
        out: List[Place] = []
        if ctx.expresion():
            out.append(self.visit(ctx.expresion()))
        else:
            out.append(_to_place_immediate(ctx.STRING_LIT()))
        out.extend(self.visit(ctx.print_pp()))
        return out

    def visitPrint_pp(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.print_p())

    # ---------- Conditionals ----------
    def visitCondition(self, ctx):
        cond = self.visit(ctx.expresion())
        # cond expected to be a bool in a temp; if not, assume non-zero truthy
        L_else = self.ctx.new_label()
        L_end = self.ctx.new_label()
        self.ctx.emit("IF_FALSE_GOTO", cond.name, None, L_else)
        self.visit(ctx.body())  # then
        self.ctx.emit("GOTO", None, None, L_end)
        self.ctx.emit("LABEL", None, None, L_else)
        else_body = self.visit(ctx.condition_p())
        self.ctx.emit("LABEL", None, None, L_end)
        return None

    def visitCondition_p(self, ctx):
        if ctx.getChildCount() == 0:
            return None
        return self.visit(ctx.body())

    # ---------- While ----------
    def visitCycle(self, ctx):
        L_begin = self.ctx.new_label()
        L_end = self.ctx.new_label()
        self.ctx.emit("LABEL", None, None, L_begin)
        cond = self.visit(ctx.expresion())
        self.ctx.emit("IF_FALSE_GOTO", cond.name, None, L_end)
        # body may be named 'body' per grammar
        body_node = self.visit(ctx.body())
        self.ctx.emit("GOTO", None, None, L_begin)
        self.ctx.emit("LABEL", None, None, L_end)
        return None

    # ---------- Function calls (stub) ----------
    def visitFcall(self, ctx):
        name = ctx.ID().getText()
        args = self.visit(ctx.fcall_p())
        # For now, emit a CALL with serialized args; not executed by runtime yet
        self.ctx.emit("CALL", name, [a.name for a in args], None)
        return None

    def visitFcall_p(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        head = self.visit(ctx.expresion())
        rest = self.visit(ctx.fcall_pp())
        return [head] + rest

    def visitFcall_pp(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.fcall_p())

    # ---------- Expressions ----------
    def visitExpresion(self, ctx):
        left = self.visit(ctx.exp())
        tail = self.visit(ctx.expresion_p())
        if tail is None:
            return left
        op, right = tail
        # comparison: produce bool temp via CMP op
        t = self.ctx.new_temp("bool")
        self.ctx.emit(f"CMP_{op}", left.name, right.name, t.name)
        return t

    def visitExpresion_p(self, ctx):
        if ctx.getChildCount() == 0:
            return None
        if ctx.GT():
            return ("GT", self.visit(ctx.exp()))
        if ctx.LT():
            return ("LT", self.visit(ctx.exp()))
        if ctx.NEQ():
            return ("NEQ", self.visit(ctx.exp()))
        return None

    def visitExp(self, ctx):
        left = self.visit(ctx.termino())
        ops = self.visit(ctx.exp_p())
        acc = left
        for op, term in ops:
            acc = self._emit_bin(acc, op, term)
        return acc

    def visitExp_p(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        if ctx.PLUS():
            op = "PLUS"
        elif ctx.MINUS():
            op = "MINUS"
        else:
            op = "?"
        right = self.visit(ctx.termino())
        rest = self.visit(ctx.exp_p())
        return [(op, right)] + rest

    def visitTermino(self, ctx):
        left = self.visit(ctx.factor())
        ops = self.visit(ctx.termino_p())
        acc = left
        for op, factor in ops:
            acc = self._emit_bin(acc, op, factor)
        return acc

    def visitTermino_p(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        if ctx.MUL():
            op = "MUL"
        elif ctx.DIV():
            op = "DIV"
        else:
            op = "?"
        right = self.visit(ctx.factor())
        rest = self.visit(ctx.termino_p())
        return [(op, right)] + rest

    def visitFactor(self, ctx):
        if ctx.expresion():
            return self.visit(ctx.expresion())
        return self.visit(ctx.factor_p())

    def visitFactor_p(self, ctx):
        sign = None
        if ctx.factor_pp().PLUS():
            sign = "+"
        elif ctx.factor_pp().MINUS():
            sign = "-"
        val = self.visit(ctx.factor_ppp())
        if sign == "+":
            return val
        if sign == "-":
            zero = Place(0, val.type) if val.type == "int" else Place(0.0, val.type)
            return self._emit_bin(zero, "MINUS", val)
        return val

    def visitFactor_pp(self, ctx):  # unused
        return None

    def visitFactor_ppp(self, ctx):
        if ctx.ID():
            name = ctx.ID().getText()
            ty = self.ctx.symbols.get(name, "int")
            return Place(name, ty)
        return self.visit(ctx.cte())

    def visitCte(self, ctx):
        if ctx.INT_LIT():
            return _to_place_immediate(ctx.INT_LIT())
        if ctx.FLOAT_LIT():
            return _to_place_immediate(ctx.FLOAT_LIT())
        # Unused in current grammar for strings outside print
        return Place(ctx.getText(), "string")

    # ---------- Helpers ----------
    def _emit_bin(self, left: Place, op: str, right: Place) -> Place:
        # simple type rules: int vs float
        ty = "float" if (left.type == "float" or right.type == "float") else "int"
        t = self.ctx.new_temp(ty)
        self.ctx.emit(op, left.name, right.name, t.name)
        return t


def translate_tree(tree) -> TranslationResult:
    tr = Translator()
    return tr.visit(tree)
