import re


class GeneradorTriplos:
    def __init__(self):
        self.triplos = []
        self.contador_temporales = 1

        self.precedencia = {
            "||": 1, "&&": 2, "==": 3, "!=": 3,
            ">": 3, "<": 3, ">=": 3, "<=": 3,
            "+": 4, "-": 4, "*": 5, "/": 5, "%": 5,
        }

        # Admite identificadores con * (por ejemplo, *unO) y sin * (x, Val).
        self.patron = re.compile(
            # Cadenas entre comillas dobles o simples; conserva las comillas.
            r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
            r'|\*?[A-Za-z_]\w*'
            r'|\d+(?:\.\d+)?'
            r'|>=|<=|==|!=|&&|\|\|'
            r'|[()+\-*/%><]'
        )

    def limpiar(self):
        self.triplos = []
        self.contador_temporales = 1

    def nuevo_temporal(self):
        temporal = f"T{self.contador_temporales}"
        self.contador_temporales += 1
        return temporal

    def nuevo_triplo(self, dato_objeto, dato_fuente, operador):
        self.triplos.append([len(self.triplos) + 1, dato_objeto, dato_fuente, operador])

    def tokenizar(self, expresion):
        tokens = []
        posicion = 0
        for coincidencia in self.patron.finditer(expresion):
            separacion = expresion[posicion:coincidencia.start()]
            if separacion.strip():
                raise ValueError(f"Elemento no reconocido: {separacion.strip()}")
            tokens.append(coincidencia.group())
            posicion = coincidencia.end()
        if expresion[posicion:].strip():
            raise ValueError(f"Elemento no reconocido: {expresion[posicion:].strip()}")
        if not tokens:
            raise ValueError("La expresión está vacía.")
        return tokens

    def generar_asignacion(self, instruccion):
        self.limpiar()
        coincidencia = re.fullmatch(
            r'\s*(\*[A-Za-z_]\w*)\s*=(?!=)\s*(.*?)\s*;?\s*', instruccion
        )
        if not coincidencia:
            raise ValueError("La asignación no es válida.")
        destino, expresion = coincidencia.groups()
        if not expresion:
            raise ValueError("La asignación no contiene una expresión.")
        resultado = self._procesar_expresion(expresion)
        if not self._es_temporal(resultado):
            temporal = self.nuevo_temporal()
            self.nuevo_triplo(temporal, resultado, "=")
            resultado = temporal
        self.nuevo_triplo(destino, resultado, "=")
        return self.triplos

    def generar_expresion(self, expresion):
        self.limpiar()
        self._procesar_expresion(expresion)
        return self.triplos

    def generar_relacional(self, expresion):
        self.limpiar()
        operadores = ("==", "!=", ">=", "<=", ">", "<")
        tokens = self.tokenizar(expresion)
        profundidad = 0
        indice = None
        for i, token in enumerate(tokens):
            if token == "(":
                profundidad += 1
            elif token == ")":
                profundidad -= 1
            elif profundidad == 0 and token in operadores:
                if indice is not None:
                    raise ValueError("La comparación contiene más de un operador relacional.")
                indice = i
        if indice is None:
            raise ValueError("No se encontró un operador relacional.")
        izquierda, operador, derecha = (
            "".join(tokens[:indice]), tokens[indice], "".join(tokens[indice + 1:])
        )
        if not izquierda or not derecha:
            raise ValueError("Falta un operando en la comparación.")
        resultado_izquierda = self._procesar_expresion(izquierda)
        if not self._es_temporal(resultado_izquierda):
            temporal = self.nuevo_temporal()
            self.nuevo_triplo(temporal, resultado_izquierda, "=")
            resultado_izquierda = temporal
        resultado_derecha = self._procesar_expresion(derecha)
        self.nuevo_triplo(resultado_izquierda, resultado_derecha, operador)
        return self.triplos

    def generar_do_while(self, codigo):
        self.limpiar()
        lineas = [linea.strip() for linea in codigo.splitlines() if linea.strip()]
        if len(lineas) < 3:
            raise ValueError("El do while está incompleto.")
        if not re.fullmatch(r'do\s*\{', lineas[0]):
            raise ValueError("Se esperaba do { al inicio.")
        indice_cierre = None
        for i, linea in enumerate(lineas):
            if re.match(r'^\}\s*while\s*\(', linea):
                indice_cierre = i
                break
        if indice_cierre is None:
            raise ValueError("No se encontró el cierre } while(...).")
        inicio_cuerpo = len(self.triplos) + 1
        for linea in lineas[1:indice_cierre]:
            self._generar_asignacion_sin_limpiar(linea)
        coincidencia = re.fullmatch(
            r'\}\s*while\s*\((.*)\)\s*;?', " ".join(lineas[indice_cierre:])
        )
        if not coincidencia:
            raise ValueError("La condición del do while no es válida.")
        self._generar_condicion(coincidencia.group(1).strip())
        self.nuevo_triplo(None, "TRUE", inicio_cuerpo)
        self.nuevo_triplo(None, "FALSE", len(self.triplos) + 2)
        return self.triplos

    def _generar_asignacion_sin_limpiar(self, instruccion):
        coincidencia = re.fullmatch(
            r'\s*(\*[A-Za-z_]\w*)\s*=(?!=)\s*(.*?)\s*;?\s*', instruccion
        )
        if not coincidencia:
            raise ValueError(f"Instrucción no admitida dentro del do while: {instruccion}")
        destino, expresion = coincidencia.groups()
        if not expresion:
            raise ValueError("La asignación no contiene una expresión.")
        resultado = self._procesar_expresion(expresion)
        if not self._es_temporal(resultado):
            temporal = self.nuevo_temporal()
            self.nuevo_triplo(temporal, resultado, "=")
            resultado = temporal
        self.nuevo_triplo(destino, resultado, "=")

    def _generar_condicion(self, condicion, destino_true=None, destino_false=None):
        """Genera saltos de cortocircuito con && de mayor precedencia que ||."""
        grupos_or = self._separar_logico(condicion, '||')
        pendientes = []
        saltos_a_siguiente_or = []
        for i_or, grupo in enumerate(grupos_or):
            inicio_grupo = len(self.triplos) + 1
            # Los FALSE de cualquier parte del grupo OR deben saltar al
            # comienzo del siguiente grupo OR, no a la siguiente parte AND.
            for fila in saltos_a_siguiente_or:
                self.triplos[fila - 1][3] = inicio_grupo
            saltos_a_siguiente_or = []

            partes_and = self._separar_logico(grupo, '&&')
            for i_and, parte in enumerate(partes_and):
                self._generar_comparacion(parte.strip())
                fila_true = len(self.triplos) + 1
                self.nuevo_triplo(None, 'TRUE', None)
                fila_false = len(self.triplos) + 1
                self.nuevo_triplo(None, 'FALSE', None)

                hay_and = i_and < len(partes_and) - 1
                hay_or = i_or < len(grupos_or) - 1
                siguiente = len(self.triplos) + 1

                if hay_and:
                    self.triplos[fila_true - 1][3] = siguiente
                elif destino_true is not None:
                    self.triplos[fila_true - 1][3] = destino_true
                else:
                    pendientes.append((fila_true, 'TRUE'))

                if hay_or:
                    saltos_a_siguiente_or.append(fila_false)
                elif destino_false is not None:
                    self.triplos[fila_false - 1][3] = destino_false
                else:
                    pendientes.append((fila_false, 'FALSE'))

        return pendientes

    def _separar_logico(self, texto, operador):
        partes, inicio, profundidad, i = [], 0, 0, 0
        while i < len(texto):
            if texto[i] == '(':
                profundidad += 1
            elif texto[i] == ')':
                profundidad -= 1
            elif profundidad == 0 and texto.startswith(operador, i):
                partes.append(texto[inicio:i].strip())
                i += len(operador)
                inicio = i
                continue
            i += 1
        if partes:
            partes.append(texto[inicio:].strip())
        return partes or [texto.strip()]

    def _generar_comparacion(self, condicion):
        self.contador_temporales = 1
        tokens = self.tokenizar(condicion)
        operadores = ("==", "!=", ">=", "<=", ">", "<")
        profundidad = 0
        indice = None
        for i, token in enumerate(tokens):
            if token == "(":
                profundidad += 1
            elif token == ")":
                profundidad -= 1
            elif profundidad == 0 and token in operadores:
                if indice is not None:
                    raise ValueError("La comparación contiene más de un operador relacional.")
                indice = i
        if indice is None:
            raise ValueError("La condición necesita un operador relacional.")
        izquierda, operador, derecha = (
            "".join(tokens[:indice]), tokens[indice], "".join(tokens[indice + 1:])
        )
        if not izquierda or not derecha:
            raise ValueError("Falta un operando en la condición.")
        resultado_izquierda = self._procesar_expresion(izquierda)
        if not self._es_temporal(resultado_izquierda):
            temporal = self.nuevo_temporal()
            self.nuevo_triplo(temporal, resultado_izquierda, "=")
            resultado_izquierda = temporal
        resultado_derecha = self._procesar_expresion(derecha)
        self.nuevo_triplo(resultado_izquierda, resultado_derecha, operador)
        return resultado_izquierda

    def _separar_instrucciones(self, codigo):
        """Separa instrucciones por ; sin cortar expresiones ni bloques { }.

        Un do { ... } while (...); se conserva como una sola instrucción,
        incluso cuando contiene varias asignaciones.
        """
        instrucciones = []
        inicio = 0
        parentesis = 0
        llaves = 0
        en_cadena = None
        i = 0
        while i < len(codigo):
            ch = codigo[i]
            if ch in ('"', "'") and (i == 0 or codigo[i - 1] != '\\'):
                if en_cadena is None:
                    en_cadena = ch
                elif en_cadena == ch:
                    en_cadena = None
            elif en_cadena is None:
                if ch == '(':
                    parentesis += 1
                elif ch == ')':
                    parentesis = max(0, parentesis - 1)
                elif ch == '{':
                    llaves += 1
                elif ch == '}':
                    llaves = max(0, llaves - 1)
                elif ch == ';' and parentesis == 0 and llaves == 0:
                    parte = codigo[inicio:i + 1].strip()
                    if parte:
                        instrucciones.append(parte.rstrip(';').strip())
                    inicio = i + 1
            i += 1
        resto = codigo[inicio:].strip()
        if resto:
            instrucciones.append(resto.rstrip(';').strip())
        return instrucciones

    def _procesar_codigo_con_bloques(self, codigo):
        """Procesa declaraciones, asignaciones y do-while sin depender de semántica."""
        i = 0
        n = len(codigo)
        while i < n:
            while i < n and (codigo[i].isspace() or codigo[i] == ';'):
                i += 1
            if i >= n:
                break
            resto = codigo[i:]
            m_do = re.match(r'do\s*\{', resto)
            if m_do:
                apertura = i + m_do.end() - 1
                cierre, profundidad = apertura + 1, 1
                while cierre < n and profundidad:
                    if codigo[cierre] == '{': profundidad += 1
                    elif codigo[cierre] == '}': profundidad -= 1
                    cierre += 1
                if profundidad:
                    raise ValueError("El bloque do no tiene llave de cierre.")
                cuerpo = codigo[apertura + 1:cierre - 1]
                m_while = re.match(r'\s*while\s*\((.*?)\)\s*;?', codigo[cierre:], re.S)
                if not m_while:
                    raise ValueError("Después del bloque do se esperaba while(condición).")
                inicio_cuerpo = len(self.triplos) + 1
                self._procesar_codigo_con_bloques(cuerpo)
                self.contador_temporales = 1
                condicion = m_while.group(1).strip()
                pendientes = self._generar_condicion(condicion, destino_true=inicio_cuerpo)
                fila_salida = len(self.triplos) + 1
                for fila, tipo_salto in pendientes:
                    self.triplos[fila - 1][3] = fila_salida
                i = cierre + m_while.end()
                continue
            # Tomar una instrucción hasta ;, sin dividir dentro de paréntesis.
            inicio = i
            profundidad = 0
            while i < n:
                if codigo[i] == '(': profundidad += 1
                elif codigo[i] == ')': profundidad -= 1
                elif codigo[i] == ';' and profundidad == 0:
                    break
                i += 1
            instruccion = codigo[inicio:i].strip()
            if i < n and codigo[i] == ';': i += 1
            if not instruccion or self._es_declaracion(instruccion):
                continue
            # Las llamadas a funciones también pueden aparecer dentro de bloques
            # (por ejemplo, dentro de un do-while). Si hay un manejador instalado,
            # se procesa la llamada sin pasarla por el analizador de expresiones.
            manejador_llamada = getattr(self, "_manejador_llamada_bloque", None)
            if manejador_llamada is not None and manejador_llamada(instruccion):
                continue
            self.contador_temporales = 1
            self._generar_asignacion_generica(instruccion)

    def generar_programa_funcion(self, codigo):
        """Genera funciones y llamadas con saltos de entrada, llamada y retorno."""
        self.limpiar()

        patron_inicio = re.compile(r'\b(ETRR|RLL|CDNN)\s+(\*?[A-Za-z_]\w*)\s*\(([^()]*)\)\s*\{')
        funciones = []
        partes_externas = []
        cursor = 0

        while True:
            m = patron_inicio.search(codigo, cursor)
            if not m:
                partes_externas.append(codigo[cursor:])
                break
            partes_externas.append(codigo[cursor:m.start()])
            apertura = m.end() - 1
            profundidad = 1
            i = apertura + 1
            while i < len(codigo) and profundidad:
                if codigo[i] == '{':
                    profundidad += 1
                elif codigo[i] == '}':
                    profundidad -= 1
                i += 1
            if profundidad:
                raise ValueError(f"La función {m.group(2)} no tiene llave de cierre.")

            tipo, nombre, texto_parametros = m.group(1), m.group(2).lstrip("*"), m.group(3).strip()
            parametros = []
            if texto_parametros:
                for parametro in texto_parametros.split(','):
                    partes = parametro.strip().split()
                    if len(partes) != 2:
                        raise ValueError(f"Parámetro no válido en {nombre}: {parametro.strip()}")
                    parametros.append(partes[1])
            funciones.append({
                "nombre": nombre, "tipo": tipo, "parametros": parametros,
                "cuerpo": codigo[apertura + 1:i - 1].strip()
            })
            cursor = i

        texto_externo = ''.join(partes_externas)
        instrucciones = self._separar_instrucciones(texto_externo)
        if not funciones:
            self._procesar_codigo_con_bloques(texto_externo)
            if not self.triplos:
                raise ValueError("No se encontraron instrucciones que generen triplos.")
            return self.triplos

        mapa = {f["nombre"]: f for f in funciones}
        if len(mapa) != len(funciones):
            raise ValueError("Hay nombres de función duplicados.")
        patron_llamada = re.compile(
            r'^(\*?[A-Za-z_]\w*)\s*=\s*(\*?[A-Za-z_]\w*)\s*\((.*?)\)\s*$'
        )

        # Una función necesita una única continuación estática para su return.
        # Se valida también el número de llamadas antes de emitir saltos.
        conteos = {f["nombre"]: 0 for f in funciones}
        for f in funciones:
            sentencias = self._separar_instrucciones(f["cuerpo"])
            if not sentencias or not re.match(r'^return\b', sentencias[-1]):
                raise ValueError(f"La función {f['nombre']} debe terminar con return.")
            self.contador_temporales = 1
            for sentencia in sentencias[:-1]:
                if not self._es_declaracion(sentencia):
                    self.contador_temporales = 1
                llamada = patron_llamada.fullmatch(sentencia)
                if llamada and llamada.group(2).lstrip('*') in mapa:
                    conteos[llamada.group(2).lstrip('*')] += 1
        for instruccion in instrucciones:
            llamada = patron_llamada.fullmatch(instruccion)
            if llamada and llamada.group(2).lstrip('*') in mapa:
                conteos[llamada.group(2).lstrip('*')] += 1
        repetidas = [nombre for nombre, total in conteos.items() if total > 1]
        if repetidas:
            raise ValueError(
                "Cada función admite una sola llamada con este esquema de JMP de retorno. "
                "Se repiten: " + ", ".join(repetidas) + "."
            )

        saltos_entrada = []
        inicios = {}
        saltos_retorno = {}

        def emitir_llamada(destino, nombre, args_txt):
            args = [a.strip() for a in args_txt.split(',')] if args_txt.strip() else []
            parametros = mapa[nombre]["parametros"]
            if len(args) != len(parametros):
                raise ValueError(f"La llamada a {nombre} requiere {len(parametros)} argumentos.")
            for parametro, argumento in zip(parametros, args):
                # El generador representa argumentos simples sin validar su
                # declaración ni su tipo: esa tarea pertenece al análisis semántico.
                toks = self.tokenizar(argumento)
                if len(toks) != 1:
                    raise ValueError("Por ahora los argumentos de función deben ser variables, cadenas o números simples.")
                self.contador_temporales = 1
                temporal_parametro = self.nuevo_temporal()
                self.nuevo_triplo(temporal_parametro, toks[0], "=")
                self.nuevo_triplo(parametro, temporal_parametro, "=")
            self.nuevo_triplo(None, inicios[nombre], "JMP")
            # Al volver de la función, se copia su variable de retorno al destino.
            self.contador_temporales = 1
            temporal = self.nuevo_temporal()
            self.nuevo_triplo(temporal, "*resulT", "=")
            self.nuevo_triplo(destino, temporal, "=")
            return len(self.triplos) - 2  # índice (base cero) de la primera fila receptora

        # Cada definición con un JMP que evita ejecutar su cuerpo
        # durante el flujo normal. El return termina con otro JMP al receptor.
        for f in funciones:
            indice_entrada = len(self.triplos)
            self.nuevo_triplo(None, None, "JMP")
            saltos_entrada.append(indice_entrada)
            inicios[f["nombre"]] = len(self.triplos) + 1

            sentencias = self._separar_instrucciones(f["cuerpo"])
            self.contador_temporales = 1
            for sentencia in sentencias[:-1]:
                if not self._es_declaracion(sentencia):
                    self.contador_temporales = 1
                llamada = patron_llamada.fullmatch(sentencia)
                if llamada and llamada.group(2).lstrip('*') in mapa:
                    destino, nombre_llamado, args_txt = llamada.groups()
                    nombre_llamado = nombre_llamado.lstrip('*')
                    emitir_llamada(destino, nombre_llamado, args_txt)
                else:
                    self._procesar_codigo_con_bloques(sentencia)

            expresion_retorno = re.sub(r'^return\s+', '', sentencias[-1]).strip()
            if not expresion_retorno:
                raise ValueError(f"La función {f['nombre']} tiene un return vacío.")
            if expresion_retorno != "*resulT":
                self.contador_temporales = 1
                valor_retorno = self._procesar_expresion(expresion_retorno)
                if valor_retorno != "*resulT":
                    self.nuevo_triplo("*resulT", valor_retorno, "=")
            indice_retorno = len(self.triplos)
            self.nuevo_triplo(None, None, "JMP")
            saltos_retorno[f["nombre"]] = indice_retorno

        # El salto de entrada de cada función apunta al JMP de la siguiente;
        # el último apunta al inicio del programa principal.
        inicio_principal = len(self.triplos) + 1
        for pos, indice in enumerate(saltos_entrada):
            destino_salto = (saltos_entrada[pos + 1] + 1) if pos + 1 < len(saltos_entrada) else inicio_principal
            self.triplos[indice][2] = destino_salto

        # Las funciones que no sean invocadas conservan un destino válido
        # para su JMP de retorno; una llamada real sustituirá este destino.
        for indice_retorno in saltos_retorno.values():
            self.triplos[indice_retorno][2] = inicio_principal

        # Permitir llamadas con retorno dentro de bloques del programa principal,
        # incluyendo do-while. El retorno salta a las dos instrucciones receptoras.
        def manejar_llamada_en_bloque(instruccion):
            llamada = patron_llamada.fullmatch(instruccion.strip())
            if not llamada:
                return False
            destino, nombre_llamado, args_txt = llamada.groups()
            nombre_llamado = nombre_llamado.lstrip('*')
            if nombre_llamado not in mapa:
                return False
            indice_jmp = emitir_llamada(destino, nombre_llamado, args_txt)
            self.triplos[saltos_retorno[nombre_llamado]][2] = indice_jmp + 1
            return True

        self._manejador_llamada_bloque = manejar_llamada_en_bloque

        # Procesar el programa principal en el orden en que aparece en el fuente.
        for instruccion in instrucciones:
            if self._es_declaracion(instruccion):
                continue
            self.contador_temporales = 1
            if re.match(r'^do\s*\{', instruccion):
                self._procesar_codigo_con_bloques(instruccion)
                continue
            llamada = patron_llamada.fullmatch(instruccion)
            if llamada and llamada.group(2).lstrip('*') in mapa:
                destino, nombre_llamado, args_txt = llamada.groups()
                nombre_llamado = nombre_llamado.lstrip('*')
                indice_jmp = emitir_llamada(destino, nombre_llamado, args_txt)
                # El JMP del return salta a la primera instrucción de recepción.
                self.triplos[saltos_retorno[nombre_llamado]][2] = indice_jmp + 1
            else:
                self._generar_asignacion_generica(instruccion)

        # Enlazar llamadas hechas desde otras funciones a su entrada y retorno.
        for f in funciones:
            sentencias = self._separar_instrucciones(f["cuerpo"])
            self.contador_temporales = 1
            for sentencia in sentencias[:-1]:
                if not self._es_declaracion(sentencia):
                    self.contador_temporales = 1
                llamada = patron_llamada.fullmatch(sentencia)
                if not llamada or llamada.group(2).lstrip('*') not in mapa:
                    continue
                destino, nombre_llamado, _ = llamada.groups()
                nombre_llamado = nombre_llamado.lstrip('*')
                for idx, triplo in enumerate(self.triplos):
                    if triplo[3] == "JMP" and triplo[2] == inicios[nombre_llamado]:
                        # El receptor está inmediatamente después del JMP y ocupa dos filas.
                        self.triplos[saltos_retorno[nombre_llamado]][2] = idx + 2
                        break

        for i, triplo in enumerate(self.triplos, start=1):
            triplo[0] = i
        if hasattr(self, "_manejador_llamada_bloque"):
            del self._manejador_llamada_bloque
        return self.triplos

    def _generar_asignacion_generica(self, instruccion):
        instruccion = instruccion.strip()
        if not instruccion or self._es_declaracion(instruccion):
            return
        coincidencia = re.fullmatch(
            r'\s*(\*?[A-Za-z_]\w*)\s*=(?!=)\s*(.*?)\s*;?\s*', instruccion
        )
        if not coincidencia:
            raise ValueError(f"Asignación no válida: {instruccion}")
        destino, expresion = coincidencia.groups()
        expresion = expresion.strip()
        if not expresion:
            raise ValueError("La asignación no contiene una expresión.")
        resultado = self._procesar_expresion(expresion)
        if not self._es_temporal(resultado):
            temporal = self.nuevo_temporal()
            self.nuevo_triplo(temporal, resultado, "=")
            resultado = temporal
        self.nuevo_triplo(destino, resultado, "=")

    def _procesar_expresion(self, expresion):
        self.tokens = self.tokenizar(expresion)
        self.posicion = 0
        resultado = self._expresion()
        if self.posicion != len(self.tokens):
            raise ValueError("La expresión contiene elementos inesperados.")
        return resultado

    def _expresion(self):
        izquierda = self._termino()
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] in ("+", "-"):
            operador = self.tokens[self.posicion]
            self.posicion += 1
            derecha = self._termino()
            izquierda = self._combinar(izquierda, operador, derecha)
        return izquierda

    def _termino(self):
        izquierda = self._factor()
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] in ("*", "/", "%"):
            operador = self.tokens[self.posicion]
            self.posicion += 1
            derecha = self._factor()
            izquierda = self._combinar(izquierda, operador, derecha)
        return izquierda

    def _factor(self):
        if self.posicion >= len(self.tokens):
            raise ValueError("Falta un operando.")
        token = self.tokens[self.posicion]
        self.posicion += 1
        if token == "(":
            resultado = self._expresion()
            if self.posicion >= len(self.tokens) or self.tokens[self.posicion] != ")":
                raise ValueError("Falta un paréntesis de cierre.")
            self.posicion += 1
            return resultado
        if token == ")" or token in self.precedencia:
            raise ValueError(f"Operando inesperado: {token}")
        return token

    def _combinar(self, izquierda, operador, derecha):
        if not self._es_temporal(izquierda):
            temporal = self.nuevo_temporal()
            self.nuevo_triplo(temporal, izquierda, "=")
            izquierda = temporal
        self.nuevo_triplo(izquierda, derecha, operador)
        return izquierda

    @staticmethod
    def _es_temporal(valor):
        return isinstance(valor, str) and re.fullmatch(r'T\d+', valor) is not None

    @staticmethod
    def _es_declaracion(instruccion):
        return re.fullmatch(
            r'\s*(?:ETRR|RLL|CDNN)\s+\*[A-Za-z_]\w*'
            r'(?:\s*,\s*\*[A-Za-z_]\w*)*\s*;?\s*',
            instruccion.strip()
        ) is not None
