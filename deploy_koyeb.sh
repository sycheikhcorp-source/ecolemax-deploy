#!/bin/bash
# Déploiement EcoleMax sur Koyeb
# Koyeb = pas de sleep, free tier toujours actif

# 1. Construire l'image Docker
docker build -t ecolemax:latest .

# 2. Se connecter à Koyeb
# Koyeb CLI : https://www.koyeb.com/docs/cli
# KOYEB_TOKEN = votre token API Koyeb

# 3. Déployer
# koyeb deploy --docker ecolemax:latest \
#   --name ecolemax \
#   --env ADMIN_PASSWORD=ecolemax2026 \
#   --env DB_PATH=/home/app/ecolemax.db \
#   --port 8000 \
#   --instance-type s-01 \
#   --region blr1

# 4. Vérifier le déploiement
# koyeb app status ecolemax

echo "✅ Script de déploiement Koyeb créé"
echo "📝 Infos : https://www.koyeb.com/docs/deployment/docker"
echo "🔑 Token API : https://app.koyeb.com/account/api-tokens"
