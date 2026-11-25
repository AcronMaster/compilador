class GestorErrores:
    """Guarda los errores semánticos como (token, lexema, línea, descripción)."""

    def __init__(self):
        self.errores = []

    def agregar(self, lexema, linea, descripcion):
        numero = len(self.errores) + 1
        token = f"*erroR{numero}"
        self.errores.append((token, lexema, linea, descripcion))

    def limpiar(self):
        self.errores.clear()

    def obtener(self):
        return list(self.errores)
