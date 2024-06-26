import logging
import requests
from telegram import Update
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters

# Definir estados de la conversación para cliente
ENTER_NAME, ENTER_PHONE, ENTER_EMAIL = range(9, 12)

logger = logging.getLogger(__name__)

async def enter_name(update: Update, context) -> int:
    await update.message.reply_text('Ingresa el nombre del cliente:')
    return ENTER_NAME

async def enter_phone(update: Update, context) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text('Ingresa el número de teléfono del cliente:')
    return ENTER_PHONE

async def enter_email(update: Update, context) -> int:
    context.user_data['phone'] = update.message.text
    await update.message.reply_text('Ingresa el email del cliente:')
    return ENTER_EMAIL

async def save_client(update: Update, context) -> int:
    context.user_data['email'] = update.message.text
    data = {
        "name": context.user_data['name'],
        "phone_number": context.user_data['phone'],
        "email": context.user_data['email']
    }
    response = requests.post('https://pocketbase-production-634a.up.railway.app/api/collections/clients/records', json=data)
    if response.status_code == 200:
        client = response.json()
        await update.message.reply_text(f'Cliente creado exitosamente con ID: {client["id"]}')
    else:
        await update.message.reply_text('Error al crear el cliente. Inténtalo de nuevo.')
    await show_help(update, context)  # Mostrar el menú de ayuda al finalizar
    return ConversationHandler.END

async def cancel(update: Update, context) -> int:
    await update.message.reply_text('Operación cancelada.')
    await show_help(update, context)  # Mostrar el menú de ayuda al cancelar
    return ConversationHandler.END

async def show_help(update: Update, context) -> None:
    help_text = (
        "Comandos disponibles:\n"
        "/create_order - Crear una nueva orden\n"
        "/create_client - Crear un nuevo cliente\n"
        "/expired_subscriptions - Ver clientes con suscripciones vencidas\n"
        "/balance - Ver el balance actual\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/cancel - Cancelar la operación actual"
    )
    await update.message.reply_text(help_text)

client_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('create_client', enter_name)],
    states={
        ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
        ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_email)],
        ENTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_client)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
