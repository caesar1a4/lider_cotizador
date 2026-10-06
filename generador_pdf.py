import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
	Paragraph,
	Spacer,
	Table,
	TableStyle,
	SimpleDocTemplate,
)
from svglib.svglib import svg2rlg


def _valor_partida(partida, indice, *claves):
	"""Obtiene un valor de una partida, ya sea diccionario o tupla."""
	if isinstance(partida, dict):
		for clave in claves:
			if clave in partida:
				return partida[clave]
		return ""

	try:
		return partida[indice]
	except (IndexError, KeyError, TypeError):
		return ""


def _texto(valor, predeterminado=""):
	if valor is None or str(valor).strip() == "":
		return predeterminado
	return str(valor)


def generar_cotizacion_pdf(
	datos_cliente: dict,
	partidas: list,
	total: str,
	ruta_salida: str = "cotizacion.pdf",
):
	"""Genera una cotizacion en formato Letter y la guarda en ``ruta_salida``."""
	datos_cliente = datos_cliente or {}
	doc = SimpleDocTemplate(
		ruta_salida,
		pagesize=LETTER,
		rightMargin=0.55 * inch,
		leftMargin=0.55 * inch,
		topMargin=0.5 * inch,
		bottomMargin=0.5 * inch,
	)
	estilos = getSampleStyleSheet()
	estilo_titulo = ParagraphStyle(
		"TituloCotizacion",
		parent=estilos["Title"],
		fontName="Helvetica-Bold",
		fontSize=25,
		leading=29,
		textColor=colors.HexColor("#17324D"),
		spaceAfter=2,
	)
	estilo_subtitulo = ParagraphStyle(
		"SubtituloCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica",
		fontSize=12,
		textColor=colors.HexColor("#527087"),
	)
	estilo_cliente = ParagraphStyle(
		"DatosCliente",
		parent=estilos["Normal"],
		fontName="Helvetica",
		fontSize=9.5,
		leading=15,
	)
	estilo_celda = ParagraphStyle(
		"CeldaCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica",
		fontSize=9,
		leading=11,
	)
	estilo_total = ParagraphStyle(
		"TotalCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica-Bold",
		fontSize=16,
		leading=20,
		alignment=TA_RIGHT,
		textColor=colors.HexColor("#17324D"),
	)

	if hasattr(sys, '_MEIPASS'):
    	base_dir = sys._MEIPASS
	else:
    	base_dir = os.path.dirname(os.path.abspath(__file__))

ruta_logo = os.path.join(base_dir, "logo.svg")
	contenido = []
	if os.path.exists(ruta_logo):
		dibujo_logo = svg2rlg(ruta_logo)
		if dibujo_logo and dibujo_logo.height:
			factor = min(1, 70 / dibujo_logo.height)
			dibujo_logo.width *= factor
			dibujo_logo.height *= factor
			dibujo_logo.scale(factor, factor)
			contenido.extend([dibujo_logo, Spacer(1, 0.08 * inch)])

	contenido.extend([
		Paragraph("COTIZACIÓN", estilo_titulo),
		Paragraph("Alquiladora LIDER", estilo_subtitulo),
		Spacer(1, 0.18 * inch),
	])

	nombres_cliente = (
		("Nombre", ("nombre", "name")),
		("Teléfono", ("telefono", "teléfono", "phone")),
		("Fecha", ("fecha", "date")),
		("Dirección", ("direccion", "dirección", "address")),
	)
	cliente_filas = []
	for etiqueta, claves in nombres_cliente:
		valor = next((datos_cliente.get(clave) for clave in claves if clave in datos_cliente), None)
		cliente_filas.append(
			Paragraph(
				f"<b>{etiqueta}:</b> {_texto(valor, 'No especificado')}",
				estilo_cliente,
			)
		)

	cliente = Table(
		[cliente_filas[:2], cliente_filas[2:]],
		colWidths=[3.55 * inch, 3.55 * inch],
		rowHeights=[0.23 * inch, 0.23 * inch],
	)
	cliente.setStyle(
		TableStyle(
			[
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("LEFTPADDING", (0, 0), (-1, -1), 0),
				("RIGHTPADDING", (0, 0), (-1, -1), 12),
				("TOPPADDING", (0, 0), (-1, -1), 0),
				("BOTTOMPADDING", (0, 0), (-1, -1), 0),
			]
		)
	)
	contenido.extend([cliente, Spacer(1, 0.25 * inch)])

	encabezados = ["Categoría", "Artículo", "Cant.", "P.U.", "Subtotal"]
	filas = [encabezados]
	for partida in partidas or []:
		filas.append(
			[
				_texto(_valor_partida(partida, 0, "categoria", "categoría", "category")),
				_texto(_valor_partida(partida, 1, "articulo", "artículo", "item")),
				_texto(_valor_partida(partida, 2, "cantidad", "cant", "quantity")),
				_texto(_valor_partida(partida, 3, "precio_unitario", "pu", "precio", "price")),
				_texto(_valor_partida(partida, 4, "subtotal", "importe")),
			]
		)

	filas_formateadas = [
		[Paragraph(f"<b>{celda}</b>", estilo_celda) for celda in filas[0]]
	]
	filas_formateadas.extend(
		[[Paragraph(celda, estilo_celda) for celda in fila] for fila in filas[1:]]
	)
	tabla = Table(
		filas_formateadas,
		colWidths=[1.28 * inch, 2.42 * inch, 0.62 * inch, 1.08 * inch, 1.7 * inch],
		repeatRows=1,
	)
	tabla.setStyle(
		TableStyle(
			[
				("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
				("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("ALIGN", (2, 1), (-1, -1), "RIGHT"),
				("ALIGN", (2, 0), (-1, 0), "RIGHT"),
				("LEFTPADDING", (0, 0), (-1, -1), 7),
				("RIGHTPADDING", (0, 0), (-1, -1), 7),
				("TOPPADDING", (0, 0), (-1, -1), 7),
				("BOTTOMPADDING", (0, 0), (-1, -1), 7),
				("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#17324D")),
				("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.HexColor("#D5DDE3")),
			]
		)
	)
	contenido.extend([tabla, Spacer(1, 0.2 * inch)])

	total_tabla = Table(
		[[Paragraph(_texto(total, "0"), estilo_total)]],
		colWidths=[7.1 * inch],
	)
	total_tabla.setStyle(
		TableStyle(
			[
				("ALIGN", (0, 0), (-1, -1), "RIGHT"),
				("TOPPADDING", (0, 0), (-1, -1), 8),
				("LINEABOVE", (0, 0), (-1, -1), 0.8, colors.HexColor("#17324D")),
			]
		)
	)
	contenido.append(total_tabla)
	doc.build(contenido)
