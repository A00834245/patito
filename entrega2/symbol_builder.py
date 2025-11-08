# Construye el directorio de funciones y tablas de variables a partir del AST de Patito.
from __future__ import annotations

from typing import Any, Iterable

from .symbols import (
    FunctionDirectory,
    DuplicateSymbolError,
)


def _iter_var_groups(groups: Iterable[Any]):
    for g in (groups or []):
        if g and g[0] == "vars":
            ids = [i[1] for i in g[1] or []]
            tname = g[2][1]
            yield ids, tname


def _iter_params(params: Iterable[Any]):
    for p in (params or []):
        if p and p[0] == "param":
            yield p[1], p[2][1]


def build_symbols_from_ast(ast: Any) -> FunctionDirectory:
    if not ast or ast[0] != "programa":
        raise ValueError("AST raíz inválido: se esperaba 'programa'")

    _, _prog_name, global_vars, funcs_node, _body = ast

    fd = FunctionDirectory()

    # Globales
    for id_list, tname in _iter_var_groups(global_vars):
        seen = set()
        for v in id_list:
            if v in seen:
                raise DuplicateSymbolError(f"Variable global duplicada en el mismo grupo: {v}")
            seen.add(v)
            fd.declare_global(v, tname)

    # Funciones
    funcs = funcs_node[1] if funcs_node and funcs_node[0] == "funcs" else []
    for f in funcs:
        if not f or f[0] != "func":
            continue
        _, fname, params_list, vars_opt, _fbody = f
        fd.declare_function(fname, return_type="void")
        for pname, ptype in _iter_params(params_list):
            fd.declare_param(fname, pname, ptype)
        for id_list, tname in _iter_var_groups(vars_opt):
            seen = set()
            for v in id_list:
                if v in seen:
                    raise DuplicateSymbolError(
                        f"Variable local duplicada en el mismo grupo (función {fname}): {v}"
                    )
                seen.add(v)
                fd.declare_local(fname, v, tname)

    return fd
