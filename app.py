import logging
from telegram import Update
from telegram.ext import Application, CommandHandler

from order import order_conv_handler
from client import client_conv_handler, show_help
from expired_subscriptions import expired_subscriptions_handler
from balance import balance_handler

# Configuración del bot
TOKEN = '7371100459:AAEpJ3lKAiQX8NFD5ExxHXPefKhw6PfPGbk'

# Configurar el logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context) -> None:
    await update.message.reply_text('¡Bienvenido! Usa /help para ver las opciones disponibles.')

def main():
    application = Application.builder().token(TOKEN).build()

    # Handlers para comandos generales
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', show_help))
    application.add_handler(expired_subscriptions_handler)
    application.add_handler(balance_handler)

    # Añadir handlers de conversación
    application.add_handler(order_conv_handler)
    application.add_handler(client_conv_handler)
    
    logger.info('Aplicación iniciada y lista para recibir comandos.')
    application.run_polling()

if __name__ == '__main__':
    main()
