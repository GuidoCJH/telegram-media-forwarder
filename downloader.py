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

    # Estrategia de formato según el sitio
    if "music.youtube.com" in url:
        # YouTube Music: Priorizar audio
        ydl_opts['format'] = 'bestaudio/best'
    elif "instagram.com" in url or "tiktok.com" in url:
        # Instagram/TikTok: Formato simple
        ydl_opts['format'] = 'best'
    else:
        # Otros (YouTube normal, etc): Intentar mejor calidad con fallbacks
        ydl_opts['format'] = 'bestvideo+bestaudio/best/bestvideo/bestaudio'

    def run_download(options):
        with yt_dlp.YoutubeDL(options) as ydl:
            logger.info(f"⬇️ Iniciando descarga: {url}")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Media')
            
            if not os.path.exists(filename):
                for f in os.listdir(temp_dir):
                    if f.startswith(unique_id):
                        filename = os.path.join(temp_dir, f)
                        break
            return filename, title

    try:
        try:
            # Intentar descarga con opciones por defecto (mejor calidad / posible fusión)
            filename, title = run_download(ydl_opts)
        except Exception as e:
            error_str = str(e).lower()
            
            # Detectar error de FFMPEG (fusión)
            if any(x in error_str for x in ["ffmpeg", "merge", "fusión", "fusion"]):
                logger.warning(f"⚠️ Error de FFMPEG. Reintentando con formato simple...")
                ydl_opts['format'] = 'best'
                filename, title = run_download(ydl_opts)
            
            # Detectar error de formato no disponible
            elif any(x in error_str for x in ["formato", "format", "available", "disponible"]):
                logger.warning(f"⚠️ Formato no disponible. Intentando formato alternativo...")
                ydl_opts['format'] = 'worst'  # Último recurso: peor calidad pero disponible
                filename, title = run_download(ydl_opts)
            
            else:
                raise e  # Otro error no relacionado con formatos
            
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
