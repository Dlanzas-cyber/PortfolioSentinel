"""
PortfolioSentinel — app.py (versión debug)
"""

import streamlit as st

# Test inicial para verificar que la app arranca
st.title("🔧 PortfolioSentinel - Debug Mode")

# Verificar que los secrets existen
st.write("### Verificación de configuración:")

try:
    api_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
    st.success(f"✅ ALPHA_VANTAGE_API_KEY encontrada (primeros 5 caracteres: {api_key[:5]}...)")
except Exception as e:
    st.error(f"❌ ALPHA_VANTAGE_API_KEY no encontrada: {e}")

try:
    bot_token = st.secrets["TELEGRAM_BOT_TOKEN"]
    st.success(f"✅ TELEGRAM_BOT_TOKEN encontrada")
except Exception as e:
    st.error(f"❌ TELEGRAM_BOT_TOKEN no encontrada: {e}")

try:
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    st.success(f"✅ TELEGRAM_CHAT_ID encontrada: {chat_id}")
except Exception as e:
    st.error(f"❌ TELEGRAM_CHAT_ID no encontrada: {e}")

# Intentar importar los módulos
st.write("### Verificación de módulos:")

try:
    import data_fetcher
    st.success("✅ data_fetcher importado correctamente")
except Exception as e:
    st.error(f"❌ Error al importar data_fetcher: {e}")

try:
    import indicators
    st.success("✅ indicators importado correctamente")
except Exception as e:
    st.error(f"❌ Error al importar indicators: {e}")

try:
    import scoring
    st.success("✅ scoring importado correctamente")
except Exception as e:
    st.error(f"❌ Error al importar scoring: {e}")

try:
    import telegram_bot
    st.success("✅ telegram_bot importado correctamente")
except Exception as e:
    st.error(f"❌ Error al importar telegram_bot: {e}")

st.write("---")
st.write("Si todos los checks están en ✅, la configuración es correcta.")
st.write("Si hay errores ❌, copia el mensaje de error completo.")
