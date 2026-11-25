import re

from reglas import (
    RE_DECLARACION, RE_ASIGNACION, RE_CONDICION, RE_FUNCION,
    RE_PARAMETRO, RE_LLAMADA_FUNCION, RE_RETURN, RE_VARIABLE,
    PALABRAS_RESERVADAS, quitar_cadenas, dividir_por_comas
)
from tipos import tipo_literal, compatible
from errores import GestorErrores
from expresiones import AnalizadorExpresiones


class AnalizadorSemantico:
    def __init__(self):
        self._reiniciar()

    def _reiniciar(self):
        # Variables globales y variables locales de la función activa.
        self.declaradas = {}
        self.locales = None
        self._locales_pendientes = None

        self.funciones = {}
        self.funcion_pendiente = None      # (nombre, tipo, línea) esperando "{"
        self.contexto_pila = []            # ('funcion', nombre, tipo) / ('bloque',)
        self.simbolos = {}
        self.gestor_errores = GestorErrores()
        self.expresiones = AnalizadorExpresiones(
            self.registrar_simbolo,
            self.buscar_variable,
            self.tipo_de,
            self.error
        )

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def registrar_simbolo(self, lexema, tipo):
        if lexema not in self.simbolos:
            self.simbolos[lexema] = tipo
        elif self.simbolos[lexema] is None and tipo is not None:
            self.simbolos[lexema] = tipo

    def error(self, lexema, linea, descripcion):
        self.gestor_errores.agregar(lexema, linea, descripcion)

    def buscar_variable(self, nombre):
        """Busca primero en la función activa y luego en las globales."""
        if self.locales is not None and nombre in self.locales:
            return self.locales[nombre]
        return self.declaradas.get(nombre)

    def _ambito(self):
        """Diccionario donde se declaran las variables nuevas."""
        return self.locales if self.locales is not None else self.declaradas

    def tipo_de(self, token, linea):
        """Tipo de un operando. Reporta 'Variable indefinida' si no existe."""
        token = token.strip()
        if token.startswith('*'):
            tipo = self.buscar_variable(token)
            if tipo is None:
                self.error(token, linea, 'Variable indefinida')
                self.registrar_simbolo(token, None)
                return None
            self.registrar_simbolo(token, tipo)
            return tipo
        tipo = tipo_literal(token)
        if tipo is not None:
            self.registrar_simbolo(token, tipo)
        return tipo

    def funcion_actual(self):
        for entrada in reversed(self.contexto_pila):
            if entrada[0] == 'funcion':
                return entrada
        return None

    def _registrar_signos_estructura(self, linea):
        linea = quitar_cadenas(linea)
        if linea.endswith(';'):
            self.registrar_simbolo(';', None)
        for simbolo in ('{', '}', '(', ')'):
            if simbolo in linea:
                self.registrar_simbolo(simbolo, None)

    # ------------------------------------------------------------------
    # Bloques y funciones
    # ------------------------------------------------------------------
    def _abrir_funcion(self, nombre, tipo, locales):
        self.contexto_pila.append(('funcion', nombre, tipo))
        self.locales = locales

    def _cerrar_bloque(self):
        if not self.contexto_pila:
            return
        entrada = self.contexto_pila.pop()
        if entrada[0] == 'funcion':
            self.locales = None     # las variables locales dejan de existir

    def _parametros(self, texto, numero_linea, ambito):
        for parte in dividir_por_comas(texto):
            m = RE_PARAMETRO.match(parte)
            if not m:
                continue
            tipo, nombre = m.groups()
            if nombre in ambito:
                self.error(nombre, numero_linea, 'Variable duplicada')
                self.registrar_simbolo(nombre, ambito[nombre])
            else:
                ambito[nombre] = tipo
                self.registrar_simbolo(nombre, tipo)

    def _funcion(self, linea, numero_linea):
        m = RE_FUNCION.match(linea)
        if not m:
            return False

        tipo_retorno, nombre, parametros, llave = m.groups()

        if nombre in self.funciones:
            self.error(nombre, numero_linea, 'Función duplicada')
            self.registrar_simbolo(nombre, self.funciones[nombre])
        else:
            self.funciones[nombre] = tipo_retorno
            self.registrar_simbolo(nombre, tipo_retorno)

        # Los parámetros son variables locales de la función.
        locales = {}
        self._parametros(parametros, numero_linea, locales)

        if llave:
            self._abrir_funcion(nombre, tipo_retorno, locales)
        else:
            # Puede que la "{" venga en la línea siguiente.
            self.funcion_pendiente = (nombre, tipo_retorno, numero_linea)
            self._locales_pendientes = locales
        return True

    # ------------------------------------------------------------------
    # Declaraciones
    # ------------------------------------------------------------------
    def _declaracion(self, linea, numero_linea):
        m = RE_DECLARACION.match(linea)
        if not m:
            return False

        tipo, resto = m.groups()
        ambito = self._ambito()

        for variable in RE_VARIABLE.findall(resto):
            if variable in ambito:
                self.error(variable, numero_linea, 'Variable duplicada')
                self.registrar_simbolo(variable, ambito[variable])
            else:
                ambito[variable] = tipo
                self.registrar_simbolo(variable, tipo)
        return True

    # ------------------------------------------------------------------
    # Llamadas, asignaciones y return
    # ------------------------------------------------------------------
    def _llamada(self, expresion, numero_linea):
        """Si la expresión es una llamada a función la valida y devuelve
        (nombre, tipo_de_retorno); tipo None si la función no existe.
        Si no es una llamada devuelve None."""
        m = RE_LLAMADA_FUNCION.match(expresion.strip())
        if not m:
            return None

        nombre, argumentos = m.groups()
        if nombre in PALABRAS_RESERVADAS:
            return None

        tipo_funcion = self.funciones.get(nombre)

        if tipo_funcion is None:
            self.error(nombre, numero_linea, 'Función no declarada')
            self.registrar_simbolo(nombre, None)
            # No se analizan los argumentos, solo quedan en la tabla.
            for argumento in dividir_por_comas(argumentos):
                self.expresiones.registrar_tokens(argumento)
            return nombre, None

        self.registrar_simbolo(nombre, tipo_funcion)
        for argumento in dividir_por_comas(argumentos):
            self.expresiones.analizar(argumento, numero_linea, None)
        return nombre, tipo_funcion

    def _evaluar(self, expresion, numero_linea, tipo_destino):
        """Valida una expresión (o llamada) contra un tipo esperado."""
        llamada = self._llamada(expresion, numero_linea)

        if llamada is not None:
            nombre, tipo_funcion = llamada
            if (
                tipo_funcion is not None
                and tipo_destino is not None
                and not compatible(tipo_destino, tipo_funcion)
            ):
                self.error(
                    nombre,
                    numero_linea,
                    f'Incompatibilidad de tipos, tipo de dato {tipo_destino}'
                )
            return

        self.expresiones.analizar(expresion, numero_linea, tipo_destino)

    def _asignacion(self, linea, numero_linea):
        m = RE_ASIGNACION.match(linea)
        if not m:
            return False

        destino, expresion = m.groups()
        expresion = expresion.strip()

        self.registrar_simbolo('=', None)

        tipo_destino = self.buscar_variable(destino)

        if tipo_destino is None:
            # Variable indefinida: se reporta y no se lee el resto de la
            # línea (solo se registran sus símbolos en la tabla).
            self.error(destino, numero_linea, 'Variable indefinida')
            self.registrar_simbolo(destino, None)
            self.expresiones.registrar_tokens(expresion)
            return True

        self.registrar_simbolo(destino, tipo_destino)
        self._evaluar(expresion, numero_linea, tipo_destino)
        return True

    def _return(self, linea, numero_linea):
        m = RE_RETURN.match(linea)
        if not m:
            return False

        expresion = m.group(1).strip()
        contexto = self.funcion_actual()

        if contexto is None:
            self.error('return', numero_linea, 'Return fuera de función')
            self._evaluar(expresion, numero_linea, None)
            return True

        # El tipo devuelto debe coincidir con el tipo de la función.
        self._evaluar(expresion, numero_linea, contexto[2])
        return True

    # ------------------------------------------------------------------
    # while / if
    # ------------------------------------------------------------------
    def _condicion(self, linea, numero_linea):
        m = RE_CONDICION.match(linea)
        if not m:
            return False

        condicion = m.group(1)
        operandos = self.expresiones.obtener_operandos(condicion)
        if not operandos:
            return True

        self.expresiones.registrar_tokens(condicion)

        tipo_base = self.tipo_de(operandos[0], numero_linea)
        if tipo_base is None:
            return True                      # indefinida: se detiene

        for token in operandos[1:]:
            tipo = self.tipo_de(token, numero_linea)
            if tipo is None:
                return True                  # indefinida: se detiene
            if tipo != tipo_base:
                self.error(
                    token,
                    numero_linea,
                    f'Incompatibilidad de tipos, tipo de dato {tipo_base}'
                )
        return True

    # ------------------------------------------------------------------
    # Programa completo
    # ------------------------------------------------------------------
    def analizar(self, codigo):
        # Reiniciar el estado para volver a procesar todo el editor.
        self._reiniciar()

        for numero_linea, linea_original in enumerate(codigo.splitlines(), start=1):
            linea = linea_original.strip()
            if not linea:
                continue

            self._registrar_signos_estructura(linea)

            # "}" cierra el bloque abierto (función o do-while).
            if linea.startswith('}'):
                self._cerrar_bloque()

            # ¿La función de la línea anterior esperaba su "{"?
            if self.funcion_pendiente is not None:
                nombre, tipo, linea_funcion = self.funcion_pendiente
                locales = self._locales_pendientes
                self.funcion_pendiente = None
                self._locales_pendientes = None
                if linea == '{':
                    self._abrir_funcion(nombre, tipo, locales)
                    continue
                self.error(nombre, linea_funcion, 'Función no iniciada')

            # "do" abre un bloque.
            if re.match(r'^do\b', linea):
                self.contexto_pila.append(('bloque',))

            # Quitar "do {", "}" inicial y ";" final para que
            # "} while (...)" y "do { ..." se analicen bien.
            linea = re.sub(r'^do\b\s*\{?\s*', '', linea)
            linea = re.sub(r'^\}\s*', '', linea)
            linea = linea.rstrip('; \t')
            if not linea:
                continue

            if self._funcion(linea, numero_linea):
                continue

            if re.match(r'^if\b', linea) and '{' in linea:
                self.contexto_pila.append(('bloque',))

            elif re.match(r'^else\b', linea) and '{' in linea:
                self.contexto_pila.append(('bloque',))

            if self._return(linea, numero_linea):
                continue

            if self._declaracion(linea, numero_linea):
                continue

            if self._asignacion(linea, numero_linea):
                continue

            if self._condicion(linea, numero_linea):
                continue

            # Llamada independiente a función: suma();
            self._llamada(linea, numero_linea)

        if self.funcion_pendiente is not None:
            nombre, _, linea_funcion = self.funcion_pendiente
            self.error(nombre, linea_funcion, 'Función no iniciada')
            

        return self.simbolos, self.gestor_errores.obtener()


def analizar(codigo):
    return AnalizadorSemantico().analizar(codigo)
