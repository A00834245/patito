from __future__ import annotations

from typing import Any, List, Optional, Tuple

from antlr4 import TerminalNode
# Support multiple generated module naming conventions
try:
    from .PatitoParser import PatitoParser  # type: ignore
except Exception:  # pragma: no cover
    from .patito_parser import PatitoParser  # type: ignore

# Prefer standard ANTLR visitor name (PatitoVisitor); fallback to ParserVisitor; lastly generic ParseTreeVisitor
try:
    from .PatitoVisitor import PatitoVisitor as _BaseVisitor  # type: ignore
except Exception:  # pragma: no cover
    try:
        from .PatitoParserVisitor import PatitoParserVisitor as _BaseVisitor  # type: ignore
    except Exception:  # pragma: no cover
        from antlr4 import ParseTreeVisitor as _BaseVisitor  # type: ignore

def _id_node(name: str):
    return ("id", name)


def _type_node(tok: TerminalNode) -> Tuple[str, str]:
    txt = tok.getText()
    if txt == "int":
        return ("type", "int")
    if txt == "float":
        return ("type", "float")
    return ("type", txt)


def _int_node(tok: TerminalNode):
    return ("cte_int", int(tok.getText()))


def _float_node(tok: TerminalNode):
    return ("cte_float", float(tok.getText()))


def _string_node(tok: TerminalNode):
    return ("string", tok.getText())


def _fold_binops(left: Any, ops: List[Tuple[str, Any]]):
    acc = left
    for op, right in ops:
        acc = ("bin", op, acc, right)
    return acc


class PatitoASTVisitor(_BaseVisitor):
    # ---- Start / Programa -------------------------------------------------
    def visitStart(self, ctx):  # start: programa EOF
        return self.visit(ctx.programa())

    def visitPrograma(self, ctx):
        # PROGRAM ID SEMI programa_p programa_pp MAIN body END
        prog_name = ctx.ID().getText()
        vars_section = self.visit(ctx.programa_p())  # list[vars-group] or None
        funcs_list = self.visit(ctx.programa_pp())   # ("funcs", [...])
        body = self.visit(ctx.body())                # ("body", [...])
        return ("programa", prog_name, vars_section, funcs_list, body)

    def visitPrograma_p(self, ctx):
        # vars | empty
        if ctx.getChildCount() == 0:
            return None
        groups = self.visit(ctx.vars())  # list of ("vars", ids, type)
        return groups

    def visitPrograma_pp(self, ctx):
        # programa_ppp | empty
        if ctx.getChildCount() == 0:
            return ("funcs", [])
        return self.visit(ctx.programa_ppp())

    def visitPrograma_ppp(self, ctx):
        # funcs programa_ppp | empty
        if ctx.getChildCount() == 0:
            return ("funcs", [])
        first = self.visit(ctx.funcs())
        rest = self.visit(ctx.programa_ppp())
        # rest is ("funcs", [...])
        return ("funcs", [first] + list(rest[1]))

    # ---- Vars -------------------------------------------------------------
    def visitVars(self, ctx):  # VAR vars_p
        return self.visit(ctx.vars_p())  # returns list of groups

    def visitVars_p(self, ctx):
        # ID vars_pp COLON type SEMI vars_ppp
        # Collect all IDs until COLON appears in this subtree
        ids: List[Tuple[str, str]] = []
        for ch in ctx.getChildren():
            if isinstance(ch, TerminalNode):
                ttype = ch.symbol.type
                if ttype == PatitoParser.COLON:
                    break
                if ttype == PatitoParser.ID:
                    ids.append(_id_node(ch.getText()))
            else:
                # Dive into nested children before ':' (e.g., vars_pp recursion)
                # Stop if this child subtree already contains ':' as immediate child
                text = getattr(ch, 'getText', lambda: '')()
                if ':' in text:
                    # We will encounter ':' as a sibling; skip diving to avoid duplicates
                    continue
                # Otherwise, collect IDs from this child
                ids.extend(self._collect_ids_until_colon(ch))
        type_node = self.visit(ctx.type_())  # ("type", ...)
        group = ("vars", ids, type_node)
        more = self.visit(ctx.vars_ppp())  # list of groups or []
        return [group] + more

    def _collect_ids_until_colon(self, node) -> List[Tuple[str, str]]:
        acc: List[Tuple[str, str]] = []
        try:
            for ch in node.getChildren():
                if isinstance(ch, TerminalNode):
                    ttype = ch.symbol.type
                    if ttype == PatitoParser.COLON:
                        return acc
                    if ttype == PatitoParser.ID:
                        acc.append(_id_node(ch.getText()))
                else:
                    acc.extend(self._collect_ids_until_colon(ch))
        except Exception:
            pass
        return acc

    def visitVars_pp(self, ctx):
        # COMMA vars_p | empty
        # Not used directly; collection handled in visitVars_p
        return None

    def visitVars_ppp(self, ctx):
        # vars_p | empty  -> returns list of groups
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.vars_p())

    def visitType(self, ctx):
        if ctx.INT_TYPE():
            return ("type", "int")
        if ctx.FLOAT_TYPE():
            return ("type", "float")
        # Fallback
        return ("type", ctx.getText())

    # ---- Funcs ------------------------------------------------------------
    def visitFuncs(self, ctx):
        # VOID ID LPAREN funcs_p RPAREN LBR funcs_pppp body RBR SEMI
        name = ctx.ID().getText()
        params = self.visit(ctx.funcs_p())  # list of ("param", name, type)
        vars_opt = self.visit(ctx.funcs_pppp())  # list of var groups or None
        body = self.visit(ctx.body())
        return ("func", name, params, vars_opt, body)

    def visitFuncs_p(self, ctx):
        # funcs_pp | empty
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.funcs_pp())

    def visitFuncs_pp(self, ctx):
        # ID COLON type funcs_ppp
        pname = ctx.ID().getText()
        ptype = self.visit(ctx.type_())
        head = ("param", pname, ptype)
        rest = self.visit(ctx.funcs_ppp())  # list
        return [head] + rest

    def visitFuncs_ppp(self, ctx):
        # COMMA funcs_pp | empty
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.funcs_pp())

    def visitFuncs_pppp(self, ctx):
        # vars | empty
        if ctx.getChildCount() == 0:
            return None
        return self.visit(ctx.vars())

    # ---- Body -------------------------------------------------------------
    def visitBody(self, ctx):
        # LB body_p RB
        stmts = self.visit(ctx.body_p())
        return ("body", stmts)

    def visitBody_p(self, ctx):
        # body_pp | empty -> returns list
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.body_pp())

    def visitBody_pp(self, ctx):
        # statement body_pp | empty
        if ctx.getChildCount() == 0:
            return []
        first = self.visit(ctx.statement())
        rest = self.visit(ctx.body_pp())
        return [first] + rest

    # ---- Statements -------------------------------------------------------
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
        return ("noop",)

    def visitAssign(self, ctx):
        # ID ASSIGN expresion SEMI
        name = ctx.ID().getText()
        expr = self.visit(ctx.expresion())
        return ("assign", _id_node(name), expr)

    def visitCondition(self, ctx):
        # IF LPAREN expresion RPAREN body condition_p SEMI
        cond = self.visit(ctx.expresion())
        then_body = self.visit(ctx.body())
        else_body = self.visit(ctx.condition_p())
        return ("if", cond, then_body, else_body)

    def visitCondition_p(self, ctx):
        # ELSE body | empty
        if ctx.getChildCount() == 0:
            return None
        return self.visit(ctx.body())

    def visitCycle(self, ctx):
        # WHILE LPAREN expresion RPAREN DO cuerpo SEMI
        cond = self.visit(ctx.expresion())
        # Some grammars name this 'cuerpo'; if not present, fallback to 'body'
        body_ctx = None
        if hasattr(ctx, "cuerpo") and callable(getattr(ctx, "cuerpo")):
            try:
                body_ctx = ctx.cuerpo()
            except Exception:
                body_ctx = None
        if body_ctx is None and hasattr(ctx, "body") and callable(getattr(ctx, "body")):
            try:
                body_ctx = ctx.body()
            except Exception:
                body_ctx = None
        body_node = self.visit(body_ctx) if body_ctx is not None else ("body", [])
        return ("while_do", cond, body_node)

    # ---- Function calls ---------------------------------------------------
    def visitFcall(self, ctx):
        # ID LPAREN fcall_p RPAREN SEMI
        name = ctx.ID().getText()
        args = self.visit(ctx.fcall_p())
        return ("call", name, args)

    def visitFcall_p(self, ctx):
        # expresion fcall_pp | empty -> returns list
        if ctx.getChildCount() == 0:
            return []
        head = self.visit(ctx.expresion())
        rest = self.visit(ctx.fcall_pp())
        return [head] + rest

    def visitFcall_pp(self, ctx):
        # COMMA fcall_p | empty
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.fcall_p())

    # ---- Print ------------------------------------------------------------
    def visitPrint_stmt(self, ctx):
        # PRINT LPAREN print_p print_pp RPAREN SEMI
        args = []
        args.extend(self.visit(ctx.print_p()))
        args.extend(self.visit(ctx.print_pp()))
        return ("print", args)

    def visitPrint_p(self, ctx):
        # expresion print_pp | STRING_LIT print_pp
        args = []
        if ctx.expresion():
            args.append(self.visit(ctx.expresion()))
        else:
            args.append(_string_node(ctx.STRING_LIT()))
        args.extend(self.visit(ctx.print_pp()))
        return args

    def visitPrint_pp(self, ctx):
        # COMMA print_p | empty -> returns list
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.print_p())

    # ---- Expressions ------------------------------------------------------
    def visitExpresion(self, ctx):
        # exp expresion_p
        left = self.visit(ctx.exp())
        tail = self.visit(ctx.expresion_p())
        if tail is None:
            return left
        op, right = tail
        return ("cmp", op, left, right)

    def visitExpresion_p(self, ctx):
        # GT exp | LT exp | NEQ exp | empty
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
        # termino exp_p
        left = self.visit(ctx.termino())
        ops = self.visit(ctx.exp_p())  # list of (op, term)
        return _fold_binops(left, ops)

    def visitExp_p(self, ctx):
        # PLUS termino exp_p | MINUS termino exp_p | empty
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
        # factor termino_p
        left = self.visit(ctx.factor())
        ops = self.visit(ctx.termino_p())
        return _fold_binops(left, ops)

    def visitTermino_p(self, ctx):
        # MUL factor termino_p | DIV factor termino_p | empty
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
        # LPAREN expresion RPAREN | factor_p
        if ctx.expresion():
            return self.visit(ctx.expresion())
        return self.visit(ctx.factor_p())

    def visitFactor_p(self, ctx):
        # factor_pp factor_ppp
        op = None
        if ctx.factor_pp().PLUS():
            op = "PLUS"
        elif ctx.factor_pp().MINUS():
            op = "MINUS"
        val = self.visit(ctx.factor_ppp())
        if op:
            return ("un", op, val)
        return val

    def visitFactor_pp(self, ctx):
        # PLUS | MINUS | empty
        return None

    def visitFactor_ppp(self, ctx):
        # ID | cte
        if ctx.ID():
            return _id_node(ctx.ID().getText())
        return self.visit(ctx.cte())

    def visitCte(self, ctx):
        if ctx.INT_LIT():
            return _int_node(ctx.INT_LIT())
        if ctx.FLOAT_LIT():
            return _float_node(ctx.FLOAT_LIT())
        # Unreachable given grammar
        return ("cte", ctx.getText())
