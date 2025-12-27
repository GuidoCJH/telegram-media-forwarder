import os
import logging
import uuid
import random
import subprocess
import httpx
import yt_dlp
import json

logger = logging.getLogger(__name__)

# Lista de User Agents para rotación (anti-detección)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def resolve_tiktok_url(url):
    """Resuelve links cortos de TikTok (vm.tiktok.com) a su URL final para detectar slideshows."""
    if 'tiktok.com' not in url:
        return url
    try:
        # Usar httpx para seguir redirecciones y obtener la URL final
        with httpx.Client(follow_redirects=True, timeout=10.0) as client:
            resp = client.head(url)
            final_url = str(resp.url)
            if final_url != url:
                logger.info(f"🔗 URL resuelta: {final_url}")
            return final_url
    except Exception as e:
        logger.warning(f"⚠️ No se pudo resolver la URL {url}: {e}")
        return url

def is_tiktok_slideshow(url):
    """Detecta si es un slideshow de TikTok basándose en la URL final."""
    return 'tiktok.com' in url and '/photo/' in url

def download_tiktok_slideshow_tikwm(url, temp_dir, unique_id):
    """Descarga slideshow TikTok usando la API de TikWM."""
    logger.info("🖼️ Usando API TikWM para obtener imágenes del slideshow...")
    api_url = f"https://www.tikwm.com/api/?url={url}"
    
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            resp = client.get(api_url)
            data = resp.json()
            
            if data.get('code') != 0:
                raise Exception(f"TikWM Error: {data.get('msg')}")
                
            media_data = data.get('data', {})
            images = media_data.get('images', [])
            title = media_data.get('title', 'TikTok Slideshow')
            
            if not images:
                # Si no hay imágenes en el campo 'images', TikWM a veces devuelve un solo video
                logger.warning("⚠️ No se encontraron imágenes en el slideshow de TikWM.")
                return None, None

            downloaded_files = []
            for i, img_url in enumerate(images):
                # Usar .jpg como extensión segura para Telegram
                file_path = os.path.join(temp_dir, f"{unique_id}_{i}.jpg")
                
                logger.debug(f"⬇️ Bajando imagen {i+1}/{len(images)}")
                r = client.get(img_url)
                if r.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(r.content)
                    downloaded_files.append(file_path)
            
            if not downloaded_files:
                raise Exception("No se pudo descargar ninguna imagen")
                
            logger.info(f"✅ Descargadas {len(downloaded_files)} imágenes vía TikWM")
            return downloaded_files, title
            
    except Exception as e:
        logger.error(f"❌ Error en TikWM: {e}")
        raise e

def download_instagram_via_api(url, temp_dir, unique_id):
    """
    Descarga media de Instagram usando APIs de terceros (SaveIG/SnapInsta) 
    para saltar el bloqueo de contenido sensible.
    """
    logger.info("📸 Usando API de respaldo para Instagram (Sensitive Content Bypass)...")
    
    # Lista de posibles endpoints para SaveIG
    api_endpoints = [
        "https://api.v02.saveig.app/api/info",
        "https://v3.saveig.app/api/info"
    ]
    
    for api_url in api_endpoints:
        try:
            full_url = f"{api_url}?url={url}"
            logger.debug(f"🔍 Probando API: {api_url}")
            
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                resp = client.get(full_url)
                if resp.status_code != 200:
                    continue
                    
                data = resp.json()
                # La estructura de SaveIG suele tener 'medias' o 'items'
                items = data.get('medias') or data.get('items', [])
                title = data.get('title', 'Instagram Media')
                
                if not items:
                    logger.warning(f"⚠️ API {api_url} no devolvió media.")
                    continue

                downloaded_files = []
                for i, item in enumerate(items):
                    # El campo 'url' suele estar en el item
                    # Puede ser 'url', 'src', o estar dentro de un objeto
                    media_url = item.get('url') or item.get('src')
                    if not media_url:
                        continue
                        
                    # Determinar extensión (Instagram suele usar jpg/mp4)
                    is_video = item.get('type') == 'video' or '.mp4' in media_url
                    ext = "mp4" if is_video else "jpg"
                    
                    file_path = os.path.join(temp_dir, f"{unique_id}_{i}.{ext}")
                    
                    logger.debug(f"⬇️ Bajando media {i+1}/{len(items)}")
                    r = client.get(media_url)
                    if r.status_code == 200:
                        with open(file_path, 'wb') as f:
                            f.write(r.content)
                        downloaded_files.append(file_path)
                
                if downloaded_files:
                    logger.info(f"✅ Descargado vía API: {len(downloaded_files)} archivos")
                    return downloaded_files, title
                    
        except Exception as e:
            logger.warning(f"⚠️ Error consultando API de IG {api_url}: {e}")
            continue
            
    return None, None

def download_media(url):
    """
    Descarga video/audio/fotos desde TikTok, Instagram y Spotify.
    """
    
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    unique_id = str(uuid.uuid4())
    
    # NUEVO: Resolver URL primero para detectar slideshows en links cortos
    resolved_url = resolve_tiktok_url(url)
    
    # Intentar con TikWM para slideshows de TikTok
    if is_tiktok_slideshow(resolved_url):
        try:
            downloaded_files, title = download_tiktok_slideshow_tikwm(resolved_url, temp_dir, unique_id)
            if downloaded_files:
                return downloaded_files, 'photo', title
        except Exception as e:
            logger.warning(f"⚠️ TikWM falló, reintentando con yt-dlp como fallback: {e}")
    
    # Fallback a yt-dlp para todo lo demás (videos TikTok, IG, Spotify)
    url_to_download = resolved_url
    
    # Template para yt-dlp (múltiples imágenes con numeración)
    output_template = f"{temp_dir}/{unique_id}_%(autonumber)s.%(ext)s"

    # Configuración simple y robusta para yt-dlp
    ydl_opts = {
        'outtmpl': output_template,
        'noplaylist': False,
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
        """Intenta descargar con un formato específico usando yt-dlp."""
        opts = ydl_opts.copy()
        opts['format'] = format_string
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            logger.info(f"⬇️ Descargando: {url_to_download[:50]}... (formato: {format_string})")
            info = ydl.extract_info(url_to_download, download=True)
            
            # Detectar si es un slideshow/playlist (múltiples archivos)
            if 'entries' in info:
                # Es una playlist/slideshow
                title = info.get('title', 'TikTok Slideshow')
                downloaded_files = []
                
                for entry in info['entries']:
                    if entry:
                        filename = ydl.prepare_filename(entry)
                        if os.path.exists(filename):
                            downloaded_files.append(filename)
                
                # Si no encontramos con prepare_filename, buscar en directorio
                if not downloaded_files:
                    for f in sorted(os.listdir(temp_dir)):
                        if f.startswith(unique_id):
                            downloaded_files.append(os.path.join(temp_dir, f))
                
                return downloaded_files, title
            else:
                # Es un solo archivo
                filename = ydl.prepare_filename(info)
                title = info.get('title', 'Media')
                
                # Buscar archivo descargado
                if not os.path.exists(filename):
                    for f in os.listdir(temp_dir):
                        if f.startswith(unique_id):
                            filename = os.path.join(temp_dir, f)
                            break
                
                return [filename], title

    # Intentar descarga con estrategias simples
    last_error = None
    for i, format_str in enumerate(format_strategies):
        try:
            downloaded_files, title = attempt_download(format_str)
            
            if not downloaded_files:
                continue
            
            # Determinar tipo basado en el primer archivo
            first_file = downloaded_files[0]
            ext = os.path.splitext(first_file)[1].lower()
            
            if ext in ['.mp4', '.mov', '.mkv', '.webm', '.avi', '.flv']:
                media_type = 'video'
            elif ext in ['.mp3', '.m4a', '.opus', '.ogg', '.wav', '.aac']:
                media_type = 'audio'
            elif ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                media_type = 'photo'
            else:
                media_type = 'video'

            logger.info(f"✅ Descarga exitosa: {len(downloaded_files)} archivo(s) ({media_type})")
            return downloaded_files, media_type, title

        except Exception as e:
            error_str = str(e).lower()
            last_error = e
            
            logger.warning(f"⚠️ Intento {i+1} falló: {str(e)[:100]}")
            
            # Cambiar User-Agent si hay bloqueo
            if any(x in error_str for x in ['403', 'forbidden', 'prohibido']):
                ydl_opts['user_agent'] = random.choice(USER_AGENTS)
            
            continue

    # SI LLEGAMOS AQUÍ, YT-DLP FALLÓ.
    # NUEVO: Si es Instagram, intentar con el motor de API de respaldo
    if 'instagram.com' in resolved_url:
        try:
            downloaded_files, title = download_instagram_via_api(resolved_url, temp_dir, unique_id)
            if downloaded_files:
                # Determinar tipo
                ext = os.path.splitext(downloaded_files[0])[1].lower()
                media_type = 'video' if ext == '.mp4' else 'photo'
                return downloaded_files, media_type, title
        except Exception as api_err:
            logger.error(f"❌ El motor de API de Instagram también falló: {api_err}")

    # Si llegamos aquí, todos los intentos fallaron
    logger.error(f"❌ Error descargando después de {len(format_strategies)} intentos")
    logger.error(f"Último error: {last_error}")
    return None, None, None
