import pytest
from entrega2.symbols import (
    FunctionDirectory,
    DuplicateSymbolError,
    UndefinedSymbolError
)


def test_global_declaration():
    fd = FunctionDirectory()
    fd.declare_global("x", "int")

    x = fd.resolve_var("x", None)
    assert x.type == "int"
    assert x.kind == "global"


def test_function_locals_and_params():
    fd = FunctionDirectory()
    fd.declare_function("foo", "void")

    fd.declare_param("foo", "a", "int")
    fd.declare_local("foo", "t", "float")

    a = fd.resolve_var("a", "foo")
    t = fd.resolve_var("t", "foo")

    assert a.kind == "param"
    assert t.kind == "local"


def test_shadowing_local_over_global():
    fd = FunctionDirectory()
    fd.declare_global("x", "int")

    fd.declare_function("foo", "void")
    fd.declare_local("foo", "x", "float")

    assert fd.resolve_var("x", "foo").type == "float"
    assert fd.resolve_var("x", None).type == "int"


def test_duplicate_global_raises():
    fd = FunctionDirectory()
    fd.declare_global("x", "int")

    with pytest.raises(DuplicateSymbolError):
        fd.declare_global("x", "float")


def test_undefined_raises():
    fd = FunctionDirectory()

    with pytest.raises(UndefinedSymbolError):
        fd.resolve_var("y", None)
