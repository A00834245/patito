# tests/test_vars_print.py
# Comprueba que la gramática acepte declaraciones de variables, asignaciones y print con expresiones y strings.

from .conftest import parse_source


def test_program_con_vars_assign_y_print():
    code = """
    program ejemplo;
    var x: int;
    var y: float;

    main {
        x = 3;
        y = x + 1.5;
        print(x, y, "hola");
    }
    end
    """
    parser, _ = parse_source(code)
    assert parser.getNumberOfSyntaxErrors() == 0
