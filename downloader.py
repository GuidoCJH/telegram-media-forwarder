import os
import logging
import uuid
import yt_dlp

logger = logging.getLogger(__name__)

def download_media(url):
    """
    Descarga video/audio desde una URL usando yt-dlp.
    Retorna: (ruta_archivo, tipo_archivo, titulo)
    """
    
    # Crear carpeta temporal si no existe
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Nombre de archivo único
    unique_id = str(uuid.uuid4())
    output_template = f"{temp_dir}/{unique_id}.%(ext)s"

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo+bestaudio/best',  # Mejor calidad disponible
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        # Opciones específicas para redes sociales
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    # Ajustes específicos para Instagram/TikTok (a veces requieren cookies o user agent)
    if "instagram.com" in url or "tiktok.com" in url:
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"⬇️ Iniciando descarga: {url}")
            info = ydl.extract_info(url, download=True)
            
            # Obtener path del archivo descargado
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Media')
            
            # Verificar si existe (yt-dlp a veces cambia la extensión)
            if not os.path.exists(filename):
                # Buscar cualquier archivo que empiece con el ID
                for f in os.listdir(temp_dir):
                    if f.startswith(unique_id):
                        filename = os.path.join(temp_dir, f)
                        break
            
            # Determinar tipo
            ext = os.path.splitext(filename)[1].lower()
            media_type = 'video' if ext in ['.mp4', '.mov', '.mkv', '.webm'] else 'audio'
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                media_type = 'photo'

            logger.info(f"✅ Descarga completada: {filename} ({media_type})")
            return filename, media_type, title

    except Exception as e:
        logger.error(f"❌ Error descargando {url}: {e}")
        return None, None, None
