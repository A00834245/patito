from entrega2.semantic_cube import (
    type_of_binary,
    type_of_unary,
    can_assign,
)


def test_arithmetic_plus():
    assert type_of_binary("+", "int", "int") == "int"
    assert type_of_binary("+", "int", "float") == "float"
    assert type_of_binary("+", "float", "int") == "float"
    assert type_of_binary("+", "float", "float") == "float"


def test_division_int_int_gives_float():
    assert type_of_binary("/", "int", "int") == "float"


def test_relational_output_bool():
    assert type_of_binary("<", "int", "float") == "bool"
    assert type_of_binary("==", "float", "float") == "bool"


def test_invalid_binary_returns_none():
    assert type_of_binary("+", "int", "bool") is None
    assert type_of_binary("*", "string", "int") is None


def test_unary_plus_minus():
    assert type_of_unary("+", "int") == "int"
    assert type_of_unary("-", "float") == "float"
    assert type_of_unary("-", "string") is None


def test_assignment_rules():
    assert can_assign("int", "int")
    assert can_assign("float", "float")
    assert can_assign("float", "int")  # promoción int → float
    assert not can_assign("int", "float")
