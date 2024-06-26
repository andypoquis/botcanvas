import requests
import csv
from io import StringIO
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime

API_URL = 'https://pocketbase-production-634a.up.railway.app/api/collections/subscriptions/records'

async def download_active_emails(update: Update, context: CallbackContext) -> None:
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Obtener suscripciones activas
    response = requests.get(f"{API_URL}?filter=end_date%3E='{current_date}'&expand=client&perPage=150")
    if response.status_code != 200:
        await update.message.reply_text('Error al obtener las suscripciones activas.')
        return
    
    data = response.json()
    active_subscriptions = data.get('items', [])
    
    if not active_subscriptions:
        await update.message.reply_text('No hay suscripciones activas.')
        return
    
    # Crear un archivo CSV en memoria
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Correo Electrónico'])

    for subscription in active_subscriptions:
        client = subscription['expand']['client']
        csv_writer.writerow([client['email']])
    
    csv_file.seek(0)
    
    # Enviar el archivo CSV al usuario
    await update.message.reply_document(document=csv_file, filename='active_subscriptions_emails.csv')

download_active_emails_handler = CommandHandler('download_active_emails', download_active_emails)
