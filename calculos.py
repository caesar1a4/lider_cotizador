import math


def calcular_pista(invitados: int) -> tuple[float, str]:
	m2_ideales = invitados * 0.12
	if m2_ideales == 0:
		return 0.0, "0m x 0m"

	lado1_modulos = round(math.sqrt(m2_ideales))
	lado2_modulos = round(m2_ideales / lado1_modulos)
	area_real = (lado1_modulos * lado2_modulos) * 1.5625
	dimensiones = f"{lado1_modulos * 1.25}m x {lado2_modulos * 1.25}m"

	return area_real, dimensiones


def calcular_carpa_sugerida(
	invitados: int, ancho: int, factor_espacio: float = 70.0
) -> tuple[int, float]:
	m2_minimos = invitados + factor_espacio
	largo_minimo = m2_minimos / ancho
	largo_modulos = math.ceil(largo_minimo / 5.0)
	largo_real = largo_modulos * 5
	area_real = ancho * largo_real

	return largo_real, area_real


def calcular_precio_carpa(
	precio_base_m2: float, area_m2: float, estilo: str
) -> float:
	precio_final_m2 = precio_base_m2
	if estilo in ("Decorada", "Plisada"):
		precio_final_m2 += 15.0

	return round(precio_final_m2 * area_m2, 2)
