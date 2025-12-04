# tests/conftest.py
# Verifica que un programa Patito mínimo (sin vars ni funcs) se pueda parsear sin errores.

from antlr4 import InputStream, CommonTokenStream
from generated.PatitoLexer import PatitoLexer
from generated.PatitoParser import PatitoParser


def parse_source(source: str):
    """
    Parsea código fuente de Patito y regresa (parser, tree).
    """
    input_stream = InputStream(source)
    lexer = PatitoLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = PatitoParser(tokens)

    # Opcional: quitar listeners por default para que no impriman errores en consola
    parser.removeErrorListeners()

    tree = parser.start()  # usa la regla 'start' de tu gramática
    return parser, tree
