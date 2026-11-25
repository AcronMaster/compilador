import tkinter as tk
from tkinter import messagebox

from interfaz import CompiladorGUI
from semantic import analizar
from Triplos import GeneradorTriplos
from exportador import exportar_excel


def ejecutar_analisis(codigo, interfaz):

    try:

        # ==============================================
        # EJECUTAR ANALIZADOR SEMÁNTICO
        # ==============================================

        tabla, errores = analizar(codigo)

        # ==============================================
        # ENVIAR RESULTADOS A LA INTERFAZ
        # ==============================================

        interfaz.mostrar_resultados(
            tabla,
            errores
        )

    except Exception as e:

        messagebox.showerror(
            "Error",
            f"Falló el análisis:\n{e}"
        )

def ejecutar_triplos(codigo, interfaz):
    try:
        generador = GeneradorTriplos()
        triplos = generador.generar_programa_funcion(codigo)

        encabezados = [
            "Número",
            "Dato objeto",
            "Dato fuente",
            "Operador"
        ]

        ruta = exportar_excel(
            encabezados,
            triplos,
            "triplos.xlsx"
        )

        interfaz.estado.set(
            f"Triplos exportados: {ruta}"
        )

        messagebox.showinfo(
            "Triplos generados",
            f"Se guardaron los triplos en:\n{ruta}"
        )

    except Exception as e:
        messagebox.showerror(
            "Error al generar triplos",
            str(e)
        )

def main():

    # ==============================================
    # CREAR VENTANA
    # ==============================================

    root = tk.Tk()

    # ==============================================
    # CREAR INTERFAZ
    # ==============================================

    interfaz = CompiladorGUI(
        root
    )

    # ==============================================
    # CONECTAR BOTÓN ANALIZAR
    # ==============================================

    interfaz.callback_analizar = lambda codigo: ejecutar_analisis(
        codigo,
        interfaz
    )

    interfaz.callback_triplos = lambda codigo: ejecutar_triplos(
        codigo,
        interfaz
    )

    # ==============================================
    # INICIAR APLICACIÓN
    # ==============================================

    root.mainloop()


if __name__ == "__main__":
    main()