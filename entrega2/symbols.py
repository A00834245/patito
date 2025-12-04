# Eestructuras del directorio de funciones 

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal

try: # no me estaba funcionando los imports
    from entrega2.semantic_cube import TypeName
except ImportError:
    TypeName = Literal["int", "float", "bool", "string", "void"]


# ---------------------- Errores semanticos basicos ---------------------- #

# Base para los errores semanticos
class SemanticError(Exception):
    pass

# Lanza error cuando se redeclara una variable o funcion en el mismo scope
class DuplicateSymbolError(SemanticError):
    pass

# Lanza error cuando se usa un identificador no declarado
class UndefinedSymbolError(SemanticError):
    pass

# Lanza error cuando hay incompatibilidad de tipos (todavia no implementado)
class TypeMismatchError(SemanticError):
    pass


# ----------------------------- VarTable --------------------------------- #

@dataclass(frozen=True)

#Representa una variable declarada
class VarInfo:
    name: str
    type: TypeName
    kind: Literal["global", "local", "param", "temp"] = "local" #saber que kind es 
    address: Optional[int] = None #para cuando asigne memoria virtual

#Tabla de variables para un scope (global o local de funcion)
#Internamente es un dict
class VarTable:

    def __init__(self) -> None:
        self._vars: Dict[str, VarInfo] = {}

    # Declara una variable nueva en el scope
    def declare(self, name: str, type_: TypeName, *, kind: Literal["global", "local", "param", "temp"] = "local") -> VarInfo:
        if name in self._vars:
            raise DuplicateSymbolError(f"Identificador duplicado en el mismo ámbito: {name}")
        info = VarInfo(name=name, type=type_, kind=kind)
        self._vars[name] = info
        return info

    #Regresa la VarInfo de una variable si existe, o None si no existe en la tabla
    def get(self, name: str) -> Optional[VarInfo]:
        return self._vars.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._vars

    #Iterar sobre (nombre, VarInfo), para depuracion o reportes
    def items(self):
        return self._vars.items()


# ---------------------- FunctionInfo y ParamInfo ------------------------ #

#Info de un parametro formal de una funcion
@dataclass
class ParamInfo:
    name: str
    type: TypeName

#Guarda toda la informacion de una funcion 
@dataclass
class FunctionInfo:
    name: str
    return_type: TypeName = "void"
    params: List[ParamInfo] = field(default_factory=list)
    vars: VarTable = field(default_factory=VarTable) #tabla de variables locales y parametros
    start_quad: Optional[int] = None #numero de cuadruplo donde inicia la funcion para gosub, ahorita no lo uso

    #Declara un parametro de la funcion, lo agrega a lista de params, y lo mete a la VarTable de la funcion (kind = param)
    def declare_param(self, name: str, type_: TypeName) -> ParamInfo:
        # Valida que no haya un param/var local con el mismo nombre
        if self.vars.get(name) is not None:
            raise DuplicateSymbolError(f"Parámetro/variable local duplicado en función '{self.name}': {name}")
        p = ParamInfo(name=name, type=type_)
        self.params.append(p)
        self.vars.declare(name, type_, kind="param")
        return p

    # Declara una variable local en la funcion (kind = local)
    def declare_local(self, name: str, type_: TypeName) -> VarInfo:
        return self.vars.declare(name, type_, kind="local")

    # Busca una variable sólo en el ambito local de la función
    def resolve_local(self, name: str) -> Optional[VarInfo]:
        return self.vars.get(name)


# --------------------------- FunctionDirectory -------------------------- #

#Estructure principal de simbolos de todo el programa
#Mantiene la tabla global de variables, un dict de nombre_funcion, y provee metodos para declara y resolver simbolos
class FunctionDirectory:
    def __init__(self) -> None:
        self._globals = VarTable()
        self._funcs: Dict[str, FunctionInfo] = {}

    #Declara una variable global
    def declare_global(self, name: str, type_: TypeName) -> VarInfo:
        return self._globals.declare(name, type_, kind="global")

    #Regresa la variable global si existe, o None si no 
    def get_global(self, name: str) -> Optional[VarInfo]:
        return self._globals.get(name)


    #Declara una nueva función, lanza DuplicateSymbolError si el nombre ya estaba registrado
    def declare_function(self, name: str, return_type: TypeName = "void") -> FunctionInfo:
        if name in self._funcs:
            raise DuplicateSymbolError(f"Función duplicada: {name}")

        fi = FunctionInfo(name=name, return_type=return_type)
        self._funcs[name] = fi
        return fi

    def has_function(self, name: str) -> bool:
        return name in self._funcs

    #Regresa la FunctionInfo de una funcion, o lanza UndefinedSymbolError si no existe
    def get_function(self, name: str) -> FunctionInfo:
        try:
            return self._funcs[name]
        except KeyError as e:
            raise UndefinedSymbolError(f"Función no definida: {name}") from e

    # Asigna el indice de cuadruplo donde inicia una funcion (lo usare en gosub despues)
    def set_start_quad(self, name: str, start_quad: int) -> None:
        func = self.get_function(name)
        func.start_quad = start_quad

    # Regresa la firma de una funcion (return_type, [param_types...]), se usa para validar llamadas
    def signature(self, name: str) -> tuple[TypeName, list[TypeName]]:
        f = self.get_function(name)
        return f.return_type, [p.type for p in f.params]

    # ---- Variables locales / parametros (helpers) ---- #

    def declare_param(self, func_name: str, param_name: str, param_type: TypeName) -> ParamInfo:
        func = self.get_function(func_name)
        return func.declare_param(param_name, param_type)

    def declare_local(self, func_name: str, var_name: str, var_type: TypeName) -> VarInfo:
        func = self.get_function(func_name)
        return func.declare_local(var_name, var_type)

    # --------- Resolucion de variables --------- #

    # Busca una variable en el ambito local de current_func (si hay), y si no en globales
    def resolve_var(self, name: str, current_func: Optional[str]) -> VarInfo:
        # 1. Primero buscar en la función actual
        if current_func is not None and current_func in self._funcs:
            local_var = self._funcs[current_func].resolve_local(name)
            if local_var is not None:
                return local_var
        # 2. Luego buscar en globales
        global_var = self._globals.get(name)
        if global_var is not None:
            return global_var
        # 3. Si no está en ningún lado, error
        raise UndefinedSymbolError(f"Identificador no definido: {name}")

    # --------- Métodos de inspección / depuración --------- #

    # Regresa una copia de la tabla global 
    def all_globals(self) -> Dict[str, VarInfo]:
        return dict(self._globals._vars)

    # Regresa una copia del diccionario de funciones
    def all_functions(self) -> Dict[str, FunctionInfo]:
        return dict(self._funcs)
