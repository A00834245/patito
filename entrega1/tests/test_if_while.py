# tests/test_if_while.py
# Prueba que estructuras de control (if/else y while do) se parseen correctamente.

from .conftest import parse_source


def test_program_con_if_else_y_while():
    code = """
    program conds;
    var x: int;

    main {
        x = 0;

        if (x < 10) {
            x = x + 1;
        } else {
            x = 100;
        };

        while (x < 5) do {
            x = x + 1;
        };
    }
    end
    """
    parser, _ = parse_source(code)
    assert parser.getNumberOfSyntaxErrors() == 0
