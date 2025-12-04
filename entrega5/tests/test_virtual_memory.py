# entrega5/tests/test_virtual_memory.py

import pytest

from entrega4.virtual_memory import VirtualMemory, ConstantTable


# ------------------ Tests de alloc_var (global/local/param) ------------------ #

def test_alloc_global_int_sequence():
    vm = VirtualMemory()

    a1 = vm.alloc_var("global", "int")
    a2 = vm.alloc_var("global", "int")
    a3 = vm.alloc_var("global", "int")

    # Segmento global/int: 1000–1499
    assert a1 == 1000
    assert a2 == 1001
    assert a3 == 1002


def test_alloc_local_float_sequence():
    vm = VirtualMemory()

    a1 = vm.alloc_var("local", "float")
    a2 = vm.alloc_var("local", "float")

    # Segmento local/float: 3500–3999
    assert a1 == 3500
    assert a2 == 3501


def test_alloc_param_uses_local_segment():
    vm = VirtualMemory()

    # param se debería mapear a segmento "local"
    a1 = vm.alloc_var("param", "int")
    a2 = vm.alloc_var("param", "int")

    # Segmento local/int: 3000–3499
    assert a1 == 3000
    assert a2 == 3001


def test_alloc_var_void_raises():
    vm = VirtualMemory()
    with pytest.raises(ValueError):
        vm.alloc_var("global", "void")


# ------------------ Tests de temporales ------------------ #

def test_alloc_temp_bool_sequence():
    vm = VirtualMemory()

    t1 = vm.alloc_temp("bool")
    t2 = vm.alloc_temp("bool")

    # Segmento temp/bool: 9000–9499
    assert t1 == 9000
    assert t2 == 9001


def test_alloc_temp_void_raises():
    vm = VirtualMemory()
    with pytest.raises(ValueError):
        vm.alloc_temp("void")


# ------------------ Tests de constantes y ConstantTable ------------------ #

def test_alloc_const_int_sequence_direct():
    vm = VirtualMemory()

    c1 = vm.alloc_const("int")
    c2 = vm.alloc_const("int")

    # Segmento const/int: 13000–13499
    assert c1 == 13000
    assert c2 == 13001


def test_constant_table_reuses_address_for_same_value():
    vm = VirtualMemory()
    consts = ConstantTable(vm)

    a1 = consts.get_or_add("int", 42)
    a2 = consts.get_or_add("int", 42)
    a3 = consts.get_or_add("int", 7)

    # Mismo valor, misma dirección
    assert a1 == a2

    # Distintos valores, direcciones diferentes
    assert a3 != a1

    # Además validamos el rango esperado
    assert a1 == 13000
    assert a3 == 13001


def test_constant_table_works_with_multiple_types():
    vm = VirtualMemory()
    consts = ConstantTable(vm)

    i = consts.get_or_add("int", 1)
    f = consts.get_or_add("float", 1.0)
    b = consts.get_or_add("bool", True)
    s = consts.get_or_add("string", "hola")

    # Revisamos que cada uno caiga en el rango correcto
    # int:    13000–13499
    # float:  13500–13999
    # bool:   14000–14499
    # string: 14500–14999
    assert 13000 <= i <= 13499
    assert 13500 <= f <= 13999
    assert 14000 <= b <= 14499
    assert 14500 <= s <= 14999


def test_alloc_const_void_raises():
    vm = VirtualMemory()
    with pytest.raises(ValueError):
        vm.alloc_const("void")


# ------------------ Tests de overflow de segmento ------------------ #

def test_global_int_segment_overflow_raises():
    vm = VirtualMemory()

    # Segmento global/int: 1000–1499 (500 direcciones)
    for _ in range(500):
        vm.alloc_var("global", "int")

    # El siguiente debería tronar
    with pytest.raises(MemoryError):
        vm.alloc_var("global", "int")


def test_temp_float_segment_overflow_raises():
    vm = VirtualMemory()

    # Segmento temp/float: 8500–8999 (500 direcciones)
    for _ in range(500):
        vm.alloc_temp("float")

    with pytest.raises(MemoryError):
        vm.alloc_temp("float")