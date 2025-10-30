import pytest

from patito.parser import parse_text


def ok(src: str):
    parse_text(src)


def test_min_program():
    ok('program P; main { } end')


def test_vars_and_assign_print():
    ok('program P; var a, b: int; main { a = 1 + 2 * 3; print(a); } end')


def test_if_else():
    ok('program P; main { if (a > 0) { print(a); } else { print(0); } ; } end')


def test_while_do():
    ok('program P; main { while (a < 3) do { a = a + 1; } ; } end')


def test_func_and_call():
    ok('program P; void f(x: int) [ var z: int; { print(x); } ] ; main { f(1); } end')


def test_print_string_and_expr_list():
    ok('program P; main { print("hola", 1+2, "x"); } end')


def test_invalid_missing_paren():
    with pytest.raises(SyntaxError):
        ok('program P; main { print(1 + 2; } end')
