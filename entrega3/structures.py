from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


class Stack(List[Any]):
    def push(self, x: Any) -> None:
        self.append(x)

    def pop_safe(self) -> Optional[Any]:
        return self.pop() if self else None

    def peek(self) -> Optional[Any]:
        return self[-1] if self else None


# Operator names normalized to match translator ops
ARITH_OPS = {"PLUS", "MINUS", "MUL", "DIV"}
REL_OPS = {"GT", "LT", "NEQ"}
ALL_OPS = ARITH_OPS | REL_OPS


class Precedence:
    # Higher number = binds tighter
    _PREC = {
        "MUL": 3,
        "DIV": 3,
        "PLUS": 2,
        "MINUS": 2,
        # Relational lower than arithmetic
        "GT": 1,
        "LT": 1,
        "NEQ": 1,
    }

    @classmethod
    def value(cls, op: str) -> int:
        return cls._PREC.get(op, 0)

    @classmethod
    def should_reduce(cls, top_op: Optional[str], incoming_op: str) -> bool:
        if top_op is None:
            return False
        # left-associative: reduce when top_prec >= incoming_prec
        return cls.value(top_op) >= cls.value(incoming_op)


# Conventional names used in course material
POper = Stack  # Operators stack
PilaO = Stack  # Operands stack (holds operand identifiers or temporaries)
PTipos = Stack  # Types stack (parallel to PilaO)


__all__ = [
    "Stack",
    "POper",
    "PilaO",
    "PTipos",
    "Precedence",
    "ARITH_OPS",
    "REL_OPS",
    "ALL_OPS",
]
