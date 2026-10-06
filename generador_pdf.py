import datetime
import os
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
	Paragraph,
	SimpleDocTemplate,
	Spacer,
	Table,
	TableStyle,
)
from svglib.svglib import svg2rlg


if hasattr(sys, "_MEIPASS"):
	base_dir = sys._MEIPASS
else:
	base_dir = os.path.dirname(os.path.abspath(__file__))

ruta_logo = os.path.join(base_dir, "logo_ancho_blanco.svg")


def dibujar_pie_pagina(canvas, doc):
	canvas.saveState()
	canvas.setStrokeColor(colors.grey)
	canvas.setLineWidth(0.6)
	canvas.line(40, 50, letter[0] - 40, 50)
	canvas.setFont("Helvetica", 9)
	canvas.setFillColor(colors.black)
	canvas.drawCentredString(
		letter[0] / 2,
		35,
		"Teléfonos: 55 19412496 / 55 43327867 | Instagram: "
		"@alquiladora.lider | https://www.alquiladoralider.com",
	)
	canvas.drawCentredString(
		letter[0] / 2,
		20,
		"Calle Olivos mz 3 lte 10, Progreso de Guadalupe Victoria, "
		"Ecatepec, Estado de México",
	)
	canvas.restoreState()


def _texto_seguro(valor):
	return escape("" if valor is None else str(valor))


def _texto_html_seguro(valor):
	return _texto_seguro(valor).replace("&lt;br/&gt;", "<br/>")


def _formatear_cantidad(valor):
	try:
		cantidad = float(valor)
	except (TypeError, ValueError):
		return _texto_seguro(valor)

	if cantidad.is_integer():
		return str(int(cantidad))
	return f"{cantidad:.2f}".rstrip("0").rstrip(".")


def _cargar_logo():
	if not os.path.exists(ruta_logo):
		return ""

	dibujo_logo = svg2rlg(ruta_logo)
	if not dibujo_logo or not dibujo_logo.height:
		return ""

	altura_maxima = 0.7 * inch
	factor = min(1, altura_maxima / dibujo_logo.height)
	dibujo_logo.scale(factor, factor)
	dibujo_logo.width *= factor
	dibujo_logo.height *= factor
	return dibujo_logo


def generar_cotizacion_pdf(
	datos_cliente, partidas, total_str, ruta_salida, tipo_formato="A"
):
	doc = SimpleDocTemplate(
		ruta_salida,
		pagesize=letter,
		rightMargin=40,
		leftMargin=40,
		topMargin=40,
		bottomMargin=60,
	)
	estilos = getSampleStyleSheet()
	color_oro = colors.HexColor("#D4AF37")
	estilo_slogan = ParagraphStyle(
		"SloganCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica-Bold",
		fontSize=11,
		leading=14,
		textColor=colors.white,
		alignment=TA_CENTER,
	)
	estilo_sub_slogan = ParagraphStyle(
		"SubSloganCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica",
		fontSize=9,
		leading=11,
		textColor=colors.lightgrey,
		alignment=TA_CENTER,
	)
	estilo_fecha = ParagraphStyle(
		"FechaCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica",
		fontSize=10,
		leading=14,
		textColor=colors.white,
		alignment=TA_RIGHT,
	)
	estilo_cliente = ParagraphStyle(
		"ClienteCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica-Bold",
		fontSize=11,
		leading=14,
		textColor=colors.HexColor("#1A1A1A"),
	)
	estilo_celda = ParagraphStyle(
		"CeldaCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica",
		fontSize=9,
		leading=11,
		textColor=colors.black,
	)
	estilo_encabezado_tabla = ParagraphStyle(
		"EncabezadoTablaCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica-Bold",
		fontSize=9,
		leading=11,
		alignment=TA_CENTER,
		textColor=colors.whitesmoke,
	)
	estilo_total = ParagraphStyle(
		"TotalCotizacion",
		parent=estilos["Normal"],
		fontName="Helvetica-Bold",
		fontSize=13,
		leading=17,
		alignment=TA_RIGHT,
		textColor=colors.black,
	)

	elementos = []
	dibujo_logo = _cargar_logo()
	fecha = datetime.date.today().strftime("%d/%m/%Y")
	texto_fecha = (
		f"<font name='Helvetica-Bold' size=14 color='#D4AF37'>COTIZACIÓN</font>"
		f"<br/><font size=9 color='white'>Ecatepec, Méx.<br/>{fecha}</font>"
	)
	slogan = Paragraph(
		"<font name='Helvetica-Bold' size=13 color='#D4AF37'>"
		"Lonas Industriales y DERivados</font>"
		"<br/><font size=9 color='#E0E0E0'>Renta de mobiliario y servicios "
		"para eventos sociales</font>",
		estilo_slogan,
	)
	encabezado = Table(
		[
			[
				dibujo_logo or Paragraph("LIDER", estilo_slogan),
				slogan,
				Paragraph(texto_fecha, estilo_fecha),
			]
		],
		colWidths=[2.0 * inch, 2.8 * inch, 2.5 * inch],
	)
	encabezado.setStyle(
		TableStyle(
			[
				("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A1A1A")),
				("LINEBELOW", (0, 0), (-1, -1), 2.5, color_oro),
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("ALIGN", (2, 0), (2, 0), "RIGHT"),
				("LEFTPADDING", (0, 0), (-1, -1), 0),
				("RIGHTPADDING", (0, 0), (-1, -1), 0),
				("TOPPADDING", (0, 0), (-1, -1), 15),
				("BOTTOMPADDING", (0, 0), (-1, -1), 15),
			]
		)
	)
	elementos.extend([encabezado, Spacer(1, 14)])

	nombre_cliente = (datos_cliente or {}).get("nombre")
	if nombre_cliente:
		datos_tabla_cliente = [["ATENCIÓN A:", _texto_seguro(nombre_cliente)]]
		tabla_cliente = Table(
			datos_tabla_cliente,
			colWidths=[1.5 * inch, 4.0 * inch],
			hAlign="LEFT",
		)
		tabla_cliente.setStyle(
			TableStyle(
				[
					("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#1A1A1A")),
					("TEXTCOLOR", (0, 0), (0, 0), colors.white),
					("BACKGROUND", (1, 0), (1, 0), colors.white),
					("TEXTCOLOR", (1, 0), (1, 0), colors.black),
					("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
					("FONTSIZE", (0, 0), (-1, -1), 10),
					("ALIGN", (0, 0), (0, 0), "CENTER"),
					("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
					("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A1A1A")),
					("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#1A1A1A")),
					("TOPPADDING", (0, 0), (-1, -1), 6),
					("BOTTOMPADDING", (0, 0), (-1, -1), 6),
				]
			)
		)
		elementos.extend(
			[
				tabla_cliente,
				Spacer(1, 14),
			]
		)

	filas = [["CANT.", "DESCRIPCIÓN", "PRECIO UNIT.", "SUBTOTAL"]]
	for partida in partidas or []:
		nombre = _texto_seguro(partida[1])
		descripcion = _texto_html_seguro(partida[2])
		if tipo_formato == "A":
			texto_descripcion = (
				f"<font name='Helvetica-Bold'>{nombre}</font><br/>"
				f"<font size=8 color='#444444'>{descripcion}</font>"
			)
		else:
			texto_descripcion = nombre
		filas.append(
			[
				_formatear_cantidad(partida[0]),
				texto_descripcion,
				_texto_seguro(partida[3]),
				_texto_seguro(partida[4]),
			]
		)
	anchos_tabla = [1 * inch, 3.5 * inch, 1.3 * inch, 1.3 * inch]

	filas_formateadas = [
		[Paragraph(_texto_seguro(celda), estilo_encabezado_tabla) for celda in filas[0]]
	]
	filas_formateadas.extend(
		[[Paragraph(celda, estilo_celda) for celda in fila] for fila in filas[1:]]
	)
	tabla_partidas = Table(
		filas_formateadas,
		colWidths=anchos_tabla,
		repeatRows=1,
	)
	tabla_partidas.setStyle(
		TableStyle(
			[
				("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
				("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
				("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
				("ALIGN", (0, 0), (-1, 0), "CENTER"),
				("ALIGN", (0, 1), (0, -1), "CENTER"),
				("ALIGN", (1, 1), (1, -1), "LEFT"),
				("ALIGN", (2, 1), (-1, -1), "CENTER"),
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("BACKGROUND", (0, 1), (-1, -1), colors.white),
				("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
				("LEFTPADDING", (0, 0), (-1, -1), 6),
				("RIGHTPADDING", (0, 0), (-1, -1), 6),
				("TOPPADDING", (0, 0), (-1, -1), 7),
				("BOTTOMPADDING", (0, 0), (-1, -1), 7),
			]
		)
	)
	for fila in range(2, len(filas), 2):
		tabla_partidas.setStyle(
			TableStyle(
				[("BACKGROUND", (0, fila), (-1, fila), colors.HexColor("#F5F5F5"))]
			)
		)
	elementos.extend([tabla_partidas, Spacer(1, 20)])

	total_limpio = str(total_str or "").strip()
	if total_limpio.upper().startswith("TOTAL:"):
		total_limpio = total_limpio.split(":", 1)[1].strip()
	tabla_total = Table(
		[
			[
				Paragraph("TOTAL:", estilo_total),
				Paragraph(_texto_seguro(total_limpio), estilo_total),
			]
		],
		colWidths=[1.8 * inch, 1.5 * inch],
		hAlign="RIGHT",
	)
	tabla_total.setStyle(
		TableStyle(
			[
				("BACKGROUND", (0, 0), (-1, -1), color_oro),
				("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
				("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
				("ALIGN", (0, 0), (-1, -1), "RIGHT"),
				("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
				("LEFTPADDING", (0, 0), (-1, -1), 10),
				("RIGHTPADDING", (0, 0), (-1, -1), 10),
				("TOPPADDING", (0, 0), (-1, -1), 9),
				("BOTTOMPADDING", (0, 0), (-1, -1), 9),
			]
		)
	)
	elementos.append(tabla_total)

	if tipo_formato == "B":
		elementos.extend([Spacer(1, 20), Paragraph(
			"<font name='Helvetica-Bold' size=11 color='#D4AF37'>"
			"DESGLOSE DE CONCEPTOS</font>",
			estilo_celda,
		), Spacer(1, 10)])
		datos_conceptos = [
			["CONCEPTO", "DESCRIPCIÓN DETALLADA"],
		]
		for partida in partidas or []:
			datos_conceptos.append(
				[
					Paragraph(f"<b>{_texto_seguro(partida[1])}</b>", estilo_celda),
					Paragraph(_texto_html_seguro(partida[2]), estilo_celda),
				]
			)
		filas_conceptos = [
			[Paragraph(_texto_seguro(celda), estilo_encabezado_tabla) for celda in datos_conceptos[0]],
		]
		filas_conceptos.extend(datos_conceptos[1:])
		tabla_conceptos = Table(
			filas_conceptos,
			colWidths=[2.5 * inch, 4.8 * inch],
			repeatRows=1,
		)
		tabla_conceptos.setStyle(
			TableStyle(
				[
					("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
					("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
					("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
					("VALIGN", (0, 0), (-1, -1), "TOP"),
					("LEFTPADDING", (0, 0), (-1, -1), 6),
					("RIGHTPADDING", (0, 0), (-1, -1), 6),
					("TOPPADDING", (0, 0), (-1, -1), 7),
					("BOTTOMPADDING", (0, 0), (-1, -1), 7),
				]
			)
		)
		elementos.append(tabla_conceptos)

	doc.build(elementos, onFirstPage=dibujar_pie_pagina)
