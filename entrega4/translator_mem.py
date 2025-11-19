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
from entrega2.semantic_cube import type_of_binary, can_assign
from entrega4.memory import AddressAllocator, ConstantTable


class TranslatorMem(_BaseVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.POper = POper()
        self.PilaO = PilaO()
        self.PTipos = PTipos()
        self.ir = IRQueue()
        self.current_func: str | None = None
        self.alloc = AddressAllocator()
        self.consts = ConstantTable(self.alloc)
        self.symbols: dict[str, tuple[str, int]] = {}

    def result(self) -> IRQueue:
        return self.ir

    def visitStart(self, ctx):
        self.visit(ctx.programa())
        return self.ir

    def visitPrograma(self, ctx):
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

    def visitVars(self, ctx):
        return self.visit(ctx.vars_p())

    def visitVars_p(self, ctx):
        ids: list[str] = []
        for ch in ctx.getChildren():
            t = getattr(getattr(ch, 'symbol', None), 'type', None)
            if t is None:
                continue
            if t == getattr(PatitoParser, 'COLON', None):
                break
            if t == getattr(PatitoParser, 'ID', None):
                ids.append(ch.getText())
        ty = self.visit(ctx.type_())
        ty_name = ty[1] if isinstance(ty, tuple) else str(ty)
        for name in ids:
            self.symbols[name] = (ty_name, self.alloc.global_var(ty_name))
        _ = self.visit(ctx.vars_ppp())
        return None

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

    def visitFuncs(self, ctx):
        return self.visitChildren(ctx)

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
        return self.visitChildren(ctx)

    # Expressions
    def visitExpresion(self, ctx):
        self.visit(ctx.exp())
        self._flush_arith()
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
                self.visit(tail.exp())
                self._flush_arith()
                self._reduce_one()
        return None

    def visitExpresion_p(self, ctx):
        return self.visitChildren(ctx)

    def visitExp(self, ctx):
        self.visit(ctx.termino())
        self.visit(ctx.exp_p())
        return None

    def visitExp_p(self, ctx):
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
        self.visit(ctx.factor())
        self.visit(ctx.termino_p())
        return None

    def visitTermino_p(self, ctx):
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
        if ctx.expresion():
            self.POper.push("(")
            self.visit(ctx.expresion())
            while self.POper and self.POper.peek() != "(":
                self._reduce_one()
            if self.POper and self.POper.peek() == "(":
                self.POper.pop()
            return None
        return self.visit(ctx.factor_p())

    def visitFactor_p(self, ctx):
        sign = None
        if ctx.factor_pp() and ctx.factor_pp().PLUS():
            sign = "+"
        elif ctx.factor_pp() and ctx.factor_pp().MINUS():
            sign = "-"
        self.visit(ctx.factor_ppp())
        if sign == "+":
            return None
        if sign == "-":
            val = self.PilaO.pop()
            val_ty = self.PTipos.pop() if self.PTipos else "int"
            zero = 0.0 if val_ty == 'float' else 0
            zaddr = self.consts.intern(zero, val_ty)
            self.PilaO.push(zaddr)
            self.PTipos.push(val_ty)
            self.PilaO.push(val)
            self.PTipos.push(val_ty)
            self._push_op("MINUS")
            self._reduce_one()
        return None

    def visitFactor_pp(self, ctx):
        return None

    def visitFactor_ppp(self, ctx):
        if ctx.ID():
            name = ctx.ID().getText()
            ty, addr = self.symbols.get(name, ("int", self.alloc.global_var("int")))
            self.PilaO.push(addr)
            self.PTipos.push(ty)
            return None
        return self.visit(ctx.cte())

    def visitCte(self, ctx):
        if ctx.INT_LIT():
            val = int(ctx.INT_LIT().getText())
            addr = self.consts.intern(val, 'int')
            self.PilaO.push(addr)
            self.PTipos.push('int')
            return None
        if ctx.FLOAT_LIT():
            val = float(ctx.FLOAT_LIT().getText())
            addr = self.consts.intern(val, 'float')
            self.PilaO.push(addr)
            self.PTipos.push('float')
            return None
        return None

    # Helpers
    def _push_op(self, op: str) -> None:
        while self.POper and self.POper.peek() not in {"("} and Precedence.should_reduce(self.POper.peek(), op):
            self._reduce_one()
        self.POper.push(op)

    def _reduce_one(self) -> None:
        op = self.POper.pop()
        if op == "(":
            return
        right, ty_r = self.PilaO.pop(), self.PTipos.pop()
        left, ty_l = self.PilaO.pop(), self.PTipos.pop()
        res_ty = type_of_binary(op, ty_l, ty_r)
        if op in {"GT", "LT", "NEQ"}:
            res_ty = res_ty or "bool"
            t = self.alloc.temp('bool')
            self.ir.emit(f"CMP_{op}", left, right, t)
        else:
            res_ty = res_ty or ("float" if (ty_l == "float" or ty_r == "float") else "int")
            t = self.alloc.temp(res_ty)
            self.ir.emit(op, left, right, t)
        self.PilaO.push(t)
        self.PTipos.push(res_ty)

    def _flush_arith(self) -> None:
        while self.POper and self.POper.peek() in {"PLUS", "MINUS", "MUL", "DIV"}:
            self._reduce_one()

    def _flush_all(self) -> None:
        while self.POper and self.POper.peek() != "(":
            self._reduce_one()

    # Linear statements
    def visitAssign(self, ctx):
        name = ctx.ID().getText()
        self.visit(ctx.expresion())
        self._flush_all()
        val = self.PilaO.pop() if self.PilaO else None
        ty = self.PTipos.pop() if self.PTipos else None
        dest = self.symbols.get(name)
        dest_ty = dest[0] if dest else None
        if dest_ty and ty and not can_assign(dest_ty, ty):
            pass
        self.ir.emit("ASSIGN", val, None, (dest[1] if dest else name))
        return None

    def visitPrint_stmt(self, ctx):
        self._process_print_p(ctx.print_p())
        self._process_print_pp(ctx.print_pp())
        return None

    def _process_print_p(self, pctx):
        if pctx is None:
            return
        if pctx.expresion():
            self.visit(pctx.expresion())
            self._flush_all()
            val = self.PilaO.pop()
            if self.PTipos: self.PTipos.pop()
            self.ir.emit("PRINT", val, None, None)
        else:
            text = pctx.STRING_LIT().getText()
            sval = text[1:-1] if len(text) >= 2 and text[0]=='"' and text[-1]=='"' else text
            addr = self.consts.intern(sval, 'string')
            self.ir.emit("PRINT", addr, None, None)
        self._process_print_pp(pctx.print_pp())

    def _process_print_pp(self, ppctx):
        if ppctx is None or ppctx.getChildCount() == 0:
            return
        self._process_print_p(ppctx.print_p())

    # Control flow
    def visitCondition(self, ctx):
        self.visit(ctx.expresion())
        self._flush_all()
        cond = self.PilaO.pop() if self.PilaO else None
        if self.PTipos: self.PTipos.pop()
        Lfalse = self.ir.new_label()
        self.ir.emit("GOTOF", cond, None, Lfalse)
        self.visit(ctx.body())
        cp = ctx.condition_p()
        if cp and cp.getChildCount() > 0:
            Lend = self.ir.new_label()
            self.ir.emit("GOTO", None, None, Lend)
            self.ir.emit("LABEL", None, None, Lfalse)
            self.visit(cp.body())
            self.ir.emit("LABEL", None, None, Lend)
        else:
            self.ir.emit("LABEL", None, None, Lfalse)
        return None

    def visitCycle(self, ctx):
        Lstart = self.ir.new_label()
        self.ir.emit("LABEL", None, None, Lstart)
        self.visit(ctx.expresion())
        self._flush_all()
        cond = self.PilaO.pop() if self.PilaO else None
        if self.PTipos: self.PTipos.pop()
        Lend = self.ir.new_label()
        self.ir.emit("GOTOF", cond, None, Lend)
        self.visit(ctx.body())
        self.ir.emit("GOTO", None, None, Lstart)
        self.ir.emit("LABEL", None, None, Lend)
        return None
