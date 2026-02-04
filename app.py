"""
=====================================================================
PortfolioSentinel — app.py (Streamlit - Fixed)
=====================================================================
Interfaz principal con integración completa del bot de Telegram
y activación manual de notificaciones.
=====================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# Importamos nuestros módulos
try:
    import data_fetcher
    import indicators
    import scoring
    import telegram_bot
except Exception as e:
    st.error(f"Error al importar módulos: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LA PÁGINA
# ══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="PortfolioSentinel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main { background-color: #0a0e1a; }
    .stMetric {
        background-color: #1a2332;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2a3f5f;
    }
    h1, h2, h3 { color: #e8f1ff !important; }
    .success-box {
        background-color: rgba(62, 207, 142, 0.1);
        border-left: 4px solid #3ecf8e;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .risk-box {
        background-color: rgba(232, 92, 92, 0.1);
        border-left: 4px solid #e85c5c;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# GESTIÓN DE ESTADO
# ══════════════════════════════════════════════════════════════════

if 'cartera' not in st.session_state:
    st.session_state.cartera = []

if 'ultimo_analisis' not in st.session_state:
    st.session_state.ultimo_analisis = None

if 'bot_telegram' not in st.session_state:
    st.session_state.bot_telegram = telegram_bot.TelegramBot()

# ══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════

def guardar_cartera_a_excel():
    """Guarda la cartera actual en Excel."""
    if not st.session_state.cartera:
        return
    
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(st.session_state.cartera)
    excel_path = "data/cartera.xlsx"
    
    try:
        df.to_excel(excel_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar cartera: {e}")
        return False

def cargar_cartera_desde_excel():
    """Carga la cartera desde el archivo Excel si existe."""
    excel_path = "data/cartera.xlsx"
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path)
            st.session_state.cartera = df.to_dict('records')
            return True
        except Exception as e:
            st.error(f"Error al cargar cartera: {e}")
            return False
    return False

def añadir_a_cartera(ticker, nombre, shares, buy_price, current_price, score, sector):
    """Añade o actualiza una posición en la cartera."""
    existente = next((p for p in st.session_state.cartera if p['ticker'] == ticker), None)
    
    if existente:
        existente.update({
            'shares': shares,
            'buy_price': buy_price,
            'current_price': current_price,
            'score': score,
            'nombre': nombre,
            'sector': sector,
            'fecha_actualizacion': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    else:
        st.session_state.cartera.append({
            'ticker': ticker,
            'nombre': nombre,
            'shares': shares,
            'buy_price': buy_price,
            'current_price': current_price,
            'score': score,
            'sector': sector,
            'fecha_compra': datetime.now().strftime("%Y-%m-%d"),
            'fecha_actualizacion': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    
    guardar_cartera_a_excel()

def eliminar_de_cartera(ticker):
    """Elimina una posición de la cartera."""
    st.session_state.cartera = [p for p in st.session_state.cartera if p['ticker'] != ticker]
    guardar_cartera_a_excel()

def calcular_metricas_cartera():
    """Calcula las métricas de la cartera completa."""
    if not st.session_state.cartera:
        return None
    
    total_invertido = sum(p['shares'] * p['buy_price'] for p in st.session_state.cartera)
    total_actual = sum(p['shares'] * p['current_price'] for p in st.session_state.cartera)
    ganancia_perdida = total_actual - total_invertido
    rendimiento_pct = (ganancia_perdida / total_invertido * 100) if total_invertido > 0 else 0
    score_medio = sum(p['score'] for p in st.session_state.cartera) / len(st.session_state.cartera)
    
    cartera_con_metricas = []
    for p in st.session_state.cartera:
        valor = p['shares'] * p['current_price']
        peso = (valor / total_actual * 100) if total_actual > 0 else 0
        ret = ((p['current_price'] - p['buy_price']) / p['buy_price'] * 100) if p['buy_price'] > 0 else 0
        
        cartera_con_metricas.append({
            **p,
            'valor': valor,
            'peso': peso,
            'rendimiento': ret
        })
    
    return {
        'total_invertido': total_invertido,
        'total_actual': total_actual,
        'ganancia_perdida': ganancia_perdida,
        'rendimiento_pct': rendimiento_pct,
        'score_medio': score_medio,
        'num_posiciones': len(st.session_state.cartera),
        'posiciones': cartera_con_metricas
    }

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════

st.sidebar.title("📊 PortfolioSentinel")
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Navegación",
    ["🔍 Análisis Individual", "💼 Mi Cartera", "🎯 Radar de Oportunidades"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Configuración")

if st.sidebar.button("📂 Cargar cartera desde Excel"):
    if cargar_cartera_desde_excel():
        st.sidebar.success("✓ Cartera cargada")
    else:
        st.sidebar.info("No hay cartera guardada")

if st.session_state.cartera:
    st.sidebar.info(f"**Posiciones activas:** {len(st.session_state.cartera)}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Telegram")

if st.sidebar.button("🔔 Test"):
    bot = st.session_state.bot_telegram
    if bot.activo:
        if bot.test_conexion():
            st.sidebar.success("✓ Funcionando")
        else:
            st.sidebar.error("✗ Error")
    else:
        st.sidebar.warning("⚠ No configurado")

if st.sidebar.button("📊 Enviar Resumen"):
    if st.session_state.cartera:
        metricas = calcular_metricas_cartera()
        bot = st.session_state.bot_telegram
        top3 = sorted(st.session_state.cartera, key=lambda x: x['score'], reverse=True)[:3]
        
        if bot.notificar_resumen_cartera(metricas['total_actual'], metricas['rendimiento_pct'], top3):
            st.sidebar.success("✓ Enviado")
        else:
            st.sidebar.error("✗ Error")
    else:
        st.sidebar.info("Cartera vacía")

# ══════════════════════════════════════════════════════════════════
# PÁGINA: ANÁLISIS INDIVIDUAL
# ══════════════════════════════════════════════════════════════════

if pagina == "🔍 Análisis Individual":
    st.title("🔍 Análisis Individual de Empresa")
    st.markdown("Introduce el ticker de una empresa para obtener un análisis completo.")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        ticker = st.text_input("Ticker", placeholder="AAPL, MSFT, GOOGL...").upper().strip()
    with col2:
        shares = st.number_input("Acciones", min_value=0, value=0, step=1)
    with col3:
        buy_price = st.number_input("Precio compra", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    with col4:
        añadir_cartera_flag = st.checkbox("Añadir a cartera", value=False)
    
    if st.button("🚀 Analizar", type="primary", use_container_width=True):
        if not ticker:
            st.warning("⚠ Introduce un ticker")
        else:
            with st.spinner(f"Analizando {ticker}..."):
                try:
                    company_data = data_fetcher.get_all_company_data(ticker, shares, buy_price)
                    
                    if not company_data:
                        st.error(f"❌ No se encontró '{ticker}'")
                    else:
                        historical = company_data.get("historical_prices", [])
                        profile = company_data.get("profile", {})
                        beta = profile.get("beta", 1.0)
                        
                        indicadores = indicators.calcular_todos_indicadores(historical, beta) or {}
                        company_data["technical_indicators"] = indicadores
                        
                        analisis = scoring.generar_analisis_completo(company_data, indicadores)
                        
                        st.session_state.ultimo_analisis = {
                            'ticker': ticker,
                            'company_data': company_data,
                            'analisis': analisis
                        }
                        
                        if añadir_cartera_flag and shares > 0 and buy_price > 0:
                            precio_actual = historical[-1].get("close", 0) if historical else 0
                            nombre = profile.get("name", ticker)
                            sector = profile.get("sector", "—")
                            score = analisis.get("score", {}).get("score_total", 0)
                            
                            añadir_a_cartera(ticker, nombre, shares, buy_price, precio_actual, score, sector)
                            st.success(f"✓ {ticker} añadido a cartera")
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Mostrar resultados
    if st.session_state.ultimo_analisis:
        datos = st.session_state.ultimo_analisis
        analisis = datos['analisis']
        score = analisis.get("score", {}).get("score_total", 0)
        
        st.markdown("---")
        st.markdown(f"### {datos['ticker']}")
        st.metric("Score", f"{score}/100")
        
        with st.expander("📊 Ver análisis completo"):
            st.json(analisis)

# ══════════════════════════════════════════════════════════════════
# PÁGINA: MI CARTERA
# ══════════════════════════════════════════════════════════════════

elif pagina == "💼 Mi Cartera":
    st.title("💼 Mi Cartera")
    
    if not st.session_state.cartera:
        st.info("📭 Tu cartera está vacía")
    else:
        metricas = calcular_metricas_cartera()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Valor Total", f"${metricas['total_actual']:,.0f}")
        with col2:
            st.metric("Rendimiento", f"{metricas['rendimiento_pct']:.1f}%")
        with col3:
            st.metric("Posiciones", metricas['num_posiciones'])
        
        st.markdown("---")
        
        df = pd.DataFrame(metricas['posiciones'])
        st.dataframe(df[['ticker', 'nombre', 'shares', 'current_price', 'score']], use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🗑️ Eliminar posición")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            ticker_eliminar = st.selectbox("Ticker", [p['ticker'] for p in st.session_state.cartera])
        with col2:
            if st.button("🗑️ Eliminar"):
                eliminar_de_cartera(ticker_eliminar)
                st.success(f"✓ {ticker_eliminar} eliminado")
                st.rerun()

# ══════════════════════════════════════════════════════════════════
# PÁGINA: RADAR
# ══════════════════════════════════════════════════════════════════

elif pagina == "🎯 Radar de Oportunidades":
    st.title("🎯 Radar de Oportunidades")
    
    if st.button("🚀 Iniciar Escaneo"):
        st.info("⚠ El escaneo completo puede tardar 5-10 minutos debido al límite de 25 llamadas/día de Alpha Vantage. Por ahora, prueba el análisis individual.")

st.sidebar.markdown("---")
st.sidebar.caption("PortfolioSentinel v1.0")
