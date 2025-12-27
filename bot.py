#!/usr/bin/env python3
"""
Bot de Telegram para reenviar videos, fotos y documentos
entre canales/grupos automáticamente.
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes
)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
SOURCE_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID'))
DESTINATION_CHAT_ID = int(os.getenv('DESTINATION_CHAT_ID'))


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja mensajes con medios (fotos, videos, documentos).
    Solo reenvía si provienen del canal/grupo origen.
    """
    message = update.message or update.channel_post
    
    if not message:
        return
    
    # Verificar que el mensaje viene del canal/grupo origen
    if message.chat_id != SOURCE_CHAT_ID:
        return
    
    try:
        # Determinar el tipo de medio
        media_type = None
        if message.photo:
            media_type = "📷 Foto"
        elif message.video:
            media_type = "🎥 Video"
        elif message.document:
            media_type = "📄 Documento"
        
        if media_type:
            # Reenviar el mensaje al canal/grupo destino
            await message.forward(chat_id=DESTINATION_CHAT_ID)
            logger.info(f"{media_type} reenviado desde {SOURCE_CHAT_ID} a {DESTINATION_CHAT_ID}")
    
    except Exception as e:
        logger.error(f"Error al reenviar mensaje: {e}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores de la aplicación."""
    logger.error(f"Error: {context.error}")


def main():
    """Inicia el bot."""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN no configurado. Revisa tu archivo .env")
        return
    
    if not SOURCE_CHAT_ID or not DESTINATION_CHAT_ID:
        logger.error("❌ SOURCE_CHAT_ID o DESTINATION_CHAT_ID no configurados")
        return
    
    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Filtro combinado para fotos, videos y documentos
    media_filter = (
        filters.PHOTO | 
        filters.VIDEO | 
        filters.Document.ALL
    )
    
    # Añadir handler para mensajes con medios
    application.add_handler(
        MessageHandler(media_filter, handle_media)
    )
    
    # Añadir handler de errores
    application.add_error_handler(error_handler)
    
    # Iniciar bot
    logger.info("🤖 Bot iniciado. Esperando mensajes...")
    logger.info(f"📥 Origen: {SOURCE_CHAT_ID}")
    logger.info(f"📤 Destino: {DESTINATION_CHAT_ID}")
    
    # Ejecutar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
