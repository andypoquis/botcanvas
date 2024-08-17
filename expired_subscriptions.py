import csv
from datetime import datetime

import requests
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

API_URL = 'https://pocketbase.similarity.canvasacademic.com/api/collections/subscriptions/records'

async def expired_subscriptions(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        await update.message.reply_text('Por favor, proporciona una fecha en el formato YYYY-MM-DD.')
        return
    
    input_date_str = context.args[0]
    try:
        input_date = datetime.strptime(input_date_str, '%Y-%m-%d')
    except ValueError:
        await update.message.reply_text('Formato de fecha inválido. Usa YYYY-MM-DD.')
        return
    
    current_date = datetime.now()
    response = requests.get(f"{API_URL}?filter=end_date<=%27'{input_date_str}%27&sort=-end_date")
    if response.status_code != 200:
        await update.message.reply_text('Error al obtener las suscripciones.')
        return
    
    data = response.json()
    subscriptions = data.get('items', [])
    
    if not subscriptions:
        await update.message.reply_text('No hay suscripciones que cumplan con los criterios.')
        return
    
    messages = []
    csv_data = []

    for item in subscriptions:
        client = item['expand']['client']
        name = client['name']
        first_name = name.split()[0]
        phone_number = client['phone_number']
        email = client['email']
        end_date_str = item['end_date']
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        price_paid = item['price_paid']

        if end_date < current_date:
            message = f"¡Hola {first_name}! Te recordamos que tu suscripción mensual de Turnitin ha *EXPIRADO*. Renueva ahora por S/19.90 y continúa disfrutando de la originalidad garantizada en tus trabajos. 💼🚀 Contáctanos para renovar. ¡Esperamos tu respuesta!"
        else:
            days_remaining = (end_date - current_date).days
            message = f"¡Hola {first_name}! Te recordamos que tu suscripción mensual está por terminar te queda {days_remaining} días. Renueva ahora por S/19.90 y continúa disfrutando de la originalidad garantizada en tus trabajos. 💼🚀 Contáctanos para renovar. ¡Esperamos tu respuesta!"

        messages.append(message)
        csv_data.append([first_name, phone_number, email, end_date_str, message])
    
    # Guardar en un archivo CSV
    csv_filename = 'subscriptions.csv'
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Nombre', 'Teléfono', 'Email', 'Fecha de Fin', 'Mensaje'])
        writer.writerows(csv_data)
    
    await update.message.reply_text(f'Se han procesado {len(subscriptions)} suscripciones. Los mensajes se han guardado en {csv_filename}.', parse_mode='Markdown')

expired_subscriptions_handler = CommandHandler('expired_subscriptions', expired_subscriptions)

