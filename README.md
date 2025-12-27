# Bot de Telegram - Reenvío Automático de Medios

Bot de Telegram que captura y reenvía automáticamente **videos, fotos y documentos** desde un canal/grupo origen a un canal/grupo destino. **No reenvía mensajes de texto.**

## 🚀 Características

✅ Reenvía automáticamente:
- 📷 **Fotos**
- 🎥 **Videos**
- 📄 **Documentos** (PDF, archivos, etc.)

❌ **NO reenvía:**
- Mensajes de texto
- Stickers
- Audio/Voice
- Enlaces
- Encuestas

## 📋 Requisitos Previos

1. **Python 3.8+** instalado
2. **Token del Bot** (obtenlo de [@BotFather](https://t.me/BotFather))
3. El bot debe ser **administrador** en ambos canales/grupos con permisos de:
   - **Canal origen**: Leer mensajes
   - **Canal destino**: Enviar mensajes / Publicar mensajes

## 🔧 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd "/home/guido/Documents/TELEGRMA BOT"
```

### 2. Crear entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate  # En Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo:
```bash
cp .env.example .env
```

Edita `.env` con tus datos:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
SOURCE_CHAT_ID=-1001234567890
DESTINATION_CHAT_ID=-1009876543210
```

## 🔑 Cómo Obtener las Credenciales

### Obtener el Bot Token

1. Abre Telegram y busca [@BotFather](https://t.me/BotFather)
2. Envía el comando `/newbot`
3. Sigue las instrucciones (nombre del bot, username)
4. Copia el **token** que te proporciona

### Obtener el Chat ID de un Canal/Grupo

**Opción 1: Usando el bot @userinfobot**
1. Añade el bot [@userinfobot](https://t.me/userinfobot) a tu canal/grupo
2. El bot te mostrará el `Chat ID`

**Opción 2: Método manual**
1. Añade tu bot al canal/grupo
2. Ejecuta temporalmente este código:

```python
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

async def get_chat_id(update: Update, context):
    print(f"Chat ID: {update.effective_chat.id}")

app = Application.builder().token("TU_BOT_TOKEN").build()
app.add_handler(MessageHandler(filters.ALL, get_chat_id))
app.run_polling()
```

3. Envía un mensaje en el canal/grupo
4. Mira la consola para ver el `Chat ID`

> **Nota:** Los canales/supergrupos tienen IDs negativos tipo `-100xxxxxxxxxx`

## ▶️ Ejecutar el Bot

```bash
python3 bot.py
```

Deberías ver:
```
🤖 Bot iniciado. Esperando mensajes...
📥 Origen: -1001234567890
📤 Destino: -1009876543210
```

## 🔄 Mantener el Bot Ejecutándose

### Usando screen (Linux)

```bash
screen -S telegram_bot
python3 bot.py
# Presiona Ctrl+A, luego D para desconectar
# Para reconectar: screen -r telegram_bot
```

### Usando systemd (Linux - Servicio)

Crea `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Media Forwarding Bot
After=network.target

[Service]
Type=simple
User=guido
WorkingDirectory=/home/guido/Documents/TELEGRMA BOT
ExecStart=/home/guido/Documents/TELEGRMA BOT/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## 📝 Logs

El bot muestra logs en consola:
- `INFO`: Mensajes reenviados exitosamente
- `ERROR`: Problemas de conexión o permisos

## ⚠️ Solución de Problemas

### El bot no reenvía mensajes

1. **Verifica que el bot sea administrador** en ambos canales
2. **Revisa los Chat IDs** en el archivo `.env`
3. **Comprueba los permisos**:
   - Canal origen: "Leer mensajes"
   - Canal destino: "Enviar mensajes" / "Publicar mensajes"

### Error: "Unauthorized"

- Token incorrecto. Verifica el `BOT_TOKEN` en `.env`

### Error: "Chat not found"

- Los Chat IDs son incorrectos. Usa el método descrito arriba para obtenerlos

## 📄 Licencia

Proyecto de código abierto. Úsalo como quieras.

## 🤝 Soporte

Si tienes problemas, verifica:
1. Logs del bot en consola
2. Permisos del bot en los canales
3. Configuración del archivo `.env`
