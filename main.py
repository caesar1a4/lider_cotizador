import datetime
import math
import os
import re
import sys
import unicodedata

import calculos
import database
import generador_pdf
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
	QApplication,
	QAbstractItemView,
	QCheckBox,
	QComboBox,
	QDialog,
	QDoubleSpinBox,
	QFileDialog,
	QFormLayout,
	QFrame,
	QGridLayout,
	QGroupBox,
	QHBoxLayout,
	QHeaderView,
	QInputDialog,
	QLabel,
	QLineEdit,
	QMainWindow,
	QMessageBox,
	QPushButton,
	QRadioButton,
	QSpinBox,
	QStyledItemDelegate,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


def formatear_cantidad(valor: float) -> str:
	valor = float(valor)
	if valor.is_integer():
		return str(int(valor))
	return str(valor)


def formatear_moneda(valor: float) -> str:
	return f"${float(valor):,.2f}"


def limpiar_moneda(texto: str) -> float:
	try:
		return float(str(texto).replace("$", "").replace(",", "").strip())
	except (TypeError, ValueError):
		return 0.0


class DialogoBuscador(QDialog):
	def __init__(self, catalogo, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Buscar artículo")
		self.resize(600, 400)
		self.producto_seleccionado = None

		layout = QVBoxLayout(self)
		self.buscar_input = QLineEdit()
		self.buscar_input.setPlaceholderText("Buscar artículo...")
		layout.addWidget(self.buscar_input)

		self.tabla = QTableWidget(0, 3)
		self.tabla.setHorizontalHeaderLabels(["Categoría", "Artículo", "Precio"])
		self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
		self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
		self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
		layout.addWidget(self.tabla)

		botones = QHBoxLayout()
		self.btn_agregar = QPushButton("Agregar")
		self.btn_cancelar = QPushButton("Cancelar")
		botones.addStretch()
		botones.addWidget(self.btn_agregar)
		botones.addWidget(self.btn_cancelar)
		layout.addLayout(botones)

		for producto in catalogo:
			fila = self.tabla.rowCount()
			self.tabla.insertRow(fila)
			valores = (
				producto["categoria"] if isinstance(producto, dict) else producto[0],
				producto["articulo"] if isinstance(producto, dict) else producto[1],
				producto["precio"] if isinstance(producto, dict) else producto[2],
			)
			for columna, valor in enumerate(valores):
				self.tabla.setItem(fila, columna, QTableWidgetItem(str(valor)))

		self.buscar_input.textChanged.connect(self.filtrar_tabla)
		self.btn_agregar.clicked.connect(self.agregar_seleccion)
		self.btn_cancelar.clicked.connect(self.reject)
		self.tabla.doubleClicked.connect(self.agregar_seleccion)

	def filtrar_tabla(self, texto):
		texto = texto.casefold()
		for fila in range(self.tabla.rowCount()):
			coincide = any(
				texto in self.tabla.item(fila, columna).text().casefold()
				for columna in range(self.tabla.columnCount())
			)
			self.tabla.setRowHidden(fila, not coincide)

	def agregar_seleccion(self):
		fila = self.tabla.currentRow()
		if fila < 0:
			return
		self.producto_seleccionado = (
			self.tabla.item(fila, 0).text(),
			self.tabla.item(fila, 1).text(),
			float(self.tabla.item(fila, 2).text()),
		)
		self.accept()


class DialogoCliente(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Datos del Cliente (Opcional)")

		layout = QVBoxLayout(self)
		formulario = QFormLayout()
		self.nombre_input = QLineEdit()
		self.telefono_input = QLineEdit()
		self.fecha_input = QLineEdit()
		self.direccion_input = QLineEdit()
		campos = (
			(self.nombre_input, "Nombre"),
			(self.telefono_input, "Teléfono"),
			(self.fecha_input, "Fecha del Evento"),
			(self.direccion_input, "Dirección"),
		)
		for campo, etiqueta in campos:
			campo.setPlaceholderText("Opcional")
			formulario.addRow(f"{etiqueta}:", campo)
		layout.addLayout(formulario)

		botones = QHBoxLayout()
		btn_generar = QPushButton("Generar PDF")
		btn_cancelar = QPushButton("Cancelar")
		botones.addStretch()
		botones.addWidget(btn_generar)
		botones.addWidget(btn_cancelar)
		layout.addLayout(botones)

		btn_generar.clicked.connect(self.accept)
		btn_cancelar.clicked.connect(self.reject)

	def obtener_datos(self) -> dict:
		return {
			"nombre": self.nombre_input.text(),
			"telefono": self.telefono_input.text(),
			"fecha": self.fecha_input.text(),
			"direccion": self.direccion_input.text(),
		}


class DialogoGestorInventario(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Gestor de Inventario")
		self.setFixedSize(800, 600)
		self.gestor_bd = database.GestorBD()
		self.id_actual = None

		layout = QVBoxLayout(self)
		self.tabla_inventario = QTableWidget(0, 6)
		self.tabla_inventario.setHorizontalHeaderLabels(
			["ID", "Categoría", "Artículo", "Costo Prov.", "Precio Público", "Unidad"]
		)
		self.tabla_inventario.setColumnHidden(0, True)
		self.tabla_inventario.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.tabla_inventario.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.tabla_inventario.horizontalHeader().setSectionResizeMode(
			1, QHeaderView.ResizeToContents
		)
		self.tabla_inventario.horizontalHeader().setSectionResizeMode(
			2, QHeaderView.Stretch
		)
		layout.addWidget(self.tabla_inventario)

		grupo = QGroupBox("Datos del Artículo")
		formulario = QFormLayout(grupo)
		self.cmb_categoria = QComboBox()
		self.cmb_categoria.addItems(
			[
				"SILLAS",
				"MESAS",
				"SALAS",
				"MANTELERIA",
				"LOSA",
				"PISTAS",
				"DECO",
				"SERVICIOS",
				"CARPAS",
			]
		)
		self.txt_articulo = QLineEdit()
		self.spn_prov = QDoubleSpinBox()
		self.spn_pub = QDoubleSpinBox()
		for spin in (self.spn_prov, self.spn_pub):
			spin.setRange(0, 999999)
			spin.setPrefix("$ ")
			spin.setDecimals(2)
		self.cmb_unidad = QComboBox()
		self.cmb_unidad.addItems(["Pieza", "Paquete", "M2"])
		formulario.addRow("Categoría:", self.cmb_categoria)
		formulario.addRow("Artículo:", self.txt_articulo)
		formulario.addRow("Costo Prov.:", self.spn_prov)
		formulario.addRow("Precio Público:", self.spn_pub)
		formulario.addRow("Unidad:", self.cmb_unidad)
		layout.addWidget(grupo)

		botones = QHBoxLayout()
		self.btn_limpiar_inventario = QPushButton("Limpiar Campos")
		self.btn_guardar_inventario = QPushButton("Guardar / Actualizar Artículo")
		self.btn_eliminar_inventario = QPushButton("Eliminar Artículo")
		self.btn_eliminar_inventario.setStyleSheet(
			"QPushButton { color: white; background-color: #b3261e; }"
		)
		botones.addWidget(self.btn_limpiar_inventario)
		botones.addWidget(self.btn_guardar_inventario)
		botones.addWidget(self.btn_eliminar_inventario)
		layout.addLayout(botones)

		self.tabla_inventario.itemSelectionChanged.connect(
			self.cargar_fila_al_formulario
		)
		self.btn_limpiar_inventario.clicked.connect(self.limpiar_campos)
		self.btn_guardar_inventario.clicked.connect(self.guardar_articulo)
		self.btn_eliminar_inventario.clicked.connect(self.eliminar_articulo)
		self.cargar_datos()

	def cargar_datos(self):
		productos = self.gestor_bd.obtener_todos_productos()
		self.tabla_inventario.setRowCount(0)
		for fila, producto in enumerate(productos):
			self.tabla_inventario.insertRow(fila)
			valores = (
				producto["id"],
				producto["categoria"],
				producto["articulo"],
				producto["precio_proveedor"],
				producto["precio_publico"],
				producto["unidad_medida"],
			)
			for columna, valor in enumerate(valores):
				self.tabla_inventario.setItem(
					fila, columna, QTableWidgetItem(str(valor))
				)
		self.tabla_inventario.clearSelection()

	def cargar_fila_al_formulario(self):
		fila = self.tabla_inventario.currentRow()
		if fila < 0:
			return
		try:
			self.id_actual = int(self.tabla_inventario.item(fila, 0).text())
			self.cmb_categoria.setCurrentText(self.tabla_inventario.item(fila, 1).text())
			self.txt_articulo.setText(self.tabla_inventario.item(fila, 2).text())
			self.spn_prov.setValue(float(self.tabla_inventario.item(fila, 3).text()))
			self.spn_pub.setValue(float(self.tabla_inventario.item(fila, 4).text()))
			self.cmb_unidad.setCurrentText(self.tabla_inventario.item(fila, 5).text())
		except (AttributeError, TypeError, ValueError):
			self.limpiar_campos()

	def limpiar_campos(self):
		self.id_actual = None
		self.tabla_inventario.clearSelection()
		self.cmb_categoria.setCurrentIndex(0)
		self.txt_articulo.clear()
		self.spn_prov.setValue(0)
		self.spn_pub.setValue(0)
		self.cmb_unidad.setCurrentIndex(0)

	def guardar_articulo(self):
		articulo = self.txt_articulo.text().strip()
		if not articulo:
			QMessageBox.warning(self, "Datos incompletos", "Escribe el nombre del artículo.")
			return

		valores = (
			self.cmb_categoria.currentText(),
			articulo,
			self.spn_prov.value(),
			self.spn_pub.value(),
			self.cmb_unidad.currentText(),
		)
		if self.id_actual is None:
			self.gestor_bd.insertar_producto(*valores)
		else:
			self.gestor_bd.actualizar_producto(self.id_actual, *valores)
		self.cargar_datos()
		self.limpiar_campos()

	def eliminar_articulo(self):
		if self.id_actual is None:
			QMessageBox.warning(self, "Sin selección", "Selecciona un artículo para eliminar.")
			return
		respuesta = QMessageBox.question(
			self,
			"Confirmar eliminación",
			"¿Deseas eliminar el artículo seleccionado?",
			QMessageBox.Yes | QMessageBox.No,
			QMessageBox.No,
		)
		if respuesta == QMessageBox.Yes:
			self.gestor_bd.eliminar_producto(self.id_actual)
			self.cargar_datos()
			self.limpiar_campos()


class DelegadoEdicion(QStyledItemDelegate):
	def __init__(self, parent=None):
		super().__init__(parent)

	def setModelData(self, editor, model, index):
		self.parent().guardar_estado()
		super().setModelData(editor, model, index)


class VentanaPrincipal(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Cotizador Interno - Alquiladora LIDER")
		self.resize(1200, 800)
		self.historial_estados = []
		self.gestor_bd = database.GestorBD()
		self._crear_interfaz()
		self._conectar_eventos()
		self.actualizar_sugerencias()
		self.alternar_precio_decoracion()

	def _crear_interfaz(self):
		central = QWidget()
		self.setCentralWidget(central)

		layout_principal = QHBoxLayout(central)
		layout_principal.setContentsMargins(16, 16, 16, 16)
		layout_principal.setSpacing(16)
		layout_principal.addWidget(self._crear_panel_izquierdo())
		layout_principal.addLayout(self._crear_panel_derecho(), 1)

	def _crear_panel_izquierdo(self):
		panel = QGroupBox("Dimensionamiento Dinámico")
		panel.setFixedWidth(350)
		layout = QVBoxLayout(panel)

		formulario = QFormLayout()
		self.spin_invitados = QSpinBox()
		self.spin_invitados.setRange(0, 5000)
		self.spin_invitados.setSuffix(" invitados")

		self.spin_factor = QSpinBox()
		self.spin_factor.setRange(0, 500)
		self.spin_factor.setValue(70)
		self.spin_factor.setSuffix(" m² extra")

		self.combo_estilo = QComboBox()
		self.combo_estilo.addItems(["Sencilla", "Decorada", "Plisada"])

		self.spn_precio_base_carpa = QDoubleSpinBox()
		self.spn_precio_base_carpa.setRange(0, 1000)
		self.spn_precio_base_carpa.setPrefix("$ ")
		self.spn_precio_base_carpa.setValue(32.00)

		self.spn_precio_decoracion = QDoubleSpinBox()
		self.spn_precio_decoracion.setRange(0, 1000)
		self.spn_precio_decoracion.setPrefix("$ ")
		self.spn_precio_decoracion.setValue(15.00)

		formulario.addRow("Invitados:", self.spin_invitados)
		formulario.addRow("Factor de Espacio extra:", self.spin_factor)
		formulario.addRow("Estilo:", self.combo_estilo)
		formulario.addRow("Precio Base (m2):", self.spn_precio_base_carpa)
		formulario.addRow("Costo Decoración (m2):", self.spn_precio_decoracion)
		layout.addLayout(formulario)

		opciones_carpa = QGroupBox("Opciones de Carpa")
		grid = QGridLayout(opciones_carpa)
		self.lbl_minimo_m2 = QLabel("Mínimo: 0 m2")
		self.lbl_minimo_m2.setAlignment(Qt.AlignRight)
		grid.addWidget(self.lbl_minimo_m2, 0, 0, 1, 3)

		self.radios_ancho = []
		self.spins_largo = []
		self.lbls_area = []
		self.anchos_carpa = [8, 10, 12, 15]
		for fila, ancho in enumerate(self.anchos_carpa, start=1):
			radio = QRadioButton(f"Ancho {ancho}m")
			radio.toggled.connect(self.activar_boton_sugerencias)
			if fila == 1:
				radio.setChecked(True)
			spin_largo = QSpinBox()
			spin_largo.setRange(0, 500)
			spin_largo.setSingleStep(5)
			spin_largo.setPrefix("Largo: ")
			spin_largo.setSuffix("m")
			spin_largo.valueChanged.connect(self.recalcular_area_manual)
			spin_largo.valueChanged.connect(self.activar_boton_sugerencias)
			lbl_area = QLabel(" = 0 m2")
			self.radios_ancho.append(radio)
			self.spins_largo.append(spin_largo)
			self.lbls_area.append(lbl_area)
			grid.addWidget(radio, fila, 0)
			grid.addWidget(spin_largo, fila, 1)
			grid.addWidget(lbl_area, fila, 2)

		layout.addWidget(opciones_carpa)

		resultados = QFrame()
		resultados.setFrameShape(QFrame.StyledPanel)
		resultados.setStyleSheet(
			"QFrame { background-color: #eef6f0; border: 1px solid #a9c9b0; "
			"border-radius: 6px; }"
		)
		resultados_layout = QVBoxLayout(resultados)
		fuente_resultados = QFont()
		fuente_resultados.setBold(True)
		fuente_resultados.setPointSize(11)

		self.chk_carpa = QCheckBox("Incluir Sugerencia de Carpa")
		self.chk_carpa.setChecked(True)
		self.lbl_carpa = QLabel("Carpa Sugerida: --")
		self.lbl_carpa.setFont(fuente_resultados)
		resultados_layout.addWidget(self.chk_carpa)
		resultados_layout.addWidget(self.lbl_carpa)

		self.chk_mesas = QCheckBox("Incluir Sugerencia de Mesas")
		self.chk_mesas.setChecked(True)
		self.lbl_mesas = QLabel("Mesas Base: --")
		self.lbl_mesas.setFont(fuente_resultados)
		resultados_layout.addWidget(self.chk_mesas)
		self.combo_paquete_mesas = QComboBox()
		self.combo_paquete_mesas.addItem("Mesa c/10 Plegables", 140.0)
		self.combo_paquete_mesas.addItem("Mesa c/10 Plegables Vestidas", 250.0)
		self.combo_paquete_mesas.addItem("Mesa c/10 Tiffany", 380.0)
		resultados_layout.addWidget(self.combo_paquete_mesas)

		self.chk_pista = QCheckBox("Incluir Sugerencia de Pista")
		self.chk_pista.setChecked(True)
		self.lbl_pista = QLabel("Pista Sugerida: --")
		self.lbl_pista.setFont(fuente_resultados)
		resultados_layout.addWidget(self.chk_pista)
		self.combo_tipo_pista = QComboBox()
		resultados_layout.addWidget(self.combo_tipo_pista)

		layout.addWidget(resultados)
		layout.addStretch()
		self.btn_inventario = QPushButton("⚙️ Gestor de Inventario")
		layout.addWidget(self.btn_inventario)
		self.aplicar_button = QPushButton("Aplicar Sugerencias al Carrito")
		self.aplicar_button.setMinimumHeight(48)
		layout.addWidget(self.aplicar_button)

		return panel

	def _crear_panel_derecho(self):
		layout = QVBoxLayout()
		acciones = QHBoxLayout()
		self.btn_agregar_manual = QPushButton("+ Agregar Artículo Manual")
		self.btn_eliminar_fila = QPushButton("- Eliminar Fila Seleccionada")
		self.btn_limpiar = QPushButton("🗑 Limpiar Cotización")
		self.btn_deshacer = QPushButton("↩ Deshacer")
		acciones.addWidget(self.btn_agregar_manual)
		acciones.addWidget(self.btn_eliminar_fila)
		acciones.addWidget(self.btn_limpiar)
		acciones.addWidget(self.btn_deshacer)
		acciones.addStretch()
		layout.addLayout(acciones)

		self.tabla = QTableWidget(0, 5)
		self.carrito_table = self.tabla
		self.tabla.setHorizontalHeaderLabels(
			["Categoría", "Artículo", "Cantidad", "P. Unitario", "Subtotal"]
		)
		delegado = DelegadoEdicion(self)
		self.tabla.setItemDelegateForColumn(2, delegado)
		self.tabla.setItemDelegateForColumn(3, delegado)
		encabezado = self.tabla.horizontalHeader()
		encabezado.setSectionResizeMode(0, QHeaderView.ResizeToContents)
		encabezado.setSectionResizeMode(1, QHeaderView.Stretch)
		encabezado.setSectionResizeMode(2, QHeaderView.ResizeToContents)
		encabezado.setSectionResizeMode(3, QHeaderView.ResizeToContents)
		encabezado.setSectionResizeMode(4, QHeaderView.ResizeToContents)
		layout.addWidget(self.tabla, 1)

		self.lbl_total = QLabel("TOTAL: $0.00")
		fuente_total = QFont()
		fuente_total.setBold(True)
		fuente_total.setPointSize(24)
		self.lbl_total.setFont(fuente_total)
		self.lbl_total.setStyleSheet("color: #176b3a;")
		self.lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		barra_total = QHBoxLayout()
		self.btn_generar_pdf = QPushButton("📄 Generar PDF")
		barra_total.addWidget(self.btn_generar_pdf)
		barra_total.addStretch()
		barra_total.addWidget(self.lbl_total)
		layout.addLayout(barra_total)
		return layout

	def _conectar_eventos(self):
		self.spin_invitados.valueChanged.connect(self.actualizar_sugerencias)
		self.spin_factor.valueChanged.connect(self.actualizar_sugerencias)
		self.aplicar_button.clicked.connect(self.aplicar_al_carrito)
		self.btn_agregar_manual.clicked.connect(self.abrir_buscador)
		self.btn_eliminar_fila.clicked.connect(self.eliminar_fila)
		self.btn_limpiar.clicked.connect(self.limpiar_cotizacion)
		self.btn_deshacer.clicked.connect(self.deshacer)
		self.btn_generar_pdf.clicked.connect(self.abrir_dialogo_pdf)
		self.btn_inventario.clicked.connect(self.abrir_gestor_inventario)
		self.tabla.cellChanged.connect(self.recalcular_fila)
		for radio in self.radios_ancho:
			radio.toggled.connect(self.actualizar_sugerencias)
		for spin in [self.spin_invitados, self.spin_factor]:
			spin.valueChanged.connect(self.activar_boton_sugerencias)
		for combo in [
			self.combo_estilo,
			self.combo_paquete_mesas,
			self.combo_tipo_pista,
		]:
			combo.currentIndexChanged.connect(self.activar_boton_sugerencias)
		self.combo_estilo.currentIndexChanged.connect(self.alternar_precio_decoracion)
		self.spn_precio_base_carpa.valueChanged.connect(
			self.activar_boton_sugerencias
		)
		self.spn_precio_decoracion.valueChanged.connect(
			self.activar_boton_sugerencias
		)
		for checkbox in [self.chk_carpa, self.chk_mesas, self.chk_pista]:
			checkbox.stateChanged.connect(self.activar_boton_sugerencias)

	def abrir_gestor_inventario(self):
		dialogo = DialogoGestorInventario(self)
		dialogo.exec()

	def alternar_precio_decoracion(self):
		es_sencilla = self.combo_estilo.currentText() == "Sencilla"
		self.spn_precio_decoracion.setEnabled(not es_sencilla)

	def actualizar_sugerencias(self):
		invitados = self.spin_invitados.value()
		factor_espacio = self.spin_factor.value()
		m2_minimos = invitados + factor_espacio
		self.lbl_minimo_m2.setText(f"Mínimo: {m2_minimos} m2")

		for ancho, radio, spin_largo, lbl_area in zip(
			self.anchos_carpa,
			self.radios_ancho,
			self.spins_largo,
			self.lbls_area,
		):
			largo_sugerido = math.ceil((m2_minimos / ancho) / 5.0) * 5
			spin_largo.blockSignals(True)
			spin_largo.setValue(largo_sugerido)
			spin_largo.blockSignals(False)
			lbl_area.setText(f"({ancho}x{largo_sugerido}) = {ancho * largo_sugerido} m2")

		_, dimensiones_pista = calculos.calcular_pista(invitados)
		self.combo_tipo_pista.blockSignals(True)
		self.combo_tipo_pista.clear()
		self.combo_tipo_pista.addItem(f"Pista de Madera ({dimensiones_pista})", 90.0)
		self.combo_tipo_pista.addItem(
			f"Pista Iluminada ({dimensiones_pista})", 290.0
		)
		self.combo_tipo_pista.addItem(f"Pista Mixta ({dimensiones_pista})", 0.0)
		self.combo_tipo_pista.blockSignals(False)
		mesas = math.ceil(invitados / 10)
		self.lbl_pista.setText(f"Pista Sugerida: {dimensiones_pista}")
		self.lbl_mesas.setText(f"Mesas Base: {mesas}")
		for ancho, radio, spin_largo, _ in zip(
			self.anchos_carpa,
			self.radios_ancho,
			self.spins_largo,
			self.lbls_area,
		):
			if radio.isChecked():
				self.lbl_carpa.setText(
					f"Carpa Sugerida: {ancho}m x {spin_largo.value()}m"
				)
				break

	def recalcular_area_manual(self, _valor):
		spin_largo = self.sender()
		for ancho, spin, lbl_area in zip(
			self.anchos_carpa, self.spins_largo, self.lbls_area
		):
			if spin is spin_largo:
				lbl_area.setText(
					f"({ancho}x{spin.value()}) = {ancho * spin.value()} m2"
				)
				if self.radios_ancho[self.spins_largo.index(spin)].isChecked():
					self.lbl_carpa.setText(
						f"Carpa Sugerida: {ancho}m x {spin.value()}m"
					)
				break

	def aplicar_al_carrito(self):
		seleccion = next(
			(
				(ancho, spin_largo)
				for ancho, radio, spin_largo in zip(
					self.anchos_carpa, self.radios_ancho, self.spins_largo
				)
				if radio.isChecked()
			),
			None,
		)
		if seleccion is None:
			return

		self.guardar_estado()
		for fila in range(self.tabla.rowCount() - 1, -1, -1):
			item_categoria = self.tabla.item(fila, 0)
			if item_categoria and item_categoria.data(Qt.UserRole) is True:
				self.tabla.removeRow(fila)

		ancho, spin_largo = seleccion
		largo = spin_largo.value()
		area_carpa = ancho * largo
		estilo = self.combo_estilo.currentText()
		if self.chk_carpa.isChecked():
			precio_base = self.spn_precio_base_carpa.value()
			precio_deco = (
				self.spn_precio_decoracion.value()
				if estilo in ["Decorada", "Plisada"]
				else 0.0
			)
			precio_final_m2 = precio_base + precio_deco
			self.agregar_fila_tabla(
				"CARPAS",
				f"Carpa {estilo} {ancho}x{largo}m",
				area_carpa,
				precio_final_m2,
				es_sugerencia=True,
			)

		invitados = self.spin_invitados.value()
		if self.chk_mesas.isChecked():
			precio_mesa = self.combo_paquete_mesas.currentData()
			nombre_mesa = self.combo_paquete_mesas.currentText()
			self.agregar_fila_tabla(
				"MESAS",
				nombre_mesa,
				math.ceil(invitados / 10),
				precio_mesa,
				es_sugerencia=True,
			)

		if self.chk_pista.isChecked():
			area_pista, dimensiones_pista = calculos.calcular_pista(invitados)
			precio_pista = self.combo_tipo_pista.currentData()
			tipo_pista = self.combo_tipo_pista.currentText()
			self.agregar_fila_tabla(
				"PISTAS",
				tipo_pista,
				area_pista,
				precio_pista,
				es_sugerencia=True,
			)
		self.aplicar_button.setText("Sugerencias Aplicadas")
		self.aplicar_button.setEnabled(False)
		self.calcular_total()

	def agregar_fila_tabla(
		self, categoria, articulo, cantidad, precio_unitario, es_sugerencia=False
	):
		self.tabla.blockSignals(True)
		try:
			fila = self.tabla.rowCount()
			self.tabla.insertRow(fila)
			subtotal = float(cantidad) * float(precio_unitario)
			valores = (
				str(categoria),
				str(articulo),
				formatear_cantidad(cantidad),
				formatear_moneda(precio_unitario),
				formatear_moneda(subtotal),
			)
			for columna, valor in enumerate(valores):
				item = QTableWidgetItem(valor)
				if columna == 0 and es_sugerencia:
					item.setData(Qt.UserRole, True)
				if columna not in (2, 3):
					item.setFlags(item.flags() & ~Qt.ItemIsEditable)
				self.tabla.setItem(fila, columna, item)
		finally:
			self.tabla.blockSignals(False)

	def recalcular_fila(self, row, col):
		if col not in (2, 3):
			return
		try:
			cantidad = float(self.tabla.item(row, 2).text())
			precio = limpiar_moneda(self.tabla.item(row, 3).text())
		except (AttributeError, ValueError):
			return

		self.tabla.blockSignals(True)
		try:
			nuevo_subtotal = cantidad * precio
			self.tabla.setItem(
				row, 4, QTableWidgetItem(formatear_moneda(nuevo_subtotal))
			)
		finally:
			self.tabla.blockSignals(False)
		self.calcular_total()

	def limpiar_cotizacion(self):
		self.guardar_estado()
		self.tabla.setRowCount(0)
		self.calcular_total()

	def eliminar_fila(self):
		fila = self.tabla.currentRow()
		if fila >= 0:
			self.guardar_estado()
			item_categoria = self.tabla.item(fila, 0)
			if item_categoria and item_categoria.data(Qt.UserRole) is True:
				self.activar_boton_sugerencias()
			self.tabla.removeRow(fila)
			self.calcular_total()

	def abrir_buscador(self):
		with self.gestor_bd._conectar() as conexion:
			catalogo = conexion.execute(
				"""
				SELECT categoria, articulo, precio_publico AS precio
				FROM Catalogo_Productos
				"""
			).fetchall()

		dialogo = DialogoBuscador(catalogo, self)
		if dialogo.exec() != QDialog.Accepted:
			return

		categoria, articulo, precio = dialogo.producto_seleccionado
		cantidad, aceptado = QInputDialog.getDouble(
			self, "Cantidad", "Ingrese la cantidad:", 1.0, 0.0, 100000.0, 2
		)
		if aceptado:
			self.guardar_estado()
			self.agregar_fila_tabla(categoria, articulo, cantidad, precio)
			self.calcular_total()

	def generar_nombre_pdf(self, datos_cliente: dict, partidas: list) -> str:
		def sanitizar(texto):
			texto = (
				unicodedata.normalize("NFKD", str(texto))
				.encode("ASCII", "ignore")
				.decode("utf-8")
			)
			return re.sub(r"[^A-Za-z0-9]", "_", texto)

		articulo_principal = "Articulo"
		mayor_subtotal = float("-inf")
		for partida in partidas:
			try:
				subtotal = float(
					str(partida[4]).replace("$", "").replace(",", "").strip()
				)
			except (IndexError, TypeError, ValueError):
				continue
			if subtotal > mayor_subtotal:
				mayor_subtotal = subtotal
				articulo_principal = sanitizar(partida[1]) or "Articulo"

		nombre_cliente = datos_cliente.get("nombre", "")
		nombre_cliente = (
			sanitizar(str(nombre_cliente).split()[0])
			if str(nombre_cliente).strip()
			else ""
		)
		fecha = datetime.date.today().strftime("%Y-%m-%d")
		nombre_base = f"COT_{fecha}_{articulo_principal}"
		if nombre_cliente:
			nombre_base += f"_{nombre_cliente}"

		carpeta = os.path.join(os.getcwd(), "Cotizaciones")
		os.makedirs(carpeta, exist_ok=True)
		ruta_final = os.path.join(carpeta, f"{nombre_base}.pdf")
		contador = 1
		while os.path.exists(ruta_final):
			ruta_final = os.path.join(carpeta, f"{nombre_base}_{contador}.pdf")
			contador += 1
		return ruta_final

	def abrir_dialogo_pdf(self):
		if self.tabla.rowCount() == 0:
			QMessageBox.warning(
				self,
				"Carrito vacío",
				"Agrega al menos una partida antes de generar el PDF.",
			)
			return

		dialogo = DialogoCliente(self)
		if dialogo.exec() != QDialog.Accepted:
			return

		datos_cliente = dialogo.obtener_datos()
		partidas = []
		for fila in range(self.tabla.rowCount()):
			partidas.append(
				[
					self.tabla.item(fila, columna).text()
					for columna in range(self.tabla.columnCount())
				]
			)

		ruta_sugerida = self.generar_nombre_pdf(datos_cliente, partidas)
		ruta_salida, _ = QFileDialog.getSaveFileName(
			self,
			"Guardar Cotización",
			ruta_sugerida,
			"Archivos PDF (*.pdf)",
		)
		if not ruta_salida:
			return
		if not ruta_salida.lower().endswith(".pdf"):
			ruta_salida += ".pdf"

		generador_pdf.generar_cotizacion_pdf(
			datos_cliente,
			partidas,
			self.lbl_total.text(),
			ruta_salida,
		)
		QMessageBox.information(
			self,
			"PDF generado",
			f"La cotización se guardó correctamente en:\n{ruta_salida}",
		)

	def guardar_estado(self):
		estado = []
		for fila in range(self.tabla.rowCount()):
			items = [self.tabla.item(fila, columna) for columna in range(5)]
			estado.append(
				{
					"valores": [item.text() if item else "" for item in items],
					"es_sugerencia": bool(
						items[0] and items[0].data(Qt.UserRole) is True
					),
				}
			)
		self.historial_estados.append(estado)
		if len(self.historial_estados) > 20:
			self.historial_estados.pop(0)

	def deshacer(self):
		if not self.historial_estados:
			return
		estado = self.historial_estados.pop()
		self.tabla.blockSignals(True)
		try:
			self.tabla.setRowCount(0)
			for fila, registro in enumerate(estado):
				self.tabla.insertRow(fila)
				for columna, valor in enumerate(registro["valores"]):
					item = QTableWidgetItem(valor)
					if columna == 0 and registro["es_sugerencia"]:
						item.setData(Qt.UserRole, True)
					if columna not in (2, 3):
						item.setFlags(item.flags() & ~Qt.ItemIsEditable)
					self.tabla.setItem(fila, columna, item)
		finally:
			self.tabla.blockSignals(False)
		self.calcular_total()

	def activar_boton_sugerencias(self, *_args):
		if not hasattr(self, "aplicar_button"):
			return
		self.aplicar_button.setText("Actualizar Sugerencias")
		self.aplicar_button.setEnabled(True)

	def calcular_total(self):
		total = 0.0
		for fila in range(self.tabla.rowCount()):
			subtotal = self.tabla.item(fila, 4).text()
			total += limpiar_moneda(subtotal)
		self.lbl_total.setText(f"TOTAL: {formatear_moneda(total)}")


if __name__ == "__main__":
	app = QApplication(sys.argv)
	ventana = VentanaPrincipal()
	ventana.show()
	sys.exit(app.exec())
