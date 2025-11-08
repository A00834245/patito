# Directorio de funciones y tablas de variables para Patito (con validaciones).
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Literal

# Tipos soportados actualmente por Patito
TypeName = Literal["int", "float", "bool", "void", "string"]


# --------------------------- Errores semánticos ---------------------------
class SemanticError(Exception):
    """Base para errores semánticos."""


class DuplicateSymbolError(SemanticError):
    pass


class UndefinedSymbolError(SemanticError):
    pass


class TypeMismatchError(SemanticError):
    pass


# ------------------------ Tablas de variables ----------------------------
@dataclass(frozen=True)
class VarInfo:
    name: str
    type: TypeName
    kind: Literal["global", "local", "param", "temp"] = "local"
    address: Optional[int] = None  # reservado para asignación de memoria futura


class VarTable:
    """Tabla de variables por ámbito (global o local/params)."""

    def __init__(self) -> None:
        self._vars: Dict[str, VarInfo] = {}

    def declare(self, name: str, type_: TypeName, *, kind: VarInfo.__annotations__["kind"] = "local") -> VarInfo:
        if name in self._vars:
            raise DuplicateSymbolError(f"Identificador duplicado: {name}")
        info = VarInfo(name=name, type=type_, kind=kind)
        self._vars[name] = info
        return info

    def get(self, name: str) -> Optional[VarInfo]:
        return self._vars.get(name)

    def __contains__(self, name: str) -> bool:  # pragma: no cover
        return name in self._vars

    def items(self):  # pragma: no cover
        return self._vars.items()


# --------------------------- Directorio de funciones ----------------------
@dataclass
class ParamInfo:
    name: str
    type: TypeName


@dataclass
class FunctionInfo:
    name: str
    return_type: TypeName  # "void" en el lenguaje actual
    params: List[ParamInfo] = field(default_factory=list)
    vars: VarTable = field(default_factory=VarTable)  # locales + params
    start_quad: Optional[int] = None  # reservado para cuadruplos

    def declare_param(self, name: str, type_: TypeName) -> ParamInfo:
        if self.vars.get(name):
            raise DuplicateSymbolError(f"Parámetro duplicado: {name}")
        p = ParamInfo(name=name, type=type_)
        self.params.append(p)
        self.vars.declare(name, type_, kind="param")
        return p

    def declare_local(self, name: str, type_: TypeName) -> VarInfo:
        return self.vars.declare(name, type_, kind="local")

    def resolve_local(self, name: str) -> Optional[VarInfo]:
        return self.vars.get(name)


class FunctionDirectory:
    """Directorio de funciones con firmas y tablas de variables (alcance local→global)."""

    def __init__(self) -> None:
        self._globals = VarTable()
        self._funcs: Dict[str, FunctionInfo] = {}

    # ---- Globales ----
    def declare_global(self, name: str, type_: TypeName) -> VarInfo:
        return self._globals.declare(name, type_, kind="global")

    def get_global(self, name: str) -> Optional[VarInfo]:
        return self._globals.get(name)

    # ---- Funciones ----
    def declare_function(self, name: str, return_type: TypeName = "void") -> FunctionInfo:
        if name in self._funcs:
            raise DuplicateSymbolError(f"Función duplicada: {name}")
        fi = FunctionInfo(name=name, return_type=return_type)
        self._funcs[name] = fi
        return fi

    def has_function(self, name: str) -> bool:
        return name in self._funcs

    def get_function(self, name: str) -> FunctionInfo:
        try:
            return self._funcs[name]
        except KeyError as e:  # pragma: no cover
            raise UndefinedSymbolError(f"Función no definida: {name}") from e

    def set_start(self, name: str, start_quad: int) -> None:
        self.get_function(name).start_quad = start_quad

    def signature(self, name: str) -> Tuple[TypeName, List[TypeName]]:
        f = self.get_function(name)
        return f.return_type, [p.type for p in f.params]

    # ---- Variables locales / parámetros ----
    def declare_param(self, func_name: str, param_name: str, param_type: TypeName) -> ParamInfo:
        return self.get_function(func_name).declare_param(param_name, param_type)

    def declare_local(self, func_name: str, var_name: str, var_type: TypeName) -> VarInfo:
        return self.get_function(func_name).declare_local(var_name, var_type)

    # ---- Resolución ----
    def resolve_var(self, name: str, current_func: Optional[str]) -> VarInfo:
        """Busca primero en local (función actual) y luego en global. Lanza error si no existe."""
        if current_func is not None and current_func in self._funcs:
            v = self._funcs[current_func].resolve_local(name)
            if v is not None:
                return v
        v = self._globals.get(name)
        if v is not None:
            return v
        raise UndefinedSymbolError(f"Identificador no definido: {name}")

    # ---- Inspección (opcional) ----
    def all_globals(self) -> Dict[str, VarInfo]:  # pragma: no cover
        return dict(self._globals._vars)

    def all_functions(self) -> Dict[str, FunctionInfo]:  # pragma: no cover
        return dict(self._funcs)


# Ejemplo de uso (ilustrativo):
# fd = FunctionDirectory()
# fd.declare_global("a", "int")
# f = fd.declare_function("f", return_type="void")
# fd.declare_param("f", "x", "int")
# fd.declare_local("f", "t1", "float")
# assert fd.resolve_var("x", current_func="f").kind == "param"
# assert fd.resolve_var("a", current_func="f").kind == "global"
