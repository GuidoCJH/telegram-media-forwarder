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
    Descarga video/audio desde una URL usando yt-dlp con técnicas anti-bloqueo.
    Incluye soporte robusto para YouTube Music.
    Retorna: (ruta_archivo, tipo_archivo, titulo)
    """
    
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    unique_id = str(uuid.uuid4())
    output_template = f"{temp_dir}/{unique_id}.%(ext)s"

    # Configuración base ultra-robusta
    base_opts = {
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'prefer_ipv4': True,  # Forzar IPv4 (mejor compatibilidad YouTube)
        # Anti-detección
        'user_agent': random.choice(USER_AGENTS),
        'referer': 'https://www.google.com/',
        # Reintentos
        'retries': 5,
        'fragment_retries': 5,
        'skip_unavailable_fragments': True,
        # Headers adicionales
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    # Intentar cookies desde navegador (solo funciona local, falla gracefully en cloud)
    try:
        base_opts['cookiesfrombrowser'] = ('firefox',)
        logger.info("🍪 Intentando usar cookies de Firefox...")
    except:
        logger.info("⚠️ Cookies de navegador no disponibles (modo cloud). Continuando sin cookies...")

    # Estrategias de formato según plataforma
    if "music.youtube.com" in url or "youtube.com/watch" in url:
        # YouTube Music: Formatos optimizados (prioridad M4A)
        format_strategies = [
            'bestaudio[ext=m4a]/bestaudio',  # M4A es el formato nativo
            '140',  # Código específico YouTube M4A 128kbps
            'bestaudio/best',
            'worst'
        ]
        # Extractores alternativos para YouTube Music
        extractor_clients = ['ios', 'android', 'web_embedded', 'tv_embedded']
    elif "instagram.com" in url or "tiktok.com" in url:
        format_strategies = ['best', 'worst']
        extractor_clients = [None]  # No rotar extractores para otras plataformas
    else:
        format_strategies = [
            'bestvideo+bestaudio/best',
            'best',
            'worst'
        ]
        extractor_clients = [None]

    def attempt_download(format_string, extractor=None):
        """Intenta descargar con formato y extractor específicos."""
        opts = base_opts.copy()
        opts['format'] = format_string
        
        # Configurar extractor si es para YouTube
        if extractor and ('youtube.com' in url or 'music.youtube.com' in url):
            opts['extractor_args'] = {
                'youtube': {
                    'player_client': [extractor],
                    'skip': ['hls', 'dash']  # Evitar streams problemáticos
                }
            }
            logger.info(f"🔄 Intentando extractor: {extractor}")
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Limpiar cache antes de cada intento (evita data corrupta)
            try:
                ydl.cache.remove()
            except:
                pass
            
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

    # Sistema de reintentos multi-nivel: Formatos × Extractores
    last_error = None
    
    for extractor in extractor_clients:
        for i, format_str in enumerate(format_strategies):
            try:
                filename, title = attempt_download(format_str, extractor)
                
                # Determinar tipo de archivo
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.mp4', '.mov', '.mkv', '.webm', '.avi', '.flv']:
                    media_type = 'video'
                elif ext in ['.mp3', '.m4a', '.opus', '.ogg', '.wav', '.aac']:
                    media_type = 'audio'
                elif ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                    media_type = 'photo'
                else:
                    media_type = 'video'  # Por defecto

                logger.info(f"✅ Descarga exitosa: {filename} ({media_type})")
                return filename, media_type, title

            except Exception as e:
                error_str = str(e).lower()
                last_error = e
                
                # Log del intento fallido
                extractor_info = f" con extractor {extractor}" if extractor else ""
                logger.warning(f"⚠️ Intento fallido{extractor_info}: {str(e)[:100]}")
                
                # Errores que justifican cambio de User-Agent
                if any(x in error_str for x in ['403', 'forbidden', 'prohibido']):
                    base_opts['user_agent'] = random.choice(USER_AGENTS)
                    logger.info("🔁 Cambiando User-Agent...")
                
                continue

    # Si llegamos aquí, todos los intentos fallaron
    total_attempts = len(format_strategies) * len(extractor_clients)
    logger.error(f"❌ Error descargando {url[:50]}... después de {total_attempts} intentos")
    logger.error(f"Último error: {last_error}")
    return None, None, None
