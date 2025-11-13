# Patito

Minimal ANTLR4-based parser plus a syntax-directed translator and CLI for the Patito language.

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
java -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor -o src/patito/generated grammar/Patito.g4
```

**If `java` command not found**, use the full path:

```powershell
& "C:\Program Files\Java\jdk-<version>\bin\java.exe" -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor -o src/patito/generated grammar/Patito.g4
```

This generates: `PatitoLexer.py`, `PatitoParser.py`, `PatitoVisitor.py`, `PatitoListener.py` in `src/patito/generated/`.

**Note**: You only need to run this once (or when you modify `grammar/Patito.g4`).

## Run tests

From the repository root:

```
pytest -q
```

## CLI usage

Default: parse and print IR (quadruples), one per line:

```
python -m patito.patito_cli path/to/program.pat
```

Execute program instead (interpret the IR) and print outputs:

```
python -m patito.patito_cli --run path/to/program.pat
```

Pipe from stdin:

```
type path\to\program.pat | python -m patito.patito_cli --run
```
