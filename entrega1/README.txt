READ ME ENTREGA 1

--- Virtual Enviroment python
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt

--- Generate ANTLR files
java -jar antlr4.jar -Dlanguage=Python3 -visitor -no-listener -o generated Patito.g4

--- Correr tests desde
cd entrega1
pytest


--- Generated files
PatitoLexer.py
* Es el scanner (analizar lexico)
* Recibe texto y lo covierte en tokens
* EJEMPLO: x -> ID

PatitoParser.py
* Es el parser (analizados sintactico)
* Toma los tokens que producio el PatitoLexer
* Valida que cumplan la gramatica
* Construye un arbol sintactico