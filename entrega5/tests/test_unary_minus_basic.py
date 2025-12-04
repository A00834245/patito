from entrega3.codegen_visitor import translate
from entrega5.vm import VirtualMachine


def test_unary_minus_basic():
    # x = -3 + 10;
    source = """
    program p;
    var x: int;
    main {
      x = -3 + 10;
      print(x);
    } end
    """
    func_dir, quads = translate(source)
    # translate cuelga func_dir.constants como mapa addr -> valor
    consts = func_dir.constants
    vm = VirtualMachine(quads, constants=consts)

    # La salida esperada es 7
    vm.run()
