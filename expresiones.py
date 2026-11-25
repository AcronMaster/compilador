from reglas import RE_OPERANDO, RE_OPERADOR, quitar_cadenas
from tipos import tipo_literal, operacion_valida


class AnalizadorExpresiones:
    """Valida los tipos de una expresión aritmética, de izquierda a derecha.

    Reglas:
    - Se lee toda la línea y se reportan todos los errores que haya.
    - La única excepción es una variable no definida: al encontrarla se
      reporta y se deja de analizar el resto (no se puede leer su tipo).
    - Si hay tipo destino, cada operando se compara contra el tipo que
      se espera. Un operando incorrecto se reporta UNA sola vez y el
      resto se sigue comparando contra el tipo correcto, para no
      arrastrar el error a operandos que sí están bien.
    """

    def __init__(self, registrar_simbolo, buscar_variable, obtener_tipo, error):
        self.registrar_simbolo = registrar_simbolo
        self.buscar_variable = buscar_variable
        self.obtener_tipo = obtener_tipo      # con error si no está definida
        self.error = error

    # ------------------------------------------------------------------
    # Tokens
    # ------------------------------------------------------------------
    def obtener_operandos(self, expresion):
        return RE_OPERANDO.findall(expresion)

    def obtener_operadores(self, expresion):
        # Se ignoran los símbolos que estén dentro de cadenas ("a+b").
        operadores = RE_OPERADOR.findall(quitar_cadenas(expresion))
        for operador in operadores:
            self.registrar_simbolo(operador, None)
        return operadores

    def tipo_silencioso(self, token):
        """Tipo de un token SIN generar errores."""
        token = token.strip()
        if token.startswith('*'):
            return self.buscar_variable(token)
        return tipo_literal(token)

    def registrar_tokens(self, expresion):
        """Registra en la tabla de símbolos todo lo que trae la expresión,
        sin analizarla ni generar errores (se usa cuando la línea ya no
        se puede analizar, por ejemplo por una variable indefinida)."""
        self.obtener_operadores(expresion)
        for token in self.obtener_operandos(expresion):
            self.registrar_simbolo(token, self.tipo_silencioso(token))

    # ------------------------------------------------------------------
    # Análisis
    # ------------------------------------------------------------------
    def analizar(self, expresion, linea, tipo_destino=None):
        operandos = self.obtener_operandos(expresion)
        operadores = self.obtener_operadores(expresion)

        # Todo lo que aparece en la línea queda en la tabla de símbolos.
        for token in operandos:
            self.registrar_simbolo(token, self.tipo_silencioso(token))

        if not operandos:
            return None

        # --- primer operando ---------------------------------------------
        primer_token = operandos[0]
        tipo_primero = self.obtener_tipo(primer_token, linea)

        # Variable no definida: ya se reportó, no se sigue leyendo.
        if tipo_primero is None:
            tipo_primero = None

        # tipo_referencia: el tipo "correcto" de esta instrucción (el del
        # destino). Cuando un operando no coincide, se compara el RESTO
        # de la expresión contra este tipo (no contra el tipo del valor
        # que resultó incorrecto), para que un solo error no arrastre
        # más errores falsos sobre operandos que sí son correctos.
        tipo_referencia = tipo_destino if tipo_destino is not None else tipo_primero

        tipo_actual = tipo_primero
        primero_marcado = False

        if (tipo_destino is not None
            and tipo_primero is not None
            and tipo_primero != tipo_destino):
            # Una división entre entero y real da real, así que
            # "RLL = ETRR / RLL" es válido y no se marca el primer operando.
            excusado = (
                tipo_destino == 'RLL'
                and tipo_primero == 'ETRR'
                and len(operandos) > 1
                and operadores
                and operadores[0] == '/'
                and self.tipo_silencioso(operandos[1]) == 'RLL'
            )

            if not excusado:
                self.error(
                    primer_token,
                    linea,
                    f"Incompatibilidad de tipos, tipo de dato {tipo_referencia}"
                )
                # A partir de aquí se compara contra el tipo correcto.
                tipo_actual = tipo_referencia
                primero_marcado = True

        # Tipo real del operando izquierdo (para la primera división, que
        # depende de los tipos reales y no del tipo esperado).
        tipo_izq_real = tipo_primero

        # --- resto de operaciones ----------------------------------------
        cantidad = min(len(operadores), len(operandos) - 1)

        for i in range(cantidad):
            operador = operadores[i]
            token = operandos[i + 1]

            tipo_der = self.obtener_tipo(token, linea)

            # Variable no definida: se reporta y se detiene el análisis.
            if tipo_der is None:
                tipo_actual = None
                continue

            if tipo_actual is None:
                if tipo_destino is not None and tipo_der != tipo_destino:
                    self.error(
                        token,
                        linea,
                        f"Incompatibilidad de tipos, tipo de dato {tipo_der}"
                    )

                tipo_actual = tipo_der
                tipo_izq_real = tipo_der
                continue

            tipo_izq = tipo_izq_real if operador == '/' else tipo_actual

            valida, resultado = operacion_valida(operador, tipo_izq, tipo_der)

            if not valida:
                # Si el operando IZQUIERDO es una cadena, "*" nunca es
                # válido sin importar qué haya del otro lado: el
                # problema es el OPERADOR en sí, se reporta su símbolo
                # (igual que con "/"). Si en cambio la cadena está del
                # lado derecho (ej. 2.3 * "a"), el problema es que ese
                # valor no es del tipo esperado: se cita el valor.
                operador_invalido_cdnn = (
                    operador == '*' and tipo_izq == 'CDNN'
                )

                if operador == '/':
                    self.error(
                        operador,
                        linea,
                        f"Incompatibilidad de tipos, tipo de dato {tipo_referencia}"
                    )
                elif operador_invalido_cdnn:
                    # El operador en sí no es válido con cadenas...
                    self.error(
                        operador,
                        linea,
                        f"Incompatibilidad de tipos, tipo de dato {tipo_referencia}"
                    )
                    # ...y ADEMÁS, si el otro operando ni siquiera es
                    # una cadena, ese valor también es del tipo
                    # equivocado: se reporta aparte.
                    if tipo_der != 'CDNN':
                        self.error(
                            token,
                            linea,
                            f"Incompatibilidad de tipos, tipo de dato {tipo_referencia}"
                        )
                else:
                    self.error(
                        token,
                        linea,
                        f"Incompatibilidad de tipos, tipo de dato {tipo_referencia}"
                    )
                # tipo_actual (el que usan +, -, *) se congela al tipo
                # CORRECTO, no al del valor que resultó incorrecto, para
                # no arrastrar este error a operandos que sí están bien.
                # tipo_izq_real sí seguimos con el tipo real del operando
                # que se acaba de leer, porque una división posterior
                # (ej. "3 / 4") debe diagnosticarse con los tipos reales.
                tipo_actual = tipo_referencia
                tipo_izq_real = tipo_izq
                continue

            # División entero/real -> real, pero el destino no es real.
            if (
                operador == '/'
                and resultado == 'RLL'
                and tipo_destino is not None
            ):
                if tipo_destino == 'RLL' and tipo_der == 'ETRR':
                    self.error(
                        token,
                        linea,
                        f"Incompatibilidad de tipos, tipo de dato {tipo_destino}"
                    )
                # Si el primer operando ya se marcó como error, es el mismo
                # problema: no se vuelve a reportar.
                elif tipo_destino != 'RLL':
                    if i == 0 and primero_marcado:
                        tipo_actual = tipo_referencia
                        tipo_izq_real = resultado
                        continue

                    culpable = token if tipo_der == 'RLL' else operador
                    self.error(
                        culpable,
                        linea,
                        f"Incompatibilidad de tipos, tipo de dato {tipo_referencia}"
                    )
                tipo_actual = tipo_referencia
                tipo_izq_real = resultado
                continue

            tipo_actual = resultado
            tipo_izq_real = resultado

        return tipo_actual
