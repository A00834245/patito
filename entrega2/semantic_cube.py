# Cubo semantico

from __future__ import annotations
from typing import Dict, Tuple, Optional, Literal

TypeName = Literal["int", "float", "bool", "string", "void"] #string es placeholder
BinKey = Tuple[TypeName, TypeName]

# Operadores binarios
# op -> { (left_type, right_type): result_type }
SEM_CUBE: Dict[str, Dict[BinKey, TypeName]] = {
    # ---------- Arirmetica ----------
    "+": {
        ("int", "int"): "int",
        ("int", "float"): "float",
        ("float", "int"): "float",
        ("float", "float"): "float",
    },
    "-": {
        ("int", "int"): "int",
        ("int", "float"): "float",
        ("float", "int"): "float",
        ("float", "float"): "float",
    },
    "*": {
        ("int", "int"): "int",
        ("int", "float"): "float",
        ("float", "int"): "float",
        ("float", "float"): "float",
    },
    "/": {
        ("int", "int"): "float",
        ("int", "float"): "float",
        ("float", "int"): "float",
        ("float", "float"): "float",
    },

    # ---------- Relacionales ----------
    ">": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
    "<": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
    ">=": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
    "<=": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
    "==": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
    "!=": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
}

# Operadores unarios (-x. +x)
# op -> { operand_type: result_type }
UNARY_CUBE: Dict[str, Dict[TypeName, TypeName]] = {
    "+": {
        "int": "int",
        "float": "float",
    },
    "-": {
        "int": "int",
        "float": "float",
    },
}

# Asignacion permitida
# (dest, src) -> True/False
ASSIGN_OK: Dict[BinKey, bool] = {
    ("int", "int"): True,
    ("float", "float"): True,
    ("float", "int"): True,  
    ("bool", "bool"): True,
    ("string", "string"): True,
    # ("int", "float"): True,  # la deje en comment pero si quiero truncar lo permito
}

#Devuelve el resultado (tipo) de una operacion binaria (left op right), o none si es invalido
def type_of_binary(op: str, left: TypeName, right: TypeName) -> Optional[TypeName]:
    return SEM_CUBE.get(op, {}).get((left, right))

#Devuelve el resultado (tipo) de una operacion unaria (op operand), o none si es invalido
def type_of_unary(op: str, operand: TypeName) -> Optional[TypeName]:
    return UNARY_CUBE.get(op, {}).get(operand)

#Devuelve True si es una asignacion valida, o False en sino
def can_assign(dest: TypeName, src: TypeName) -> bool:
    return ASSIGN_OK.get((dest, src), False)

