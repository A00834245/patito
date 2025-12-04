import pytest
from antlr4 import InputStream, CommonTokenStream

from entrega1.generated.PatitoLexer import PatitoLexer
from entrega1.generated.PatitoParser import PatitoParser

from entrega2.semantic_visitor import SemanticVisitor
from entrega2.symbols import DuplicateSymbolError


def build_dir(source: str):
    """
    Parsea código Patito y devuelve el FunctionDirectory generado por SemanticVisitor.
    """
    input_stream = InputStream(source)
    lexer = PatitoLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = PatitoParser(tokens)
    tree = parser.start()

    visitor = SemanticVisitor()
    return visitor.visit(tree)


def test_globals_and_function():
    source = """
    program p;
    var x, y: int;
    var z: float;

    void foo(a: int, b: float) {
        var c: int;
        { }
    };

    main { }
    end
    """

    fd = build_dir(source)

    # Globales
    assert fd.resolve_var("x", None).type == "int"
    assert fd.resolve_var("y", None).type == "int"
    assert fd.resolve_var("z", None).type == "float"

    # Función foo
    foo = fd.get_function("foo")
    assert foo.return_type == "void"
    assert [p.name for p in foo.params] == ["a", "b"]
    assert [p.type for p in foo.params] == ["int", "float"]

    # Locales de foo
    c = fd.resolve_var("c", "foo")
    assert c.kind == "local"
    assert c.type == "int"


def test_duplicate_global():
    source = """
    program p;
    var x: int;
    var x: float;

    main { }
    end
    """

    with pytest.raises(DuplicateSymbolError):
        build_dir(source)


def test_duplicate_local():
    source = """
    program p;

    void foo(a: int) {
        var x, x: int;
        { }
    };

    main { }
    end
    """

    with pytest.raises(DuplicateSymbolError):
        build_dir(source)


def test_duplicate_param():
    source = """
    program p;

    void foo(a: int, a: float) {
        { }
    };

    main { }
    end
    """

    with pytest.raises(DuplicateSymbolError):
        build_dir(source)
