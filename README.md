# PortfolioSentinel 📊

Sistema inteligente de análisis y monitoreo de carteras de inversión con notificaciones automáticas a Telegram.

## 🎯 Características

- **Análisis Individual**: Análisis completo de cualquier empresa con score 1-100, indicadores técnicos y fundamentales
- **Gestión de Cartera**: Visualización completa con gráficos, métricas y gestión de posiciones
- **Radar de Oportunidades**: Escaneo automático del mercado por capitalización
- **Notificaciones Telegram**: Alertas automáticas de cambios en el top 10 y nuevas oportunidades
- **Excel Integrado**: Guarda y carga tu cartera automáticamente

## 🚀 Instalación Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/PortfolioSentinel.git
cd PortfolioSentinel
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar API Keys

Crea el archivo `.streamlit/secrets.toml`:
```toml
FMP_API_KEY = "tu_api_key_de_fmp"
TELEGRAM_BOT_TOKEN = "tu_token_de_telegram"
TELEGRAM_CHAT_ID = "tu_chat_id"
```

#### Obtener API Key de FMP:
1. Ve a [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/)
2. Regístrate (plan gratuito: 250 llamadas/día)
3. Copia tu API Key

#### Configurar Bot de Telegram:
1. Habla con [@BotFather](https://t.me/BotFather) en Telegram
2. Ejecuta `/newbot` y sigue las instrucciones
3. Copia el token que te da
4. Inicia conversación con tu bot
5. Envía cualquier mensaje
6. Visita: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
7. Busca `"chat":{"id": TU_NUMERO}` y copia ese número

### 4. Ejecutar la aplicación
```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## ☁️ Desplegar en Streamlit Cloud (GRATIS)

### 1. Sube tu código a GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Configura Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu cuenta de GitHub
3. Selecciona tu repositorio `PortfolioSentinel`
4. En "Advanced settings" → "Secrets", pega el contenido de `secrets.toml`
5. Click en "Deploy"

¡Listo! Tu app estará en `https://tu-usuario-portfoliosentinel.streamlit.app`

## 📁 Estructura del Proyecto

```
PortfolioSentinel/
├── app.py                    # Interfaz Streamlit
├── data_fetcher.py           # Conexión con API de datos
├── indicators.py             # Cálculo de indicadores técnicos
├── scoring.py                # Sistema de puntuación
├── telegram_bot.py           # Notificaciones Telegram
├── requirements.txt          # Dependencias Python
├── .streamlit/
│   ├── config.toml          # Configuración tema
│   └── secrets.toml         # API Keys (NO SUBIR A GITHUB)
├── data/
│   └── cartera.xlsx         # Tu cartera (se crea automáticamente)
└── .gitignore               # Archivos a ignorar en git
```

## 🔔 Notificaciones Telegram

El bot envía alertas automáticas cuando:
- Una empresa entra o sale del top 10 de tu cartera
- Hay un cambio significativo (±5 puntos) en el score de una posición
- Se detecta una nueva oportunidad en el Radar
- Una empresa entra en zona de compra favorable

Para activar las notificaciones, configura el bot en `secrets.toml` y el sistema monitoreará automáticamente.

## 📊 Uso

### Análisis Individual
1. Introduce el ticker (ej: AAPL, MSFT, GOOGL)
2. Opcionalmente: número de acciones y precio de compra
3. Activa "Añadir a cartera" si quieres guardarla
4. Click en "Analizar"

### Gestión de Cartera
1. Ve a "Mi Cartera" en el sidebar
2. Visualiza métricas, gráficos y tabla de posiciones
3. Para eliminar una posición (después de vender), usa el selector "Gestionar Posiciones"

### Radar de Oportunidades
1. Ve a "Radar de Oportunidades"
2. Click en "Iniciar Escaneo"
3. Espera 1-2 minutos mientras escanea 40 empresas
4. Revisa las 5 mejores de cada categoría (MegaCap, LargeCap, MidCap, SmallCap)

## 🛠️ Tecnologías

- **Python 3.9+**
- **Streamlit**: Interfaz web
- **Financial Modeling Prep API**: Datos financieros
- **Pandas**: Gestión de datos
- **Plotly**: Gráficos interactivos
- **Telegram Bot API**: Notificaciones

## 📝 Licencia

MIT License - Libre para uso personal y comercial

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Abre un issue o pull request.

## ⚠️ Disclaimer

Este software es solo para fines educativos e informativos. No constituye asesoramiento financiero. Las decisiones de inversión son responsabilidad exclusiva del usuario.

---

Hecho con ❤️ para inversores inteligentes
