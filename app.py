"""
=====================================================================
PortfolioSentinel — app.py (Streamlit - versión final)
=====================================================================
Interfaz principal con integración completa del bot de Telegram
y activación manual de notificaciones.
=====================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import json

# Importamos nuestros módulos
import data_fetcher
import indicators
import scoring
import telegram_bot

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
    .stMetric label { color: #7c8db0 !important; font-size: 0.85rem !important; }
    .stMetric [data-testid="stMetricValue"] {
        color: #4a9eff !important;
        font-size: 1.8rem !important;
        font-family: 'Share Tech Mono', monospace !important;
    }
    h1, h2, h3 {
        color: #e8f1ff !important;
        font-family: 'Share Tech Mono', monospace !important;
    }
    .success-box {
        background-color: rgba(62, 207, 142, 0.1);
        border-left: 4px solid #3ecf8e;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: rgba(240, 168, 78, 0.1);
        border-left: 4px solid #f0a84e;
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


def añadir_a_cartera(ticker, nombre, shares, buy_price, current_price, score, sector):
    """Añade o actualiza una posición en la cartera."""
    existente = next((p for p in st.session_state.cartera if p['ticker'] == ticker), None)
    
    if existente:
        existente['shares'] = shares
        existente['buy_price'] = buy_price
        existente['current_price'] = current_price
        existente['score'] = score
        existente['nombre'] = nombre
        existente['sector'] = sector
        existente['fecha_actualizacion'] = datetime.now().strftime("%Y-%m-%d %H:%M")
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
# SIDEBAR - NAVEGACIÓN
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
st.sidebar.markdown("### 📱 Notificaciones Telegram")

# Test de conexión del bot
if st.sidebar.button("🔔 Test Telegram"):
    bot = st.session_state.bot_telegram
    if bot.activo:
        if bot.test_conexion():
            st.sidebar.success("✓ Bot funcionando")
        else:
            st.sidebar.error("✗ Error al enviar")
    else:
        st.sidebar.warning("⚠ Bot no configurado")

# Enviar resumen de cartera
if st.sidebar.button("📊 Enviar Resumen"):
    if st.session_state.cartera:
        metricas = calcular_metricas_cartera()
        bot = st.session_state.bot_telegram
        top3 = sorted(st.session_state.cartera, key=lambda x: x['score'], reverse=True)[:3]
        
        if bot.notificar_resumen_cartera(
            metricas['total_actual'],
            metricas['rendimiento_pct'],
            top3
        ):
            st.sidebar.success("✓ Resumen enviado")
        else:
            st.sidebar.error("✗ Error al enviar")
    else:
        st.sidebar.info("Cartera vacía")


# ══════════════════════════════════════════════════════════════════
# PÁGINA 1: ANÁLISIS INDIVIDUAL
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
        añadir_cartera = st.checkbox("Añadir a cartera", value=False)
    
    analizar_btn = st.button("🚀 Analizar", type="primary", use_container_width=True)
    
    if analizar_btn and ticker:
        with st.spinner(f"Obteniendo datos de {ticker}..."):
            company_data = data_fetcher.get_all_company_data(ticker, shares, buy_price)
            
            if not company_data:
                st.error(f"❌ No se encontró la empresa con ticker '{ticker}'. Verifica el código.")
            else:
                historical = company_data.get("historical_prices", [])
                beta = company_data.get("profile", {}).get("beta", 1.0)
                indicadores = indicators.calcular_todos_indicadores(historical, beta)
                
                if not indicadores:
                    indicadores = {}
                
                company_data["technical_indicators"] = indicadores
                analisis = scoring.generar_analisis_completo(company_data, indicadores)
                
                st.session_state.ultimo_analisis = {
                    'ticker': ticker,
                    'company_data': company_data,
                    'analisis': analisis
                }
                
                if añadir_cartera and shares > 0 and buy_price > 0:
                    precio_actual = historical[-1].get("close", 0) if historical else 0
                    nombre = company_data.get("profile", {}).get("name", ticker)
                    sector = company_data.get("profile", {}).get("sector", "—")
                    score = analisis.get("score", {}).get("score_total", 0)
                    
                    añadir_a_cartera(ticker, nombre, shares, buy_price, precio_actual, score, sector)
                    st.success(f"✓ {ticker} añadido a tu cartera")
    
    if st.session_state.ultimo_analisis:
        datos = st.session_state.ultimo_analisis
        ticker = datos['ticker']
        company_data = datos['company_data']
        analisis = datos['analisis']
        
        profile = company_data.get("profile", {})
        score_data = analisis.get("score", {})
        score = score_data.get("score_total", 0)
        
        st.markdown("---")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {ticker} — {profile.get('name', '')} ")
            st.caption(f"{profile.get('sector', '')} | {profile.get('exchange', '')}")
        with col2:
            if score >= 70:
                color = "#3ecf8e"
            elif score >= 50:
                color = "#f0a84e"
            else:
                color = "#e85c5c"
            
            st.markdown(f"""
            <div style='text-align: center; padding: 20px; background-color: rgba(30, 45, 69, 0.3); border-radius: 10px; border: 2px solid {color};'>
                <div style='font-size: 3rem; font-weight: bold; color: {color};'>{score}</div>
                <div style='font-size: 0.9rem; color: #7c8db0;'>SCORE</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Indicadores", "📝 Resumen Ejecutivo", "⚠️ Riesgos y Oportunidades", "🎯 Zona de Entrada"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💰 Precio y Valoración")
                precio = analisis.get("precio", {})
                st.metric("PER actual", f"{precio.get('per_actual', 0):.1f}x")
                st.metric("PER sector", f"{precio.get('per_sector', 0):.1f}x")
                st.metric("Precio/Valor Contable", f"{precio.get('precio_valor_contable', 0):.1f}x")
                
                st.markdown("#### 📈 Crecimiento")
                crec = analisis.get("crecimiento", {})
                st.metric("Ventas 5 años", f"{crec.get('ventas_5y', 0):.1f}%")
                st.metric("BPA 5 años", f"{crec.get('bpa_5y', 0):.1f}%")
            
            with col2:
                st.markdown("#### 💎 Dividendo")
                div = analisis.get("dividendo", {})
                st.metric("Rentabilidad", f"{div.get('rentabilidad_precio_compra', 0):.2f}%")
                st.metric("Crecimiento 3 años", f"{div.get('crecimiento_dividendo_3y', 0):.1f}%")
                st.metric("Acciones circulación", div.get('acciones_circulacion', '—'))
                
                st.markdown("#### 💪 Fortaleza Financiera")
                fort = analisis.get("fortaleza_financiera", {})
                st.metric("Deuda/Fondos propios", f"{fort.get('deuda_fondos_propios', 0):.2f}x")
                st.metric("Sector", f"{fort.get('deuda_fondos_propios_sector', 0):.2f}x")
        
        with tab2:
            resumen = analisis.get("resumen_ejecutivo", [])
            for parrafo in resumen:
                st.markdown(parrafo)
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ⚠️ Riesgos")
                riesgos = analisis.get("riesgos", [])
                for riesgo in riesgos:
                    st.markdown(f"""
                    <div class='risk-box'>
                        <strong>•</strong> {riesgo}
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### ✨ Oportunidades")
                oportunidades = analisis.get("oportunidades", [])
                for opp in oportunidades:
                    st.markdown(f"""
                    <div class='success-box'>
                        <strong>•</strong> {opp}
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab4:
            zona = analisis.get("zona_entrada", {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Precio actual", f"${zona.get('precio_actual', 0):.2f}")
            with col2:
                st.metric("Soporte MM200", f"${zona.get('soporte_mm200', 0):.2f}")
            with col3:
                st.metric("Soporte Bollinger", f"${zona.get('soporte_bollinger', 0):.2f}")
            
            estado = zona.get("estado", "—")
            if "activa" in estado.lower():
                st.success(f"✓ {estado}")
                
                # Botón para notificar zona de entrada activa
                if st.button("📱 Enviar notificación de zona activa"):
                    bot = st.session_state.bot_telegram
                    if bot.notificar_zona_entrada_activa(
                        ticker,
                        zona.get('precio_actual', 0),
                        zona.get('zona_ideal_min', 0),
                        zona.get('zona_ideal_max', 0)
                    ):
                        st.success("✓ Notificación enviada")
                    else:
                        st.error("✗ Error al enviar")
            else:
                st.warning(f"⚠ {estado}")


# ══════════════════════════════════════════════════════════════════
# PÁGINA 2: MI CARTERA
# ══════════════════════════════════════════════════════════════════

elif pagina == "💼 Mi Cartera":
    st.title("💼 Mi Cartera")
    
    if not st.session_state.cartera:
        st.info("📭 Tu cartera está vacía. Añade empresas desde 'Análisis Individual' activando la opción 'Añadir a cartera'.")
    else:
        metricas = calcular_metricas_cartera()
        
        st.markdown("### 📊 Resumen General")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Valor Total", f"${metricas['total_actual']:,.0f}")
        with col2:
            st.metric("Invertido", f"${metricas['total_invertido']:,.0f}")
        with col3:
            delta_color = "normal" if metricas['rendimiento_pct'] >= 0 else "inverse"
            st.metric("Rendimiento", f"{metricas['rendimiento_pct']:.1f}%", 
                     delta=f"${metricas['ganancia_perdida']:,.0f}",
                     delta_color=delta_color)
        with col4:
            st.metric("Posiciones", metricas['num_posiciones'])
        with col5:
            st.metric("Score Medio", f"{metricas['score_medio']:.0f}/100")
        
        st.markdown("---")
        
        st.markdown("### 📈 Distribución de la Cartera")
        
        df_posiciones = pd.DataFrame(metricas['posiciones'])
        
        fig = go.Figure(data=[go.Pie(
            labels=df_posiciones['ticker'],
            values=df_posiciones['valor'],
            hole=.4,
            marker=dict(colors=['#4a9eff', '#3ecf8e', '#f0a84e', '#e85c5c', '#a78bfa', '#5bb8d4', '#e8845c', '#8ecf3e'])
        )])
        
        fig.update_layout(
            showlegend=True,
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e8f1ff')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        st.markdown("### 📋 Detalle de Posiciones")
        
        df_tabla = df_posiciones[[
            'ticker', 'nombre', 'shares', 'buy_price', 'current_price', 
            'rendimiento', 'peso', 'score', 'sector'
        ]].copy()
        
        df_tabla.columns = [
            'Ticker', 'Nombre', 'Acciones', 'Precio Compra', 'Precio Actual',
            'Rendimiento %', 'Peso %', 'Score', 'Sector'
        ]
        
        df_tabla['Precio Compra'] = df_tabla['Precio Compra'].apply(lambda x: f"${x:.2f}")
        df_tabla['Precio Actual'] = df_tabla['Precio Actual'].apply(lambda x: f"${x:.2f}")
        df_tabla['Rendimiento %'] = df_tabla['Rendimiento %'].apply(lambda x: f"{x:+.1f}%")
        df_tabla['Peso %'] = df_tabla['Peso %'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        st.markdown("### 🗑️ Gestionar Posiciones")
        st.caption("Selecciona una empresa para eliminarla de la cartera (por ejemplo, después de venderla)")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            ticker_a_eliminar = st.selectbox(
                "Selecciona ticker a eliminar",
                options=[p['ticker'] for p in st.session_state.cartera],
                label_visibility="collapsed"
            )
        with col2:
            if st.button("🗑️ Eliminar", type="secondary", use_container_width=True):
                eliminar_de_cartera(ticker_a_eliminar)
                st.success(f"✓ {ticker_a_eliminar} eliminado de la cartera")
                st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 🏆 Ranking por Score")
        top3 = sorted(st.session_state.cartera, key=lambda x: x['score'], reverse=True)[:3]
        
        col1, col2, col3 = st.columns(3)
        for i, pos in enumerate(top3):
            with [col1, col2, col3][i]:
                medal = ["🥇", "🥈", "🥉"][i]
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background-color: rgba(30, 45, 69, 0.3); border-radius: 10px;'>
                    <div style='font-size: 2rem;'>{medal}</div>
                    <div style='font-size: 1.2rem; font-weight: bold; color: #4a9eff;'>{pos['ticker']}</div>
                    <div style='font-size: 0.9rem; color: #7c8db0;'>{pos['nombre']}</div>
                    <div style='font-size: 1.5rem; font-weight: bold; color: #3ecf8e; margin-top: 10px;'>{pos['score']}/100</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PÁGINA 3: RADAR
# ══════════════════════════════════════════════════════════════════

elif pagina == "🎯 Radar de Oportunidades":
    st.title("🎯 Radar de Oportunidades")
    st.markdown("Escaneo automático del mercado buscando las mejores oportunidades por capitalización.")
    
    if st.button("🚀 Iniciar Escaneo", type="primary"):
        with st.spinner("Escaneando mercado... esto puede tomar 1-2 minutos"):
            
            empresas_radar = {
                "MegaCap": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "UNH"],
                "LargeCap": ["AMD", "INTC", "SPGI", "CRM", "ADBE", "PYPL", "NFLX", "UBER", "SHOP", "ABNB"],
                "MidCap": ["PLTR", "SIRI", "W", "Z", "ROKU", "ETSY", "FSLY", "CFLT", "TOST", "PINS"],
                "SmallCap": ["IONQ", "PERI", "BIMI", "VERB", "NXPL", "SOFI", "ACHR", "JOBY", "NKLA", "LCID"]
            }
            
            resultado_radar = {}
            
            for categoria, tickers in empresas_radar.items():
                empresas_categoria = []
                progress_bar = st.progress(0, text=f"Escaneando {categoria}...")
                
                for idx, ticker in enumerate(tickers):
                    try:
                        company_data = data_fetcher.get_all_company_data(ticker, 0, 0)
                        if not company_data:
                            continue
                        
                        historical = company_data.get("historical_prices", [])
                        beta = company_data.get("profile", {}).get("beta", 1.0)
                        indicadores = indicators.calcular_todos_indicadores(historical, beta)
                        
                        if not indicadores:
                            indicadores = {}
                        
                        company_data["technical_indicators"] = indicadores
                        analisis = scoring.generar_analisis_completo(company_data, indicadores)
                        score = analisis.get("score", {}).get("score_total", 0)
                        
                        precio_actual = historical[-1].get("close", 0) if historical else 0
                        profile = company_data.get("profile", {})
                        
                        señales = []
                        if indicadores:
                            mm = indicadores.get("medias_moviles", {})
                            if mm.get("mm200", {}).get("precio_encima"):
                                señales.append("Sobre MM200")
                            if indicadores.get("macd", {}).get("es_alcista"):
                                señales.append("MACD alcista")
                            rsi = indicadores.get("rsi", {})
                            if rsi and rsi.get("valor", 50) < 35:
                                señales.append("RSI sobreventa")
                        
                        empresas_categoria.append({
                            "ticker": ticker,
                            "nombre": profile.get("name", ""),
                            "sector": profile.get("sector", ""),
                            "precio": precio_actual,
                            "score": score,
                            "señales": señales
                        })
                        
                    except Exception as e:
                        continue
                    
                    progress_bar.progress((idx + 1) / len(tickers), text=f"Escaneando {categoria}... {idx+1}/{len(tickers)}")
                
                empresas_categoria.sort(key=lambda x: x["score"], reverse=True)
                resultado_radar[categoria] = empresas_categoria[:5]
                progress_bar.empty()
            
            st.success("✓ Escaneo completado")
            
            # Botón para enviar las mejores oportunidades por Telegram
            if st.button("📱 Enviar mejores oportunidades por Telegram"):
                bot = st.session_state.bot_telegram
                enviados = 0
                for categoria, empresas in resultado_radar.items():
                    if empresas:  # Solo si hay empresas en esa categoría
                        mejor = empresas[0]
                        if bot.notificar_oportunidad_radar(
                            categoria,
                            mejor['ticker'],
                            mejor['score'],
                            mejor['señales']
                        ):
                            enviados += 1
                
                if enviados > 0:
                    st.success(f"✓ {enviados} notificaciones enviadas")
                else:
                    st.error("✗ Error al enviar notificaciones")
            
            st.markdown("---")
            
            for categoria, empresas in resultado_radar.items():
                st.markdown(f"### {categoria}")
                
                for i, emp in enumerate(empresas):
                    col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
                    
                    with col1:
                        st.markdown(f"**#{i+1}**")
                    with col2:
                        st.markdown(f"**{emp['ticker']}** — {emp['nombre']}")
                    with col3:
                        tags_html = " ".join([f"<span style='background-color: rgba(74, 158, 255, 0.2); padding: 3px 8px; border-radius: 3px; font-size: 0.8rem; margin-right: 5px;'>{s}</span>" for s in emp['señales']])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    with col4:
                        color = "#3ecf8e" if emp['score'] >= 70 else "#f0a84e" if emp['score'] >= 50 else "#e85c5c"
                        st.markdown(f"<div style='text-align: center; font-size: 1.5rem; font-weight: bold; color: {color};'>{emp['score']}</div>", unsafe_allow_html=True)
                
                st.markdown("---")


# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════

st.sidebar.markdown("---")
st.sidebar.caption("PortfolioSentinel v1.0")
st.sidebar.caption("Powered by FMP API")
