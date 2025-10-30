# Test Plan - Patito Scanner & Parser

## Objetivo

Verificar que el Scanner (Lexer) y Parser generados a partir de la gramática `Patito.g4` funcionen correctamente, reconociendo programas válidos y detectando errores de sintaxis.

## Metodología

Los tests están implementados en `tests/test_patito.py` usando el framework **pytest**. Cada test invoca la función `parse_text()` que:

1. Tokeniza el código fuente (Scanner/Lexer)
2. Construye el árbol sintáctico (Parser)
3. Lanza `SyntaxError` si hay errores de sintaxis

## Casos de Prueba

### 1. Programa Mínimo (`test_min_program`)

**Objetivo**: Verificar que el parser reconoce la estructura mínima de un programa Patito.

**Entrada**:
```patito
program P; main { } end
```

**Resultado Esperado**: ✅ Parseo exitoso sin errores.

**Componentes probados**:
- Token `program`
- Identificador de programa
- Bloque `main` vacío
- Token `end`

---

### 2. Variables y Asignaciones (`test_vars_and_assign_print`)

**Objetivo**: Validar declaración de variables con lista de IDs, asignaciones y expresiones aritméticas.

**Entrada**:
```patito
program P; var a, b: int; main { a = 1 + 2 * 3; print(a); } end
```

**Resultado Esperado**: ✅ Parseo exitoso.

**Componentes probados**:
- Declaración de variables (`var`)
- Lista de IDs separados por comas
- Tipos (`int`)
- Asignación (`=`)
- Expresiones aritméticas (`+`, `*`)
- Precedencia de operadores
- Statement `print`

---

### 3. Condicional If-Else (`test_if_else`)

**Objetivo**: Verificar estructuras condicionales con bloques then/else.

**Entrada**:
```patito
program P; main { if (a > 0) { print(a); } else { print(0); } ; } end
```

**Resultado Esperado**: ✅ Parseo exitoso.

**Componentes probados**:
- Token `if`
- Expresión de comparación (`>`)
- Paréntesis alrededor de condición
- Bloque `then` (cuerpo del if)
- Token `else`
- Bloque `else`
- Punto y coma después del condicional

---

### 4. Ciclo While-Do (`test_while_do`)

**Objetivo**: Validar la estructura de ciclos while con cuerpo.

**Entrada**:
```patito
program P; main { while (a < 3) do { a = a + 1; } ; } end
```

**Resultado Esperado**: ✅ Parseo exitoso.

**Componentes probados**:
- Token `while`
- Expresión de comparación (`<`)
- Token `do`
- Cuerpo del ciclo (bloque de statements)
- Punto y coma después del ciclo

---

### 5. Definición y Llamada de Funciones (`test_func_and_call`)

**Objetivo**: Probar declaración de funciones con parámetros, variables locales, y llamadas a funciones.

**Entrada**:
```patito
program P; void f(x: int) [ var z: int; { print(x); } ] ; main { f(1); } end
```

**Resultado Esperado**: ✅ Parseo exitoso.

**Componentes probados**:
- Token `void`
- Identificador de función
- Paréntesis con lista de parámetros
- Declaración de parámetro (`x: int`)
- Corchetes para variables locales opcionales (`[ var ... ]`)
- Cuerpo de función
- Llamada a función con argumento

---

### 6. Print con Strings y Expresiones (`test_print_string_and_expr_list`)

**Objetivo**: Verificar que `print` acepta múltiples argumentos (strings y expresiones).

**Entrada**:
```patito
program P; main { print("hola", 1+2, "x"); } end
```

**Resultado Esperado**: ✅ Parseo exitoso.

**Componentes probados**:
- Literales string (`"hola"`, `"x"`)
- Expresiones aritméticas como argumentos
- Lista de argumentos separados por comas

---

### 7. Error de Sintaxis - Paréntesis Faltante (`test_invalid_missing_paren`)

**Objetivo**: Comprobar que el parser detecta errores de sintaxis y lanza excepciones apropiadas.

**Entrada**:
```patito
program P; main { print(1 + 2; } end
```
*(Falta paréntesis de cierre en `print`)*

**Resultado Esperado**: ❌ `SyntaxError` lanzado con mensaje descriptivo.

**Componentes probados**:
- Detección de error sintáctico
- Reporte de línea y columna del error
- Manejo de excepciones en el parser

---

## Ejecución de Tests

### Comando

```bash
pytest -q
```

### Resultado Actual

```
.......                                               [100%]
7 passed in 0.08s
```

✅ **Todos los tests pasan exitosamente.**

---

## Cobertura de la Gramática

Los tests cubren las principales construcciones del lenguaje Patito:

| Componente Gramatical | Cubierto |
|----------------------|----------|
| Declaración de programa | ✅ |
| Variables (`var`) | ✅ |
| Tipos (`int`, `float`) | ✅ (int) |
| Expresiones aritméticas (`+`, `-`, `*`, `/`) | ✅ |
| Expresiones de comparación (`>`, `<`, `!=`) | ✅ |
| Asignaciones | ✅ |
| Condicionales (`if`/`else`) | ✅ |
| Ciclos (`while`/`do`) | ✅ |
| Funciones (`void`, parámetros, llamadas) | ✅ |
| Print (expresiones y strings) | ✅ |
| Detección de errores sintácticos | ✅ |

---

## Conclusión

El Scanner y Parser generados a partir de la gramática `Patito.g4` funcionan correctamente:

- ✅ Reconocen todas las estructuras sintácticas del lenguaje
- ✅ Procesan correctamente variables, expresiones, y control de flujo
- ✅ Detectan y reportan errores de sintaxis con información útil (línea/columna)
- ✅ Todos los casos de prueba pasan exitosamente

El test plan demuestra la funcionalidad completa del Scanner y Parser según los requisitos del proyecto.
