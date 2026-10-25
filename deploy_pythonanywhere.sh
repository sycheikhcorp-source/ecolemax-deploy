#!/bin/bash
# Déploiement EcoleMax sur PythonAnywhere
# PythonAnywhere = pas de sleep, mais restrictions réseau

# 1. Créer une account PythonAnywhere
# https://www.pythonanywhere.com/register/

# 2. Créer une nouvelle web app
# https://www.pythonanywhere.com/dashboard/webapps/new/manual/

# 3. Configurer le domaine
# ecolemax.pythonanywhere.com (gratuit) ou custom domain (payant)

# 4. Cloner le repo
# git clone https://github.com/sycheikhcorp-source/ecolemax-deploy.git

# 5. Configurer la virtualenv
# python3 -m venv ~/.virtualenvs/ecolemax
# pip install flask gunicorn

# 6. Configurer le serveur
# Dans PythonAnywhere dashboard → Web app → Flask :
#   - Source code : /home/yourusername/ecolemax-deploy
#   - Working directory : /home/yourusername/ecolemax-deploy
#   - Command : gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 app:app
#   - Variables d'environnement :
#       ADMIN_PASSWORD=ecolemax2026
#       DB_PATH=/home/yourusername/ecolemax-deploy/ecolemax.db

# 7. Reloader le web app
# ⚠️ ⚠️ ⚠️ NOTE IMPORTANTE : PythonAnywhere bloque les appels réseau sortants
#     L'IA (Pollinations, OVH AI) ne fonctionnera pas sur PythonAnywhere free !
#     Utiliser Pollinations (whitelistée) ou déployer sur Koyeb.

echo "✅ Script de déploiement PythonAnywhere créé"
echo "⚠️ ⚠️ ⚠️ PythonAnywhere bloque les appels réseau sortants → IA externe NE FONCTIONNERA PAS"
echo "📚 Infos : https://help.pythonanywhere.com/en/latest/networking/outgoing-networking/"
