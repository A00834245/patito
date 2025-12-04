# entrega3/codegen_visitor.py

from __future__ import annotations
from typing import List

from antlr4 import InputStream, CommonTokenStream

from ..entrega1.generated.PatitoLexer import PatitoLexer
from ..entrega1.generated.PatitoParser import PatitoParser

from ..entrega2.semantic_visitor import SemanticVisitor
from ..entrega2.semantic_cube import (
    TypeName,
    type_of_binary,
    type_of_unary,
    can_assign,
)
from ..entrega2.symbols import TypeMismatchError

from ..entrega4.virtual_memory import ConstantTable


Quad = tuple[str, object, object, object]


class CodeGenVisitor(SemanticVisitor):
    """
    Visitor de entrega 3:
    - Reusa toda la semántica de entrega2 (directorios, tipos, etc.)
    - Agrega:
        * PilaO      (operandos: direcciones virtuales)
        * PTypes     (tipos de cada operando)
        * POper      (operadores)
        * quads      (lista de cuádruplos)
    - Traduce:
        * expresion, exp, termino, factor
        * assign
        * print_cfg
    """

    def __init__(self) -> None:
        super().__init__()  # construye func_dir, vm, etc.
        # Pilas
        self.PilaO: List[int] = []          # operandos (dir. virtuales)
        self.PTypes: List[TypeName] = []    # tipos de operandos
        self.POper: List[str] = []          # operadores (+, -, *, /, <, >, ==, ...)
        # Fila de cuádruplos
        self.quads: List[Quad] = []
        # Tabla de constantes (usa la misma instancia de VirtualMemory)
        self.const_table = ConstantTable(self.vm)

    # ----------------- Helper interno para binarios ----------------- #

    def _reduce_binary(self, valid_ops: set[str]) -> None:
        """
        Mientras el tope de POper sea uno de valid_ops,
        genera el cuádruplo correspondiente.
        """
        while self.POper and self.POper[-1] in valid_ops:
            op = self.POper.pop()

            # Sacar operandos
            right_addr = self.PilaO.pop()
            right_type = self.PTypes.pop()
            left_addr = self.PilaO.pop()
            left_type = self.PTypes.pop()

            # Validación de tipos
            result_type = type_of_binary(op, left_type, right_type)
            if result_type is None:
                raise TypeMismatchError(
                    f"Tipos incompatibles para '{op}': {left_type} {op} {right_type}"
                )

            # Temporal para el resultado
            temp_addr = self.vm.alloc_temp(result_type)

            # Crear cuádruplo: (op, left, right, result)
            self.quads.append((op, left_addr, right_addr, temp_addr))

            # Empujar resultado a las pilas
            self.PilaO.append(temp_addr)
            self.PTypes.append(result_type)

    # ----------------- PROGRAMA / START ----------------- #

    # Sobrescribimos start para regresar también los quads
    def visitStart(self, ctx: PatitoParser.StartContext):
        # Esto construye directorio de funciones, variables, etc. (Entrega 2)
        super().visitStart(ctx)
        # Al final ya tenemos:
        #   - self.func_dir
        #   - self.quads
        return self.func_dir, self.quads

    # ----------------- STATEMENTS LINEALES ----------------- #

    # statement : assign | condition | cycle | fcall SEMI | print_cfg | LB statement_p RB ;
    def visitStatement(self, ctx: PatitoParser.StatementContext):
        if ctx.assign():
            return self.visit(ctx.assign())
        if ctx.print_cfg():
            return self.visit(ctx.print_cfg())
        if ctx.fcall():
            # Por ahora, para entrega 3, podemos sólo visitar la llamada
            # (sin generar GOSUB todavía)
            return self.visit(ctx.fcall())
        if ctx.condition():
            # Condicionales se verán en entrega 4
            return super().visitCondition(ctx.condition())
        if ctx.cycle():
            # Ciclos también en entrega 4
            return super().visitCycle(ctx.cycle())
        if ctx.LB():
            # Bloque { statement_p }
            return self.visit(ctx.statement_p())
        return None

    # body : LB body_p RB ;
    def visitBody(self, ctx: PatitoParser.BodyContext):
        # Delegar al mismo recorrido recursivo que en SemanticVisitor,
        # pero permitiendo generación de cuádruplos en los statements internos.
        return self.visit(ctx.body_p())

    # statement_p : statement statement_p | /* empty */ ;
    def visitStatement_p(self, ctx: PatitoParser.Statement_pContext):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.statement())
        self.visit(ctx.statement_p())
        return None

    # ----------------- ASSIGN ----------------- #

    # assign : ID ASSIGN expresion SEMI ;
    def visitAssign(self, ctx: PatitoParser.AssignContext):
        var_name = ctx.ID().getText()

        # Resolvemos la variable usando el directorio (global/local)
        var_info = self.func_dir.resolve_var(var_name, self.current_function)
        dest_addr = var_info.address
        dest_type = var_info.type

        # Evaluar la expresion del lado derecho
        self.visit(ctx.expresion())

        expr_addr = self.PilaO.pop()
        expr_type = self.PTypes.pop()

        # Validar asignación con el cubo
        if not can_assign(dest_type, expr_type):
            raise TypeMismatchError(
                f"No se puede asignar {expr_type} a variable {var_name} de tipo {dest_type}"
            )

        # Cuádruplo (=, expr, -, dest)
        self.quads.append(("=", expr_addr, None, dest_addr))
        return None

    # ----------------- PRINT ----------------- #

    # print_cfg : PRINT LP print_p RP SEMI ;
    def visitPrint_cfg(self, ctx: PatitoParser.Print_cfgContext):
        self.visit(ctx.print_p())
        return None

    # print_p : expresion print_pp | STRING_LIT print_pp ;
    def visitPrint_p(self, ctx: PatitoParser.Print_pContext):
        if ctx.expresion():
            # Caso: print(expresion, ...)
            self.visit(ctx.expresion())
            value_addr = self.PilaO.pop()
            value_type = self.PTypes.pop()
            # Cuádruplo: PRINT value
            self.quads.append(("PRINT", value_addr, None, None))
        else:
            # Caso: print("string", ...)
            text = ctx.STRING_LIT().getText()   # incluye comillas
            # Registramos la constante (tipo string)
            const_addr = self.const_table.get_or_add("string", text)
            self.quads.append(("PRINT", const_addr, None, None))

        # Continuar con más argumentos, si hay
        self.visit(ctx.print_pp())
        return None

    # print_pp : COMMA print_p | /* empty */ ;
    def visitPrint_pp(self, ctx: PatitoParser.Print_ppContext):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.print_p())
        return None

    # ----------------- EXPRESIÓN (relacionales) ----------------- #

    # expresion : exp expresion_p ;
    def visitExpresion(self, ctx: PatitoParser.ExpresionContext):
        self.visit(ctx.exp())
        self.visit(ctx.expresion_p())
        return None

    # expresion_p : GT exp | LT exp | NEQ exp | EQ exp | GEQ exp | LEQ exp | /* empty */ ;
    def visitExpresion_p(self, ctx: PatitoParser.Expresion_pContext):
        if ctx.getChildCount() == 0:
            return None

        # Determinar operador relacional
        if ctx.GT():
            op = ">"
        elif ctx.LT():
            op = "<"
        elif ctx.NEQ():
            op = "!="
        elif ctx.EQ():
            op = "=="
        elif ctx.GEQ():
            op = ">="
        elif ctx.LEQ():
            op = "<="
        else:
            raise RuntimeError("Operador relacional no reconocido")

        # 1. Meter operador a la POper
        self.POper.append(op)

        # 2. Evaluar el exp de la derecha
        self.visit(ctx.exp())

        # 3. Reducir operadores relacionales (todos tienen misma precedencia)
        self._reduce_binary({">", "<", "!=", "==", ">=", "<="})
        return None

    # ----------------- EXP (suma / resta) ----------------- #

    # exp : termino exp_p ;
    def visitExp(self, ctx: PatitoParser.ExpContext):
        self.visit(ctx.termino())
        self.visit(ctx.exp_p())
        return None

    # exp_p : PLUS termino exp_p | MINUS termino exp_p | /* empty */ ;
    def visitExp_p(self, ctx: PatitoParser.Exp_pContext):
        if ctx.getChildCount() == 0:
            return None

        if ctx.PLUS():
            op = "+"
        else:
            op = "-"

        # 1. Push operador +/-
        self.POper.append(op)

        # 2. Procesar el siguiente termino
        self.visit(ctx.termino())

        # 3. Reducir todas las +, - pendientes
        self._reduce_binary({"+", "-"})
        # 4. Seguir con más exp_p
        self.visit(ctx.exp_p())
        return None

    # ----------------- TERMINO (*, /) ----------------- #

    # termino : factor termino_p ;
    def visitTermino(self, ctx: PatitoParser.TerminoContext):
        self.visit(ctx.factor())
        self.visit(ctx.termino_p())
        return None

    # termino_p : MUL factor termino_p | DIV factor termino_p | /* empty */ ;
    def visitTermino_p(self, ctx: PatitoParser.Termino_pContext):
        if ctx.getChildCount() == 0:
            return None

        if ctx.MUL():
            op = "*"
        else:
            op = "/"

        # 1. Push operador
        self.POper.append(op)

        # 2. Procesar factor
        self.visit(ctx.factor())

        # 3. Reducir todas las * y / pendientes
        self._reduce_binary({"*", "/"})
        # 4. Seguir
        self.visit(ctx.termino_p())
        return None

    # ----------------- FACTOR ----------------- #

    # factor : LP expresion RP | factor_p | fcall ;
    def visitFactor(self, ctx: PatitoParser.FactorContext):
        if ctx.LP():
            # ( expresion )
            self.visit(ctx.expresion())
        elif ctx.fcall():
            # Para entrega 3, podemos sólo visitar la llamada;
            # en entrega 4 ya generaremos ERA/PARAM/GOSUB
            self.visit(ctx.fcall())
        else:
            # factor_p: posible +id, -id, +cte, -cte, id, cte
            self.visit(ctx.factor_p())
        return None

    # factor_p : factor_pp factor_ppp ;
    def visitFactor_p(self, ctx: PatitoParser.Factor_pContext):
        # factor_pp me dice si hay +, -, o nada
        sign = self.visit(ctx.factor_pp())
        # factor_ppp mete el operando a PilaO/PTypes
        self.visit(ctx.factor_ppp())

        # Si hay signo unario negativo, generamos cuádruplo unario
        if sign == "-":
            operand_addr = self.PilaO.pop()
            operand_type = self.PTypes.pop()

            result_type = type_of_unary("-", operand_type)
            if result_type is None:
                raise TypeMismatchError(f"No se puede aplicar - a tipo {operand_type}")

            temp_addr = self.vm.alloc_temp(result_type)
            # Usamos '-' con right=None para indicar unario
            self.quads.append(("-", operand_addr, None, temp_addr))

            self.PilaO.append(temp_addr)
            self.PTypes.append(result_type)

        # Si es '+', no necesitamos cuádruplo unario
        return None

    # factor_pp : PLUS | MINUS | /* empty */ ;
    def visitFactor_pp(self, ctx: PatitoParser.Factor_ppContext):
        if ctx.PLUS():
            return "+"
        if ctx.MINUS():
            return "-"
        return None  # sin signo

    # factor_ppp : ID | cte ;
    def visitFactor_ppp(self, ctx: PatitoParser.Factor_pppContext):
        if ctx.ID():
            name = ctx.ID().getText()
            info = self.func_dir.resolve_var(name, self.current_function)
            self.PilaO.append(info.address)
            self.PTypes.append(info.type)
        else:
            # cte: INT_LIT | FLOAT_LIT
            self.visit(ctx.cte())
        return None

    # ----------------- CTE ----------------- #

    # cte : INT_LIT | FLOAT_LIT ;
    def visitCte(self, ctx: PatitoParser.CteContext):
        if ctx.INT_LIT():
            raw = ctx.INT_LIT().getText()
            value = int(raw)
            addr = self.const_table.get_or_add("int", value)
            self.PilaO.append(addr)
            self.PTypes.append("int")
        else:
            raw = ctx.FLOAT_LIT().getText()
            value = float(raw)
            addr = self.const_table.get_or_add("float", value)
            self.PilaO.append(addr)
            self.PTypes.append("float")
        return None


def build_quads_from_source(source: str):  # Solo para los tests
    """Construye lexer, parser y visitor a partir de código fuente y regresa
    (FunctionDirectory, lista_de_quads)."""
    input_stream = InputStream(source)
    lexer = PatitoLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = PatitoParser(tokens)

    tree = parser.start()

    visitor = CodeGenVisitor()
    func_dir, quads = visitor.visit(tree)
    return func_dir, quads
