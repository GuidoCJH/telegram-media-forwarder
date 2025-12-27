# Railway Configuration for Telegram Bot

## Optimización de Recursos

Este bot usa **polling** (no webhooks), por lo que NO necesita exponer un puerto HTTP.

### Configuración en Railway Dashboard:

1. **Eliminar la variable `PORT`** (si existe):
   - Settings → Variables → Borrar `PORT`

2. **Verificar el Start Command**:
   - Settings → Deploy → Start Command: `python3 bot.py`

3. **Tipo de servicio**:
   - El bot se ejecuta como **Worker** (proceso en background)
   - No necesita configuración de red pública

### Archivos de configuración incluidos:

- `Procfile`: Define explícitamente el proceso como `worker`
- `nixpacks.toml`: Configuración optimizada con `type = "worker"`

### Ahorro de recursos:

✅ **Sin puerto HTTP expuesto** → Menor overhead de red  
✅ **Sin health checks HTTP** → Reduce llamadas innecesarias  
✅ **Proceso worker puro** → Railway no intenta balancear carga HTTP  

### Variables de entorno requeridas:

```
BOT_TOKEN=tu_token_aqui
SOURCE_CHAT_ID=id_origen (opcional)
DESTINATION_CHAT_ID=id_destino
```

### Troubleshooting:

Si Railway muestra "No PORT detected":
1. Esto es **normal** para un worker
2. Asegúrate de tener `type = "worker"` en `nixpacks.toml`
3. El bot funcionará correctamente sin puerto

## Monitoreo

Logs → Ver que el bot se conecta correctamente:
```
INFO - Bot iniciado correctamente
INFO - Polling iniciado
```
