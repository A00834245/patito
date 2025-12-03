# tests/test_syntax_errors.py
# Confirma que el parser detecta correctamente programas con errores de sintaxis.

from .conftest import parse_source


def test_error_falta_punto_y_coma_en_program():
    code = """
    program foo
    main {
    }
    end
    """
    parser, _ = parse_source(code)
    assert parser.getNumberOfSyntaxErrors() > 0


def test_error_falta_end():
    code = """
    program foo;
    main {
        print("hola");
    }
    """
    parser, _ = parse_source(code)
    assert parser.getNumberOfSyntaxErrors() > 0
