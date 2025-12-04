from entrega3.codegen_visitor import translate
from entrega5.vm import VirtualMachine


def test_function_return_execution():
    source = """
    program p;
    var x: int;
    int f(a: int) {
      {
        return a * 2;
      }
    };
    main {
      x = f(5);
      print(x);
    } end
    """
    func_dir, quads = translate(source)
    consts = func_dir.constants
    vm = VirtualMachine(quads, constants=consts)
    vm.run()  # salida: 10
