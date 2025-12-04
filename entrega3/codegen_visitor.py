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
    Visitor de entrega 3, 4 y ahora 5 (cuádruplos de funciones).

    Reusa toda la semántica de entrega2 (directorios, tipos, etc.) y agrega:

      * PilaO      (operandos: direcciones virtuales)
      * PTypes     (tipos de operandos)
      * POper      (operadores)
      * PSaltos    (índices de cuádruplos de salto: GOTOF / GOTO)
      * quads      (lista de cuádruplos)

    Traduce con Syntax-Directed Translation:

      * expresion, exp, termino, factor
      * assign
      * print_cfg
      * condition / condition_p (if / if-else)
      * cycle (while)
      * funcs / fcall / return (entrega 5)
    """

    def __init__(self) -> None:
        super().__init__()  # construye func_dir, vm, etc.

        # Pilas para la traducción de expresiones y saltos
        self.PilaO: List[int] = []          # operandos (dir. virtuales)
        self.PTypes: List[TypeName] = []    # tipos de operandos
        self.POper: List[str] = []          # operadores (+, -, *, /, <, >, ==, ...)
        self.PSaltos: List[int] = []        # índices de cuádruplos de salto

        # Fila de cuádruplos generados
        self.quads: List[Quad] = []

        # Tabla de constantes (encima de la misma VirtualMemory)
        self.const_table = ConstantTable(self.vm)

        # Soporte para llamadas a funciones (ERA / PARAM / GOSUB)
        # Pila de nombres de función actualmente en llamada (para anidar f(g()))
        self._call_func_stack: List[str] = []
        # Pila con el índice de parámetro que sigue para cada llamada
        self._call_param_index_stack: List[int] = []
        # Flag para que visitStatement sepa si la última fcall produjo valor
        self._last_call_had_value: bool = False

    # ----------------- Helpers internos ----------------- #

    def _push_operand(self, addr: int, type_: TypeName) -> None:
        self.PilaO.append(addr)
        self.PTypes.append(type_)

    def _push_operator(self, op: str) -> None:
        self.POper.append(op)

    def _emit(self, op: str, left: object, right: object, result: object) -> int:
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
        # Aquí ya generamos cuádruplos dentro de visitPrograma.
        self.visit(ctx.programa())
        return self.func_dir, self.quads

    # programa : PROGRAM ID SEMI programa_p programa_pp MAIN body END ;
    def visitPrograma(self, ctx: PatitoParser.ProgramaContext):
        # Nombre del programa (no lo usamos como función)
        prog_name = ctx.ID().getText()

        # Estamos en ámbito global
        self.current_function = None

        # 1) Emitir un GOTO placeholder al inicio de main para que la VM
        # comience ejecutando main y no los cuerpos de las funciones.
        goto_main_idx = self._emit("GOTO", None, None, None)

        # 2) Declarar variables globales (no generan cuádruplos)
        self.visit(ctx.programa_p())  # VARS globales

        # 3) Generar cuádruplos de todas las funciones
        self.visit(ctx.programa_pp())  # FUNCS

        # 4) Calcular el índice de inicio de main y parchear el GOTO
        main_start = len(self.quads)
        self._fill_jump(goto_main_idx, main_start)

        # 5) Traducir el cuerpo de main (BODY)
        self.visit(ctx.body())

        # 6) Marcar fin de programa explícito para la VM
        self.quads.append(("END", None, None, None))

        # Seguimos en ámbito global después de main
        self.current_function = None
        return self.func_dir

    # ----------------- FUNCIONES (declaración) ----------------- #

    # funcs : funcs_p ID LP funcs_pp RP LB funcs_ppp body RB SEMI ;
    def visitFuncs(self, ctx: PatitoParser.FuncsContext):
        # 1) Obtener tipo de retorno desde la regla auxiliar (int, float o void)
        return_type: TypeName = self.visit(ctx.funcs_p())
        func_name = ctx.ID().getText()

        # 2) Registrar la función en el directorio (mismo comportamiento que SemanticVisitor)
        func_info = self.func_dir.declare_function(func_name, return_type=return_type)

        # 3) Si la función no es void, reservar una celda global para su valor de retorno
        if return_type != "void":
            # Usamos una variable global "oculta" para almacenar el resultado de la función.
            ret_addr = self.vm.alloc_var(kind="global", type_=return_type)
            hidden_name = f"__ret_{func_name}"
            # La damos de alta en la tabla global solo para tener la dirección registrada.
            self.func_dir.declare_global(hidden_name, return_type, address=ret_addr)
            func_info.return_address = ret_addr

        # 4) Cambiar el contexto actual a la función
        prev_func = self.current_function
        self.current_function = func_name

        # 5) Guardar el índice del primer cuádruplo de la función
        self.func_dir.set_start_quad(func_name, len(self.quads))

        # 6) Procesar parámetros y variables locales (misma lógica que SemanticVisitor)
        self.visit(ctx.funcs_pp())   # parámetros
        self.visit(ctx.funcs_ppp())  # variables locales (vars)

        # 7) Traducir el cuerpo de la función
        self.visit(ctx.body())

        # 8) Marcar el final de la función (útil para la Máquina Virtual)
        self.quads.append(("ENDFUNC", None, None, None))

        # 9) Restaurar contexto anterior
        self.current_function = prev_func
        return None

    # ----------------- LLAMADAS A FUNCIÓN (ERA / PARAM / GOSUB) ----------------- #

    # fcall : ID LP fcall_p RP ;
    def visitFcall(self, ctx: PatitoParser.FcallContext):
        func_name = ctx.ID().getText()

        # Verificar que la función exista y obtener su firma
        ret_type, param_types = self.func_dir.signature(func_name)

        # Preparar contexto de la llamada
        self._call_func_stack.append(func_name)
        self._call_param_index_stack.append(0)
        self._last_call_had_value = False

        # ERA: reservar el 'activation record' para la función
        self._emit("ERA", func_name, None, None)

        # Traducir la lista de argumentos
        self.visit(ctx.fcall_p())

        # Verificar número de argumentos
        given_count = self._call_param_index_stack.pop()
        self._call_func_stack.pop()
        expected_count = len(param_types)
        if given_count != expected_count:
            raise TypeMismatchError(
                f"Llamada a función '{func_name}' con {given_count} argumentos; "
                f"se esperaban {expected_count}"
            )

        # GOSUB: saltar al inicio de la función
        func_info = self.func_dir.get_function(func_name)
        if func_info.start_quad is None:
            raise RuntimeError(f"La función '{func_name}' no tiene start_quad asignado")
        self._emit("GOSUB", func_name, None, func_info.start_quad)

        # Si la función regresa un valor, dejamos en la pila de operandos
        # la dirección donde la VM depositará el resultado.
        if ret_type != "void":
            if func_info.return_address is None:
                raise RuntimeError(
                    f"La función '{func_name}' tiene tipo de retorno '{ret_type}' "
                    "pero no tiene return_address asignado"
                )
            self.PilaO.append(func_info.return_address)
            self.PTypes.append(ret_type)
            self._last_call_had_value = True
        else:
            self._last_call_had_value = False

        return None

    # fcall_p : expresion fcall_pp | /* empty */ ;
    def visitFcall_p(self, ctx: PatitoParser.Fcall_pContext):
        if ctx.getChildCount() == 0:
            return None

        # Evaluar el argumento (expresion)
        self.visit(ctx.expresion())
        arg_addr = self.PilaO.pop()
        arg_type: TypeName = self.PTypes.pop()

        if not self._call_func_stack:
            raise RuntimeError("visitFcall_p llamado fuera de contexto de llamada a función")

        func_name = self._call_func_stack[-1]
        _, param_types = self.func_dir.signature(func_name)
        index = self._call_param_index_stack[-1]

        if index >= len(param_types):
            raise TypeMismatchError(
                f"Demasiados argumentos en llamada a función '{func_name}'"
            )

        expected_type = param_types[index]
        if not can_assign(expected_type, arg_type):
            raise TypeMismatchError(
                f"Tipo incorrecto para argumento {index+1} de '{func_name}': "
                f"se esperaba {expected_type}, se encontró {arg_type}"
            )

        # Dirección del parámetro formal dentro de la función
        func_info = self.func_dir.get_function(func_name)
        param_info = func_info.params[index]
        param_var = func_info.vars.get(param_info.name)
        if param_var is None or param_var.address is None:
            raise RuntimeError(
                f"El parámetro '{param_info.name}' de la función '{func_name}' "
                "no tiene dirección virtual asignada"
            )

        # PARAM arg -> dirParam
        self._emit("PARAM", arg_addr, None, param_var.address)

        # Avanzar índice de parámetro y continuar con el resto (si los hay)
        self._call_param_index_stack[-1] = index + 1
        self.visit(ctx.fcall_pp())
        return None

    # fcall_pp : COMMA fcall_p | /* empty */ ;
    def visitFcall_pp(self, ctx: PatitoParser.Fcall_ppContext):
        if ctx.getChildCount() == 0:
            return None
        # Regla: COMMA fcall_p
        self.visit(ctx.fcall_p())
        return None

    # ----------------- RETURN ----------------- #

    # return_cfg : RETURN return_p SEMI ;
    def visitReturn_cfg(self, ctx: PatitoParser.Return_cfgContext):
        if self.current_function is None:
            # Un return fuera de función no tiene sentido
            raise RuntimeError("return fuera de una función")

        func_info = self.func_dir.get_function(self.current_function)
        func_ret_type = func_info.return_type

        value_addr, value_type = self.visit(ctx.return_p())

        if func_ret_type == "void":
            # Funciones void no deben regresar valor
            if value_addr is not None:
                raise TypeMismatchError(
                    f"La función '{self.current_function}' es void y no puede regresar un valor"
                )
            # RETURN simple: la VM regresará al llamador
            self.quads.append(("RETURN", None, None, None))
        else:
            # Funciones con valor de retorno
            if value_addr is None:
                raise TypeMismatchError(
                    f"La función '{self.current_function}' debe regresar un valor de tipo "
                    f"{func_ret_type}"
                )
            if not can_assign(func_ret_type, value_type):
                raise TypeMismatchError(
                    f"Tipo de retorno incorrecto en función '{self.current_function}': "
                    f"se esperaba {func_ret_type}, se encontró {value_type}"
                )
            if func_info.return_address is None:
                raise RuntimeError(
                    f"La función '{self.current_function}' no tiene return_address asignado"
                )

            # Asignar el valor de la expresión a la celda de retorno
            self.quads.append(("=", value_addr, None, func_info.return_address))
            # Y generar el RETURN para que la VM regrese al llamador
            self.quads.append(("RETURN", func_info.return_address, None, None))

        return None

    # return_p : expresion | /* empty */ ;
    def visitReturn_p(self, ctx: PatitoParser.Return_pContext):
        if ctx.getChildCount() == 0:
            # No hay expresión: return;
            return None, "void"
        self.visit(ctx.expresion())
        addr = self.PilaO.pop()
        type_ = self.PTypes.pop()
        return addr, type_

    # ----------------- STATEMENTS (lineales + condicionales + cíclicos) ----------------- #

    # statement : assign | condition | cycle | fcall SEMI | print_cfg | LB statement_p RB ;
    def visitStatement(self, ctx: PatitoParser.StatementContext):
        if ctx.assign():
            return self.visit(ctx.assign())
        if ctx.print_cfg():
            return self.visit(ctx.print_cfg())
        if ctx.fcall():
            # Llamada a función como STATEMENT (f();)
            self.visit(ctx.fcall())
            # Si la función regresó un valor, lo descartamos porque no se usa
            if self._last_call_had_value:
                self.PilaO.pop()
                self.PTypes.pop()
            return None
        if ctx.condition():
            # Traducción dirigida por la sintaxis para if / if-else
            return self.visit(ctx.condition())
        if ctx.cycle():
            # Traducción para while
            return self.visit(ctx.cycle())
        if ctx.return_cfg():
            # return dentro del cuerpo de una función
            return self.visit(ctx.return_cfg())
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

        # 2. Crear GOTOF y recordar su índice para rellenar luego
        gotof_idx = self._emit("GOTOF", cond_addr, None, None)
        self.PSaltos.append(gotof_idx)

        # 3. Traducir el cuerpo del if (body)
        self.visit(ctx.body())

        # 4. Revisar si hay else
        self.visit(ctx.condition_p())
        return None

    def visitCondition_p(self, ctx: PatitoParser.Condition_pContext):
        if ctx.getChildCount() == 0:
            # No hay else; rellenamos GOTOF con el final del if
            gotof_idx = self.PSaltos.pop()
            self._fill_jump(gotof_idx, len(self.quads))
            return None

        # Hay else:
        # - Primero generamos un GOTO para saltar al final del else
        goto_end_idx = self._emit("GOTO", None, None, None)

        # - Rellenamos el GOTOF para que vaya al inicio del else
        gotof_idx = self.PSaltos.pop()
        self._fill_jump(gotof_idx, len(self.quads))

        # - Traducimos el body del else
        self.visit(ctx.body())

        # - Finalmente rellenamos el GOTO para que vaya al final total
        self._fill_jump(goto_end_idx, len(self.quads))
        return None

    # ----------------- CICLOS (WHILE) ----------------- #

    # cycle : WHILE LP expresion RP body ;
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

        # Relacional: exp <exp>
        right_label = ctx.getChild(0).getText()  # el operador: <, >, ==, etc.
        self.visit(ctx.exp())

        # Sacar operandos
        right_addr = self.PilaO.pop()
        right_type: TypeName = self.PTypes.pop()
        left_addr = self.PilaO.pop()
        left_type: TypeName = self.PTypes.pop()

        # Tipo resultado según el cubo semántico (op, left, right)
        result_type = type_of_binary(right_label, left_type, right_type)
        if result_type is None:
            raise TypeMismatchError(
                f"No se puede aplicar {right_label} entre {left_type} y {right_type}"
            )

        # Temporal bool
        temp_addr = self.vm.alloc_temp(result_type)
        self.quads.append((right_label, left_addr, right_addr, temp_addr))

        self.PilaO.append(temp_addr)
        self.PTypes.append(result_type)
        return None

    # ----------------- EXP (suma/resta) ----------------- #

    # exp : termino exp_p ;
    def visitExp(self, ctx: PatitoParser.ExpContext):
        self.visit(ctx.termino())
        self.visit(ctx.exp_p())
        return None

    # exp_p : PLUS termino exp_p | MINUS termino exp_p | /* empty */ ;
    def visitExp_p(self, ctx: PatitoParser.Exp_pContext):
        if ctx.getChildCount() == 0:
            return None

        op = ctx.getChild(0).getText()  # '+' o '-'
        self._push_operator(op)
        self.visit(ctx.termino())

        # Reducir mientras en la cima haya + o -
        while self.POper and self.POper[-1] in {"+", "-"}:
            op = self.POper.pop()
            right_addr = self.PilaO.pop()
            right_type: TypeName = self.PTypes.pop()
            left_addr = self.PilaO.pop()
            left_type: TypeName = self.PTypes.pop()

            # Cubo semántico espera (op, left, right)
            result_type = type_of_binary(op, left_type, right_type)
            if result_type is None:
                raise TypeMismatchError(
                    f"No se puede aplicar {op} entre {left_type} y {right_type}"
                )

            temp_addr = self.vm.alloc_temp(result_type)
            self.quads.append((op, left_addr, right_addr, temp_addr))

            self.PilaO.append(temp_addr)
            self.PTypes.append(result_type)

        # Continuar con recursión a la derecha
        self.visit(ctx.exp_p())
        return None

    # ----------------- TERMINO (multiplicación/división) ----------------- #

    # termino : factor termino_p ;
    def visitTermino(self, ctx: PatitoParser.TerminoContext):
        self.visit(ctx.factor())
        self.visit(ctx.termino_p())
        return None

    # termino_p : MUL factor termino_p | DIV factor termino_p | /* empty */ ;
    def visitTermino_p(self, ctx: PatitoParser.Termino_pContext):
        if ctx.getChildCount() == 0:
            return None

        op = ctx.getChild(0).getText()  # '*' o '/'
        self._push_operator(op)
        self.visit(ctx.factor())

        # Reducir mientras en la cima haya * o /
        while self.POper and self.POper[-1] in {"*", "/"}:
            op = self.POper.pop()
            right_addr = self.PilaO.pop()
            right_type: TypeName = self.PTypes.pop()
            left_addr = self.PilaO.pop()
            left_type: TypeName = self.PTypes.pop()

            # Cubo semántico espera (op, left, right)
            result_type = type_of_binary(op, left_type, right_type)
            if result_type is None:
                raise TypeMismatchError(
                    f"No se puede aplicar {op} entre {left_type} y {right_type}"
                )

            temp_addr = self.vm.alloc_temp(result_type)
            self.quads.append((op, left_addr, right_addr, temp_addr))

            self.PilaO.append(temp_addr)
            self.PTypes.append(result_type)

        self.visit(ctx.termino_p())
        return None

    # ----------------- FACTOR ----------------- #

    # factor : LP expresion RP | factor_p | fcall ;
    def visitFactor(self, ctx: PatitoParser.FactorContext):
        if ctx.LP():
            # ( expresion )
            self.visit(ctx.expresion())
        elif ctx.fcall():
            # Llamada a función usada como EXPRESIÓN
            self.visit(ctx.fcall())
            # (si la función no es void, visitFcall ya dejó el valor en PilaO/PTypes)
        else:
            # factor_p: posible +id, -id, +cte, -cte, id, cte
            self.visit(ctx.factor_p())
        return None

    # factor_p : factor_pp factor_ppp ;
    def visitFactor_p(self, ctx: PatitoParser.Factor_pContext):
        self.visit(ctx.factor_pp())
        self.visit(ctx.factor_ppp())
        return None

    # factor_pp : PLUS | MINUS | /* empty */ ;
    def visitFactor_pp(self, ctx: PatitoParser.Factor_ppContext):
        # Solo anotamos el signo unario; se aplicará en factor_ppp
        return None

    # factor_ppp : ID | cte ;
    def visitFactor_ppp(self, ctx: PatitoParser.Factor_pppContext):
        # Puede ser un ID o una constante
        if ctx.ID():
            name = ctx.ID().getText()
            var_info = self.func_dir.resolve_var(name, self.current_function)
            addr = var_info.address
            if addr is None:
                raise RuntimeError(f"La variable '{name}' no tiene dirección asignada")

            self.PilaO.append(addr)
            self.PTypes.append(var_info.type)
        else:
            # cte
            cte_ctx = ctx.cte()
            if cte_ctx.INT_LIT():
                text = cte_ctx.INT_LIT().getText()
                value = int(text)
                addr = self.const_table.get_or_add("int", value)
                self.PilaO.append(addr)
                self.PTypes.append("int")
            elif cte_ctx.FLOAT_LIT():
                text = cte_ctx.FLOAT_LIT().getText()
                value = float(text)
                addr = self.const_table.get_or_add("float", value)
                self.PilaO.append(addr)
                self.PTypes.append("float")
            else:
                raise RuntimeError("cte sin INT_LIT ni FLOAT_LIT")

        # ¿hay signo unario?
        parent = ctx.parentCtx  # Factor_p
        sign_ctx = parent.factor_pp()
        if sign_ctx.PLUS():
            # +x  => igual
            return None
        if sign_ctx.MINUS():
            # -x  => generar temporal con 0 - x o unario
            operand_addr = self.PilaO.pop()
            operand_type = self.PTypes.pop()

            result_type = type_of_unary("-", operand_type)
            if result_type is None:
                raise TypeMismatchError(
                    f"No se puede aplicar - a tipo {operand_type}"
                )

            temp_addr = self.vm.alloc_temp(result_type)
            # Usamos '-' con right=None para indicar unario
            self.quads.append(("-", operand_addr, None, temp_addr))

            self.PilaO.append(temp_addr)
            self.PTypes.append(result_type)

        # Si es '+', no necesitamos cuádruplo unario
        return None

    # ----------------- ASSIGN ----------------- #

    # assign : ID ASSIGN expresion SEMI ;
    def visitAssign(self, ctx: PatitoParser.AssignContext):
        var_name = ctx.ID().getText()
        var_info = self.func_dir.resolve_var(var_name, self.current_function)

        dest_addr = var_info.address
        dest_type = var_info.type

        self.visit(ctx.expresion())
        expr_addr = self.PilaO.pop()
        expr_type: TypeName = self.PTypes.pop()

        # Verificar que se pueda asignar expr_type a dest_type
        if not can_assign(dest_type, expr_type):
            raise TypeMismatchError(
                f"No se puede asignar {expr_type} a variable {var_name} de tipo {dest_type}"
            )

        # Cuádruplo (=, expr, -, dest)
        self.quads.append(("=", expr_addr, None, dest_addr))
        return None


# ----------------- Función de conveniencia translate() ----------------- #

def translate(source: str) -> Tuple[object, List[Quad]]:
    """Recibe código fuente Patito como string, ejecuta scanner + parser +
    CodeGenVisitor (Syntax-Directed Translation) y regresa (func_dir, quads)."""
    input_stream = InputStream(source)
    lexer = PatitoLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = PatitoParser(tokens)

    tree = parser.start()

    visitor = CodeGenVisitor()
    func_dir, quads = visitor.visit(tree)

    # Construir un mapa addr -> valor de constantes para la VM y pruebas
    const_addr_to_value = {
        addr: value
        for (type_, value), addr in visitor.const_table.items
    }
    # Lo colgamos del directorio de funciones como ayuda para entrega 5
    setattr(func_dir, "constants", const_addr_to_value)

    return func_dir, quads


# Alias para compatibilidad con entregas anteriores y pruebas existentes
# que importan build_quads_from_source.
def build_quads_from_source(source: str) -> Tuple[object, List[Quad]]:
    return translate(source)
