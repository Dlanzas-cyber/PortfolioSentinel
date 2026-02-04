# =====================================================================
# PortfolioSentinel — data_fetcher.py (Alpha Vantage)
# =====================================================================
# Conector a la API de Alpha Vantage para obtener:
#  - Perfil de empresa (OVERVIEW)
#  - Precios diarios ajustados (TIME_SERIES_DAILY_ADJUSTED)
#
# Compatible con app.py:
#  - Proporciona get_all_company_data(ticker, shares, buy_price)
#  - Estructura: profile, historical_prices, current_price, etc.
# =====================================================================

import os
import time
from typing import Dict, Any, List, Optional

import requests
import streamlit as st


# ──────────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    """
    Obtiene la API key de Alpha Vantage:
      1) st.secrets["ALPHA_VANTAGE_API_KEY"]
      2) os.environ["ALPHA_VANTAGE_API_KEY"]
      3) "demo" (fallback)
    """
    # 1) Streamlit secrets
    try:
        key = st.secrets["ALPHA_VANTAGE_API_KEY"]
        if key:
            return key
    except Exception:
        pass

    # 2) Variables de entorno
    key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if key:
        return key

    # 3) Fallback
    return "demo"


def _to_float(value: Any) -> Optional[float]:
    try:
        if value in (None, "", "None"):
            return None
        return float(value)
    except Exception:
        return None


def _sleep_backoff(seconds: float) -> None:
    """Espera simple para respetar límites si la API responde con rate limit."""
    try:
        time.sleep(seconds)
    except Exception:
        pass


def api_get(url: str, max_retries: int = 3, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """
    Llamada GET con reintentos básicos.
    Maneja los mensajes de límite de Alpha Vantage ("Note", "Information").
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code != 200:
                return None

            data = resp.json()

            # Mensajes de límite / cadencia de Alpha Vantage
            if isinstance(data, dict) and any(k in data for k in ("Note", "Information")):
                _sleep_backoff(60)
                continue

            return data
        except Exception:
            if attempt < max_retries:
                _sleep_backoff(2)
            else:
                return None

    return None


# ──────────────────────────────────────────────────────────────────
# Fetchers específicos de Alpha Vantage
# ──────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False, ttl=60 * 60)  # 1 hora
def get_company_profile(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene el perfil de la empresa desde OVERVIEW.
    Retorna un dict con campos clave utilizados por la app y scoring.
    """
    api_key = get_api_key()
    t = (ticker or "").upper().strip()
    if not t:
        return None

    url = (
        "https://www.alphavantage.co/query"
        f"?function=OVERVIEW&symbol={t}&apikey={api_key}"
    )

    data = api_get(url)
    if not data or not isinstance(data, dict) or "Symbol" not in data:
        return None

    profile = {
        "symbol": data.get("Symbol", t),
        "name": data.get("Name", t),
        "sector": data.get("Sector") or "—",
        "industry": data.get("Industry"),
        "exchange": data.get("Exchange"),
        "country": data.get("Country"),
        "description": data.get("Description"),
        "beta": _to_float(data.get("Beta")) or 1.0,
        "market_cap": _to_float(data.get("MarketCapitalization")),
        "pe_ratio": _to_float(data.get("PERatio")),
        "peg_ratio": _to_float(data.get("PEGRatio")),
        "dividend_yield": _to_float(data.get("DividendYield")),
        "fiscal_year_end": data.get("FiscalYearEnd"),
        "latest_quarter": data.get("LatestQuarter"),
        "profit_margin": _to_float(data.get("ProfitMargin")),
        "operating_margin_ttm": _to_float(data.get("OperatingMarginTTM")),
        "return_on_assets_ttm": _to_float(data.get("ReturnOnAssetsTTM")),
        "return_on_equity_ttm": _to_float(data.get("ReturnOnEquityTTM")),
    }
    return profile


@st.cache_data(show_spinner=False, ttl=15 * 60)  # 15 minutos
def get_daily_adjusted_prices(ticker: str, outputsize: str = "compact") -> Optional[List[Dict[str, Any]]]:
    """
    Obtiene la serie diaria ajustada. Devuelve una lista de velas ordenadas (ascendente por fecha).
    Cada elemento: date, open, high, low, close, adj_close, volume, dividend, split_coeff
    """
    api_key = get_api_key()
    t = (ticker or "").upper().strip()
    if not t:
        return None

    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY_ADJUSTED&symbol={t}&outputsize={outputsize}&apikey={api_key}"
    )

    data = api_get(url)
    if not data or not isinstance(data, dict):
        return None

    ts_key = "Time Series (Daily)"
    if ts_key not in data:
        return None

    series = data[ts_key]  # dict: "YYYY-MM-DD" -> campos
    rows: List[Dict[str, Any]] = []
    for date_str, vals in series.items():
        rows.append({
            "date": date_str,
            "open": _to_float(vals.get("1. open")),
            "high": _to_float(vals.get("2. high")),
            "low": _to_float(vals.get("3. low")),
            "close": _to_float(vals.get("4. close")),
            "adj_close": _to_float(vals.get("5. adjusted close")),
            "volume": _to_float(vals.get("6. volume")),
            "dividend": _to_float(vals.get("7. dividend amount")),
            "split_coeff": _to_float(vals.get("8. split coefficient")),
        })

    # Ordena por fecha ASC (de más antiguo a más reciente)
    rows.sort(key=lambda r: r["date"])
    return rows


# ──────────────────────────────────────────────────────────────────
# Orquestador para la app
# ──────────────────────────────────────────────────────────────────

def get_all_company_data(ticker: str, shares: int = 0, buy_price: float = 0.0) -> Optional[Dict[str, Any]]:
    """
    Devuelve estructura esperada por app.py:
    {
        "ticker": str,
        "profile": {...},
        "historical_prices": [...],
        "current_price": float,
        "last_refreshed": "YYYY-MM-DD",
        "shares": int,
        "buy_price": float
    }
    """
    t = (ticker or "").upper().strip()
    if not t:
        return None

    profile = get_company_profile(t)
    prices = get_daily_adjusted_prices(t, outputsize="compact")  # usa "full" si necesitas todo el histórico

    if not profile and not prices:
        return None

    last_close = 0.0
    last_date = None
    if prices:
        last = prices[-1]  # último tras ordenar ASC
        last_close = last.get("close") or 0.0
        last_date = last.get("date")

    if not profile:
        profile = {
            "symbol": t,
            "name": t,
            "sector": "—",
            "beta": 1.0,
        }
    else:
        profile["beta"] = profile.get("beta", 1.0) or 1.0

    result = {
        "ticker": t,
        "profile": profile,
        "historical_prices": prices or [],
        "current_price": last_close,
        "last_refreshed": last_date,
        "shares": int(shares or 0),
        "buy_price": float(buy_price or 0.0),
    }
    return result


# ──────────────────────────────────────────────────────────────────
# Prueba rápida desde consola
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ejecuta: python data_fetcher.py
    # Usa la API key de secrets/env o "demo" (MSFT suele funcionar con demo).
    test_ticker = os.environ.get("TEST_TICKER", "MSFT")
    print(f"Testing data_fetcher with ticker {test_ticker}...")

    prof = get_company_profile(test_ticker)
    prices = get_daily_adjusted_prices(test_ticker, outputsize="compact")
    data = get_all_company_data(test_ticker, shares=10, buy_price=100.0)

    print("Profile (resumen):", prof and {k: prof[k] for k in ("symbol", "name", "sector", "beta")})
    if prices:
        print("Last 3 candles:", prices[-3:])
    print("All data keys:", list((data or {}).keys()))
