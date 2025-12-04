from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from entrega3.codegen_visitor import Quad

# Rangos de direcciones virtuales, deben coincidir con virtual_memory.py
GLOBAL_MIN, GLOBAL_MAX = 1000, 2999
LOCAL_MIN, LOCAL_MAX = 3000, 4999
TEMP_MIN, TEMP_MAX = 8000, 9999
CONST_MIN, CONST_MAX = 13000, 14999


@dataclass
class MemorySpace:
    """
    Representa un espacio de memoria simple:
    dirección virtual -> valor en tiempo de ejecución.
    """
    values: Dict[int, Any] = field(default_factory=dict)

    def get(self, addr: int) -> Any:
        if addr not in self.values:
            raise RuntimeError(f"Acceso a dirección no inicializada: {addr}")
        return self.values[addr]

    def set(self, addr: int, value: Any) -> None:
        self.values[addr] = value


@dataclass
class ActivationRecord:
    """
    Activation Record para una llamada a función.

    - locals:  direcciones del segmento LOCAL (3000–4999)
    - temps:   direcciones del segmento TEMP  (8000–9999)
    - return_ip: índice de cuádruplo al que se debe regresar
    - func_name: nombre de la función (opcional, útil para debug)
    """
    locals: MemorySpace = field(default_factory=MemorySpace)
    temps: MemorySpace = field(default_factory=MemorySpace)
    return_ip: Optional[int] = None
    func_name: Optional[str] = None


class VirtualMachine:
    """
    Máquina Virtual de Patito (Entrega 5/6).

    Ejecuta los cuádruplos generados por CodeGenVisitor usando un
    mapa de memoria de ejecución.

    Soporta:

        - Expresiones aritméticas: +, -, *, /  (incluyendo - unario)
        - Expresiones relacionales: <, >, <=, >=, ==, !=
        - Asignación: =
        - PRINT
        - Control de flujo: GOTO, GOTOF
        - Llamadas a función: ERA, PARAM, GOSUB, RETURN, ENDFUNC
        - Final de programa: END
    """

    def __init__(
        self,
        quads: List[Quad],
        constants: Optional[Dict[int, Any]] = None,
        debug: bool = False,
    ) -> None:
        self.quads: List[Quad] = quads
        self.ip: int = 0  # instruction pointer
        self.debug: bool = debug

        # Memoria global (segmento 1000–2999)
        self.global_mem = MemorySpace()

        # Memoria de constantes (segmento 13000–14999)
        self.const_mem = MemorySpace(constants.copy() if constants else {})

        # Memoria temporal cuando NO hay función activa (por ejemplo en main)
        self._global_temps = MemorySpace()

        # Pila de activaciones (llamadas a funciones)
        self.call_stack: List[ActivationRecord] = []

        # Frame "pendiente" para la próxima llamada (creado por ERA, llenado por PARAM)
        self._pending_frame: Optional[ActivationRecord] = None

    # ----------------- Helpers de memoria ----------------- #

    def _space_for_address(self, addr: int) -> MemorySpace:
        """
        Decide en qué espacio de memoria vive una dirección virtual.
        """
        if addr is None:
            raise RuntimeError("Dirección None inesperada")

        if CONST_MIN <= addr <= CONST_MAX:
            # Constantes: siempre vienen precargadas
            return self.const_mem

        if GLOBAL_MIN <= addr <= GLOBAL_MAX:
            # variables globales
            return self.global_mem

        # Locales y temporales dependen de si hay un frame activo
        frame: Optional[ActivationRecord] = self.call_stack[-1] if self.call_stack else None

        if LOCAL_MIN <= addr <= LOCAL_MAX:
            if frame is None:
                # Técnicamente no deberíamos tener locales sin función,
                # pero lo marcamos como error explícito.
                raise RuntimeError(f"Acceso a dirección local {addr} sin función activa")
            return frame.locals

        if TEMP_MIN <= addr <= TEMP_MAX:
            if frame is None:
                # Temporales globales (por ejemplo, expresiones en main)
                return self._global_temps
            return frame.temps

        raise RuntimeError(f"Dirección fuera de rango: {addr}")

    def _read(self, addr: int) -> Any:
        space = self._space_for_address(addr)
        return space.get(addr)

    def _write(self, addr: int, value: Any) -> None:
        space = self._space_for_address(addr)
        space.set(addr, value)

    # ----------------- Loop principal de ejecución ----------------- #

    def run(self) -> None:
        """
        Ejecuta los cuádruplos hasta encontrar un END o
        hasta que se salga por error.
        """
        while self.ip < len(self.quads):
            op, left, right, res = self.quads[self.ip]

            if self.debug:
                print(f"[IP={self.ip:03}] {op}, {left}, {right}, {res}")

            # Aritmética básica (+, -, *, /) incluyendo - unario
            if op in {"+", "-", "*", "/"}:
                self._exec_arithmetic(op, left, right, res)

            # Relacionales (siempre regresan bool)
            elif op in {">", "<", ">=", "<=", "==", "!="}:
                self._exec_relational(op, left, right, res)

            # Asignación
            elif op == "=":
                value = self._read(left)
                self._write(res, value)

            # PRINT
            elif op == "PRINT":
                value = self._read(left)
                # Para Patito basta con imprimir en stdout
                print(value)

            # GOTO incondicional
            elif op == "GOTO":
                self.ip = int(res)
                continue

            # GOTOF: salto si la condición es falsa
            elif op == "GOTOF":
                cond = self._read(left)
                if not cond:
                    self.ip = int(res)
                    continue

            # --------- Soporte para funciones --------- #

            elif op == "ERA":
                # Prepara un nuevo frame para la próxima llamada a función.
                func_name = str(left)
                self._pending_frame = ActivationRecord(func_name=func_name)

            elif op == "PARAM":
                if self._pending_frame is None:
                    raise RuntimeError("PARAM sin ERA previo")
                value = self._read(left)
                addr = int(res)
                self._pending_frame.locals.set(addr, value)

            elif op == "GOSUB":
                if self._pending_frame is None:
                    raise RuntimeError("GOSUB sin ERA/PARAM previos")
                # Guardar IP de retorno en el frame pendiente y activarlo
                self._pending_frame.return_ip = self.ip + 1
                self.call_stack.append(self._pending_frame)
                self._pending_frame = None

                # Brincar al inicio de la función:
                self.ip = int(res)
                continue

            elif op == "RETURN":
                # La convención típica es que el valor de retorno ya se asignó
                # a alguna dirección global (por cuádruplo '=').
                # Aquí solo hacemos pop del frame y regresamos.
                if not self.call_stack:
                    raise RuntimeError("RETURN sin frame activo")
                frame = self.call_stack.pop()
                if frame.return_ip is None:
                    # No hay a dónde regresar: terminamos programa
                    return
                self.ip = frame.return_ip
                continue

            elif op == "ENDFUNC":
                # Equivalente a un RETURN implícito
                if not self.call_stack:
                    raise RuntimeError("ENDFUNC sin frame activo")
                frame = self.call_stack.pop()
                if frame.return_ip is None:
                    return
                self.ip = frame.return_ip
                continue

            # END: fin del programa
            elif op == "END":
                break

            else:
                raise RuntimeError(f"Opcode desconocido: {op}")

            # Avanzar al siguiente cuádruplo
            self.ip += 1

    # ----------------- Implementación de operadores ----------------- #

    def _exec_arithmetic(
        self,
        op: str,
        left: Optional[int],
        right: Optional[int],
        res: int,
    ) -> None:
        """
        Soporta operadores aritméticos binarios y el menos unario.

        - Binario: (op, left, right, res)
        - Unario:  ("-", operand, None, res)
        """
        # Caso especial: menos unario
        if op == "-" and right is None:
            a = self._read(left)
            value = -a
        else:
            a = self._read(left)
            b = self._read(right)

            if op == "+":
                value = a + b
            elif op == "-":
                value = a - b
            elif op == "*":
                value = a * b
            elif op == "/":
                # En Patito, int / int regresa float según el cubo semántico;
                # aquí delegamos en Python (que ya hace eso si hay float).
                value = a / b
            else:
                raise RuntimeError(f"Operador aritmético desconocido: {op}")

        self._write(res, value)

    def _exec_relational(self, op: str, left: int, right: int, res: int) -> None:
        a = self._read(left)
        b = self._read(right)

        if op == ">":
            value = a > b
        elif op == "<":
            value = a < b
        elif op == ">=":
            value = a >= b
        elif op == "<=":
            value = a <= b
        elif op == "==":
            value = a == b
        elif op == "!=":
            value = a != b
        else:
            raise RuntimeError(f"Operador relacional desconocido: {op}")

        # Resultado se guarda como bool en la dirección resultante
        self._write(res, value)
