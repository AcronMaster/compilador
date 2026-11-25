import re

TIPOS = ("ETRR", "RLL", "CDNN")


def tipo_literal(token):
    token = token.strip()
    if token.startswith('"') and token.endswith('"'):
        return "CDNN"
    if re.fullmatch(r'\d+\.\d+', token):
        return "RLL"
    if re.fullmatch(r'\d+', token):
        return "ETRR"
    return None


def compatible(tipo_destino, tipo_origen):
    """No existe conversión automática: los tipos deben ser iguales."""
    return tipo_destino == tipo_origen


def tipo_division(tipo_izq, tipo_der):
    """Tipo resultante de / o None si es inválida.

    ETRR / ETRR -> inválida (división de enteros)
    RLL  / RLL  -> RLL
    ETRR / RLL  -> RLL   (se promueve a real)
    RLL  / ETRR -> RLL   (se promueve a real)
    CDNN / cualquiera -> inválida
    """
    if tipo_izq == "ETRR" and tipo_der == "ETRR":
        return None
    if tipo_izq in ("ETRR", "RLL") and tipo_der in ("ETRR", "RLL"):
        return "RLL"
    return None


def operacion_valida(operador, tipo_izq, tipo_der):
    """Devuelve (es_valida, tipo_resultado).

    Para CDNN (cadenas): solo se permiten "+" y "-".
    "*" y "/" NUNCA son válidos con CDNN.
    Para ETRR/RLL: "+", "-" y "*" requieren el mismo tipo;
    la división sigue las reglas de tipo_division (permite
    mezclar ETRR con RLL, dando RLL).
    """
    if tipo_izq is None or tipo_der is None:
        return False, None

    if operador == "/":
        resultado = tipo_division(tipo_izq, tipo_der)
        return resultado is not None, resultado

    if tipo_izq != tipo_der:
        return False, None

    if operador in ("+", "-"):
        return True, tipo_izq

    if operador == "*":
        if tipo_izq == "CDNN":
            return False, None
        return True, tipo_izq

    return False, None
