import re

RE_DECLARACION = re.compile(r'^(ETRR|RLL|CDNN)\s+(.+)$')
RE_ASIGNACION = re.compile(r'^(\*[A-Za-z]+)\s*=\s*(.+)$')
RE_CONDICION = re.compile(r'^(?:while|if)\s*\((.*)\)\s*;?$')
RE_VARIABLE = re.compile(r'\*[A-Za-z]+')
RE_FUNCION = re.compile(
    r'^(ETRR|RLL|CDNN)\s+(\*[A-Za-z]\w*)\s*\(([^)]*)\)\s*(\{)?\s*$'
)
RE_PARAMETRO = re.compile(r'^(ETRR|RLL|CDNN)\s+(\*[A-Za-z]+)$')
RE_LLAMADA_FUNCION = re.compile(
    r'^(\*[A-Za-z]\w*)\s*\(([^)]*)\)\s*$'
)
RE_RETURN = re.compile(r'^return\s+(.+)$')
RE_OPERANDO = re.compile(r'"[^"]*"|\d+\.\d+|\d+|\*[A-Za-z]+')
# El "*" solo es multiplicación si NO va pegado a una letra
# (si lo va, es el prefijo de una variable).
RE_OPERADOR = re.compile(r'[+\-/]|\*(?![A-Za-z])')
RE_CADENA = re.compile(r'"[^"]*"')

PALABRAS_RESERVADAS = ('while', 'if', 'do', 'return')


def quitar_cadenas(texto):
    """Reemplaza cada cadena "..." por "" para que los símbolos que
    contiene (+, -, {, ;, etc.) no se confundan con código real."""
    return RE_CADENA.sub('""', texto)


def dividir_por_comas(texto):
    """Divide por comas ignorando las que estén dentro de una cadena."""
    if texto is None:
        return []
    partes, actual, en_cadena = [], '', False
    for caracter in texto:
        if caracter == '"':
            en_cadena = not en_cadena
        if caracter == ',' and not en_cadena:
            partes.append(actual.strip())
            actual = ''
        else:
            actual += caracter
    partes.append(actual.strip())
    return [p for p in partes if p]
