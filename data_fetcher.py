"""
=====================================================================
PortfolioSentinel — data_fetcher.py
=====================================================================
Este archivo se encarga de conectar con la API de Financial Modeling Prep (FMP)
y obtener todos los datos necesarios para el análisis de cada empresa.

ANTES DE USAR ESTE ARCHIVO:
1. Ve a https://financialmodelingprep.com y crea una cuenta gratuita.
2. Copia tu API Key (un código largo de letras y números).
3. Sustituye el texto "TU_API_KEY_AQUI" por tu API Key real,
   en la línea que pone: API_KEY = "TU_API_KEY_AQUI"
=====================================================================
"""

import requests       # Para hacer llamadas a la API (obtener datos de internet)
import json           # Para procesar datos en formato JSON
from datetime import datetime, timedelta  # Para trabajar con fechas


# ─── CONFIGURACIÓN ───────────────────────────────────────────────
# Aquí va tu API Key de FMP. Sustitúyela cuando la tengas.
API_KEY = "xp24XXnXOiOJTmSorRoBJ9qf1QfGfxDd"

# URL base de la API. No necesitas cambiar esto.
BASE_URL = "https://financialmodelingprep.com/api/v3"


# ─── FUNCIÓN AUXILIAR: HACER LLAMADAS A LA API ───────────────────
# Esta función se usa internamente para hacer cualquier consulta a FMP.
# No necesitas modificarla.
def api_get(endpoint, params=None):
    """
    Hace una llamada GET a la API de FMP.
    - endpoint: la ruta específica que queremos consultar
    - params: parámetros adicionales (opcional)
    Retorna los datos en formato diccionario de Python.
    """
    # Construimos la URL completa añadiendo la API Key
    url = f"{BASE_URL}/{endpoint}"
    
    # Si no hay parámetros extra, creamos un diccionario vacío
    if params is None:
        params = {}
    
    # Añadimos la API Key a los parámetros
    params["apikey"] = API_KEY
    
    try:
        # Hacemos la llamada a la API
        response = requests.get(url, params=params)
        
        # Comprobamos si la llamada fue exitosa (código 200 = OK)
        if response.status_code == 200:
            return response.json()  # Devolvemos los datos
        else:
            # Si hay error, lo mostramos
            print(f"Error en la API: código {response.status_code}")
            print(f"Mensaje: {response.text}")
            return None
    
    except requests.exceptions.ConnectionError:
        # Este error aparece si no hay conexión a internet
        print("Error: No se puede conectar a internet. Comprueba tu conexión.")
        return None
    except Exception as e:
        # Cualquier otro error inesperado
        print(f"Error inesperado: {e}")
        return None


# ─── OBTENER PERFIL DE LA EMPRESA ────────────────────────────────
# Obtiene información básica: nombre, sector, descripción, capitalización...
def get_company_profile(ticker):
    """
    Retorna un diccionario con:
    - name: nombre de la empresa
    - sector: sector al que pertenece
    - industry: industria específica
    - marketCap: capitalización bursátil
    - exchange: bolsa donde cotiza (NASDAQ, NYSE, BME...)
    - description: descripción breve de la empresa
    - beta: sensibilidad al mercado
    """
    data = api_get(f"profile/{ticker}")
    
    if data and len(data) > 0:
        profile = data[0].get("profile", {})
        return {
            "name": profile.get("name", "Desconocido"),
            "sector": profile.get("sector", "Desconocido"),
            "industry": profile.get("industry", "Desconocido"),
            "marketCap": profile.get("marketCap", 0),
            "exchange": profile.get("exchange", "Desconocido"),
            "description": profile.get("description", ""),
            "beta": profile.get("beta", 0),
            "currency": profile.get("currency", "USD"),
        }
    return None


# ─── OBTENER DATOS FUNDAMENTALES ─────────────────────────────────
# Estos son los datos más importantes para el análisis fundamental:
# PER, precio/valor contable, márgenes, deuda, dividendos...
def get_fundamentals(ticker):
    """
    Obtiene los datos fundamentales de la empresa usando los estados
    financieros más recientes.
    
    Retorna un diccionario con todos los ratios necesarios.
    """
    # Obtenemos los datos financieros anuales (los últimos 5 años)
    income_data = api_get(f"income-statement/{ticker}", {"period": "annual", "limit": 5})
    balance_data = api_get(f"balance-sheet-statement/{ticker}", {"period": "annual", "limit": 5})
    cashflow_data = api_get(f"cash-flow-statement/{ticker}", {"period": "annual", "limit": 5})
    
    # También obtenemos los ratios calculados por FMP directamente
    ratios_data = api_get(f"financial-ratios/{ticker}", {"period": "annual", "limit": 5})
    
    # Si no hay datos, retornamos None
    if not income_data or not balance_data or not cashflow_data:
        print(f"No se encontraron datos fundamentales para {ticker}")
        return None
    
    # ── Datos del último año (posición 0 = más reciente) ──
    latest_income = income_data[0] if income_data else {}
    latest_balance = balance_data[0] if balance_data else {}
    latest_cashflow = cashflow_data[0] if cashflow_data else {}
    latest_ratios = ratios_data[0] if ratios_data else {}
    
    # ── Cálculo de márgenes brutos a 5 años ──
    # Calculamos el promedio de los últimos 5 años si están disponibles
    gross_margins = []
    for year_data in income_data:
        revenue = year_data.get("revenue", 0)
        gross_profit = year_data.get("grossProfit", 0)
        if revenue and revenue > 0:
            gross_margins.append((gross_profit / revenue) * 100)
    
    avg_gross_margin_5y = sum(gross_margins) / len(gross_margins) if gross_margins else 0
    
    # ── Cálculo de crecimiento de ventas a 5 años ──
    # Comparamos las ventas del año más antiguo con las del más reciente
    if len(income_data) >= 5:
        oldest_revenue = income_data[4].get("revenue", 0)   # Hace 5 años
        latest_revenue = income_data[0].get("revenue", 0)   # Este año
        if oldest_revenue and oldest_revenue > 0:
            sales_growth_5y = ((latest_revenue - oldest_revenue) / oldest_revenue) * 100
        else:
            sales_growth_5y = 0
    else:
        sales_growth_5y = 0
    
    # ── Cálculo de crecimiento de BPA (Beneficio Por Acción) a 5 años ──
    if len(income_data) >= 5:
        oldest_eps = income_data[4].get("eps", 0)   # Hace 5 años
        latest_eps = income_data[0].get("eps", 0)   # Este año
        if oldest_eps and oldest_eps > 0:
            eps_growth_5y = ((latest_eps - oldest_eps) / oldest_eps) * 100
        else:
            eps_growth_5y = 0
    else:
        eps_growth_5y = 0
    
    # ── Datos de deuda y fortaleza financiera ──
    total_debt = latest_balance.get("totalDebt", 0)
    shareholders_equity = latest_balance.get("totalShareholderEquity", 0)
    
    # Ratio deuda/fondos propios (evitamos división por cero)
    debt_to_equity = (total_debt / shareholders_equity) if shareholders_equity and shareholders_equity != 0 else 0
    
    # ── Datos de dividendo ──
    dividends_per_share = latest_income.get("dividendPerShare", 0)
    payout_ratio = latest_ratios.get("payoutRatio", 0)
    if payout_ratio:
        payout_ratio = payout_ratio * 100  # Convertir a porcentaje
    
    # ── Datos de recompra de acciones (Buyback) ──
    # Un valor negativo en "issuanceOfStock" significa que la empresa recompró acciones
    stock_issuance = latest_cashflow.get("issuanceOfStock", 0)
    has_buyback = stock_issuance is not None and stock_issuance < 0
    buyback_amount = abs(stock_issuance) if has_buyback else 0
    
    # ── Empaquetamos todo en un diccionario ──
    return {
        # Ratios de precio (estos los obtenemos del perfil + precio actual)
        "pe_ratio": latest_ratios.get("peRatio", 0),                    # PER
        "price_to_book": latest_ratios.get("priceToBookRatio", 0),      # Precio/Valor Contable
        
        # Márgenes
        "gross_margin_5y_avg": round(avg_gross_margin_5y, 2),           # Margen bruto promedio 5 años
        
        # Crecimiento
        "sales_growth_5y": round(sales_growth_5y, 2),                   # Crecimiento ventas 5 años
        "eps_growth_5y": round(eps_growth_5y, 2),                       # Crecimiento BPA 5 años
        
        # Fortaleza financiera
        "debt_to_equity": round(debt_to_equity, 2),                     # Deuda/Fondos propios
        "total_debt": total_debt,                                        # Deuda total absoluta
        "shareholders_equity": shareholders_equity,                     # Fondos propios
        
        # Dividendo
        "dividends_per_share": dividends_per_share,                     # Dividendo por acción
        "payout_ratio": round(payout_ratio, 2) if payout_ratio else 0, # Payout ratio (%)
        
        # Buyback
        "has_buyback": has_buyback,                                      # ¿Hace recompra?
        "buyback_amount": buyback_amount,                               # Cantidad recomprada
        
        # Datos en bruto para cálculos posteriores
        "revenue_history": [d.get("revenue", 0) for d in income_data], # Historial de ventas
        "eps_history": [d.get("eps", 0) for d in income_data],         # Historial BPA
    }


# ─── OBTENER DATOS DE DIVIDENDO DETALLADOS ──────────────────────
# Calcula la rentabilidad por dividendo y el crecimiento a 3 y 5 años
def get_dividend_details(ticker, buy_price):
    """
    - ticker: código de la empresa
    - buy_price: precio al que el usuario compró las acciones
    
    Retorna:
    - dividend_yield_at_buy: rentabilidad por dividendo a precio de compra
    - dividend_growth_3y: crecimiento del dividendo en los últimos 3 años
    - dividend_growth_5y: crecimiento del dividendo en los últimos 5 años
    """
    # Obtenemos el historial de dividendos
    data = api_get(f"dividend-history/{ticker}", {"limit": 20})
    
    if not data or len(data) == 0:
        return {
            "dividend_yield_at_buy": 0,
            "dividend_growth_3y": 0,
            "dividend_growth_5y": 0,
            "pays_dividend": False
        }
    
    # Agrupamos los dividendos por año para calcular el dividendo anual total
    dividends_by_year = {}
    for div in data:
        # Extraemos el año de la fecha de pago
        payment_date = div.get("paymentDate", "")
        if payment_date:
            year = payment_date[:4]  # Los primeros 4 caracteres son el año
            amount = div.get("dividend", 0)
            if year not in dividends_by_year:
                dividends_by_year[year] = 0
            dividends_by_year[year] += amount
    
    # Ordenamos los años de más reciente a más antiguo
    sorted_years = sorted(dividends_by_year.keys(), reverse=True)
    
    # Si no hay datos suficientes, retornamos valores por defecto
    if len(sorted_years) == 0:
        return {"dividend_yield_at_buy": 0, "dividend_growth_3y": 0, "dividend_growth_5y": 0, "pays_dividend": False}
    
    # Dividendo anual más reciente
    latest_annual_dividend = dividends_by_year[sorted_years[0]]
    
    # Rentabilidad por dividendo a precio de compra
    dividend_yield_at_buy = (latest_annual_dividend / buy_price) * 100 if buy_price > 0 else 0
    
    # Crecimiento del dividendo a 3 años
    dividend_growth_3y = 0
    if len(sorted_years) >= 4:  # Necesitamos al menos 4 años de datos
        div_3y_ago = dividends_by_year[sorted_years[3]]
        if div_3y_ago > 0:
            dividend_growth_3y = ((latest_annual_dividend - div_3y_ago) / div_3y_ago) * 100
    
    # Crecimiento del dividendo a 5 años
    dividend_growth_5y = 0
    if len(sorted_years) >= 6:  # Necesitamos al menos 6 años de datos
        div_5y_ago = dividends_by_year[sorted_years[5]]
        if div_5y_ago > 0:
            dividend_growth_5y = ((latest_annual_dividend - div_5y_ago) / div_5y_ago) * 100
    
    return {
        "dividend_yield_at_buy": round(dividend_yield_at_buy, 2),
        "dividend_growth_3y": round(dividend_growth_3y, 2),
        "dividend_growth_5y": round(dividend_growth_5y, 2),
        "pays_dividend": latest_annual_dividend > 0,
        "latest_annual_dividend": latest_annual_dividend,
    }


# ─── OBTENER ACCIONES EN CIRCULACIÓN Y SU EVOLUCIÓN ─────────────
# Compara el número de acciones en circulación actual con hace 3 años
def get_shares_outstanding(ticker):
    """
    Retorna:
    - shares_outstanding: número actual de acciones en circulación
    - shares_trend_3y: cambio porcentual en los últimos 3 años
      (negativo = la empresa recompró acciones, positivo = emitió más)
    """
    # Obtenemos los datos de balance de los últimos 5 años
    data = api_get(f"balance-sheet-statement/{ticker}", {"period": "annual", "limit": 5})
    
    if not data or len(data) < 2:
        return {"shares_outstanding": 0, "shares_trend_3y": 0}
    
    # Acciones actuales (dato más reciente)
    current_shares = data[0].get("commonStockSharesOutstanding", 0)
    
    # Acciones hace 3 años (o el dato más antiguo disponible)
    idx_3y = min(3, len(data) - 1)  # Si no hay 3 años, usamos el más antiguo
    shares_3y_ago = data[idx_3y].get("commonStockSharesOutstanding", 0)
    
    # Calculamos el cambio porcentual
    if shares_3y_ago and shares_3y_ago > 0:
        trend = ((current_shares - shares_3y_ago) / shares_3y_ago) * 100
    else:
        trend = 0
    
    return {
        "shares_outstanding": current_shares,
        "shares_trend_3y": round(trend, 2),
    }


# ─── OBTENER PRECIOS HISTÓRICOS ──────────────────────────────────
# Necesarios para calcular los indicadores técnicos (medias móviles, RSI, etc.)
def get_historical_prices(ticker, days=365):
    """
    Obtiene el historial de precios de los últimos X días.
    Por defecto obtiene 1 año de datos (suficiente para calcular
    medias móviles de hasta 200 sesiones).
    
    Retorna una lista de diccionarios con fecha, precio de apertura,
    máximo, mínimo, cierre y volumen.
    """
    # Calculamos las fechas de inicio y fin
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Hacemos la llamada a la API
    data = api_get(
        f"historical-price-full/{ticker}",
        {"from": start_date, "to": end_date}
    )
    
    if not data or "historical" not in data:
        print(f"No se encontró historial de precios para {ticker}")
        return []
    
    # Ordenamos los datos de más antiguo a más reciente (para los cálculos)
    historical = sorted(data["historical"], key=lambda x: x["date"])
    
    # Devolvemos solo los campos que necesitamos
    return [
        {
            "date": item["date"],
            "open": item.get("open", 0),
            "high": item.get("high", 0),
            "low": item.get("low", 0),
            "close": item.get("close", 0),
            "volume": item.get("volume", 0),
        }
        for item in historical
    ]


# ─── OBTENER DATOS DEL SECTOR ────────────────────────────────────
# Para comparar la empresa con sus competidores en el mismo sector
def get_sector_data(ticker):
    """
    Obtiene datos de los competidores principales para calcular
    promedios sectoriales de PER, precio/valor contable, márgenes y deuda.
    
    Retorna un diccionario con los promedios del sector.
    """
    # Primero obtenemos los competidores
    peers_data = api_get(f"stock-peers/{ticker}")
    
    if not peers_data or len(peers_data) == 0:
        return None
    
    # peers_data es una lista con un elemento que contiene la lista de peers
    peers = peers_data[0].get("peers", []) if isinstance(peers_data[0], dict) else peers_data
    
    # Limitamos a los 5 competidores principales para no hacer demasiadas llamadas
    peers = peers[:5] if len(peers) > 5 else peers
    
    # Colectamos los ratios de cada competidor
    pe_ratios = []
    pb_ratios = []
    margins = []
    debt_ratios = []
    
    for peer_ticker in peers:
        # Obtenemos los ratios de cada competidor
        peer_ratios = api_get(f"financial-ratios/{peer_ticker}", {"period": "annual", "limit": 1})
        
        if peer_ratios and len(peer_ratios) > 0:
            ratio = peer_ratios[0]
            
            # PER
            pe = ratio.get("peRatio", None)
            if pe and pe > 0:
                pe_ratios.append(pe)
            
            # Precio/Valor Contable
            pb = ratio.get("priceToBookRatio", None)
            if pb and pb > 0:
                pb_ratios.append(pb)
            
            # Margen bruto
            gm = ratio.get("grossProfitMargin", None)
            if gm:
                margins.append(gm * 100)  # Convertir a porcentaje
            
            # Deuda/Fondos propios
            de = ratio.get("debtEquityRatio", None)
            if de and de >= 0:
                debt_ratios.append(de)
    
    # Calculamos los promedios del sector
    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0
    
    return {
        "sector_pe": avg(pe_ratios),
        "sector_pb": avg(pb_ratios),
        "sector_gross_margin": avg(margins),
        "sector_debt_to_equity": avg(debt_ratios),
        "peers_analyzed": len(peers),
    }


# ─── OBTENER DATOS DE NOTICIAS ───────────────────────────────────
# Noticias recientes sobre la empresa
def get_news(ticker, count=5):
    """
    Obtiene las últimas noticias sobre la empresa.
    Retorna una lista de diccionarios con título, fecha y resumen.
    """
    data = api_get(f"stock/news", {"tickers": ticker, "limit": count})
    
    if not data:
        return []
    
    return [
        {
            "title": item.get("title", ""),
            "date": item.get("publishedDate", ""),
            "summary": item.get("text", ""),
            "source": item.get("source", ""),
        }
        for item in data[:count]
    ]


# ─── FUNCIÓN PRINCIPAL: OBTENER TODOS LOS DATOS DE UNA EMPRESA ──
# Esta es la función que la interfaz llamará cuando el usuario pulse "Analizar"
def get_all_company_data(ticker, shares=0, buy_price=0):
    """
    Función principal que obtiene TODOS los datos necesarios para
    generar el análisis completo de una empresa.
    
    Parámetros:
    - ticker: código de la empresa (ej. "AAPL")
    - shares: número de acciones que tiene el usuario (opcional)
    - buy_price: precio medio de compra del usuario (opcional)
    
    Retorna un diccionario grande con todos los datos organizados.
    """
    print(f"\n{'='*50}")
    print(f"  Analizando: {ticker}")
    print(f"{'='*50}\n")
    
    # Paso 1: Perfil de la empresa
    print("  → Obteniendo perfil...")
    profile = get_company_profile(ticker)
    if not profile:
        print(f"  ✗ No se encontró la empresa con ticker '{ticker}'")
        return None
    
    # Paso 2: Datos fundamentales
    print("  → Obteniendo fundamentales...")
    fundamentals = get_fundamentals(ticker)
    
    # Paso 3: Datos de dividendo
    print("  → Obteniendo datos de dividendo...")
    dividends = get_dividend_details(ticker, buy_price) if buy_price > 0 else {
        "dividend_yield_at_buy": 0, "dividend_growth_3y": 0,
        "dividend_growth_5y": 0, "pays_dividend": False
    }
    
    # Paso 4: Acciones en circulación
    print("  → Obteniendo acciones en circulación...")
    shares_data = get_shares_outstanding(ticker)
    
    # Paso 5: Precios históricos (necesarios para indicadores técnicos)
    print("  → Obteniendo precios históricos...")
    historical_prices = get_historical_prices(ticker, days=365)
    
    # Paso 6: Datos del sector
    print("  → Obteniendo datos del sector...")
    sector_data = get_sector_data(ticker)
    
    # Paso 7: Noticias
    print("  → Obteniendo noticias...")
    news = get_news(ticker)
    
    print(f"\n  ✓ Análisis de {ticker} completado.\n")
    
    # ── Empaquetamos todo en un único diccionario ──
    return {
        "ticker": ticker,
        "user_shares": shares,
        "user_buy_price": buy_price,
        "profile": profile,
        "fundamentals": fundamentals,
        "dividends": dividends,
        "shares_outstanding": shares_data,
        "historical_prices": historical_prices,
        "sector": sector_data,
        "news": news,
        "fetched_at": datetime.now().isoformat(),  # Fecha y hora de la consulta
    }


# ─── EJEMPLO DE USO ──────────────────────────────────────────────
# Este bloque solo se ejecuta si abres este archivo directamente
# (no cuando otro archivo lo importa). Útil para probar.
if __name__ == "__main__":
    # Ejemplo: analizar Apple con 100 acciones compradas a $185
    resultado = get_all_company_data("AAPL", shares=100, buy_price=185.20)
    
    if resultado:
        # Guardamos el resultado en un archivo JSON para revisarlo
        with open("test_output.json", "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=4, ensure_ascii=False)
        print("Datos guardados en test_output.json")
    else:
        print("No se pudieron obtener los datos.")
