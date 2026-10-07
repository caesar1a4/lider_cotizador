import sqlite3

def actualizar_base_datos():
    conexion = sqlite3.connect('cotizador.db')
    cursor = conexion.cursor()
    try:
        # Inyectamos la columna usando el nombre exacto de tu tabla
        cursor.execute("ALTER TABLE Catalogo_Productos ADD COLUMN descripcion TEXT DEFAULT ''")
        print("¡Columna 'descripcion' agregada con éxito a Catalogo_Productos!")
    except sqlite3.OperationalError as e:
        print("Aviso:", e) # Si ya existe, te avisará sin causar problemas
    
    conexion.commit()
    conexion.close()

if __name__ == "__main__":
    actualizar_base_datos()