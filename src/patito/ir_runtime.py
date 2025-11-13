from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _resolve(val: Any, mem: Dict[str, Any]) -> Any:
    if isinstance(val, str) and val in mem:
        return mem[val]
    return val


def run(quads: List[Tuple[str, Any, Any, Any]]) -> List[str]:
    """Execute a simple quadruple IR.

    Supported ops: ASSIGN, PRINT, PLUS, MINUS, MUL, DIV,
    CMP_GT, CMP_LT, CMP_NEQ, IF_FALSE_GOTO, GOTO, LABEL.
    """
    # memory holds variables and temporaries as string keys
    mem: Dict[str, Any] = {}
    output: List[str] = []
    # build label -> pc map
    labels: Dict[str, int] = {}
    for i, q in enumerate(quads):
        op, a1, a2, r = q.op if hasattr(q, "op") else q[0], q.arg1 if hasattr(q, "arg1") else q[1], q.arg2 if hasattr(q, "arg2") else q[2], q.res if hasattr(q, "res") else q[3]
        if op == "LABEL" and isinstance(r, str):
            labels[r] = i

    pc = 0
    n = len(quads)
    while pc < n:
        q = quads[pc]
        op = q.op if hasattr(q, "op") else q[0]
        a1 = q.arg1 if hasattr(q, "arg1") else q[1]
        a2 = q.arg2 if hasattr(q, "arg2") else q[2]
        r = q.res if hasattr(q, "res") else q[3]

        if op == "ASSIGN":
            mem[str(r)] = _resolve(a1, mem)
        elif op in ("PLUS", "MINUS", "MUL", "DIV"):
            v1 = _resolve(a1, mem)
            v2 = _resolve(a2, mem)
            if op == "PLUS":
                mem[str(r)] = v1 + v2
            elif op == "MINUS":
                mem[str(r)] = v1 - v2
            elif op == "MUL":
                mem[str(r)] = v1 * v2
            else:
                mem[str(r)] = v1 / v2
        elif op in ("CMP_GT", "CMP_LT", "CMP_NEQ"):
            v1 = _resolve(a1, mem)
            v2 = _resolve(a2, mem)
            if op == "CMP_GT":
                mem[str(r)] = bool(v1 > v2)
            elif op == "CMP_LT":
                mem[str(r)] = bool(v1 < v2)
            else:
                mem[str(r)] = bool(v1 != v2)
        elif op == "PRINT":
            v = _resolve(a1, mem)
            # Keep quotes for string literals in grammar (already quoted)
            output.append(str(v))
        elif op == "IF_FALSE_GOTO":
            cond = _resolve(a1, mem)
            if not cond:
                pc = labels.get(str(r), pc)
                continue
        elif op == "GOTO":
            pc = labels.get(str(r), pc)
            continue
        # LABEL: no-op at execution
        pc += 1

    return output
