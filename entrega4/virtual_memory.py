# entrega3/virtual_memory.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Any, Literal

TypeName = Literal["int", "float", "bool", "string", "void"]
SegmentName = Literal["global", "local", "temp", "const"]


@dataclass
class MemorySegment:
    base: int
    limit: int
    next: int

    def alloc(self, size: int = 1) -> int:
        if self.next + size - 1 > self.limit:
            raise MemoryError(
                f"Overflow de segmento [{self.base}, {self.limit}] al pedir {size} direcciones"
            )
        addr = self.next
        self.next += size
        return addr


class VirtualMemory:
    def __init__(self) -> None:
        self._segments: Dict[SegmentName, Dict[TypeName, MemorySegment]] = {
            "global": {
                "int":    MemorySegment(1000, 1499, 1000),
                "float":  MemorySegment(1500, 1999, 1500),
                "bool":   MemorySegment(2000, 2499, 2000),
                "string": MemorySegment(2500, 2999, 2500),
                "void":   MemorySegment(0, 0, 0),
            },
            "local": {
                "int":    MemorySegment(3000, 3499, 3000),
                "float":  MemorySegment(3500, 3999, 3500),
                "bool":   MemorySegment(4000, 4499, 4000),
                "string": MemorySegment(4500, 4999, 4500),
                "void":   MemorySegment(0, 0, 0),
            },
            "temp": {
                "int":    MemorySegment(8000, 8499, 8000),
                "float":  MemorySegment(8500, 8999, 8500),
                "bool":   MemorySegment(9000, 9499, 9000),
                "string": MemorySegment(9500, 9999, 9500),
                "void":   MemorySegment(0, 0, 0),
            },
            "const": {
                "int":    MemorySegment(13000, 13499, 13000),
                "float":  MemorySegment(13500, 13999, 13500),
                "bool":   MemorySegment(14000, 14499, 14000),
                "string": MemorySegment(14500, 14999, 14500),
                "void":   MemorySegment(0, 0, 0),
            },
        }

    # ------------ helper functions ------------ #

    def alloc_var(self, kind: Literal["global", "local", "param"], type_: TypeName) -> int:
        if type_ == "void":
            raise ValueError("No se pueden declarar variables de tipo void")
        seg: SegmentName = "global" if kind == "global" else "local"
        return self._segments[seg][type_].alloc()

    def alloc_temp(self, type_: TypeName) -> int:
        if type_ == "void":
            raise ValueError("No se pueden crear temporales de tipo void")
        return self._segments["temp"][type_].alloc()

    def alloc_const(self, type_: TypeName) -> int:
        if type_ == "void":
            raise ValueError("No se pueden crear constantes de tipo void")
        return self._segments["const"][type_].alloc()


class ConstantTable:
    def __init__(self, vm: VirtualMemory) -> None:
        self._vm = vm
        self._table: Dict[Tuple[TypeName, Any], int] = {}

    def get_or_add(self, type_: TypeName, value: Any) -> int:
        key = (type_, value)
        if key not in self._table:
            addr = self._vm.alloc_const(type_)
            self._table[key] = addr
        return self._table[key]

    @property
    def items(self):
        return self._table.items()