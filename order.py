import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters

# Definir estados de la conversación para orden
SELECT_CLIENT, SELECT_PRODUCT, SELECT_VARIANT, ENTER_START_DATE, ENTER_END_DATE, ENTER_PRICE, CONFIRM_SUBSCRIPTION, ADD_ANOTHER_SUBSCRIPTION, SELECT_STATUS = range(9)

logger = logging.getLogger(__name__)

# Funciones para crear orden
async def start_order(update: Update, context) -> int:
    logger.info('Iniciando la creación de una orden')
    context.user_data['subscriptions'] = []  # Inicializar las suscripciones
    await update.message.reply_text('Vamos a empezar seleccionando un cliente.')
    return await list_clients(update, context)

async def list_clients(update: Update, context) -> int:
    logger.info('Listando clientes')
    response = requests.get('https://pocketbase-production-634a.up.railway.app/api/collections/clients/records?perPage=150')
    clients = response.json().get('items', [])
    buttons = [[InlineKeyboardButton(client['name'], callback_data=client['id'])] for client in clients]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text('Selecciona un cliente:', reply_markup=keyboard)
    return SELECT_CLIENT

async def list_products(update: Update, context) -> int:
    logger.info('Listando productos')
    query = update.callback_query
    context.user_data['client_id'] = query.data
    response = requests.get('https://pocketbase-production-634a.up.railway.app/api/collections/products/records')
    products = response.json().get('items', [])
    buttons = [[InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text('Selecciona un producto:', reply_markup=keyboard)
    return SELECT_PRODUCT

async def list_variants(update: Update, context) -> int:
    logger.info('Listando variantes')
    query = update.callback_query
    context.user_data['product_id'] = query.data
    response = requests.get('https://pocketbase-production-634a.up.railway.app/api/collections/variants/records')
    variants = response.json().get('items', [])
    buttons = [[InlineKeyboardButton(variant['name'], callback_data=variant['id'])] for variant in variants]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text('Selecciona una variante:', reply_markup=keyboard)
    return SELECT_VARIANT

async def enter_start_date(update: Update, context) -> int:
    logger.info('Ingresando fecha de inicio')
    query = update.callback_query
    context.user_data['variant_id'] = query.data
    await query.edit_message_text('Ingresa la fecha de inicio (dd/mm/aaaa):')
    return ENTER_START_DATE

async def enter_end_date(update: Update, context) -> int:
    logger.info('Ingresando fecha de fin')
    try:
        start_date = datetime.strptime(update.message.text, '%d/%m/%Y')
        context.user_data['start_date'] = start_date.isoformat() + 'Z'
        await update.message.reply_text('Ingresa la fecha de fin (dd/mm/aaaa):')
        return ENTER_END_DATE
    except ValueError:
        await update.message.reply_text('Formato de fecha inválido. Por favor, ingresa la fecha de inicio en el formato dd/mm/aaaa:')
        return ENTER_START_DATE

async def enter_price(update: Update, context) -> int:
    logger.info('Ingresando precio')
    try:
        end_date = datetime.strptime(update.message.text, '%d/%m/%Y')
        context.user_data['end_date'] = end_date.isoformat() + 'Z'
        await update.message.reply_text('Ingresa el precio pagado:')
        return ENTER_PRICE
    except ValueError:
        await update.message.reply_text('Formato de fecha inválido. Por favor, ingresa la fecha de fin en el formato dd/mm/aaaa:')
        return ENTER_END_DATE

async def confirm_subscription(update: Update, context) -> int:
    logger.info('Confirmando suscripción')
    try:
        context.user_data['price_paid'] = float(update.message.text)
        data = {
            "product": context.user_data['product_id'],
            "price_paid": context.user_data['price_paid'],
            "start_date": context.user_data['start_date'],
            "end_date": context.user_data['end_date'],
            "variant": context.user_data['variant_id'],
            "client": context.user_data['client_id']
        }
        response = requests.post('https://pocketbase-production-634a.up.railway.app/api/collections/subscriptions/records', json=data)
        subscription = response.json()
        context.user_data['subscriptions'].append(subscription)
        await update.message.reply_text('Suscripción creada. ¿Deseas agregar otra suscripción? (si/no)')
        return ADD_ANOTHER_SUBSCRIPTION
    except ValueError:
        await update.message.reply_text('Por favor, ingresa un valor numérico válido para el precio:')
        return ENTER_PRICE

async def add_another_subscription(update: Update, context) -> int:
    logger.info('Agregando otra suscripción')
    if update.message.text.lower() == 'si':
        return await list_products(update, context)
    else:
        return await select_status(update, context)

async def select_status(update: Update, context) -> int:
    logger.info('Seleccionando estado')
    buttons = [
        [InlineKeyboardButton('Pagado', callback_data='pagado')],
        [InlineKeyboardButton('Pendiente', callback_data='pendiente')]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text('Selecciona el estado de la orden:', reply_markup=keyboard)
    return SELECT_STATUS

async def create_order(update: Update, context) -> int:
    logger.info('Creando orden')
    query = update.callback_query
    context.user_data['status'] = query.data
    subscriptions = context.user_data['subscriptions']
    
    total_price = sum(float(subscription['price_paid']) for subscription in subscriptions)
    
    data = {
        "subscriptions": [sub['id'] for sub in subscriptions],
        "totalprice": total_price,
        "order_date": context.user_data['start_date'],
        "status": context.user_data['status'],
        "client": context.user_data['client_id']
    }
    response = requests.post('https://pocketbase-production-634a.up.railway.app/api/collections/orders/records', json=data)
    order = response.json()
    await query.edit_message_text(f'Orden creada con ID: {order["id"]}')
    context.user_data.clear()  # Limpiar user_data para evitar acumulación de suscripciones
    await show_help(query, context)  # Mostrar el menú de ayuda al finalizar
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

order_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('create_order', start_order)],
    states={
        SELECT_CLIENT: [CallbackQueryHandler(list_products)],
        SELECT_PRODUCT: [CallbackQueryHandler(list_variants)],
        SELECT_VARIANT: [CallbackQueryHandler(enter_start_date)],
        ENTER_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_end_date)],
        ENTER_END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_price)],
        ENTER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_subscription)],
        ADD_ANOTHER_SUBSCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_another_subscription)],
        SELECT_STATUS: [CallbackQueryHandler(create_order)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
