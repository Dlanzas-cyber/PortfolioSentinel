"""
=====================================================================
PortfolioSentinel — telegram_bot.py
=====================================================================
Bot de Telegram para enviar notificaciones sobre cambios importantes
en las posiciones de tu cartera.

Notificaciones que envía:
- Cambios significativos en el score de las top 10 posiciones
- Nuevas oportunidades detectadas en el Radar
- Alertas cuando una empresa sale o entra en el top 10

Para configurar el bot:
1. Habla con @BotFather en Telegram
2. Crea un nuevo bot con /newbot
3. Copia el token que te da
4. Pégalo en .streamlit/secrets.toml en TELEGRAM_BOT_TOKEN

Para obtener tu CHAT_ID:
1. Inicia conversación con tu bot
2. Envíale cualquier mensaje
3. Visita: https://api.telegram.org/bot<TU_TOKEN>/getUpdates
4. Busca "chat":{"id": tu_numero}
5. Copia ese número y pégalo en secrets.toml

=====================================================================
"""

import requests
import json
from datetime import datetime
import streamlit as st


class TelegramBot:
    """
    Clase para gestionar las notificaciones de Telegram.
    """
    
    def __init__(self):
        """Inicializa el bot con las credenciales de secrets.toml"""
        try:
            self.token = st.secrets["TELEGRAM_BOT_TOKEN"]
            self.chat_id = st.secrets["TELEGRAM_CHAT_ID"]
            self.base_url = f"https://api.telegram.org/bot{self.token}"
            self.activo = True
        except Exception as e:
            print(f"⚠️ Bot de Telegram no configurado: {e}")
            self.activo = False
    
    
    def enviar_mensaje(self, mensaje, parse_mode="HTML"):
        """
        Envía un mensaje de texto al chat configurado.
        
        Args:
            mensaje (str): El texto a enviar
            parse_mode (str): 'HTML' o 'Markdown'
        
        Returns:
            bool: True si se envió correctamente, False si hubo error
        """
        if not self.activo:
            return False
        
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": mensaje,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error al enviar mensaje de Telegram: {e}")
            return False
    
    
    def notificar_cambio_score(self, ticker, score_anterior, score_nuevo):
        """
        Notifica cuando hay un cambio significativo en el score de una empresa.
        """
        diferencia = score_nuevo - score_anterior
        emoji = "📈" if diferencia > 0 else "📉"
        
        mensaje = f"""
{emoji} <b>Cambio en Score</b>

<b>{ticker}</b>
Score anterior: {score_anterior}
Score nuevo: {score_nuevo}
Cambio: {diferencia:+d} puntos

Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}
        """
        
        return self.enviar_mensaje(mensaje.strip())
    
    
    def notificar_entrada_top10(self, ticker, posicion, score):
        """
        Notifica cuando una empresa entra en el top 10.
        """
        mensaje = f"""
🎯 <b>Nueva en Top 10</b>

<b>{ticker}</b> ha entrado en tu top 10

Posición: #{posicion}
Score: {score}/100

¡Revisa el análisis completo en PortfolioSentinel!
        """
        
        return self.enviar_mensaje(mensaje.strip())
    
    
    def notificar_salida_top10(self, ticker, score):
        """
        Notifica cuando una empresa sale del top 10.
        """
        mensaje = f"""
⚠️ <b>Salida del Top 10</b>

<b>{ticker}</b> ha salido de tu top 10

Score actual: {score}/100

Puede ser momento de revisar esta posición.
        """
        
        return self.enviar_mensaje(mensaje.strip())
    
    
    def notificar_oportunidad_radar(self, categoria, ticker, score, señales):
        """
        Notifica cuando el Radar detecta una nueva oportunidad.
        """
        señales_texto = "\n".join([f"  • {s}" for s in señales]) if señales else "  Sin señales técnicas"
        
        mensaje = f"""
✨ <b>Nueva Oportunidad Detectada</b>

Categoría: {categoria}
<b>{ticker}</b>

Score: {score}/100

Señales:
{señales_texto}

Considera analizar esta empresa en detalle.
        """
        
        return self.enviar_mensaje(mensaje.strip())
    
    
    def notificar_resumen_cartera(self, total_valor, rendimiento, top3):
        """
        Envía un resumen diario de la cartera.
        
        Args:
            total_valor (float): Valor total de la cartera
            rendimiento (float): Rendimiento porcentual
            top3 (list): Lista con las top 3 posiciones [{'ticker': 'AAPL', 'score': 85}, ...]
        """
        emoji_rendimiento = "📈" if rendimiento >= 0 else "📉"
        
        top3_texto = "\n".join([
            f"{i+1}. {pos['ticker']}: {pos['score']}/100"
            for i, pos in enumerate(top3)
        ])
        
        mensaje = f"""
📊 <b>Resumen Diario de Cartera</b>

Valor total: ${total_valor:,.0f}
Rendimiento: {emoji_rendimiento} {rendimiento:+.1f}%

<b>Top 3 por Score:</b>
{top3_texto}

Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}
        """
        
        return self.enviar_mensaje(mensaje.strip())
    
    
    def notificar_zona_entrada_activa(self, ticker, precio_actual, zona_min, zona_max):
        """
        Notifica cuando una empresa entra en zona de compra favorable.
        """
        mensaje = f"""
🎯 <b>Zona de Entrada Activa</b>

<b>{ticker}</b>

Precio actual: ${precio_actual:.2f}
Zona ideal: ${zona_min:.2f} - ${zona_max:.2f}

El precio está dentro de la zona de entrada técnicamente favorable.
Considera revisar los fundamentales antes de comprar.
        """
        
        return self.enviar_mensaje(mensaje.strip())
    
    
    def test_conexion(self):
        """
        Prueba la conexión con Telegram enviando un mensaje de test.
        
        Returns:
            bool: True si funciona, False si hay error
        """
        mensaje = """
✅ <b>PortfolioSentinel - Test de Conexión</b>

El bot de Telegram está configurado correctamente y funcionando.

Recibirás notificaciones sobre:
• Cambios en el score de tus empresas
• Nuevas oportunidades en el Radar
• Zonas de entrada activas
• Resúmenes diarios de cartera
        """
        
        return self.enviar_mensaje(mensaje.strip())


# ══════════════════════════════════════════════════════════════════
# MONITOREO AUTOMÁTICO DE CARTERA
# ══════════════════════════════════════════════════════════════════

def monitorear_cambios_cartera(cartera_actual, cartera_anterior, bot):
    """
    Compara la cartera actual con la anterior y envía notificaciones
    de cambios importantes.
    
    Args:
        cartera_actual (list): Lista de posiciones actuales
        cartera_anterior (list): Lista de posiciones anteriores
        bot (TelegramBot): Instancia del bot
    """
    if not bot.activo:
        return
    
    # Convertir a diccionarios para comparar fácilmente
    dict_actual = {p['ticker']: p for p in cartera_actual}
    dict_anterior = {p['ticker']: p for p in cartera_anterior} if cartera_anterior else {}
    
    # Obtener threshold de cambio desde secrets
    threshold = st.secrets.get("SCORE_CHANGE_THRESHOLD", 5)
    
    # Detectar cambios en scores
    for ticker, pos_actual in dict_actual.items():
        if ticker in dict_anterior:
            pos_anterior = dict_anterior[ticker]
            cambio = abs(pos_actual['score'] - pos_anterior['score'])
            
            if cambio >= threshold:
                bot.notificar_cambio_score(
                    ticker,
                    pos_anterior['score'],
                    pos_actual['score']
                )
    
    # Detectar entradas/salidas del top 10
    top10_actual = sorted(cartera_actual, key=lambda x: x['score'], reverse=True)[:10]
    top10_anterior = sorted(cartera_anterior, key=lambda x: x['score'], reverse=True)[:10] if cartera_anterior else []
    
    tickers_top10_actual = {p['ticker'] for p in top10_actual}
    tickers_top10_anterior = {p['ticker'] for p in top10_anterior}
    
    # Nuevas en top 10
    nuevas_top10 = tickers_top10_actual - tickers_top10_anterior
    for ticker in nuevas_top10:
        pos = dict_actual[ticker]
        posicion = next(i+1 for i, p in enumerate(top10_actual) if p['ticker'] == ticker)
        bot.notificar_entrada_top10(ticker, posicion, pos['score'])
    
    # Salidas del top 10
    salidas_top10 = tickers_top10_anterior - tickers_top10_actual
    for ticker in salidas_top10:
        if ticker in dict_actual:  # Solo si sigue en la cartera
            pos = dict_actual[ticker]
            bot.notificar_salida_top10(ticker, pos['score'])


def enviar_resumen_diario(cartera, bot):
    """
    Envía un resumen diario de la cartera.
    Esta función se puede llamar una vez al día.
    """
    if not bot.activo or not cartera:
        return
    
    # Calcular métricas
    total_invertido = sum(p['shares'] * p['buy_price'] for p in cartera)
    total_actual = sum(p['shares'] * p['current_price'] for p in cartera)
    rendimiento = ((total_actual - total_invertido) / total_invertido * 100) if total_invertido > 0 else 0
    
    # Top 3
    top3 = sorted(cartera, key=lambda x: x['score'], reverse=True)[:3]
    
    bot.notificar_resumen_cartera(total_actual, rendimiento, top3)


# ══════════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Crear instancia del bot
    bot = TelegramBot()
    
    # Test de conexión
    if bot.activo:
        print("Enviando mensaje de test...")
        if bot.test_conexion():
            print("✓ Mensaje enviado correctamente")
        else:
            print("✗ Error al enviar mensaje")
    else:
        print("Bot no configurado. Revisa .streamlit/secrets.toml")
