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
    CommandHandler,
    filters,
    ContextTypes
)
from downloader import download_media

# Dominios soportados (Solo TikTok, Instagram, Spotify)
SUPPORTED_DOMAINS = [
    'tiktok.com', 'vm.tiktok.com',
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
    # (DESACTIVADO: Permitir acceso universal desde DMs u otros grupos)
    # if message.chat_id != SOURCE_CHAT_ID:
    #     return
    
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
        
    # Verificar origen (DESACTIVADO para acceso universal)
    # if message.chat_id != SOURCE_CHAT_ID:
    #    return

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
    
    # Obtener el ID del usuario que pidió el link
    user_chat_id = update.effective_chat.id

    # Descargar
    downloaded_files = None
    try:
        downloaded_files, media_type, title = download_media(url)
        
        if downloaded_files and all(os.path.exists(f) for f in downloaded_files):
            # Caption SIN URL (según solicitud del usuario)
            caption = f"🎥 {title}"
            
            # Función helper para enviar media
            async def send_media_to_chat(chat_id):
                """Envía el media al chat especificado."""
                try:
                    if media_type == 'photo' and len(downloaded_files) > 1:
                        # TikTok Slideshow: Enviar como álbum de fotos
                        from telegram import InputMediaPhoto
                        media_group = []
                        
                        for i, file_path in enumerate(downloaded_files[:10]):  # Límite 10 fotos por grupo
                            media_group.append(
                                InputMediaPhoto(
                                    media=open(file_path, 'rb'),
                                    caption=caption if i == 0 else None  # Solo primera foto con caption
                                )
                            )
                        
                        await context.bot.send_media_group(
                            chat_id=chat_id,
                            media=media_group
                        )
                        logger.info(f"✅ {len(downloaded_files)} fotos enviadas como álbum a {chat_id}")
                    
                    elif media_type == 'video':
                        await context.bot.send_video(
                            chat_id=chat_id,
                            video=open(downloaded_files[0], 'rb'),
                            caption=caption,
                            supports_streaming=True
                        )
                        logger.info(f"✅ Video enviado a {chat_id}")
                        
                    elif media_type == 'audio':
                        await context.bot.send_audio(
                            chat_id=chat_id,
                            audio=open(downloaded_files[0], 'rb'),
                            caption=caption
                        )
                        logger.info(f"✅ Audio enviado a {chat_id}")
                        
                    elif media_type == 'photo':
                        # Una sola foto
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=open(downloaded_files[0], 'rb'),
                            caption=caption
                        )
                        logger.info(f"✅ Foto enviada a {chat_id}")
                    
                    return True
                except Exception as e:
                    logger.error(f"❌ Error enviando archivo a {chat_id}: {e}")
                    return False
            
            # 1. Enviar al usuario que lo pidió
            user_success = await send_media_to_chat(user_chat_id)
            
            # 2. Enviar al canal/grupo destino (si es diferente al usuario)
            dest_success = False
            if user_chat_id != DESTINATION_CHAT_ID:
                dest_success = await send_media_to_chat(DESTINATION_CHAT_ID)
            else:
                dest_success = True  # Es el mismo chat
            
            # 3. Mensaje de confirmación al usuario
            if user_success and dest_success:
                await context.bot.send_message(
                    chat_id=user_chat_id,
                    text="✅ Descarga completada"
                )
            elif user_success:
                await context.bot.send_message(
                    chat_id=user_chat_id,
                    text="✅ Descarga completada"
                )
        else:
             logger.warning(f"⚠️ No se pudo descargar contenido de: {url}")
             # Notificar al usuario del error
             await context.bot.send_message(
                 chat_id=user_chat_id,
                 text=f"❌ No se pudo descargar el contenido de este link.\n\nPosibles razones:\n• Contenido privado o restringido\n• Link inválido\n• Plataforma no soportada"
             )

    except Exception as e:
        logger.error(f"❌ Error en handle_url: {e}")
        # Notificar al usuario del error
        try:
            await context.bot.send_message(
                chat_id=user_chat_id,
                text=f"❌ Error procesando el link:\n{str(e)[:200]}"
            )
        except:
            pass
    
    finally:
        # Limpieza de todos los archivos descargados
        if downloaded_files:
            for file_path in downloaded_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"🗑️ Archivo temporal eliminado: {file_path}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores de la aplicación."""
    logger.error(f"Error: {context.error}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start: Bienvenida y Chequeo de Estado."""
    user = update.effective_user
    welcome_msg = (
        f"👋 ¡Hola {user.first_name}!\n\n"
        f"🤖 **Bot de Reenvío y Descarga ACTIVO**\n\n"
        f"✅ **Estado:** En línea y funcionando.\n"
        f"📤 **Destino:** Los archivos se enviarán al canal configurado.\n\n"
        f"**Funciones:**\n"
        f"1. 📨 **Reenvío:** Envíame fotos, videos o documentos y los subiré al canal.\n"
        f"2. 🔗 **Descargas:** Envíame enlaces de TikTok, YouTube, Instagram o Spotify.\n\n"
        f"¡Empieza a enviar contenido!"
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')


def main():
    """Inicia el bot."""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN no configurado. Revisa tu archivo .env")
        return
    
    # Nota: SOURCE_CHAT_ID ya no es estricto para recibir, pero DESTINATION_CHAT_ID sí es necesario para enviar.
    if not DESTINATION_CHAT_ID:
        logger.error("❌ DESTINATION_CHAT_ID no configurado")
        return
    
    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).build()

    # Añadir handler para comando /start
    application.add_handler(CommandHandler("start", start_command))
    
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
