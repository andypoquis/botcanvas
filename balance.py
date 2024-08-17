from datetime import datetime, timedelta

import requests
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

API_URL = 'https://pocketbase.similarity.canvasacademic.com/api/collections/subscriptions/records'

async def get_balance(update: Update, context: CallbackContext) -> None:
    current_date = datetime.now()
    current_date_str = current_date.strftime('%Y-%m-%d')
    first_day_of_month_str = current_date.replace(day=1).strftime('%Y-%m-%d')

    # Obtener suscripciones activas
    active_subscriptions_response = requests.get(f"{API_URL}?filter=end_date%3E='{current_date_str}'&perPage=250")
    active_subscriptions = active_subscriptions_response.json().get('items', [])

    # Obtener suscripciones terminadas
    ended_subscriptions_response = requests.get(f"{API_URL}?filter=end_date%3C='{current_date_str}'&perPage=250")
    ended_subscriptions = ended_subscriptions_response.json().get('items', [])

    # Obtener suscripciones del día de hoy
    today_subscriptions_response = requests.get(f"{API_URL}?filter=created>='{current_date_str}'&perPage=250")
    today_subscriptions = today_subscriptions_response.json().get('items', [])
    today_total = sum(subscription['price_paid'] for subscription in today_subscriptions)

    # Obtener suscripciones del mes actual
    month_subscriptions_response = requests.get(f"{API_URL}?filter=start_date%3E='{first_day_of_month_str}'&perPage=250")
    month_subscriptions = month_subscriptions_response.json().get('items', [])
    month_total = sum(subscription['price_paid'] for subscription in month_subscriptions)

    # Generar mensaje
    message = (
        f"📊 **Balance Actual** 📊\n\n"
        f"🟢 **Suscripciones Activas:** {len(active_subscriptions)}\n"
        f"🔴 **Suscripciones Terminadas:** {len(ended_subscriptions)}\n\n"
        f"💰 **Dinero Ganado Hoy:** PEN {round(today_total, 2)}\n"
        f"📅 **Dinero Ganado en el Mes:** PEN {round(month_total, 2)}\n"
    )
    await update.message.reply_text(message, parse_mode='Markdown')

balance_handler = CommandHandler('balance', get_balance)
