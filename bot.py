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
from downloader import download_media

# Dominios soportados
SUPPORTED_DOMAINS = [
    'tiktok.com', 'vm.tiktok.com',
    'youtube.com', 'youtu.be',
    'instagram.com',
    'open.spotify.com'
]

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
def get_chat_id(env_var):
    """Obtiene y limpia el ID del chat de las variables de entorno."""
    val = os.getenv(env_var, '')
    if not val:
        return None
    # Limpiar espacios y comillas comunes
    val = val.strip().strip("'").strip('"')
    # Corregir error común de doble guión (copy-paste) -> --100... a -100...
    while val.startswith('--'):
        val = val[1:]
    return int(val)

BOT_TOKEN = os.getenv('BOT_TOKEN')
SOURCE_CHAT_ID = get_chat_id('SOURCE_CHAT_ID')
DESTINATION_CHAT_ID = get_chat_id('DESTINATION_CHAT_ID')


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
            try:
                # Intentar reenviar (Mantiene "Reenviado de...")
                await message.forward(chat_id=DESTINATION_CHAT_ID)
                logger.info(f"✅ {media_type} reenviado (Forward) a {DESTINATION_CHAT_ID}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo reenviar (Forward): {e}. Intentando copiar...")
                # Fallback: Copiar contenido (Si falla forward por privacidad/permisos)
                try:
                    await message.copy(chat_id=DESTINATION_CHAT_ID)
                    logger.info(f"✅ {media_type} copiado (Copy) a {DESTINATION_CHAT_ID}")
                except Exception as e2:
                    logger.error(f"❌ Error CRÍTICO: No se pudo ni reenviar ni copiar: {e2}")
    
    except Exception as e:
        logger.error(f"❌ Error general en handle_media: {e}")


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detecta enlaces y descarga contenido multimedia."""
    message = update.message or update.channel_post
    
    if not message or not message.text:
        return
        
    # Verificar origen
    if message.chat_id != SOURCE_CHAT_ID:
        return

    text = message.text.lower()
    
    # Verificar si contiene un link soportado
    if not any(domain in text for domain in SUPPORTED_DOMAINS):
        return

    # Extraer URL (simple)
    url = None
    for word in message.text.split():
        if word.startswith('http') and any(d in word for d in SUPPORTED_DOMAINS):
            url = word
            break
            
    if not url:
        return

    # Notificar que se está procesando (opcional, solo log)
    logger.info(f"🔗 Detectado enlace: {url}")

    # Descargar
    file_path, media_type, title = None, None, None
    try:
        # Enviar mensaje de "Procesando..." al log o admin si se desea
        # await context.bot.send_message(chat_id=DESTINATION_CHAT_ID, text=f"⏳ Procesando: {url}")
        
        file_path, media_type, title = download_media(url)
        
        if file_path and os.path.exists(file_path):
            caption = f"🎥 {title}\n🔗 {url}"
            
            try:
                if media_type == 'video':
                    await context.bot.send_video(
                        chat_id=DESTINATION_CHAT_ID,
                        video=open(file_path, 'rb'),
                        caption=caption,
                        supports_streaming=True
                    )
                elif media_type == 'audio':
                    await context.bot.send_audio(
                        chat_id=DESTINATION_CHAT_ID,
                        audio=open(file_path, 'rb'),
                        caption=caption
                    )
                elif media_type == 'photo':
                    await context.bot.send_photo(
                        chat_id=DESTINATION_CHAT_ID,
                        photo=open(file_path, 'rb'),
                        caption=caption
                    )
                
                logger.info(f"✅ Contenido descargado enviado a {DESTINATION_CHAT_ID}")

            except Exception as e:
                logger.error(f"❌ Error enviando archivo a Telegram: {e}")
        else:
             logger.warning(f"⚠️ No se pudo descargar contenido de: {url}")

    except Exception as e:
        logger.error(f"❌ Error en handle_url: {e}")
    
    finally:
        # Limpieza
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Archivo temporal eliminado: {file_path}")


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

    # Añadir handler para enlaces en texto (excluyendo comandos)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)
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
