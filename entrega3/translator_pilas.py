from __future__ import annotations

from antlr4 import ParseTreeVisitor

try:
    from src.patito.generated.PatitoParser import PatitoParser  # type: ignore
    try:
        from src.patito.generated.PatitoVisitor import PatitoVisitor as _BaseVisitor  # type: ignore
    except Exception:
        _BaseVisitor = ParseTreeVisitor  # type: ignore
except Exception:
    try:
        from patito.generated.PatitoParser import PatitoParser  # type: ignore
        try:
            from patito.generated.PatitoVisitor import PatitoVisitor as _BaseVisitor  # type: ignore
        except Exception:
            _BaseVisitor = ParseTreeVisitor  # type: ignore
    except Exception:
        try:
            from patito.PatitoParser import PatitoParser  # type: ignore
            try:
                from patito.PatitoVisitor import PatitoVisitor as _BaseVisitor  # type: ignore
            except Exception:
                _BaseVisitor = ParseTreeVisitor  # type: ignore
        except Exception:
            PatitoParser = None  # type: ignore
            _BaseVisitor = ParseTreeVisitor  # type: ignore

from entrega3 import POper, PilaO, PTipos, Precedence, IRQueue
from entrega2.semantic_cube import type_of_binary, type_of_unary, can_assign


class TranslatorPilas(_BaseVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.POper = POper()
        self.PilaO = PilaO()
        self.PTipos = PTipos()
        self.ir = IRQueue()
        self.current_func: str | None = None
        self.symbols: dict[str, str] = {}  # simple symbol table (name -> type)

    def result(self) -> IRQueue:
        return self.ir

    # ---- Program ----
    def visitStart(self, ctx):
        self.visit(ctx.programa())
        return self.ir

    def visitPrograma(self, ctx):
        # PROGRAM ID SEMI programa_p programa_pp MAIN body END
        if ctx.programa_p():
            self.visit(ctx.programa_p())
        if ctx.programa_pp():
            self.visit(ctx.programa_pp())
        self.visit(ctx.body())
        return None

    def visitPrograma_p(self, ctx):
        return self.visitChildren(ctx)

    def visitPrograma_pp(self, ctx):
        return self.visitChildren(ctx)

    # ---- Vars ----
    def visitVars(self, ctx):
        # VAR vars_p
        return self.visit(ctx.vars_p())

    def visitVars_p(self, ctx):
        # ID vars_pp COLON type SEMI vars_ppp
        ids: list[str] = []
        # Collect identifiers before ':'
        for ch in ctx.getChildren():
            t = getattr(getattr(ch, 'symbol', None), 'type', None)
            if t is None:
                continue
            if t == getattr(PatitoParser, 'COLON', None):
                break
            if t == getattr(PatitoParser, 'ID', None):
                ids.append(ch.getText())

        ty = self.visit(ctx.type_())  # ('type', name)
        ty_name = ty[1] if isinstance(ty, tuple) else str(ty)
        for name in ids:
            # last one wins; duplicate detection deferred to entrega2 if needed
            self.symbols[name] = ty_name

        # Continue chains
        _ = self.visit(ctx.vars_ppp())
        return None

    def visitVars_pp(self, ctx):  # ',' ID vars_pp | empty
        return None

    def visitVars_ppp(self, ctx):  # vars_p | empty
        if ctx.getChildCount() == 0:
            return None
        return self.visit(ctx.vars_p())

    def visitType(self, ctx):
        if ctx.INT_TYPE():
            return ("type", "int")
        if ctx.FLOAT_TYPE():
            return ("type", "float")
        return ("type", ctx.getText())

    # ---- Funcs ----
    def visitFuncs(self, ctx):
        return self.visitChildren(ctx)

    # ---- Body / Statements ----
    def visitBody(self, ctx):
        # LB body_p RB
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
        # For step 3, no linear statements yet; traverse children
        return self.visitChildren(ctx)

    def visitAssign(self, ctx):
        return self.visitChildren(ctx)

    def visitPrint_stmt(self, ctx):
        return self.visitChildren(ctx)

    # ---- Expressions ----
    def visitExpresion(self, ctx):
        # left exp
        self.visit(ctx.exp())
        # complete arithmetic on the left
        self._flush_arith()
        # optional relational tail
        tail = ctx.expresion_p()
        if tail and tail.getChildCount() > 0:
            if tail.GT():
                op = "GT"
            elif tail.LT():
                op = "LT"
            elif tail.NEQ():
                op = "NEQ"
            else:
                op = None
            if op:
                self._push_op(op)
                # right exp
                self.visit(tail.exp())
                self._flush_arith()  # finish arithmetic inside right
                # reduce the relational operator
                self._reduce_one()
        return None

    def visitExpresion_p(self, ctx):
        return self.visitChildren(ctx)

    def visitExp(self, ctx):
        # termino exp_p
        self.visit(ctx.termino())
        self.visit(ctx.exp_p())
        return None

    def visitExp_p(self, ctx):
        # (+|-) termino exp_p | empty
        if ctx.getChildCount() == 0:
            return None
        if ctx.PLUS():
            self._push_op("PLUS")
        elif ctx.MINUS():
            self._push_op("MINUS")
        self.visit(ctx.termino())
        self.visit(ctx.exp_p())
        return None

    def visitTermino(self, ctx):
        # factor termino_p
        self.visit(ctx.factor())
        self.visit(ctx.termino_p())
        return None

    def visitTermino_p(self, ctx):
        # (*|/) factor termino_p | empty
        if ctx.getChildCount() == 0:
            return None
        if ctx.MUL():
            self._push_op("MUL")
        elif ctx.DIV():
            self._push_op("DIV")
        self.visit(ctx.factor())
        self.visit(ctx.termino_p())
        return None

    def visitFactor(self, ctx):
        # '(' expresion ')' | factor_p
        if ctx.expresion():
            # parenthesis handling using '(' sentinel
            self.POper.push("(")
            self.visit(ctx.expresion())
            # reduce until '('
            while self.POper and self.POper.peek() != "(":
                self._reduce_one()
            if self.POper and self.POper.peek() == "(":
                self.POper.pop()
            return None
        return self.visit(ctx.factor_p())

    def visitFactor_p(self, ctx):
        # optional unary +|-
        sign = None
        if ctx.factor_pp() and ctx.factor_pp().PLUS():
            sign = "+"
        elif ctx.factor_pp() and ctx.factor_pp().MINUS():
            sign = "-"
        self.visit(ctx.factor_ppp())
        if sign == "+":
            # unary plus: no-op
            return None
        if sign == "-":
            # emulate 0 - x (ensure correct operand order: left=0, right=x)
            val = self.PilaO.pop()
            val_ty = self.PTipos.pop() if self.PTipos else "int"
            zero = 0.0 if val_ty == "float" else 0
            self.PilaO.push(zero)
            self.PTipos.push(val_ty)
            self.PilaO.push(val)
            self.PTipos.push(val_ty)
            self._push_op("MINUS")
            # immediate reduction of unary
            self._reduce_one()
        return None

    def visitFactor_pp(self, ctx):
        return None

    def visitFactor_ppp(self, ctx):
        if ctx.ID():
            name = ctx.ID().getText()
            ty = self.symbols.get(name, "int")
            self.PilaO.push(name)
            self.PTipos.push(ty)
            return None
        return self.visit(ctx.cte())

    def visitCte(self, ctx):
        if ctx.INT_LIT():
            self.PilaO.push(int(ctx.INT_LIT().getText()))
            self.PTipos.push("int")
            return None
        if ctx.FLOAT_LIT():
            self.PilaO.push(float(ctx.FLOAT_LIT().getText()))
            self.PTipos.push("float")
            return None
        return None

    # ----------------- Helpers (stacks/IR) -----------------
    def _push_op(self, op: str) -> None:
        # Reduce while top has higher or equal precedence (left-associative)
        while self.POper and self.POper.peek() not in {"("} and Precedence.should_reduce(self.POper.peek(), op):
            self._reduce_one()
        self.POper.push(op)

    def _reduce_one(self) -> None:
        op = self.POper.pop()
        if op == "(":
            return
        # Arithmetic or relational
        right, ty_r = self.PilaO.pop(), self.PTipos.pop()
        left, ty_l = self.PilaO.pop(), self.PTipos.pop()
        # type via semantic cube when available
        res_ty = type_of_binary(op, ty_l, ty_r)
        if op in {"GT", "LT", "NEQ"}:
            res_ty = res_ty or "bool"
            t = self.ir.new_temp()
            self.ir.emit(f"CMP_{op}", left, right, t)
        else:
            res_ty = res_ty or ("float" if (ty_l == "float" or ty_r == "float") else "int")
            t = self.ir.new_temp()
            self.ir.emit(op, left, right, t)
        self.PilaO.push(t)
        self.PTipos.push(res_ty)

    def _flush_arith(self) -> None:
        while self.POper and self.POper.peek() in {"PLUS", "MINUS", "MUL", "DIV"}:
            self._reduce_one()

    def _flush_all(self) -> None:
        while self.POper and self.POper.peek() != "(":
            self._reduce_one()

    # ----------------- Linear statements -----------------
    def visitAssign(self, ctx):
        # ID ASSIGN expresion SEMI
        name = ctx.ID().getText()
        self.visit(ctx.expresion())
        # complete any pending ops
        self._flush_all()
        val = self.PilaO.pop() if self.PilaO else None
        ty = self.PTipos.pop() if self.PTipos else None
        # optional type check against declared symbol
        dest_ty = self.symbols.get(name)
        if dest_ty and ty and not can_assign(dest_ty, ty):
            # minimal: still emit; full error handling can be future work
            pass
        self.ir.emit("ASSIGN", val, None, name)
        return None

    def visitPrint_stmt(self, ctx):
        # PRINT LP print_p print_pp RP SEMI
        self._process_print_p(ctx.print_p())
        self._process_print_pp(ctx.print_pp())
        return None

    def _process_print_p(self, pctx):
        if pctx is None:
            return
        if pctx.expresion():
            self.visit(pctx.expresion())
            self._flush_all()
            val = self.PilaO.pop();
            if self.PTipos: self.PTipos.pop()
            self.ir.emit("PRINT", val, None, None)
        else:
            text = pctx.STRING_LIT().getText()
            self.ir.emit("PRINT", text, None, None)
        # inner tail
        self._process_print_pp(pctx.print_pp())

    def _process_print_pp(self, ppctx):
        if ppctx is None or ppctx.getChildCount() == 0:
            return
        # COMMA print_p
        self._process_print_p(ppctx.print_p())
