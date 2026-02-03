"""
=====================================================================
PortfolioSentinel — data_fetcher.py (Alpha Vantage)
=====================================================================
Este archivo se conecta con la API de Alpha Vantage para obtener
datos financieros de empresas.

Alpha Vantage es GRATUITO y no requiere tarjeta de crédito.
- 25 llamadas por día (plan gratuito)
- Datos de precios, fundamentales, y más

API Key: Obtén la tuya gratis en https://www.alphavantage.co/support/#api-key

NO necesitas modificar nada en este archivo.
=====================================================================
"""

import requests
import json
from datetime import datetime, timedelta
import time
import streamlit as st


def get_api_key():
    """Obtiene la API key desde los secrets de Streamlit."""
    try:
        return st.secrets["ALPHA_VANTAGE_API_KEY"]
    except:
        # Fallback para testing local
        return "demo"


def api_get(url, max_retries=3):
    """
    Hace una llamada GET a la API con reintentos automáticos.
    
    Alpha Vantage tiene un límite de 25 llamadas/día (gratis).
    Si se alcanza el límite, espera y reintenta.
    """
    for intento in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Alpha Vantage devuelve un mensaje si alcanzas el límite
                if "Note" in data or "Information" in data:
                    print(f"⚠️ Límite de API alcanzado. Esperando 60 segundos...")
                    time.sleep(60)
                    continue
                
                return data
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error en llamada API (intento {intento + 1}/{max_retries}): {e}")
            if intento < max_retries - 1:
                time.sleep(2)
            else:
                return None
    
    return None


# ══════════════════════════════════════════════════════════════════
# INFORMACIÓN DE LA EMPRESA
# ══════════════════════════════════════════════════════════════════

def get_company_profile(ticker):
    """
    Obtiene el perfil general de la empresa.
    
    Retorna: dict con nombre, sector, industria, descripción, etc.
    """
    api_key = get_api_key()
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    
    data = api_get(url)
    
    if not data or not data.get("Symbol"):
        return None
    
    return {
        "symbol": data.get("Symbol", ticker),
        "name": data.get("Name", ""),
        "sector": data.get("Sector", ""),
        "industry": data.get("Industry", ""),
        "exchange": data.get("Exchange", ""),
        "currency": data.get("Currency", "USD"),
        "description": data.get("Description", ""),
        "marketCap": float(data.get("MarketCapitalization", 0)) if data.get("MarketCapitalization") else 0,
        "beta": float(data.get("Beta", 1.0)) if data.get("Beta") else 1.0,
    }


# ══════════════════════════════════════════════════════════════════
# DATOS FUNDAMENTALES
# ══════════════════════════════════════════════════════════════════

def get_fundamentals(ticker):
    """
    Obtiene métricas fundamentales de la empresa.
    
    Retorna: dict con PER, P/B, márgenes, deuda, etc.
    """
    api_key = get_api_key()
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    
    data = api_get(url)
    
    if not data or not data.get("Symbol"):
        return None
    
    # Función auxiliar para convertir a float de forma segura
    def safe_float(value, default=0):
        try:
            return float(value) if value and value != "None" else default
        except:
            return default
    
    return {
        "pe_ratio": safe_float(data.get("PERatio")),
        "price_to_book": safe_float(data.get("PriceToBookRatio")),
        "gross_margin_5y_avg": safe_float(data.get("GrossProfitTTM")) / safe_float(data.get("RevenueTTM")) * 100 if data.get("RevenueTTM") else 0,
        "sales_growth_5y": safe_float(data.get("QuarterlyRevenueGrowthYOY")) * 100,
        "eps_growth_5y": safe_float(data.get("QuarterlyEarningsGrowthYOY")) * 100,
        "debt_to_equity": safe_float(data.get("DebtToEquity")) / 100 if data.get("DebtToEquity") else 0,
        "payout_ratio": safe_float(data.get("PayoutRatio")) * 100 if data.get("PayoutRatio") else 0,
        "has_buyback": False,  # Alpha Vantage no proporciona este dato directamente
        "buyback_amount": 0,
    }


# ══════════════════════════════════════════════════════════════════
# DIVIDENDOS
# ══════════════════════════════════════════════════════════════════

def get_dividend_details(ticker, buy_price=0):
    """
    Obtiene información sobre dividendos.
    
    Args:
        ticker: símbolo de la empresa
        buy_price: precio de compra (para calcular rentabilidad)
    
    Retorna: dict con rentabilidad, crecimiento, etc.
    """
    api_key = get_api_key()
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    
    data = api_get(url)
    
    if not data or not data.get("Symbol"):
        return None
    
    dividend_per_share = float(data.get("DividendPerShare", 0)) if data.get("DividendPerShare") else 0
    dividend_yield = float(data.get("DividendYield", 0)) * 100 if data.get("DividendYield") else 0
    
    # Calcular rentabilidad al precio de compra si se proporciona
    if buy_price > 0 and dividend_per_share > 0:
        yield_at_buy = (dividend_per_share / buy_price) * 100
    else:
        yield_at_buy = dividend_yield
    
    return {
        "pays_dividend": dividend_per_share > 0,
        "dividend_per_share": dividend_per_share,
        "dividend_yield_at_buy": yield_at_buy,
        "dividend_growth_3y": 0,  # Alpha Vantage no proporciona histórico de dividendos fácilmente
        "dividend_growth_5y": 0,
    }


# ══════════════════════════════════════════════════════════════════
# ACCIONES EN CIRCULACIÓN
# ══════════════════════════════════════════════════════════════════

def get_shares_outstanding(ticker):
    """
    Obtiene información sobre acciones en circulación.
    
    Retorna: dict con número de acciones y tendencia.
    """
    api_key = get_api_key()
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    
    data = api_get(url)
    
    if not data or not data.get("Symbol"):
        return None
    
    shares = float(data.get("SharesOutstanding", 0)) if data.get("SharesOutstanding") else 0
    
    return {
        "shares_outstanding": shares,
        "shares_trend_3y": 0,  # No disponible en Alpha Vantage fácilmente
    }


# ══════════════════════════════════════════════════════════════════
# PRECIOS HISTÓRICOS
# ══════════════════════════════════════════════════════════════════

def get_historical_prices(ticker, days=365):
    """
    Obtiene precios históricos diarios.
    
    Args:
        ticker: símbolo de la empresa
        days: número de días a obtener (máx 365 en plan gratuito)
    
    Retorna: lista de dicts con fecha, open, high, low, close, volume
    """
    api_key = get_api_key()
    
    # Alpha Vantage: TIME_SERIES_DAILY devuelve hasta 100 días
    # TIME_SERIES_DAILY_ADJUSTED devuelve datos completos
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={api_key}"
    
    data = api_get(url)
    
    if not data or "Time Series (Daily)" not in data:
        return []
    
    time_series = data["Time Series (Daily)"]
    
    # Convertir a lista de dicts
    historical = []
    for date_str, values in sorted(time_series.items(), reverse=True)[:days]:
        historical.append({
            "date": date_str,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "volume": int(values["5. volume"]),
        })
    
    # Invertir para que el más antiguo esté primero
    return historical[::-1]


# ══════════════════════════════════════════════════════════════════
# DATOS DEL SECTOR (ESTIMACIÓN)
# ══════════════════════════════════════════════════════════════════

def get_sector_data(ticker, sector):
    """
    Obtiene promedios del sector.
    
    Alpha Vantage no proporciona datos sectoriales directos,
    así que usamos estimaciones basadas en el sector.
    """
    # Promedios estimados por sector (basados en S&P 500)
    sector_averages = {
        "Technology": {
            "sector_pe": 28.0,
            "sector_pb": 6.5,
            "sector_gross_margin": 42.0,
            "sector_debt_to_equity": 0.45,
        },
        "Healthcare": {
            "sector_pe": 22.0,
            "sector_pb": 4.2,
            "sector_gross_margin": 38.0,
            "sector_debt_to_equity": 0.55,
        },
        "Financials": {
            "sector_pe": 12.0,
            "sector_pb": 1.2,
            "sector_gross_margin": 28.0,
            "sector_debt_to_equity": 1.8,
        },
        "Consumer Cyclical": {
            "sector_pe": 18.0,
            "sector_pb": 3.5,
            "sector_gross_margin": 32.0,
            "sector_debt_to_equity": 0.65,
        },
        "Industrials": {
            "sector_pe": 20.0,
            "sector_pb": 3.8,
            "sector_gross_margin": 28.0,
            "sector_debt_to_equity": 0.75,
        },
        "Energy": {
            "sector_pe": 15.0,
            "sector_pb": 1.8,
            "sector_gross_margin": 25.0,
            "sector_debt_to_equity": 0.85,
        },
        "Consumer Defensive": {
            "sector_pe": 22.0,
            "sector_pb": 5.0,
            "sector_gross_margin": 35.0,
            "sector_debt_to_equity": 0.50,
        },
        "Utilities": {
            "sector_pe": 18.0,
            "sector_pb": 1.5,
            "sector_gross_margin": 22.0,
            "sector_debt_to_equity": 1.2,
        },
        "Real Estate": {
            "sector_pe": 25.0,
            "sector_pb": 2.0,
            "sector_gross_margin": 30.0,
            "sector_debt_to_equity": 1.5,
        },
        "Communication Services": {
            "sector_pe": 20.0,
            "sector_pb": 3.0,
            "sector_gross_margin": 35.0,
            "sector_debt_to_equity": 0.70,
        },
    }
    
    # Valores por defecto si el sector no está en la lista
    default = {
        "sector_pe": 20.0,
        "sector_pb": 3.5,
        "sector_gross_margin": 30.0,
        "sector_debt_to_equity": 0.70,
    }
    
    return sector_averages.get(sector, default)


# ══════════════════════════════════════════════════════════════════
# NOTICIAS (SIMPLIFICADO)
# ══════════════════════════════════════════════════════════════════

def get_news(ticker):
    """
    Obtiene noticias recientes.
    
    Alpha Vantage tiene un endpoint NEWS_SENTIMENT, pero tiene
    un límite muy bajo. Por ahora retornamos vacío.
    """
    # TODO: Implementar con NEWS_SENTIMENT si es necesario
    return []


# ══════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL: OBTENER TODOS LOS DATOS
# ══════════════════════════════════════════════════════════════════

def get_all_company_data(ticker, shares=0, buy_price=0):
    """
    Función principal que obtiene TODOS los datos de una empresa.
    
    Args:
        ticker: símbolo de la empresa (ej: AAPL, MSFT)
        shares: número de acciones (opcional)
        buy_price: precio de compra (opcional)
    
    Retorna: diccionario con toda la información
    """
    print(f"\n{'='*60}")
    print(f"  Obteniendo datos de {ticker}...")
    print(f"{'='*60}\n")
    
    # 1. Perfil de la empresa
    print("  [1/6] Perfil de la empresa...")
    profile = get_company_profile(ticker)
    if not profile:
        print(f"  ✗ No se encontró la empresa '{ticker}'")
        return None
    
    # 2. Datos fundamentales
    print("  [2/6] Datos fundamentales...")
    fundamentals = get_fundamentals(ticker)
    
    # 3. Datos del sector
    print("  [3/6] Promedios del sector...")
    sector = get_sector_data(ticker, profile.get("sector", ""))
    
    # 4. Dividendos
    print("  [4/6] Información de dividendos...")
    dividends = get_dividend_details(ticker, buy_price)
    
    # 5. Acciones en circulación
    print("  [5/6] Acciones en circulación...")
    shares_outstanding = get_shares_outstanding(ticker)
    
    # 6. Precios históricos
    print("  [6/6] Precios históricos...")
    historical_prices = get_historical_prices(ticker, days=365)
    
    # Noticias (opcional, por ahora vacío)
    news = []
    
    print(f"\n  ✓ Datos de {ticker} obtenidos correctamente\n")
    
    return {
        "ticker": ticker,
        "profile": profile,
        "fundamentals": fundamentals,
        "sector": sector,
        "dividends": dividends,
        "shares_outstanding": shares_outstanding,
        "historical_prices": historical_prices,
        "news": news,
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test con Apple
    data = get_all_company_data("AAPL")
    
    if data:
        print("\n" + "="*60)
        print("  DATOS OBTENIDOS:")
        print("="*60)
        print(f"\n  Empresa: {data['profile']['name']}")
        print(f"  Sector: {data['profile']['sector']}")
        print(f"  PER: {data['fundamentals']['pe_ratio']}")
        print(f"  Precio/Valor Contable: {data['fundamentals']['price_to_book']}")
        print(f"  Días de histórico: {len(data['historical_prices'])}")
        print(f"  Último precio: ${data['historical_prices'][-1]['close']:.2f}")
    else:
        print("\n  ✗ Error al obtener datos")
