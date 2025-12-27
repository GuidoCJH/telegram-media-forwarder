import os
import logging
import uuid
import random
import yt_dlp

logger = logging.getLogger(__name__)

# Lista de User Agents para rotación (anti-detección)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def download_media(url):
    """
    Descarga video/audio desde TikTok, Instagram y Spotify únicamente.
    Retorna: (ruta_archivo, tipo_archivo, titulo)
    """
    
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    unique_id = str(uuid.uuid4())
    output_template = f"{temp_dir}/{unique_id}.%(ext)s"

    # Configuración simple y robusta
    ydl_opts = {
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'user_agent': random.choice(USER_AGENTS),
        'referer': 'https://www.google.com/',
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
    }

    # Formato simple para todas las plataformas soportadas
    format_strategies = ['best', 'worst']

    def attempt_download(format_string):
        """Intenta descargar con un formato específico."""
        opts = ydl_opts.copy()
        opts['format'] = format_string
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            logger.info(f"⬇️ Descargando: {url[:50]}... (formato: {format_string})")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Media')
            
            # Buscar archivo descargado
            if not os.path.exists(filename):
                for f in os.listdir(temp_dir):
                    if f.startswith(unique_id):
                        filename = os.path.join(temp_dir, f)
                        break
            
            return filename, title

    # Intentar descarga con estrategias simples
    last_error = None
    for i, format_str in enumerate(format_strategies):
        try:
            filename, title = attempt_download(format_str)
            
            # Determinar tipo de archivo
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.mp4', '.mov', '.mkv', '.webm', '.avi', '.flv']:
                media_type = 'video'
            elif ext in ['.mp3', '.m4a', '.opus', '.ogg', '.wav', '.aac']:
                media_type = 'audio'
            elif ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                media_type = 'photo'
            else:
                media_type = 'video'

            logger.info(f"✅ Descarga exitosa: {filename} ({media_type})")
            return filename, media_type, title

        except Exception as e:
            error_str = str(e).lower()
            last_error = e
            
            logger.warning(f"⚠️ Intento {i+1} falló: {str(e)[:100]}")
            
            # Cambiar User-Agent si hay bloqueo
            if any(x in error_str for x in ['403', 'forbidden', 'prohibido']):
                ydl_opts['user_agent'] = random.choice(USER_AGENTS)
            
            continue

    # Si llegamos aquí, todos los intentos fallaron
    logger.error(f"❌ Error descargando después de {len(format_strategies)} intentos")
    logger.error(f"Último error: {last_error}")
    return None, None, None
