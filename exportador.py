
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


def exportar_excel(encabezados, filas, nombre_archivo="triplos.xlsx"):
    """Exporta una tabla a un archivo Excel."""

    carpeta_salida = Path("resultados")
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    ruta_archivo = carpeta_salida / nombre_archivo

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Triplos"

    # Encabezados de la tabla
    hoja.append(encabezados)

    # Datos de la tabla
    for fila in filas:
        hoja.append(fila)

    # Formato básico del encabezado
    for celda in hoja[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill(
            fill_type="solid",
            fgColor="252538"
        )
        celda.alignment = Alignment(horizontal="center")

    # Ajustar ancho de columnas
    for columna in hoja.columns:
        letra = columna[0].column_letter
        ancho = max(
            len(str(celda.value or "")) for celda in columna
        )
        hoja.column_dimensions[letra].width = min(ancho + 4, 35)

    libro.save(ruta_archivo)
    return ruta_archivo
