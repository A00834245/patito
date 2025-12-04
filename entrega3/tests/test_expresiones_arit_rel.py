from entrega3.codegen_visitor import build_quads_from_source

def test_expresiones_arit_rel():
    source = """
    program p;
    var x: int;

    main {
        x = (3 + 5) * 2;
        print(x > 10);
    } end
    """

    _, quads = build_quads_from_source(source)

    print("\n=== Cuádruplos expresiones arit+rel ===")
    for i, q in enumerate(quads):
        print(i, q)

    # Asegurarnos de que sí se generó al menos un cuádruplo relacional
    ops = [q[0] for q in quads]
    assert ">" in ops
