import requests
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime

API_URL = 'https://pocketbase-production-634a.up.railway.app/api/collections/subscriptions/records'
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')

async def expired_subscriptions(update: Update, context: CallbackContext) -> None:
    # Obtener suscripciones vencidas
    response = requests.get(f"{API_URL}?filter=end_date%3C='{CURRENT_DATE}'&expand=client")
    if response.status_code != 200:
        await update.message.reply_text('Error al obtener las suscripciones vencidas.')
        return
    
    data = response.json()
    expired_clients = data.get('items', [])
    
    if not expired_clients:
        await update.message.reply_text('No hay clientes con suscripciones vencidas.')
        return
    
    # Generar mensaje
    message = 'Clientes con suscripciones vencidas:\n\n'
    for item in expired_clients:
        client = item['expand']['client']
        name = client['name']
        phone_number = client['phone_number']
        price_paid = item['price_paid']
        email = client['email']

        message += f'Nombre: {name}\n'
        message += f'Teléfono: {phone_number}\n'
        message += f'Email: {email}\n'
        message += f'Precio pagado: {price_paid}\n'
        whatsapp_link = f"https://api.whatsapp.com/send?phone={phone_number}&text=Hola {name}, tu suscripción ha vencido. Puedes renovarla al mismo precio de {price_paid}.%20¡Contáctanos%20para%20más%20información!"
        message += f'Contactar: [Enlace a WhatsApp]({whatsapp_link})\n\n'
    
    await update.message.reply_text(message, parse_mode='Markdown')

expired_subscriptions_handler = CommandHandler('expired_subscriptions', expired_subscriptions)
