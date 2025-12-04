from __future__ import annotations
from typing import List, Tuple, Optional

from antlr4 import InputStream, CommonTokenStream

from entrega1.generated.PatitoLexer import PatitoLexer
from entrega1.generated.PatitoParser import PatitoParser

from entrega2.semantic_visitor import SemanticVisitor
from entrega2.semantic_cube import (
    TypeName,
    type_of_binary,
    type_of_unary,
    can_assign,
)
from entrega2.symbols import TypeMismatchError

from entrega4.virtual_memory import ConstantTable


Quad = Tuple[str, object, object, object]


class CodeGenVisitor(SemanticVisitor):
    """
    Visitor de entrega 3 y 4:
    - Reusa toda la semántica de entrega2 (directorios, tipos, etc.)
    - Agrega:
        * PilaO      (operandos: direcciones virtuales)
        * PTypes     (tipos de cada operando)
        * POper      (operadores)
        * PSaltos    (índices de cuádruplos de salto: GOTOF / GOTO)
        * quads      (lista de cuádruplos)
    - Traduce con Syntax-Directed Translation:
        * expresion, exp, termino, factor
        * assign
        * print_cfg
        * condition / condition_p (if / if-else)
        * cycle (while)
    """

    def __init__(self) -> None:
        super().__init__()  # construye func_dir, vm, etc.

        # Pilas
        self.PilaO: List[int] = []          # operandos (dir. virtuales)
        self.PTypes: List[TypeName] = []    # tipos de operandos
        self.POper: List[str] = []          # operadores (+, -, *, /, <, >, ==, ...)
        self.PSaltos: List[int] = []        # índices de cuádruplos de salto

        # Fila de cuádruplos
        self.quads: List[Quad] = []

        # Tabla de constantes (encima de la misma VirtualMemory)
        self.const_table = ConstantTable(self.vm)

    # ----------------- Helpers internos ----------------- #

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

    def _emit(self, op: str, left: Optional[object],
              right: Optional[object], result: Optional[object]) -> int:
        """
        Agrega un cuádruplo a la fila y regresa su índice.
        Útil para GOTOF / GOTO en estatutos condicionales y cíclicos.
        """
        idx = len(self.quads)
        self.quads.append((op, left, right, result))
        return idx

    def _fill_jump(self, quad_index: int, target: int) -> None:
        """
        Rellena el campo RESULT de un cuádruplo de salto (GOTOF / GOTO)
        con el índice de destino.
        """
        op, left, right, _ = self.quads[quad_index]
        self.quads[quad_index] = (op, left, right, target)

    # ----------------- PROGRAMA / START ----------------- #

    # Sobrescribimos start para regresar también los quads
    def visitStart(self, ctx: PatitoParser.StartContext):
        # Esto construye directorio de funciones, variables, etc. (Entrega 2)
        super().visitStart(ctx)
        # Al final ya tenemos:
        #   - self.func_dir
        #   - self.quads
        return self.func_dir, self.quads

    # ----------------- STATEMENTS (lineales + condicionales + cíclicos) ----------------- #

    # statement : assign | condition | cycle | fcall SEMI | print_cfg | LB statement_p RB ;
    def visitStatement(self, ctx: PatitoParser.StatementContext):
        if ctx.assign():
            return self.visit(ctx.assign())
        if ctx.print_cfg():
            return self.visit(ctx.print_cfg())
        if ctx.fcall():
            # Aún no generamos ERA/PARAM/GOSUB; solo visitamos la llamada.
            return self.visit(ctx.fcall())
        if ctx.condition():
            # Traducción dirigida por la sintaxis para if / if-else
            return self.visit(ctx.condition())
        if ctx.cycle():
            # Traducción para while
            return self.visit(ctx.cycle())
        if ctx.LB():
            # Bloque { statement_p }
            return self.visit(ctx.statement_p())
        return None

    # body : LB body_p RB ;
    def visitBody(self, ctx: PatitoParser.BodyContext):
        return self.visit(ctx.body_p())

    # body_p : body_pp | /* empty */ ;
    def visitBody_p(self, ctx: PatitoParser.Body_pContext):
        if ctx.getChildCount() == 0:
            return None
        return self.visit(ctx.body_pp())

    # body_pp : statement body_pp | /* empty */ ;
    def visitBody_pp(self, ctx: PatitoParser.Body_ppContext):
        if ctx.getChildCount() == 0:
            return None
        self.visit(ctx.statement())
        self.visit(ctx.body_pp())
        return None

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

        # Evaluar la expresión del lado derecho
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
            _value_type = self.PTypes.pop()
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

    # ----------------- CONDICIONALES (IF / IF-ELSE) ----------------- #

    # condition   : IF LP expresion RP body condition_p SEMI ;
    # condition_p : ELSE body | /* empty */ ;
    def visitCondition(self, ctx: PatitoParser.ConditionContext):
        # 1. Evaluar la expresión condicional
        self.visit(ctx.expresion())

        cond_addr = self.PilaO.pop()
        cond_type: TypeName = self.PTypes.pop()

        # Debe ser bool (producto de un relacional, p.ej. x > 3)
        if cond_type != "bool":
            raise TypeMismatchError("La condición de un if debe ser de tipo bool")

        # 2. Generar GOTOF cond, -, -
        gotof_idx = self._emit("GOTOF", cond_addr, None, None)

        # Guardar índice en la pila de saltos
        self.PSaltos.append(gotof_idx)

        # 3. Traducir el bloque del if (parte verdadera)
        self.visit(ctx.body())

        # 4. Manejar la parte opcional (else / vacío)
        self.visit(ctx.condition_p())

        return None

    def visitCondition_p(self, ctx: PatitoParser.Condition_pContext):
        # Sin ELSE: condition_p -> ε
        if ctx.getChildCount() == 0:
            # Rellenar el GOTOF para que salte al final del if
            falso = self.PSaltos.pop()
            self._fill_jump(falso, len(self.quads))
            return None

        # Con ELSE: condition_p -> ELSE body
        # 1. Generar GOTO para saltar el bloque else al final
        goto_idx = self._emit("GOTO", None, None, None)

        # 2. Rellenar el GOTOF anterior para que brinque al inicio del else
        falso = self.PSaltos.pop()
        self._fill_jump(falso, len(self.quads))  # siguiente cuádruplo (inicio del else)

        # 3. Guardar el GOTO para rellenarlo al final del else
        self.PSaltos.append(goto_idx)

        # 4. Traducir bloque else
        self.visit(ctx.body())

        # 5. Rellenar el GOTO del final del if-else
        fin = self.PSaltos.pop()
        self._fill_jump(fin, len(self.quads))

        return None

    # ----------------- CICLOS (WHILE) ----------------- #

    # cycle : WHILE LP expresion RP DO body SEMI ;
    def visitCycle(self, ctx: PatitoParser.CycleContext):
        # 1. Marcar el inicio del ciclo (antes de evaluar la condición)
        loop_start = len(self.quads)
        self.PSaltos.append(loop_start)

        # 2. Evaluar la condición del while
        self.visit(ctx.expresion())
        cond_addr = self.PilaO.pop()
        cond_type: TypeName = self.PTypes.pop()

        if cond_type != "bool":
            raise TypeMismatchError("La condición de un while debe ser de tipo bool")

        # 3. GOTOF para salir del ciclo
        gotof_idx = self._emit("GOTOF", cond_addr, None, None)
        self.PSaltos.append(gotof_idx)

        # 4. Traducir el cuerpo del while
        self.visit(ctx.body())

        # 5. GOTO de regreso al inicio del ciclo
        falso = self.PSaltos.pop()
        loop_start = self.PSaltos.pop()
        self._emit("GOTO", None, None, loop_start)

        # 6. Rellenar GOTOF para que salga al final del ciclo
        self._fill_jump(falso, len(self.quads))

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

        # 2. Procesar el siguiente término
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
            # Para esta entrega, solo visitamos la llamada;
            # en una etapa posterior se pueden generar ERA/PARAM/GOSUB.
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


# ----------------- Helper para pruebas (Syntax-Directed Translation completa) ----------------- #

def build_quads_from_source(source: str):
    """
    Recibe código fuente Patito como string, ejecuta
    scanner + parser + CodeGenVisitor (Syntax-Directed Translation)
    y regresa (func_dir, quads).
    """
    input_stream = InputStream(source)
    lexer = PatitoLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = PatitoParser(tokens)

    tree = parser.start()

    visitor = CodeGenVisitor()
    func_dir, quads = visitor.visit(tree)
    return func_dir, quads