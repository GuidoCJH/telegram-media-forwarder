#!/bin/bash
# Script para detener el bot de Telegram

cd "/home/guido/Documents/TELEGRMA BOT"

if [ -f bot.pid ]; then
    PID=$(cat bot.pid)
    echo "🛑 Deteniendo bot (PID: $PID)..."
    kill $PID 2>/dev/null
    rm bot.pid
    echo "✅ Bot detenido"
else
    echo "⚠️  No hay bot ejecutándose (bot.pid no encontrado)"
fi
