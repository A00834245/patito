from entrega3.codegen_visitor import build_quads_from_source


def test_while_simple():
    source = """
    program p;
    var x: int;

    main {
        x = 0;
        while (x < 3) do {
            print(x);
            x = x + 1;
        };
    } end
    """

    _, quads = build_quads_from_source(source)

    print("\n=== Cuádruplos WHILE simple ===")
    for i, q in enumerate(quads):
        print(i, q)

    ops = [q[0] for q in quads]

    # Debe haber comparación, un GOTOF y un GOTO (para regresar al inicio)
    assert "<" in ops
    assert "GOTOF" in ops
    assert "GOTO" in ops

    # Checar que el GOTO regrese hacia arriba (a la parte de la condición)
    goto_index = ops.index("GOTO")
    _, _, _, target = quads[goto_index]
    assert isinstance(target, int)
    assert target < goto_index
