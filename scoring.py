"""
=====================================================================
PortfolioSentinel — scoring.py
=====================================================================
Este archivo recibe todos los datos obtenidos por data_fetcher.py
y los indicadores calculados por indicators.py, y genera:

  1. La puntuación global de 1 a 100
  2. El resumen ejecutivo detallado
  3. Los riesgos identificados
  4. Las oportunidades identificadas
  5. Las recomendaciones finales

Sistema de puntuación (100 puntos máximos):

  FUNDAMENTALES (60 puntos)
    - Precio y valoración:     15 puntos
    - Dividendo y retribución: 15 puntos
    - Crecimiento:             15 puntos
    - Fortaleza financiera:    15 puntos

  TÉCNICOS (25 puntos)
    - Medias móviles:          10 puntos
    - RSI + MACD + Bollinger:  10 puntos
    - Volumen:                  5 puntos

  CONTEXTO (15 puntos)
    - Beta y riesgo:            8 puntos
    - Acciones en circulación:  7 puntos

NO necesitas modificar nada en este archivo.
=====================================================================
"""


# ─── BLOQUE FUNDAMENTALES ─────────────────────────────────────────

def puntuar_precio_valoracion(fundamentals, sector_data):
    """
    Puntúa la valoración comparada con el sector.
    Máximo: 15 puntos.
    """
    if not fundamentals or not sector_data:
        return 7  # Puntuación neutra si no hay datos

    puntos = 0

    # PER vs Sector (máximo 8 puntos)
    # Cuanto más bajo el PER respecto al sector, más barata está la empresa
    per = fundamentals.get("pe_ratio", 0)
    per_sector = sector_data.get("sector_pe", 0)

    if per and per_sector and per > 0 and per_sector > 0:
        ratio_per = per / per_sector
        if ratio_per < 0.7:
            puntos += 8
        elif ratio_per < 0.9:
            puntos += 6
        elif ratio_per < 1.1:
            puntos += 4
        elif ratio_per < 1.3:
            puntos += 2
        else:
            puntos += 1
    else:
        puntos += 4  # Sin datos, neutra

    # Precio/Valor Contable vs Sector (máximo 7 puntos)
    pb = fundamentals.get("price_to_book", 0)
    pb_sector = sector_data.get("sector_pb", 0)

    if pb and pb_sector and pb > 0 and pb_sector > 0:
        ratio_pb = pb / pb_sector
        if ratio_pb < 0.7:
            puntos += 7
        elif ratio_pb < 0.9:
            puntos += 5
        elif ratio_pb < 1.1:
            puntos += 4
        elif ratio_pb < 1.3:
            puntos += 2
        else:
            puntos += 1
    else:
        puntos += 3

    return min(puntos, 15)


def puntuar_dividendo(dividends, fundamentals):
    """
    Puntúa la política de retribución al accionista.
    Máximo: 15 puntos.
    """
    if not dividends:
        return 5

    puntos = 0

    # Rentabilidad por dividendo (máximo 4 puntos)
    yield_div = dividends.get("dividend_yield_at_buy", 0)
    if yield_div >= 4:
        puntos += 4
    elif yield_div >= 2.5:
        puntos += 3
    elif yield_div >= 1.5:
        puntos += 2
    elif yield_div > 0:
        puntos += 1

    # Crecimiento del dividendo a 3 y 5 años (máximo 4 puntos)
    crec_3y = dividends.get("dividend_growth_3y", 0)
    crec_5y = dividends.get("dividend_growth_5y", 0)

    if crec_3y > 10 and crec_5y > 8:
        puntos += 4
    elif crec_3y > 5 and crec_5y > 3:
        puntos += 3
    elif crec_3y > 0 and crec_5y > 0:
        puntos += 2
    elif crec_3y > 0 or crec_5y > 0:
        puntos += 1

    # Payout ratio sostenible (máximo 3 puntos)
    # Entre 30-60% es la zona ideal: reparte beneficios pero retiene para crecer
    payout = fundamentals.get("payout_ratio", 0) if fundamentals else 0
    if 30 <= payout <= 60:
        puntos += 3
    elif 20 <= payout < 30 or 60 < payout <= 75:
        puntos += 2
    elif payout > 0:
        puntos += 1

    # Buyback activo (máximo 2 puntos)
    if fundamentals and fundamentals.get("has_buyback"):
        puntos += 2

    # Punto extra si las acciones en circulación bajan (se ajusta desde el llamador)
    puntos += 1

    return min(puntos, 15)


def puntuar_crecimiento(fundamentals, sector_data):
    """
    Puntúa el crecimiento de ventas y BPA.
    Máximo: 15 puntos.
    """
    if not fundamentals:
        return 7

    puntos = 0

    # Crecimiento de ventas 5 años (máximo 8 puntos)
    vs5 = fundamentals.get("sales_growth_5y", 0)
    if vs5 > 20:
        puntos += 8
    elif vs5 > 10:
        puntos += 6
    elif vs5 > 5:
        puntos += 4
    elif vs5 > 0:
        puntos += 2
    elif vs5 > -5:
        puntos += 1

    # Crecimiento de BPA 5 años (máximo 7 puntos)
    bpa5 = fundamentals.get("eps_growth_5y", 0)
    if bpa5 > 25:
        puntos += 7
    elif bpa5 > 15:
        puntos += 5
    elif bpa5 > 8:
        puntos += 4
    elif bpa5 > 0:
        puntos += 2
    elif bpa5 > -5:
        puntos += 1

    return min(puntos, 15)


def puntuar_fortaleza_financiera(fundamentals, sector_data):
    """
    Puntúa la solidez del balance.
    Máximo: 15 puntos.
    """
    if not fundamentals or not sector_data:
        return 7

    puntos = 0

    # Deuda/Fondos propios vs sector (máximo 8 puntos)
    df = fundamentals.get("debt_to_equity", 0)
    df_sector = sector_data.get("sector_debt_to_equity", 1)

    if df_sector and df_sector > 0:
        ratio_df = df / df_sector
        if ratio_df < 0.5:
            puntos += 8
        elif ratio_df < 0.8:
            puntos += 6
        elif ratio_df < 1.0:
            puntos += 5
        elif ratio_df < 1.3:
            puntos += 3
        elif ratio_df < 1.8:
            puntos += 2
        else:
            puntos += 1
    else:
        puntos += 4

    # Márgenes brutos vs sector (máximo 7 puntos)
    margen = fundamentals.get("gross_margin_5y_avg", 0)
    margen_sector = sector_data.get("sector_gross_margin", 35)

    if margen_sector and margen_sector > 0:
        ratio_margen = margen / margen_sector
        if ratio_margen > 1.3:
            puntos += 7
        elif ratio_margen > 1.1:
            puntos += 5
        elif ratio_margen > 0.9:
            puntos += 4
        elif ratio_margen > 0.7:
            puntos += 2
        else:
            puntos += 1
    else:
        puntos += 3

    return min(puntos, 15)


# ─── BLOQUE TÉCNICOS ──────────────────────────────────────────────

def puntuar_medias_moviles(indicadores):
    """
    Puntúa las señales de medias móviles.
    Máximo: 10 puntos.

    La MM200 vale más porque marca la tendencia de largo plazo.
    """
    if not indicadores or "medias_moviles" not in indicadores:
        return 5

    mm = indicadores["medias_moviles"]
    puntos = 0

    # MM50: 2 puntos si el precio está por encima
    if mm.get("mm50") and mm["mm50"].get("precio_encima"):
        puntos += 2

    # MM100: 3 puntos
    if mm.get("mm100") and mm["mm100"].get("precio_encima"):
        puntos += 3

    # MM200: 5 puntos (la más importante)
    if mm.get("mm200") and mm["mm200"].get("precio_encima"):
        puntos += 5

    return puntos


def puntuar_osciladores(indicadores):
    """
    Puntúa RSI, MACD y Bollinger.
    Máximo: 10 puntos.
    """
    if not indicadores:
        return 5

    puntos = 0

    # RSI (máximo 4 puntos)
    rsi = indicadores.get("rsi")
    if rsi:
        valor = rsi.get("valor", 50)
        if 30 <= valor < 40:
            puntos += 4   # Cerca de sobreventa: posible oportunidad de rebote
        elif valor < 30:
            puntos += 4   # En sobreventa
        elif 40 <= valor <= 60:
            puntos += 3   # Zona neutra
        elif 60 < valor <= 70:
            puntos += 2   # Algo alto
        else:
            puntos += 1   # Sobrecompra

    # MACD (máximo 3 puntos)
    macd = indicadores.get("macd")
    if macd:
        if macd.get("es_alcista"):
            puntos += 3
        else:
            puntos += 1

    # Bollinger (máximo 3 puntos)
    bollinger = indicadores.get("bollinger")
    if bollinger:
        pos = bollinger.get("posicion", "")
        if pos == "Banda inferior":
            puntos += 3   # Posible rebote
        elif pos == "Banda media":
            puntos += 2
        else:
            puntos += 1   # Banda superior

    return min(puntos, 10)


def puntuar_volumen(indicadores):
    """
    Puntúa el análisis de volumen.
    Máximo: 5 puntos.
    """
    if not indicadores or "volumen" not in indicadores:
        return 2

    variacion = indicadores["volumen"].get("variacion_pct", 0)

    if variacion > 50:
        return 5
    elif variacion > 20:
        return 4
    elif variacion > 0:
        return 3
    elif variacion > -20:
        return 2
    else:
        return 1


# ─── BLOQUE CONTEXTO ──────────────────────────────────────────────

def puntuar_contexto_beta(indicadores):
    """
    Puntúa según los niveles de riesgo evaluados.
    Máximo: 8 puntos.
    """
    if not indicadores or "riesgos" not in indicadores:
        return 4

    riesgos = indicadores["riesgos"]
    niveles = {"Bajo": 3, "Medio": 2, "Alto": 0}

    puntos = 0
    puntos += niveles.get(riesgos.get("riesgo_corto_plazo", "Medio"), 2)
    puntos += niveles.get(riesgos.get("riesgo_medio_plazo", "Medio"), 2)
    puntos += niveles.get(riesgos.get("riesgo_largo_plazo", "Medio"), 2)

    return min(puntos, 8)


def puntuar_acciones_circulacion(shares_data):
    """
    Puntúa la evolución de acciones en circulación.
    Máximo: 7 puntos.

    Si bajan → muy positivo (la empresa recompra)
    Si suben → negativo (dilución)
    """
    if not shares_data:
        return 3

    trend = shares_data.get("shares_trend_3y", 0)

    if trend < -5:
        return 7
    elif trend < -2:
        return 5
    elif trend < 0:
        return 4
    elif trend == 0:
        return 3
    elif trend < 3:
        return 2
    elif trend < 7:
        return 1
    else:
        return 0


# ─── SCORE TOTAL ──────────────────────────────────────────────────

def calcular_score(company_data, indicadores):
    """
    Calcula el score total de 1 a 100 sumando los tres bloques.

    Retorna un diccionario con el score y el desglose completo.
    """
    fundamentals = company_data.get("fundamentals", {})
    sector_data  = company_data.get("sector", {})
    dividends    = company_data.get("dividends", {})
    shares_data  = company_data.get("shares_outstanding", {})

    # Puntuaciones individuales
    p_precio      = puntuar_precio_valoracion(fundamentals, sector_data)
    p_dividendo   = puntuar_dividendo(dividends, fundamentals)
    p_crecimiento = puntuar_crecimiento(fundamentals, sector_data)
    p_fortaleza   = puntuar_fortaleza_financiera(fundamentals, sector_data)
    p_mm          = puntuar_medias_moviles(indicadores)
    p_osciladores = puntuar_osciladores(indicadores)
    p_volumen     = puntuar_volumen(indicadores)
    p_beta        = puntuar_contexto_beta(indicadores)
    p_acciones    = puntuar_acciones_circulacion(shares_data)

    # Ajuste: si las acciones bajan, +1 punto al bloque dividendo
    trend = shares_data.get("shares_trend_3y", 0) if shares_data else 0
    if trend < 0:
        p_dividendo = min(p_dividendo + 1, 15)

    # Suma total, capped entre 1 y 100
    score_total = max(1, min(100,
        p_precio + p_dividendo + p_crecimiento + p_fortaleza +
        p_mm + p_osciladores + p_volumen +
        p_beta + p_acciones
    ))

    return {
        "score_total": score_total,
        "desglose": {
            "precio_valoracion":     p_precio,
            "dividendo_retribucion": p_dividendo,
            "crecimiento":           p_crecimiento,
            "fortaleza_financiera":  p_fortaleza,
            "medias_moviles":        p_mm,
            "osciladores":           p_osciladores,
            "volumen":               p_volumen,
            "contexto_beta":         p_beta,
            "contexto_acciones":     p_acciones,
        }
    }


# ─── RESUMEN EJECUTIVO ────────────────────────────────────────────

def generar_resumen_ejecutivo(company_data, indicadores, score_data):
    """
    Genera el resumen ejecutivo como lista de párrafos en español.
    Cada párrafo se construye dinámicamente según los datos reales.
    """
    profile      = company_data.get("profile", {})
    fundamentals = company_data.get("fundamentals", {})
    sector_data  = company_data.get("sector", {})
    shares_data  = company_data.get("shares_outstanding", {})
    score        = score_data.get("score_total", 0)
    nombre       = profile.get("name", "La empresa")

    # Valores necesarios con defaults
    per       = fundamentals.get("pe_ratio", 0) if fundamentals else 0
    per_s     = sector_data.get("sector_pe", 0) if sector_data else 0
    pb        = fundamentals.get("price_to_book", 0) if fundamentals else 0
    pb_s      = sector_data.get("sector_pb", 0) if sector_data else 0
    mg5       = fundamentals.get("gross_margin_5y_avg", 0) if fundamentals else 0
    mg_s      = sector_data.get("sector_gross_margin", 0) if sector_data else 0
    vs5       = fundamentals.get("sales_growth_5y", 0) if fundamentals else 0
    bpa5      = fundamentals.get("eps_growth_5y", 0) if fundamentals else 0
    df        = fundamentals.get("debt_to_equity", 0) if fundamentals else 0
    df_s      = sector_data.get("sector_debt_to_equity", 0) if sector_data else 0
    buyback   = fundamentals.get("has_buyback", False) if fundamentals else False
    trend_acc = shares_data.get("shares_trend_3y", 0) if shares_data else 0
    shares_out= shares_data.get("shares_outstanding", 0) if shares_data else 0
    beta      = profile.get("beta", 1.0)

    # Datos técnicos
    mm200_encima  = indicadores.get("medias_moviles", {}).get("mm200", {}).get("precio_encima", False) if indicadores else False
    rsi_valor     = indicadores.get("rsi", {}).get("valor", 50) if indicadores else 50
    macd_alcista  = indicadores.get("macd", {}).get("es_alcista", False) if indicadores else False

    parrafos = []

    # ── P1: Valoración ──
    p1 = f"{nombre} presenta un perfil inversor que merece atención detallada. "
    if per and per_s and per > 0 and per_s > 0:
        if per > per_s:
            p1 += f"Con un PER de {per:.1f}x frente al {per_s:.1f}x del sector, la valoración actual se sitúa por encima de la media, lo que indica que el mercado descuenta expectativas de crecimiento elevadas. "
        else:
            p1 += f"Con un PER de {per:.1f}x frente al {per_s:.1f}x del sector, la valoración actual se mantiene por debajo del promedio sectorial, sugiriendo que la empresa podría estar infravalorada en relación a sus pares. "
    if pb and pb_s and pb > 0 and pb_s > 0:
        if pb > pb_s:
            p1 += f"El precio respecto al valor contable ({pb:.1f}x vs {pb_s:.1f}x del sector) refleja una prima que el mercado atribuye a la calidad o posicionamiento competitivo de la empresa."
        else:
            p1 += f"El precio respecto al valor contable ({pb:.1f}x vs {pb_s:.1f}x del sector) se alinea con el sector, sin indicar sobrevaloración significativa."
    parrafos.append(p1)

    # ── P2: Rentabilidad y crecimiento ──
    p2 = ""
    if mg5 and mg_s:
        comp = "por encima" if mg5 > mg_s else "por debajo"
        p2 += f"Desde el punto de vista de la rentabilidad, el margen bruto promedio de los últimos 5 años se sitúa en el {mg5:.1f}%, {comp} del {mg_s:.1f}% del sector. "
    if vs5 is not None:
        if vs5 > 10:
            p2 += f"El crecimiento de ventas a 5 años del {vs5:.1f}% indica una expansión de negocio dinámica. "
        elif vs5 > 0:
            p2 += f"El crecimiento de ventas a 5 años del {vs5:.1f}% refleja un crecimiento moderado. "
        else:
            p2 += f"El crecimiento de ventas a 5 años muestra una contracción del {abs(vs5):.1f}%, señal que debe valorarse en contexto. "
    if bpa5 is not None:
        if bpa5 > 0:
            p2 += f"El BPA ha crecido un {bpa5:.1f}% en el mismo período, lo cual es relevante para evaluar la calidad de los beneficios generados."
        else:
            p2 += f"El BPA ha mostrado una evolución negativa del {abs(bpa5):.1f}%, un aspecto que requiere seguimiento cercano."
    if p2:
        parrafos.append(p2)

    # ── P3: Estructura financiera ──
    p3 = ""
    if df is not None and df_s:
        if df > df_s:
            p3 += f"La estructura financiera muestra un ratio deuda/fondos propios de {df:.2f}x, notablemente superior al sector ({df_s:.2f}x). Este nivel de apalancamiento eleva el riesgo financiero y merece seguimiento cercano, especialmente en entornos de tipos de interés al alza. "
        else:
            p3 += f"La estructura financiera muestra un ratio deuda/fondos propios de {df:.2f}x, en línea o por debajo del sector ({df_s:.2f}x). Esta posición indica una estructura de balance relativamente conservadora, lo cual aporta estabilidad en escenarios adversos. "
    if buyback:
        p3 += "El programa de recompra de acciones activo refuerza la confianza de la directiva en la empresa y contribuye directamente a la creación de valor para el accionista."
    if p3:
        parrafos.append(p3)

    # ── P4: Capital accionarial ──
    if shares_out:
        shares_f = f"{shares_out/1e9:.2f}B" if shares_out >= 1e9 else f"{shares_out/1e6:.0f}M"
        if trend_acc < 0:
            p4 = f"En cuanto al capital accionarial, las acciones en circulación ({shares_f}) han disminuido un {abs(trend_acc):.1f}% en los últimos 3 años. Esta reducción es un indicador positivo, ya que sugiere que la empresa está devolviendo valor al accionista mediante recompras y que no recurre a ampliaciones dilutivas para financiar su crecimiento."
        else:
            p4 = f"En cuanto al capital accionarial, las acciones en circulación ({shares_f}) han aumentado un {trend_acc:.1f}% en los últimos 3 años, lo cual puede reflejar planes de retribución a empleados basados en acciones o necesidades de financiación externa. Es importante evaluar si este aumento afecta de manera significativa al valor por acción."
        parrafos.append(p4)

    # ── P5: Análisis técnico ──
    if indicadores:
        p5 = f"El análisis técnico indica que el precio se encuentra {'por encima' if mm200_encima else 'por debajo'} de la media móvil de 200 sesiones, con señales {'alcistas' if macd_alcista else 'bajistas'} en el MACD. "
        if rsi_valor > 70:
            p5 += f"El RSI en {rsi_valor:.1f} se encuentra en zona de sobrecompra, lo que puede anticipar una corrección a corto plazo. "
        elif rsi_valor < 30:
            p5 += f"El RSI en {rsi_valor:.1f} se encuentra en zona de sobreventa, presentando un potencial punto de rebote. "
        else:
            p5 += f"El RSI en {rsi_valor:.1f} se sitúa en zona neutra, sin señales extremas. "
        if beta:
            if beta > 1:
                p5 += f"La beta de {beta:.2f} indica que la acción es más volátil que el mercado general, lo que amplifica tanto las subidas como las caídas y debe considerarse al dimensionar la posición."
            else:
                p5 += f"La beta de {beta:.2f} indica que la acción tiende a moverse menos que el mercado, ofreciendo mayor estabilidad en entornos de incertidumbre."
        parrafos.append(p5)

    # ── P6: Síntesis ──
    if score >= 70:
        p6 = f"En síntesis, {nombre} se presenta como una empresa de alta calidad con fundamentales sólidos. El perfil de riesgo es manejable y la posición técnica actual permitiría considerar una entrada gradual, especialmente si se observa un retroceso hacia las zonas de soporte identificadas."
    elif score >= 50:
        p6 = f"En síntesis, {nombre} presenta potencial interesante, aunque presenta áreas que requieren seguimiento cercano, especialmente en relación al endeudamiento y la evolución del capital accionarial. Se recomienda una entrada cautelosa."
    else:
        p6 = f"En síntesis, {nombre} presenta desafíos significativos, ya sea en su estructura financiera, valoración o dinámica de crecimiento. Se aconseja un análisis más profundo y esperar condiciones técnicas más favorables antes de tomar decisiones de inversión."
    parrafos.append(p6)

    return parrafos


# ─── RIESGOS ──────────────────────────────────────────────────────

def identificar_riesgos(company_data, indicadores):
    """
    Identifica los principales riesgos de la empresa.
    Retorna una lista de strings.
    """
    riesgos = []
    fund   = company_data.get("fundamentals", {})
    sector = company_data.get("sector", {})
    shares = company_data.get("shares_outstanding", {})
    perfil = company_data.get("profile", {})

    # Deuda alta
    df   = fund.get("debt_to_equity", 0) if fund else 0
    df_s = sector.get("sector_debt_to_equity", 0) if sector else 0
    if df and df_s and df > df_s * 1.3:
        riesgos.append(f"Endeudamiento superior al sector ({df:.2f}x vs {df_s:.2f}x del sector)")

    # PER elevado
    per   = fund.get("pe_ratio", 0) if fund else 0
    per_s = sector.get("sector_pe", 0) if sector else 0
    if per and per_s and per > per_s * 1.2:
        riesgos.append(f"PER por encima de la media sectorial ({per:.1f}x vs {per_s:.1f}x)")

    # Beta alta
    beta = perfil.get("beta", 1.0) if perfil else 1.0
    if beta and beta > 1.3:
        riesgos.append(f"Beta elevada ({beta:.2f}): mayor sensibilidad a caídas del mercado general")

    # Dilución
    trend = shares.get("shares_trend_3y", 0) if shares else 0
    if trend > 3:
        riesgos.append(f"Aumento de acciones en circulación (+{trend:.1f}% en 3 años): posible dilución del valor por acción")

    # RSI sobrecompra
    rsi = indicadores.get("rsi", {}).get("valor", 50) if indicadores else 50
    if rsi > 70:
        riesgos.append(f"RSI en zona de sobrecompra ({rsi:.1f}): riesgo de corrección técnica a corto plazo")

    # Márgenes bajo el sector
    mg   = fund.get("gross_margin_5y_avg", 0) if fund else 0
    mg_s = sector.get("sector_gross_margin", 0) if sector else 0
    if mg and mg_s and mg < mg_s * 0.8:
        riesgos.append(f"Márgenes brutos por debajo del sector ({mg:.1f}% vs {mg_s:.1f}%)")

    # Precio encima de zona de entrada
    zona = indicadores.get("zona_entrada", {}) if indicadores else {}
    if zona.get("estado") == "Esperar retroceso":
        dist = zona.get("distancia_zona_pct", 0)
        riesgos.append(f"Precio actual por encima de la zona de entrada ({dist:.1f}% por encima de la zona ideal)")

    if not riesgos:
        riesgos.append("Incertidumbre macroeconómica general del sector")

    return riesgos


# ─── OPORTUNIDADES ────────────────────────────────────────────────

def identificar_oportunidades(company_data, indicadores):
    """
    Identifica las principales oportunidades de la empresa.
    Retorna una lista de strings.
    """
    oportunidades = []
    fund   = company_data.get("fundamentals", {})
    sector = company_data.get("sector", {})
    shares = company_data.get("shares_outstanding", {})
    div    = company_data.get("dividends", {})

    # Crecimiento ventas fuerte
    vs5 = fund.get("sales_growth_5y", 0) if fund else 0
    if vs5 > 10:
        oportunidades.append(f"Crecimiento de ventas sostenido y fuerte ({vs5:.1f}% en 5 años)")

    # Buyback activo
    if fund and fund.get("has_buyback"):
        oportunidades.append("Programa de recompra de acciones activo: la empresa devuelve valor al accionista")

    # Reducción acciones
    trend = shares.get("shares_trend_3y", 0) if shares else 0
    if trend < -2:
        oportunidades.append(f"Reducción de acciones en circulación ({abs(trend):.1f}% en 3 años): el valor por acción creciente beneficia al accionista")

    # Márgenes superiores al sector
    mg   = fund.get("gross_margin_5y_avg", 0) if fund else 0
    mg_s = sector.get("sector_gross_margin", 0) if sector else 0
    if mg and mg_s and mg > mg_s * 1.1:
        oportunidades.append(f"Márgenes brutos por encima del sector ({mg:.1f}% vs {mg_s:.1f}%): posicionamiento competitivo favorable")

    # BPA creciente
    bpa5 = fund.get("eps_growth_5y", 0) if fund else 0
    if bpa5 > 10:
        oportunidades.append(f"Crecimiento BPA fuerte ({bpa5:.1f}% en 5 años): los beneficios generan valor real")

    # RSI sobreventa
    rsi = indicadores.get("rsi", {}).get("valor", 50) if indicadores else 50
    if rsi < 35:
        oportunidades.append(f"RSI en zona de sobreventa ({rsi:.1f}): potencial punto de rebote técnico")

    # Zona de entrada activa
    zona = indicadores.get("zona_entrada", {}) if indicadores else {}
    if zona.get("estado") == "Zona de entrada activa":
        oportunidades.append("El precio actual se encuentra dentro de la zona de entrada técnica identificada")

    # Dividendo creciente
    if div and div.get("dividend_growth_5y", 0) > 5:
        oportunidades.append(f"Dividendo con crecimiento consistente ({div['dividend_growth_5y']:.1f}% en 5 años): retribución fiable al accionista")

    if not oportunidades:
        oportunidades.append("Posible expansión en mercados emergentes y nuevas líneas de negocio")

    return oportunidades


# ─── FUNCIÓN PRINCIPAL ────────────────────────────────────────────

def generar_analisis_completo(company_data, indicadores):
    """
    Función principal que genera todo el análisis de una empresa.

    Recibe:
    - company_data: datos de data_fetcher.py
    - indicadores:  datos de indicators.py

    Retorna un diccionario con:
    - score y desglose
    - resumen ejecutivo (lista de párrafos)
    - riesgos (lista de strings)
    - oportunidades (lista de strings)
    - zona de entrada
    """
    score_data     = calcular_score(company_data, indicadores)
    resumen        = generar_resumen_ejecutivo(company_data, indicadores, score_data)
    riesgos        = identificar_riesgos(company_data, indicadores)
    oportunidades  = identificar_oportunidades(company_data, indicadores)
    zona_entrada   = indicadores.get("zona_entrada", {}) if indicadores else {}

    return {
        "score":            score_data,
        "resumen_ejecutivo": resumen,
        "riesgos":          riesgos,
        "oportunidades":    oportunidades,
        "zona_entrada":     zona_entrada,
    }


# ─── EJEMPLO DE USO ──────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Datos simulados para probar sin necesidad de API
    company_data_ejemplo = {
        "profile": {"name": "Apple Inc.", "beta": 1.19, "sector": "Tecnología"},
        "fundamentals": {
            "pe_ratio": 28.4, "price_to_book": 7.2,
            "gross_margin_5y_avg": 43.1, "sales_growth_5y": 11.2,
            "eps_growth_5y": 13.8, "debt_to_equity": 1.81,
            "has_buyback": True, "payout_ratio": 15.4,
        },
        "sector": {
            "sector_pe": 24.1, "sector_pb": 5.8,
            "sector_gross_margin": 38.6, "sector_debt_to_equity": 0.72,
        },
        "dividends": {
            "dividend_yield_at_buy": 1.82,
            "dividend_growth_3y": 4.5, "dividend_growth_5y": 5.2,
            "pays_dividend": True,
        },
        "shares_outstanding": {"shares_outstanding": 15.4e9, "shares_trend_3y": -3.2},
    }

    indicadores_ejemplo = {
        "precio_actual": 228.40,
        "medias_moviles": {
            "mm50":  {"valor": 215.0, "precio_encima": True,  "texto": "Precio sobre MM50 ↑"},
            "mm100": {"valor": 205.0, "precio_encima": True,  "texto": "Precio sobre MM100 ↑"},
            "mm200": {"valor": 195.0, "precio_encima": True,  "texto": "Precio sobre MM200 ↑"},
        },
        "rsi":      {"valor": 62.4, "zona": "Zona neutra", "texto": "62.4 — Zona neutra"},
        "macd":     {"valor_macd": 3.2, "valor_señal": 1.8, "es_alcista": True, "texto": "Línea señal alcista ↑"},
        "bollinger":{"banda_superior": 235.0, "banda_media": 220.0, "banda_inferior": 205.0, "posicion": "Banda media"},
        "volumen":  {"volumen_actual": 85000000, "promedio_30d": 65000000, "variacion_pct": 30.8},
        "zona_entrada": {"precio_actual": 228.40, "soporte_mm200": 195.0, "soporte_bollinger": 205.0, "zona_ideal_min": 195.0, "zona_ideal_max": 205.0, "estado": "Esperar retroceso", "distancia_zona_pct": 11.5},
        "riesgos": {"riesgo_corto_plazo": "Medio", "riesgo_medio_plazo": "Bajo", "riesgo_largo_plazo": "Bajo"},
    }

    analisis = generar_analisis_completo(company_data_ejemplo, indicadores_ejemplo)

    print(json.dumps(analisis, indent=4, ensure_ascii=False))
