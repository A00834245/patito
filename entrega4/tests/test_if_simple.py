from entrega3.codegen_visitor import build_quads_from_source


def test_if_simple():
    source = """
    program p;
    var x: int;

    main {
        x = 5;
        if (x > 3) {
            print(x);
        };
    } end
    """

    _, quads = build_quads_from_source(source)

    print("\n=== Cuádruplos IF simple ===")
    for i, q in enumerate(quads):
        print(i, q)

    ops = [q[0] for q in quads]

    # Debe haber comparación relacional, un GOTOF y un PRINT
    assert ">" in ops
    assert "GOTOF" in ops
    assert ("PRINT" in ops) or ("PRINT_CFG" in ops)

    # No debe haber GOTO extra (porque no hay else)
    assert "GOTO" not in ops
