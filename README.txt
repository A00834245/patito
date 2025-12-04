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

-- Entrega 2 tests
pytest entrega2/tests

-- Entrega 3 tests (con resultados)
pytest -s entrega3/tests

-- Entrega 4 tests (con resultados)
pytest -s entrega4/tests

-- Entrega 5 tests
pytest -s entrega5/tests
