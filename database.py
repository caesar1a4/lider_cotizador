import sqlite3
from contextlib import contextmanager


class GestorBD:
	def __init__(self, ruta_bd="cotizador.db"):
		self.ruta_bd = ruta_bd
		self._crear_tablas()

	@contextmanager
	def _conectar(self):
		conexion = sqlite3.connect(self.ruta_bd)
		conexion.row_factory = sqlite3.Row
		try:
			with conexion:
				yield conexion
		finally:
			conexion.close()

	def _crear_tablas(self):
		with self._conectar() as conexion:
			conexion.execute(
				"""
				CREATE TABLE IF NOT EXISTS Catalogo_Productos (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					categoria TEXT NOT NULL,
					articulo TEXT NOT NULL,
					precio_proveedor REAL DEFAULT 0.0,
					precio_publico REAL NOT NULL,
					unidad_medida TEXT NOT NULL
				)
				"""
			)

	def insertar_producto(
		self,
		categoria,
		articulo,
		precio_proveedor,
		precio_publico,
		unidad_medida,
	):
		with self._conectar() as conexion:
			cursor = conexion.execute(
				"""
				INSERT INTO Catalogo_Productos (
					categoria,
					articulo,
					precio_proveedor,
					precio_publico,
					unidad_medida
				) VALUES (?, ?, ?, ?, ?)
				""",
				(
					categoria,
					articulo,
					precio_proveedor,
					precio_publico,
					unidad_medida,
				),
			)
			return cursor.lastrowid

	def obtener_todos_productos(self):
		with self._conectar() as conn:
			cursor = conn.cursor()
			cursor.execute(
				"""
				SELECT * FROM Catalogo_Productos
				ORDER BY categoria, articulo
				"""
			)
			return cursor.fetchall()

	def actualizar_producto(
		self,
		id_producto: int,
		categoria: str,
		articulo: str,
		precio_prov: float,
		precio_pub: float,
		unidad: str,
	):
		with self._conectar() as conn:
			conn.execute(
				"""
				UPDATE Catalogo_Productos
				SET categoria=?, articulo=?, precio_proveedor=?,
					precio_publico=?, unidad_medida=?
				WHERE id=?
				""",
				(
					categoria,
					articulo,
					precio_prov,
					precio_pub,
					unidad,
					id_producto,
				),
			)

	def eliminar_producto(self, id_producto: int):
		with self._conectar() as conn:
			conn.execute(
				"DELETE FROM Catalogo_Productos WHERE id=?",
				(id_producto,),
			)
