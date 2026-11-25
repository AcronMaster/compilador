
from Triplos import GeneradorTriplos

generador = GeneradorTriplos()

generador = GeneradorTriplos()

codigo = """
Float Val(int x, int w)
{
    w = y + x % 2;
    return w;
}

J = (y * 2) / (2 + 6);
n = Val(2, 6);
"""

for triplo in generador.generar_programa_funcion(codigo):
    print(triplo)
