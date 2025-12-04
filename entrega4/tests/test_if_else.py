from entrega3.codegen_visitor import build_quads_from_source


def test_if_else():
    source = """
    program p;
    var x: int;

    main {
        x = 2;
        if (x > 3) {
            print(1);
        }
        else {
            print(0);
        };
    } end
    """

    _, quads = build_quads_from_source(source)

    print("\n=== Cuádruplos IF-ELSE ===")
    for i, q in enumerate(quads):
        print(i, q)

    ops = [q[0] for q in quads]

    # Debe haber comparación, GOTOF, GOTO y dos PRINTs
    assert ">" in ops
    assert "GOTOF" in ops
    assert "GOTO" in ops
    assert ops.count("PRINT") >= 2

    # Checar que el GOTOF salte al inicio del else
    gotof_index = ops.index("GOTOF")
    _, _, _, false_target = quads[gotof_index]

    # El cuádruplo en false_target debe ser el PRINT del else
    assert 0 <= false_target < len(quads)
    assert quads[false_target][0] == "PRINT"
