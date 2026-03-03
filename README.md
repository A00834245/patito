# Patito — Compilador de Lenguaje Patito

Patito es un compilador/intérprete completo para un lenguaje de programación educativo llamado **Patito**, desarrollado de manera incremental en cinco entregas. El proyecto abarca todas las etapas clásicas de la construcción de un compilador: análisis léxico-sintáctico, análisis semántico, generación de código intermedio, administración de memoria virtual y ejecución en una máquina virtual.

---

## Tabla de Contenidos

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Requisitos](#requisitos)
3. [Instalación y Configuración](#instalación-y-configuración)
4. [Estructura del Proyecto](#estructura-del-proyecto)
5. [Arquitectura](#arquitectura)
6. [Patrones de Diseño](#patrones-de-diseño)
7. [Dependencias entre Módulos](#dependencias-entre-módulos)
8. [Dependencias Externas](#dependencias-externas)
9. [El Lenguaje Patito](#el-lenguaje-patito)
10. [Ejecución de Pruebas](#ejecución-de-pruebas)

---

## Descripción del Proyecto

El compilador de Patito transforma código fuente escrito en el lenguaje Patito en una secuencia de **cuádruplos** (representación intermedia) que luego son ejecutados por una **Máquina Virtual** propia. El lenguaje soporta:

- Declaración de variables de tipo `int` y `float`.
- Definición de funciones con parámetros y valor de retorno (`int`, `float` o `void`).
- Estructuras de control: `if / else` y `while`.
- Expresiones aritméticas (`+`, `-`, `*`, `/`) y relacionales (`<`, `>`, `<=`, `>=`, `==`, `!=`).
- Instrucción `print` para salida de texto y valores.
- Llamadas a funciones anidadas.

---

## Requisitos

- Python 3.10 o superior
- Java (para regenerar los archivos del parser ANTLR4, opcional)

---

## Instalación y Configuración

```bash
# 1. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\Activate      # Windows
source .venv/bin/activate   # Linux / macOS

# 2. Instalar dependencias de Python
pip install -r requirements.txt

# 3. (Opcional) Regenerar archivos del parser ANTLR4
cd entrega1
java -jar antlr4.jar -Dlanguage=Python3 -visitor -no-listener -o generated Patito.g4
```

> Los archivos generados por ANTLR4 ya se encuentran en `entrega1/generated/` y no es necesario regenerarlos a menos que se modifique la gramática.

---

## Estructura del Proyecto

```
patito/
├── README.md
├── requirements.txt
├── __init__.py
│
├── entrega1/                        # Etapa 1 — Análisis léxico y sintáctico
│   ├── Patito.g4                    # Gramática ANTLR4 del lenguaje Patito
│   ├── antlr4.jar                   # Herramienta ANTLR4
│   ├── generated/                   # Archivos generados por ANTLR4
│   │   ├── PatitoLexer.py
│   │   ├── PatitoParser.py
│   │   └── PatitoVisitor.py
│   └── tests/
│
├── entrega2/                        # Etapa 2 — Análisis semántico
│   ├── semantic_cube.py             # Cubo semántico (compatibilidad de tipos)
│   ├── semantic_visitor.py          # Visitor del AST con validaciones semánticas
│   ├── symbols.py                   # Tablas de símbolos (variables y funciones)
│   └── tests/
│
├── entrega3/                        # Etapa 3 — Generación de código intermedio
│   ├── codegen_visitor.py           # Visitor que emite cuádruplos
│   └── tests/
│
├── entrega4/                        # Etapa 4 — Memoria virtual
│   ├── virtual_memory.py            # Gestor de espacio de direcciones virtuales
│   └── tests/
│
└── entrega5/                        # Etapa 5 — Máquina virtual
    ├── vm.py                        # Motor de ejecución de cuádruplos
    └── tests/
```

---

## Arquitectura

El compilador sigue un **pipeline lineal por etapas**. Cada etapa consume la salida de la anterior:

```
Código fuente (.patito)
        │
        ▼
┌─────────────────────┐
│  Entrega 1          │  ANTLR4 Lexer + Parser
│  Análisis L/S       │  → Árbol de parseo (Parse Tree)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Entrega 2          │  SemanticVisitor (Visitor Pattern)
│  Análisis Semántico │  → Directorio de funciones + Tablas de símbolos
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Entrega 3          │  CodeGenVisitor (extiende SemanticVisitor)
│  Generación de IR   │  → Lista de cuádruplos (Quad[])
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Entrega 4          │  VirtualMemory + ConstantTable
│  Memoria Virtual    │  → Asignación de direcciones virtuales
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Entrega 5          │  VirtualMachine
│  Ejecución          │  → Salida del programa
└─────────────────────┘
```

### Flujo de ejecución detallado

1. **`PatitoLexer`** tokeniza el código fuente.
2. **`PatitoParser`** construye el árbol de parseo.
3. **`CodeGenVisitor`** recorre el árbol con el patrón Visitor:
   - Hereda de `SemanticVisitor` para reutilizar la validación de tipos.
   - Usa `VirtualMemory` para asignar direcciones a variables, temporales y constantes.
   - Genera una lista de `Quad` (cuádruplos).
4. **`VirtualMachine`** recibe los cuádruplos y la tabla de constantes y los ejecuta instrucción por instrucción.

---

## Patrones de Diseño

### 1. Visitor (Visitante)
**Archivos:** `entrega2/semantic_visitor.py`, `entrega3/codegen_visitor.py`

El recorrido del árbol de parseo se delega completamente al patrón Visitor proporcionado por ANTLR4. `SemanticVisitor` implementa `PatitoVisitor` y define un método `visit*` por cada regla gramatical. `CodeGenVisitor` extiende `SemanticVisitor`, lo que permite **herencia de comportamiento semántico** y adición de lógica de generación de código sin modificar la clase base.

```
PatitoVisitor  (ANTLR4 — interfaz generada)
     │
     └── SemanticVisitor   (validaciones semánticas + tablas de símbolos)
              │
              └── CodeGenVisitor  (generación de cuádruplos)
```

### 2. Tabla de Símbolos (Symbol Table)
**Archivos:** `entrega2/symbols.py`

Gestiona el ámbito léxico del programa con una jerarquía de clases:

- **`VarTable`**: diccionario de `VarInfo` para un único scope.
- **`FunctionInfo`**: agrupa parámetros, variables locales y metadatos de una función.
- **`FunctionDirectory`**: punto de acceso central que mantiene la tabla global de variables y el diccionario de funciones. Implementa resolución de nombre en dos pasos (local → global).

### 3. Cubo Semántico (Semantic Cube)
**Archivo:** `entrega2/semantic_cube.py`

Encapsula las reglas de compatibilidad de tipos en un diccionario de diccionarios (`SEM_CUBE`). Dado un operador y los tipos de los operandos, devuelve el tipo resultante o `None` si la operación es inválida. Esto separa la lógica de tipos del visitor, haciendo que ambos sean intercambiables de forma independiente.

### 4. Traducción Dirigida por Sintaxis (Syntax-Directed Translation)
**Archivo:** `entrega3/codegen_visitor.py`

La generación de cuádruplos está integrada directamente en el recorrido del árbol. Cuatro pilas coordinan la traducción:

| Pila | Contenido |
|------|-----------|
| `PilaO` | Operandos (direcciones virtuales) |
| `PTypes` | Tipos de los operandos |
| `POper` | Operadores pendientes de evaluar |
| `PSaltos` | Índices de cuádruplos de salto (`GOTOF` / `GOTO`) |

Las pilas se llenan y vacían al visitar cada sub-expresión, produciendo los cuádruplos en el orden correcto.

### 5. Espacio de Direcciones Virtuales (Virtual Memory Segmentation)
**Archivo:** `entrega4/virtual_memory.py`

La memoria se divide en segmentos por **scope** y **tipo**, cada uno con un rango de direcciones fijo:

| Segmento | Tipo | Rango |
|----------|------|-------|
| Global   | int / float / bool / string | 1000 – 2999 |
| Local    | int / float / bool / string | 3000 – 4999 |
| Temporal | int / float / bool / string | 8000 – 9999 |
| Constante| int / float / bool / string | 13000 – 14999 |

`MemorySegment` asigna la siguiente dirección libre y detecta desbordamiento. `ConstantTable` implementa el patrón **Flyweight**: reutiliza la misma dirección para constantes con igual valor y tipo.

### 6. Máquina de Pila con Registros de Activación (Stack-based VM)
**Archivo:** `entrega5/vm.py`

`VirtualMachine` ejecuta los cuádruplos en un ciclo principal (`while ip < len(quads)`). Las llamadas a funciones se gestionan con:

- **`ActivationRecord`**: contiene la memoria local, la memoria temporal y la dirección de retorno de cada invocación.
- **`call_stack`**: pila de `ActivationRecord` activos (soporte para llamadas anidadas).
- **`_pending_frame`**: frame en construcción durante `ERA` / `PARAM` antes del `GOSUB`.

---

## Dependencias entre Módulos

```
entrega5/vm.py
    └── importa: entrega3/codegen_visitor.py  (tipo Quad)

entrega3/codegen_visitor.py
    ├── extiende: entrega2/semantic_visitor.py
    ├── importa:  entrega4/virtual_memory.py   (ConstantTable)
    ├── importa:  entrega2/semantic_cube.py    (type_of_binary, type_of_unary, can_assign)
    └── importa:  entrega2/symbols.py          (TypeMismatchError)

entrega2/semantic_visitor.py
    ├── importa: entrega1/generated/PatitoParser   (nodos del árbol)
    ├── importa: entrega1/generated/PatitoVisitor  (interfaz Visitor)
    ├── importa: entrega2/symbols.py               (FunctionDirectory)
    ├── importa: entrega2/semantic_cube.py         (TypeName)
    └── importa: entrega4/virtual_memory.py        (VirtualMemory)

entrega2/symbols.py
    └── importa: entrega2/semantic_cube.py  (TypeName)

entrega4/virtual_memory.py
    └── (sin dependencias internas del proyecto)

entrega1/generated/
    └── (generado por ANTLR4 — sin dependencias internas)
```

**Diagrama de dependencias simplificado:**

```
entrega1 (ANTLR generated)
    ▲
entrega2/symbols  ◄──  entrega2/semantic_cube
    ▲
entrega2/semantic_visitor  ◄──  entrega4/virtual_memory
    ▲
entrega3/codegen_visitor  ◄──  entrega4/virtual_memory
    ▲
entrega5/vm
```

---

## Dependencias Externas

| Paquete | Versión | Uso |
|---------|---------|-----|
| `antlr4-python3-runtime` | >=4.13 | Runtime de ANTLR4 para el lexer/parser |
| `pytest` | >=7.0 | Framework de pruebas |

Instalar con:

```bash
pip install -r requirements.txt
```

---

## El Lenguaje Patito

### Tipos de datos

| Tipo | Descripción |
|------|-------------|
| `int` | Número entero |
| `float` | Número de punto flotante |
| `void` | Sin valor de retorno (solo para funciones) |

### Ejemplo de programa

```patito
program miPrograma;

var x, y : int;
var resultado : float;

float suma(a : int, b : int) {
    var local : float;
    local = a + b;
    return local;
};

main {
    x = 3;
    y = 4;
    resultado = suma(x, y);
    print(resultado);

    if (resultado > 5.0) {
        print("Mayor que 5");
    } else {
        print("Menor o igual a 5");
    };

    while (x < 10) do {
        x = x + 1;
        print(x);
    };
}
end
```

### Operadores soportados

| Categoría | Operadores |
|-----------|-----------|
| Aritméticos | `+`, `-`, `*`, `/` |
| Relacionales | `<`, `>`, `<=`, `>=`, `==`, `!=` |
| Asignación | `=` |

---

## Ejecución de Pruebas

```bash
# Pruebas de análisis léxico/sintáctico (Entrega 1)
cd entrega1
pytest

# Pruebas de análisis semántico (Entrega 2)
pytest entrega2/tests

# Pruebas de generación de cuádruplos — con salida (Entrega 3)
pytest -s entrega3/tests

# Pruebas de control de flujo — con salida (Entrega 4)
pytest -s entrega4/tests

# Pruebas de ejecución completa — con salida (Entrega 5)
pytest -s entrega5/tests
```
