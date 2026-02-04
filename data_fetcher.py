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

from __future__ import annotations

import os
import time
from datetime import datetime
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
    """Pequeño helper para respetar límites si la API responde con nota de rate limit."""
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
                # Error HTTP no recuperable en general
                return None

            data = resp.json()

            # Mensajes de límite / cadencia de Alpha Vantage
            if isinstance(data, dict) and any(k in data for k in ("Note", "Information")):
                # Espera y reintenta
                _sleep_backoff(60)
                continue

            # Si llega aquí, devolvemos data (puede ser {} si no hay contenido)
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
        f"https://www.alphavantage.co/query"
        f"?function=OVERVIEW&symbol={t}&apikey={api_key}"
    )

    data = api_get(url)
    if not data or not isinstance(data, dict) or "Symbol" not in data:
        return None

    # Normalizamos algunos campos
    profile = {
        "symbol": data.get("Symbol", t),
        "name": data.get("Name", t),
        "sector": data.get("Sector", None) or "—",
        "industry": data.get("Industry", None),
        "exchange": data.get("Exchange", None),
        "country": data.get("Country", None),
        "description": data.get("Description", None),
        "beta": _to_float(data.get("Beta", None)) or 1.0,
        "market_cap": _to_float(data.get("MarketCapitalization", None)),
        "pe_ratio": _to_float(data.get("PERatio", None)),
        "peg_ratio": _to_float(data.get("PEGRatio", None)),
        "dividend_yield": _to_float(data.get("DividendYield", None)),
        "fiscal_year_end": data.get("FiscalYearEnd", None),
        "latest_quarter": data.get("LatestQuarter", None),
        "profit_margin": _to_float(data.get("ProfitMargin", None)),
        "operating_margin_ttm": _to_float(data.get("OperatingMarginTTM", None)),
        "return_on_assets_ttm": _to_float(data.get("ReturnOnAssetsTTM", None)),
        "return_on_equity_ttm": _to_float(data.get("ReturnOnEquityTTM", None)),
    }
    return profile


@st.cache_data(show_spinner=False, ttl=15 * 60)  # 15 minutos
def get_daily_adjusted_prices(ticker: str, outputsize: str = "compact") -> Optional[List[Dict[str, Any]]]:
    """
    Obtiene la serie diaria ajustada. Devuelve una lista de velas ordenadas (ascendente por fecha).
    Cada elemento contiene: date, open, high, low, close, adj_close, volume.
    """
    api_key = get_api_key()
    t = (ticker or "").upper().strip()
    if not t:
        return None

    # outputsize: "compact" (últimos ~100) o "full" (histórico completo)
    url = (
        f"https://www.alphavantage.co/query"
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
        # Alpha Vantage keys típicas:
        # 1. open, 2. high, 3. low, 4. close, 5. adjusted close, 6. volume, 7. dividend amount, 8. split coefficient
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

    # Ordenamos por fecha ASC (de más antiguo a más reciente)
    rows.sort(key=lambda r: r["date"])
    return rows


# ──────────────────────────────────────────────────────────────────
# Orquestador para la app
# ──────────────────────────────────────────────────────────────────

def get_all_company_data(ticker: str, shares: int = 0, buy_price: float = 0.0) -> Optional[Dict[str, Any]]:
    """
    Orquesta la obtención de perfil + precios y devuelve el diccionario
    que la app espera para análisis y scoring.

    Estructura devuelta:
    {
        "ticker": str,
        "profile": { ... },
        "historical_prices": [ {date, open, high, low, close, adj_close, volume, ...}, ... ],
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
    prices = get_daily_adjusted_prices(t, outputsize="compact")  # usa "full" si necesitas histórico completo

    if not profile and not prices:
        # Nada que devolver
        return None

    # Precio actual = último 'close' disponible
    last_close = None
    last_date = None
    if prices:
        last = prices[-1]  # tras ordenar ASC, el último es el más reciente
        last_close = last.get("close")
        last_date = last.get("date")

    # Beta por defecto si falta
    if not profile:
