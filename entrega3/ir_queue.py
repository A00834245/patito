from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass
class Quad:
    op: str
    arg1: Any = None
    arg2: Any = None
    res: Any = None


class IRQueue:
    def __init__(self) -> None:
        self._quads: List[Quad] = []
        self._temp_counter = 0
        self._label_counter = 0

    # --- Emit & access ---
    def emit(self, op: str, a1: Any = None, a2: Any = None, r: Any = None) -> Quad:
        q = Quad(op, a1, a2, r)
        self._quads.append(q)
        return q

    def __iter__(self):
        return iter(self._quads)

    def __len__(self) -> int:
        return len(self._quads)

    def list(self) -> List[Quad]:  # explicit access
        return list(self._quads)

    # --- Temps & Labels (deterministic) ---
    def new_temp(self) -> str:
        self._temp_counter += 1
        return f"t{self._temp_counter}"

    def new_label(self) -> str:
        self._label_counter += 1
        return f"L{self._label_counter}"

    # --- Formatting ---
    def to_lines(self) -> List[str]:
        out: List[str] = []
        for q in self._quads:
            out.append(f"{q.op}\t{q.arg1}\t{q.arg2}\t{q.res}")
        return out


__all__ = ["Quad", "IRQueue"]
