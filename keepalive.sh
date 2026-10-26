#!/bin/bash
# Keepalive EcoleMax - empêche le serveur de dormir et relancent cloudflared si mort
while true; do
  # Ping le serveur local pour maintenir Flask actif
  curl -s -o /dev/null --max-time 5 http://localhost:8000/api/health 2>/dev/null || curl -s -o /dev/null --max-time 5 http://localhost:8000/ 2>/dev/null
  
  # Vérifie que cloudflared est actif, relance si mort
  if ! pgrep -f "cloudflared tunnel" > /dev/null 2>&1; then
    echo "[$(date)] cloudflared mort - relance..."
    cloudflared tunnel --url http://localhost:8000 --no-autoupdate >> /home/user/deploy/cloudflared.log 2>&1 &
    sleep 10
    echo "[$(date)] cloudflared relancé"
  fi
  
  sleep 60
done
