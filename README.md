# 🧠 Compilador - Analizador Semántico

Compilador con interfaz gráfica para un lenguaje imperativo tipado. Incluye **análisis semántico** con detección de errores de tipos, **generación de código intermedio** en forma de triplos y **exportación de resultados** a Excel.

---

## 📋 Descripción

Este proyecto implementa la fase de **análisis semántico** de un compilador para un lenguaje imperativo con tipado estático estricto (sin conversión automática de tipos) y la posterior **generación de triplos** (código intermedio de tres direcciones).

La aplicación permite:

- ✍️ Escribir código fuente en un editor con números de línea.
- 🔍 Validar tipos, declaraciones y operaciones de forma semántica.
- 📊 Visualizar la **tabla de símbolos** con el tipo de cada lexema.
- ⚠️ Consultar la **tabla de errores** con token, lexema, línea y descripción.
- 🧩 Generar los **triplos** correspondientes al programa analizado.
- 📥 Exportar los triplos a un archivo **Excel** (`.xlsx`).

---

## 🧠 Tipos de dato del lenguaje

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| `ETRR` | Entero      | `42`    |
| `RLL`  | Real        | `3.14`  |
| `CDNN` | Cadena      | `"hola"`|

Los **identificadores** se escriben con el prefijo `*` (ej. `*x`, `*contador`, `*resulT`).

> ⚠️ **No existe conversión automática de tipos**: para asignar, comparar o combinar valores, ambos deben ser del mismo tipo (salvo la división, que permite mezclar `ETRR` y `RLL`).

---

## 🧩 Sintaxis del lenguaje

### Declaración de variables
```
ETRR *x;
RLL  *pi;
CDNN *nombre;
```

### Asignación
```
*x = 10;
*pi = 3.14;
*nombre = "Ana";
```

### Expresiones aritméticas
```
*x = 5 + 3 * 2;
*pi = 4.0 / 2.0;
```

### Condicionales
```
if (*x == 0) {
    *y = 1;
}
```

### Ciclos
```
while (*i < 10) {
    *i = *i + 1;
}

do {
    *i = *i - 1;
} while (*i > 0);
```

### Funciones
```
ETRR *suma(ETRR *a, ETRR *b) {
    *resulT = *a + *b;
    return *resulT;
}

*x = suma(2, 3);
```

### Return
```
return *variable;
return 5 + 3;
```

---

## 🧮 Reglas semánticas principales

### Operaciones binarias

| Operador | `ETRR` / `RLL` | `CDNN` |
|----------|----------------|--------|
| `+` `-`  | ✅ Requiere mismo tipo | ✅ Válido |
| `*`      | ✅ Requiere mismo tipo | ❌ Nunca válido |
| `/`      | ✅ Mezcla `ETRR`/`RLL` → `RLL`; `ETRR/ETRR` ❌ inválido | ❌ Nunca válido |

### División
- `ETRR / ETRR` → **inválida** (división entera no permitida).
- `RLL / RLL`   → `RLL`.
- `ETRR / RLL`  → `RLL`.
- `RLL / ETRR`  → `RLL`.
- `CDNN / CDNN` → **inválida**.

### Otras reglas
- Asignación: el tipo del destino debe coincidir con el tipo de la expresión.
- `return`: el tipo devuelto debe coincidir con el tipo de retorno de la función.
- Variables: no se puede usar una variable sin declararla (error `Variable indefinida`).
- Funciones: no se pueden duplicar nombres de función ni de variables en el mismo ámbito.
- Funciones: deben declararse antes de usarse y deben empezar con `{`.

---

## ⚠️ Tipos de errores reportados

Los errores se muestran con el formato `*erroR<n>`:

| Token        | Descripción                                       |
|--------------|---------------------------------------------------|
| `*erroR1`    | Variable indefinida                               |
| `*erroR2`    | Variable duplicada                                |
| `*erroR3`    | Función duplicada                                 |
| `*erroR4`    | Función no declarada                              |
| `*erroR5`    | Función no iniciada (falta `{`)                   |
| `*erroR6`    | Return fuera de función                           |
| `*erroR7`    | Incompatibilidad de tipos                         |
| `*erroR8`    | …

---

## 🗂️ Estructura del proyecto

```
├── main.py              # Punto de entrada + callbacks GUI
├── interfaz.py          # Interfaz gráfica (Tkinter)
├── semantic.py          # Analizador semántico principal
├── expresiones.py       # Validador de tipos de expresiones
├── tipos.py             # Definición de tipos y reglas de operación
├── reglas.py            # Expresiones regulares y utilidades
├── errores.py           # Gestor de errores semánticos
├── Triplos.py           # Generador de código intermedio (triplos)
├── exportador.py        # Exportación a Excel (openpyxl)
└── prueba_triplos.py    # Script de prueba del generador de triplos
```

---

## 🚀 Instalación y ejecución

### Requisitos
- Python **3.9+**
- `openpyxl` (para exportación a Excel)
- `tkinter` (viene incluido con Python en la mayoría de sistemas)

### Instalar dependencias
```bash
pip install openpyxl
```

### Ejecutar la aplicación
```bash
python main.py
```

### Ejecutar prueba de triplos
```bash
python prueba_triplos.py
```

---

## 🖥️ Uso de la interfaz

1. **Escribir código** en el editor del panel izquierdo.
2. Presionar **▶ Analizar** para ejecutar el análisis semántico.
3. Revisar los resultados en las pestañas:
   - **Tabla de Símbolos**: lexema y tipo.
   - **Tabla de Errores**: token, lexema, línea y descripción.
4. Presionar **Generar triplos** para obtener el código intermedio; se exportará a `resultados/triplos.xlsx`.
5. Usar **🧹 Limpiar** para borrar todo o **📋 Copiar código** para copiar al portapapeles.

---

## 🧾 Generación de triplos

Los triplos se generan en el formato:

| Número | Dato objeto | Dato fuente | Operador |
|--------|-------------|-------------|----------|
| 1      | `T1`        | `5`         | `=`      |
| 2      | `T2`        | `3`         | `=`      |
| 3      | `T1`        | `T2`        | `*`      |
| 4      | `*x`        | `T1`        | `=`      |

### Características del generador

- Manejo de **temporales** (`T1`, `T2`, …).
- Respeto de **precedencia de operadores**.
- Soporte para **funciones** (parámetros, retorno con `*resulT`, `JMP` de llamada y retorno).
- Soporte para **do-while** y bloques `{ }`.
- Soporte para **expresiones relacionales** (`==`, `!=`, `<`, `>`, `<=`, `>=`).
- Operadores lógicos `&&` y `||` con cortocircuito.

> ⚠️ Cada función admite **una sola llamada** en el esquema actual de `JMP` de retorno.

---

## 🧪 Ejemplo completo

```c
ETRR *suma(ETRR *a, ETRR *b)
{
    *resulT = *a + *b;
    return *resulT;
}

ETRR *x;
ETRR *y;
*x = 2;
*y = 3;
ETRR *r;
*r = suma(*x, *y);
```

Al analizar:
- Tabla de símbolos incluirá: `*suma`, `*a`, `*b`, `*resulT`, `*x`, `*y`, `*r`, literales `2` y `3`, operadores `+`, `=`, etc.
- Sin errores, la interfaz mostrará `✔ Análisis completado — N variable(s), 0 errores.`
- Al generar triplos, se obtendrá una secuencia de operaciones con temporales y saltos.

---

## 🏗️ Arquitectura

### Flujo de ejecución

```
Editor (GUI) 
   │
   ▼
main.ejecutar_analisis(codigo)
   │
   ▼
semantic.analizar(codigo)
   ├── Reglas léxicas (reglas.py)
   ├── Análisis de expresiones (expresiones.py)
   ├── Reglas de tipo (tipos.py)
   └── Gestión de errores (errores.py)
   │
   ▼
interfaz.mostrar_resultados(tabla, errores)
```

### Componentes principales

| Módulo | Responsabilidad |
|--------|-----------------|
| `main.py` | Orquesta la ejecución y conecta la GUI con el compilador. |
| `interfaz.py` | Interfaz gráfica Tkinter (editor, tablas, botones). |
| `semantic.py` | Analizador semántico: declaraciones, funciones, retornos, etc. |
| `expresiones.py` | Valida tipos en expresiones aritméticas de izquierda a derecha. |
| `tipos.py` | Tipos del lenguaje y reglas de operación. |
| `reglas.py` | Expresiones regulares y utilidades de parsing. |
| `errores.py` | Gestor de errores (`*erroR<n>`). |
| `Triplos.py` | Generador de código intermedio de tres direcciones. |
| `exportador.py` | Exportación de tablas a Excel (`openpyxl`). |

---

## 📌 Notas y limitaciones

- La interfaz **no realiza el análisis**; solo delega a `main.py`.
- La tabla de símbolos conserva el orden de aparición y **no sobrescribe** un tipo ya asignado con `None`.
- Los operadores, literales y símbolos estructurales (`;`, `{`, `}`, `(`, `)`) también se registran en la tabla de símbolos.
- Al encontrar una **variable indefinida**, se reporta el error y se detiene el análisis de esa expresión (no puede inferirse su tipo).
- El generador de triplos es independiente del analizador semántico: si el código tiene errores semánticos, los triplos pueden generarse igualmente, pero conviene corregir primero.

---

## 👨‍💻 Autor

Proyecto académico de **Compiladores / Lenguajes Formales** — implementación de análisis semántico y generación de código intermedio.
