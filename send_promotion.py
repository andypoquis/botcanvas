import requests
import pandas as pd
from io import BytesIO
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime

API_URL = 'https://pocketbase.similarity.canvasacademic.com/api/collections/subscriptions/records'

PROMOTION_MESSAGE = (
    "📢 *¡Turnitin a Mitad de Precio!* 📢\n\n"
    "🎓 *¡Solo S/12.5 al mes!* Suscríbete por un año por *S/150* (precio normal *S/249.95*) y obtén un *50% de descuento*. "
    "Esta oferta exclusiva incluye *activación inmediata*, *envío de hasta 150 documentos diarios*, *sin repositorio* (tus documentos no se guardan) "
    "y *soporte 24/7*. Solo *3 cuentas disponibles para activar*. 💡 *Ahorra y asegura la originalidad de tus trabajos académicos todo el año*. "
    "*¡Espero tu respuesta para aprovechar esta oferta única!* 🎉"
)

async def send_promotion(update: Update, context: CallbackContext) -> None:
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
    
    # Generar datos para el archivo Excel
    rows = []
    for subscription in active_subscriptions:
        client = subscription['expand']['client']
        name = client['name']
        phone_number = client['phone_number']
        whatsapp_link = (
            f"https://api.whatsapp.com/send?phone={phone_number}&text="
            f"%F0%9F%93%A2%20*%C2%A1Turnitin%20a%20Mitad%20de%20Precio!*%20%F0%9F%93%A2%0A%0A"
            f"%F0%9F%8E%93%20*%C2%A1Solo%20S%2F12.5%20al%20mes!*%20Suscr%C3%ADbete%20por%20un%20a%C3%B1o%20por%20"
            f"*S%2F150*%20(precio%20normal%20*S%2F249.95*)%20y%20obt%C3%A9n%20un%20*50%25%20de%20descuento*.%20Esta%20oferta%20exclusiva%20"
            f"incluye%20*activaci%C3%B3n%20inmediata*%2C%20*env%C3%ADo%20de%20hasta%20150%20documentos%20diarios*%2C%20"
            f"*sin%20repositorio*%20(tus%20documentos%20no%20se%20guardan)%20y%20*soporte%2024%2F7*.%20Solo%20*3%20cuentas%20"
            f"disponibles%20para%20activar*.%20%F0%9F%92%A1%20*Ahorra%20y%20asegura%20la%20originalidad%20de%20tus%20trabajos%20"
            f"acad%C3%A9micos%20todo%20el%20a%C3%B1o*.%20*%C2%A1Espero%20tu%20respuesta%20para%20aprovechar%20esta%20oferta%20%C3%BAnica!*%20%F0%9F%8E%89%0A"
        )
        rows.append([name, phone_number, whatsapp_link])
    
    df = pd.DataFrame(rows, columns=['Nombre', 'Teléfono', 'Enlace WhatsApp'])

    # Guardar el archivo en memoria
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Suscripciones Activas')
    
    excel_buffer.seek(0)
    
    # Enviar el archivo Excel al usuario
    await update.message.reply_document(document=excel_buffer, filename='suscripciones_activas.xlsx')

send_promotion_handler = CommandHandler('send_promotion', send_promotion)
