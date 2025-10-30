# Patito

Minimal ANTLR4-based parser + AST visitor and CLI for the Patito language.

## Prerequisites

- Python 3.10+
- Java 11+ (required only for generating parser from grammar)

## Setup

### 1. Create virtual environment and install Python dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

### 2. Generate ANTLR parser files from grammar:

After installing Java 11+, restart your terminal/PowerShell, then run:

```powershell
java -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor -o src/patito src/patito/Patito.g4
```

**If `java` command not found**, use the full path:

```powershell
& "C:\Program Files\Java\jdk-<version>\bin\java.exe" -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor -o src/patito src/patito/Patito.g4
```

This generates: `PatitoLexer.py`, `PatitoParser.py`, `PatitoVisitor.py`, `PatitoListener.py` in `src/patito/`.

**Note**: You only need to run this once (or when you modify `Patito.g4`).

## Run tests

From the repository root:

```
pytest -q
```

## CLI usage

Parse a file and print the tuple-based AST:

```
python -m patito.patito_cli path/to/program.pat
```

Or pipe from stdin:

```
type path\to\program.pat | python -m patito.patito_cli
```
