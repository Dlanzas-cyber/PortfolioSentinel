"""
=====================================================================
PortfolioSentinel — indicators.py
=====================================================================
Este archivo calcula todos los indicadores técnicos necesarios
para el análisis de cada empresa.

Recibe los precios históricos que descarga data_fetcher.py
y devuelve las señales técnicas calculadas.

NO necesitas modificar nada en este archivo.
=====================================================================
"""


# ─── FUNCIÓN AUXILIAR: CALCULAR MEDIA MÓVIL SIMPLE ───────────────
# Una media móvil simple es el promedio de los últimos X precios de cierre.
# Por ejemplo, la MM50 es el promedio de los últimos 50 días de cierre.
def calcular_media_movil(precios_cierre, periodo):
    """
    Calcula la media móvil simple para un período dado.
    
    - precios_cierre: lista de precios de cierre ordenados de antiguo a reciente
    - periodo: número de sesiones (50, 100 o 200)
    
    Retorna: el valor de la media móvil actual (último dato)
    """
    # Si no hay suficientes datos, no podemos calcular
    if len(precios_cierre) < periodo:
        return None
    
    # Tomamos los últimos X precios y calculamos el promedio
    ultimos_precios = precios_cierre[-periodo:]
    return round(sum(ultimos_precios) / len(ultimos_precios), 2)


# ─── FUNCIÓN AUXILIAR: CALCULAR EL RSI (Índice de Fuerza Relativa) ──
# El RSI mide si una acción está sobrecomprada (>70) o sobreventa (<30).
# Se calcula comparando los días en que sube el precio con los que baja.
def calcular_rsi(precios_cierre, periodo=14):
    """
    Calcula el RSI con un período estándar de 14 días.
    
    - precios_cierre: lista de precios de cierre ordenados de antiguo a reciente
    - periodo: número de sesiones para el cálculo (por defecto 14)
    
    Retorna: valor del RSI entre 0 y 100
    """
    # Necesitamos al menos periodo + 1 datos
    if len(precios_cierre) < periodo + 1:
        return None
    
    # Calculamos los cambios diarios (precio hoy - precio ayer)
    cambios = []
    for i in range(1, len(precios_cierre)):
        cambio = precios_cierre[i] - precios_cierre[i - 1]
        cambios.append(cambio)
    
    # Separamos los cambios positivos (subidas) y negativos (bajadas)
    subidas = [c if c > 0 else 0 for c in cambios]
    bajadas = [abs(c) if c < 0 else 0 for c in cambios]
    
    # Calculamos el promedio de subidas y bajadas de los últimos X días
    # Usamos una media exponencial suavizada (método estándar de Wilder)
    avg_subida = sum(subidas[-periodo:]) / periodo
    avg_bajada = sum(bajadas[-periodo:]) / periodo
    
    # Para datos más recientes, aplicamos el suavizado exponencial
    for i in range(periodo, len(cambios)):
        avg_subida = (avg_subida * (periodo - 1) + subidas[i]) / periodo
        avg_bajada = (avg_bajada * (periodo - 1) + bajadas[i]) / periodo
    
    # Calculamos el RSI
    # Si no hay bajadas, el RSI es 100 (máximo alcista)
    if avg_bajada == 0:
        return 100.0
    
    # RS = promedio subidas / promedio bajadas
    rs = avg_subida / avg_bajada
    
    # RSI = 100 - (100 / (1 + RS))
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


# ─── FUNCIÓN AUXILIAR: CALCULAR EL MACD ──────────────────────────
# El MACD (Moving Average Convergence Divergence) mide el momentum.
# Se basa en la diferencia entre dos medias móviles exponenciales.
# Cuando la línea MACD cruza por encima de la línea señal → señal alcista.
# Cuando cruza por debajo → señal bajista.
def calcular_media_movil_exponencial(precios, periodo):
    """
    Calcula la media móvil exponencial (EMA).
    La EMA da más peso a los precios más recientes que la media simple.
    """
    if len(precios) < periodo:
        return None
    
    # El multiplicador determina cuánto peso tiene cada nuevo dato
    multiplicador = 2.0 / (periodo + 1)
    
    # Comenzamos con la media simple de los primeros X datos como base
    ema = sum(precios[:periodo]) / periodo
    
    # A partir de ahí, cada nuevo precio se incorpora con el multiplicador
    for i in range(periodo, len(precios)):
        ema = (precios[i] - ema) * multiplicador + ema
    
    return round(ema, 2)


def calcular_macd(precios_cierre):
    """
    Calcula el MACD usando las medias exponenciales estándar:
    - EMA rápida: 12 días
    - EMA lenta: 26 días
    - Línea señal: EMA de 9 días del MACD
    
    Retorna:
    - macd_value: valor actual del MACD
    - signal_value: valor actual de la línea señal
    - is_bullish: True si el MACD está por encima de la señal (alcista)
    """
    if len(precios_cierre) < 26:
        return {"macd_value": 0, "signal_value": 0, "is_bullish": False}
    
    # Calculamos las dos EMAs
    ema_12 = calcular_media_movil_exponencial(precios_cierre, 12)
    ema_26 = calcular_media_movil_exponencial(precios_cierre, 26)
    
    if ema_12 is None or ema_26 is None:
        return {"macd_value": 0, "signal_value": 0, "is_bullish": False}
    
    # El MACD es la diferencia entre la EMA rápida y la lenta
    macd_value = round(ema_12 - ema_26, 4)
    
    # Para la línea señal necesitamos calcular una serie de valores MACD
    # y luego hacer una EMA de 9 períodos sobre ellos
    macd_series = []
    for i in range(26, len(precios_cierre)):
        ema12_i = calcular_media_movil_exponencial(precios_cierre[:i+1], 12)
        ema26_i = calcular_media_movil_exponencial(precios_cierre[:i+1], 26)
        if ema12_i and ema26_i:
            macd_series.append(ema12_i - ema26_i)
    
    # La línea señal es la EMA de 9 períodos de la serie MACD
    signal_value = 0
    if len(macd_series) >= 9:
        signal_value = round(calcular_media_movil_exponencial(macd_series, 9), 4)
    
    return {
        "macd_value": macd_value,
        "signal_value": signal_value,
        "is_bullish": macd_value > signal_value,
    }


# ─── FUNCIÓN AUXILIAR: CALCULAR BANDAS DE BOLLINGER ──────────────
# Las bandas de Bollinger muestran un rango de precios esperado.
# Si el precio sale por encima de la banda superior → posible sobrecompra.
# Si cae por debajo de la banda inferior → posible sobreventa / oportunidad.
def calcular_bollinger(precios_cierre, periodo=20, desviaciones=2):
    """
    Calcula las bandas de Bollinger.
    
    - periodo: número de sesiones (por defecto 20)
    - desviaciones: número de desviaciones estándar (por defecto 2)
    
    Retorna:
    - banda_superior: precio límite superior
    - banda_media: media móvil simple (centro)
    - banda_inferior: precio límite inferior
    - posicion: donde está el precio actual respecto a las bandas
    """
    if len(precios_cierre) < periodo:
        return None
    
    # Tomamos los últimos X precios
    ultimos = precios_cierre[-periodo:]
    precio_actual = precios_cierre[-1]
    
    # Banda media = media simple
    media = sum(ultimos) / len(ultimos)
    
    # Calculamos la desviación estándar
    diferencias_al_cuadrado = [(p - media) ** 2 for p in ultimos]
    varianza = sum(diferencias_al_cuadrado) / len(diferencias_al_cuadrado)
    desviacion_estandar = varianza ** 0.5
    
    # Bandas superior e inferior
    banda_superior = round(media + (desviaciones * desviacion_estandar), 2)
    banda_inferior = round(media - (desviaciones * desviacion_estandar), 2)
    banda_media = round(media, 2)
    
    # Determinamos la posición del precio actual
    if precio_actual > banda_superior:
        posicion = "Banda superior"
    elif precio_actual < banda_inferior:
        posicion = "Banda inferior"
    else:
        posicion = "Banda media"
    
    return {
        "banda_superior": banda_superior,
        "banda_media": banda_media,
        "banda_inferior": banda_inferior,
        "posicion": posicion,
    }


# ─── FUNCIÓN AUXILIAR: ANALIZAR VOLUMEN ──────────────────────────
# Compara el volumen de los últimos días con el promedio de los últimos 30 días.
# Un volumen mucho más alto de lo habitual puede indicar movimientos importantes.
def analizar_volumen(datos_historicos, dias_promedio=30):
    """
    Analiza el volumen de negociación.
    
    Retorna:
    - volumen_actual: volumen del último día
    - volumen_promedio_30d: promedio de los últimos 30 días
    - variacion_pct: porcentaje de variación respecto al promedio
    """
    if len(datos_historicos) < dias_promedio:
        return {"volumen_actual": 0, "volumen_promedio_30d": 0, "variacion_pct": 0}
    
    volumen_actual = datos_historicos[-1].get("volume", 0)
    
    volumenes_30d = [d.get("volume", 0) for d in datos_historicos[-dias_promedio:]]
    volumen_promedio = sum(volumenes_30d) / len(volumenes_30d) if volumenes_30d else 0
    
    if volumen_promedio > 0:
        variacion = ((volumen_actual - volumen_promedio) / volumen_promedio) * 100
    else:
        variacion = 0
    
    return {
        "volumen_actual": volumen_actual,
        "volumen_promedio_30d": round(volumen_promedio, 0),
        "variacion_pct": round(variacion, 2),
    }


# ─── FUNCIÓN AUXILIAR: CALCULAR ZONA DE ENTRADA ──────────────────
# Determina si es un buen momento para comprar basándose en los niveles
# de soporte técnicos identificados.
def calcular_zona_entrada(precios_cierre, mm200, bollinger):
    """
    Calcula la zona potencial de entrada basándose en:
    - Soporte de la MM200
    - Banda inferior de Bollinger
    - Precio actual
    
    Retorna:
    - zona_ideal_min: precio mínimo de la zona ideal de entrada
    - zona_ideal_max: precio máximo de la zona ideal de entrada
    - estado: "Zona de entrada activa" o "Esperar retroceso"
    - distancia_zona_pct: cuánto tendría que bajar el precio para entrar en zona
    """
    precio_actual = precios_cierre[-1] if precios_cierre else 0
    
    if not mm200 or not bollinger:
        return {
            "zona_ideal_min": 0,
            "zona_ideal_max": 0,
            "estado": "Datos insuficientes",
            "distancia_zona_pct": 0,
        }
    
    soporte_mm200 = mm200
    soporte_bollinger = bollinger["banda_inferior"]
    
    zona_min = round(min(soporte_mm200, soporte_bollinger), 2)
    zona_max = round(max(soporte_mm200, soporte_bollinger), 2)
    
    if precio_actual <= zona_max:
        estado = "Zona de entrada activa"
    else:
        estado = "Esperar retroceso"
    
    if precio_actual > zona_max and precio_actual > 0:
        distancia = ((precio_actual - zona_max) / precio_actual) * 100
    else:
        distancia = 0
    
    return {
        "precio_actual": round(precio_actual, 2),
        "soporte_mm200": soporte_mm200,
        "soporte_bollinger": soporte_bollinger,
        "zona_ideal_min": zona_min,
        "zona_ideal_max": zona_max,
        "estado": estado,
        "distancia_zona_pct": round(distancia, 2),
    }


# ─── FUNCIÓN AUXILIAR: EVALUAR RIESGOS ───────────────────────────
# Asigna un nivel de riesgo (Bajo, Medio, Alto) según varios factores
def evaluar_riesgos(beta, rsi, volumen_variacion, bollinger_posicion):
    """
    Evalúa el nivel de riesgo a corto, medio y largo plazo.
    """
    # ── Riesgo a corto plazo ──
    riesgo_cp_score = 0
    if rsi and rsi > 70:
        riesgo_cp_score += 2
    elif rsi and rsi < 30:
        riesgo_cp_score += 1
    if bollinger_posicion == "Banda superior":
        riesgo_cp_score += 2
    if volumen_variacion > 50:
        riesgo_cp_score += 1
    
    # ── Riesgo a medio plazo ──
    riesgo_mp_score = 0
    if beta and beta > 1.5:
        riesgo_mp_score += 2
    elif beta and beta > 1.0:
        riesgo_mp_score += 1
    if bollinger_posicion == "Banda superior":
        riesgo_mp_score += 1
    
    # ── Riesgo a largo plazo ──
    riesgo_lp_score = 0
    if beta and beta > 1.8:
        riesgo_lp_score += 2
    elif beta and beta > 1.3:
        riesgo_lp_score += 1
    
    def score_a_nivel(score):
        if score >= 3:
            return "Alto"
        elif score >= 1:
            return "Medio"
        else:
            return "Bajo"
    
    return {
        "riesgo_corto_plazo": score_a_nivel(riesgo_cp_score),
        "riesgo_medio_plazo": score_a_nivel(riesgo_mp_score),
        "riesgo_largo_plazo": score_a_nivel(riesgo_lp_score),
    }


# ─── FUNCIÓN PRINCIPAL: CALCULAR TODOS LOS INDICADORES TÉCNICOS ─
def calcular_todos_indicadores(datos_historicos, beta=1.0):
    """
    Función principal que calcula todos los indicadores técnicos.
    
    - datos_historicos: lista de precios históricos (output de data_fetcher)
    - beta: beta de la empresa (viene del perfil)
    
    Retorna un diccionario con todos los indicadores calculados.
    """
    if not datos_historicos or len(datos_historicos) < 30:
        print("  ✗ No hay suficientes datos históricos para calcular indicadores.")
        return None
    
    # Extraemos solo los precios de cierre en una lista simple
    precios_cierre = [d["close"] for d in datos_historicos]
    precio_actual = precios_cierre[-1]
    
    # ── Medias móviles ──
    mm50 = calcular_media_movil(precios_cierre, 50)
    mm100 = calcular_media_movil(precios_cierre, 100)
    mm200 = calcular_media_movil(precios_cierre, 200)
    
    # ── RSI ──
    rsi = calcular_rsi(precios_cierre)
    
    # ── MACD ──
    macd = calcular_macd(precios_cierre)
    
    # ── Bollinger ──
    bollinger = calcular_bollinger(precios_cierre)
    
    # ── Volumen ──
    volumen = analizar_volumen(datos_historicos)
    
    # ── Zona de entrada ──
    zona_entrada = calcular_zona_entrada(precios_cierre, mm200, bollinger)
    
    # ── Riesgos ──
    bollinger_pos = bollinger["posicion"] if bollinger else "Banda media"
    riesgos = evaluar_riesgos(beta, rsi, volumen["variacion_pct"], bollinger_pos)
    
    # ── Señales de las medias móviles ──
    señal_mm50 = None
    if mm50:
        señal_mm50 = {
            "valor": mm50,
            "precio_encima": precio_actual > mm50,
            "texto": f"Precio {'sobre' if precio_actual > mm50 else 'bajo'} MM50 ({'↑' if precio_actual > mm50 else '↓'})",
        }
    
    señal_mm100 = None
    if mm100:
        señal_mm100 = {
            "valor": mm100,
            "precio_encima": precio_actual > mm100,
            "texto": f"Precio {'sobre' if precio_actual > mm100 else 'bajo'} MM100 ({'↑' if precio_actual > mm100 else '↓'})",
        }
    
    señal_mm200 = None
    if mm200:
        señal_mm200 = {
            "valor": mm200,
            "precio_encima": precio_actual > mm200,
            "texto": f"Precio {'sobre' if precio_actual > mm200 else 'bajo'} MM200 ({'↑' if precio_actual > mm200 else '↓'})",
        }
    
    # ── Señal RSI ──
    señal_rsi = None
    if rsi is not None:
        if rsi > 70:
            zona_rsi = "Sobrecompra"
        elif rsi < 30:
            zona_rsi = "Sobreventa"
        else:
            zona_rsi = "Zona neutra"
        señal_rsi = {"valor": rsi, "zona": zona_rsi, "texto": f"{rsi} — {zona_rsi}"}
    
    # ── Señal MACD ──
    señal_macd = {
        "valor_macd": macd["macd_value"],
        "valor_señal": macd["signal_value"],
        "es_alcista": macd["is_bullish"],
        "texto": f"Línea señal {'alcista ↑' if macd['is_bullish'] else 'bajista ↓'}",
    }
    
    # ── Señal Bollinger ──
    señal_bollinger = None
    if bollinger:
        señal_bollinger = {
            "banda_superior": bollinger["banda_superior"],
            "banda_media": bollinger["banda_media"],
            "banda_inferior": bollinger["banda_inferior"],
            "posicion": bollinger["posicion"],
        }
    
    # ── Señal Volumen ──
    señal_volumen = {
        "volumen_actual": volumen["volumen_actual"],
        "promedio_30d": volumen["volumen_promedio_30d"],
        "variacion_pct": volumen["variacion_pct"],
        "texto": f"{'+' if volumen['variacion_pct'] > 0 else ''}{volumen['variacion_pct']}% vs promedio",
    }
    
    # ── Empaquetamos todo ──
    return {
        "precio_actual": precio_actual,
        "medias_moviles": {
            "mm50": señal_mm50,
            "mm100": señal_mm100,
            "mm200": señal_mm200,
        },
        "rsi": señal_rsi,
        "macd": señal_macd,
        "bollinger": señal_bollinger,
        "volumen": señal_volumen,
        "zona_entrada": zona_entrada,
        "riesgos": riesgos,
    }


# ─── EJEMPLO DE USO ──────────────────────────────────────────────
if __name__ == "__main__":
    import json
    
    # Datos simulados para probar los cálculos
    datos_ejemplo = [{"close": 150 + i * 0.3, "volume": 1000000 + i * 5000} for i in range(250)]
    
    indicadores = calcular_todos_indicadores(datos_ejemplo, beta=1.2)
    
    if indicadores:
        print(json.dumps(indicadores, indent=4, ensure_ascii=False))
    else:
        print("No se pudieron calcular los indicadores.")
