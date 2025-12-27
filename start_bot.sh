#!/bin/bash
# Script para iniciar el bot de Telegram en segundo plano

cd "/home/guido/Documents/TELEGRMA BOT"

echo "🤖 Iniciando bot de Telegram..."
nohup python3 bot.py > bot.log 2>&1 &
echo $! > bot.pid

echo "✅ Bot iniciado en segundo plano"
echo "📝 PID: $(cat bot.pid)"
echo "📋 Logs: tail -f /home/guido/Documents/TELEGRMA\ BOT/bot.log"
