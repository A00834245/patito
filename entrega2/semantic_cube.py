# Cubo semántico en estructuras Python para validación de tipos.
from __future__ import annotations

from typing import Dict, Tuple

T = Tuple[str, str]

# Tipos soportados
TYPES = {"int", "float", "bool", "string", "void"}

# Operadores binarios: op -> {(left_type, right_type): result_type}
SEM_CUBE: Dict[str, Dict[T, str]] = {
    # Aritmética
    "PLUS": {
        ("int", "int"): "int",
        ("int", "float"): "float",
        ("float", "int"): "float",
        ("float", "float"): "float",
    },
    "MINUS": {
        ("int", "int"): "int",
        ("int", "float"): "float",
        ("float", "int"): "float",
        ("float", "float"): "float",
    },
    "MUL": {
        ("int", "int"): "int",
        ("int", "float"): "float",
        ("float", "int"): "float",
        ("float", "float"): "float",
    },
    "DIV": {
        ("int", "int"): "float",
        ("int", "float"): "float",
        ("float", "int"): "float",
        ("float", "float"): "float",
    },
    # Comparaciones → bool (solo numéricas)
    "GT": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
    "LT": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
    "NEQ": {
        ("int", "int"): "bool",
        ("int", "float"): "bool",
        ("float", "int"): "bool",
        ("float", "float"): "bool",
    },
}

# Operadores unarios: op -> {operand_type: result_type}
UNARY = {
    "PLUS": {"int": "int", "float": "float"},
    "MINUS": {"int": "int", "float": "float"},
}

# Asignación permitida: (dest_type, src_type) -> True
ASSIGN_OK = {
    ("int", "int"): True,
    ("float", "int"): True,
    ("float", "float"): True,
}


def type_of_binary(op: str, left: str, right: str) -> str | None:
    return SEM_CUBE.get(op, {}).get((left, right))


def type_of_unary(op: str, operand: str) -> str | None:
    return UNARY.get(op, {}).get(operand)


def can_assign(dest: str, src: str) -> bool:
    return ASSIGN_OK.get((dest, src), False)
