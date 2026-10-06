import pandas as pd

from database import GestorBD


gestor = GestorBD()
datos = pd.read_excel("LIDER.xlsx", sheet_name="INVENTARIO")

columnas_numericas = datos.select_dtypes(include="number").columns
columnas_texto = datos.select_dtypes(exclude="number").columns
datos[columnas_numericas] = datos[columnas_numericas].fillna(0)
datos[columnas_texto] = datos[columnas_texto].fillna("")

for indice, fila in datos.iterrows():
    try:
        gestor.insertar_producto(
            fila["Categoría"],
            fila["Artículo"],
            fila["Precio Proveedor"],
            fila["Precio Público"],
            fila["Unidad de Medida"],
        )
    except Exception as error:
        print(f"Error en la fila {indice}: {error}")

print("Importación completada con éxito")