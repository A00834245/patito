# entrega3/tests/test_quads_basicos.py

from ..codegen_visitor import build_quads_from_source

def test_quads_asignacion_y_print():
    source = """
    program p;
    var a: int;
    var b: int;

    main {
        a = 3 + 4 * 2;
        print(a);
    } end
    """

    func_dir, quads = build_quads_from_source(source)

    # Solo validar que generó cuádruplos
    assert len(quads) > 0

    # Desplegar los cuádruplos en consola (para evidencia)
    print("\n=== Cuádruplos ===")
    for i, q in enumerate(quads):
        print(i, q)
