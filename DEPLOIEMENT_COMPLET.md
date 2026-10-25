# 🎯 DÉPLOIEMENT ÉCOLEMAX - SOLUTION ALTERNATIVE

## Problème
Render ne redéploie pas le Flask app (BaseHTTP/0.6 = serveur Python actif, v5.0).

## Solution : Koyeb (PAS DE SLEEP)

### Pourquoi Koyeb ?
- ✅ **PAS DE SLEEP** - le serveur reste actif 24/7
- ✅ Free tier (512MB RAM, 0.1 vCPU, 2GB SSD)
- ✅ Outbound internet OK (IA fonctionnera)
- ✅ Déploiement via Docker/Git
- ✅ 5 custom domains gratuits

### Étapes de déploiement sur Koyeb :

#### 1. Créer un compte Koyeb
- https://app.koyeb.com/auth/login
- Utiliser email ou GitHub

#### 2. Obtenir le token API
- https://app.koyeb.com/account/api-tokens
- Cliquer "New API token"

#### 3. Déployer via Koyeb CLI :
```bash
# Installer la CLI Koyeb
npm install -g @koyeb/koyeb-cli

# Se connecter
koyeb login --token YOUR_KOYEB_TOKEN

# Déployer l'application
koyeb deploy \
  --dockerfile /home/user/deploy/Dockerfile \
  --name ecolemax \
  --port 8000 \
  --instance-type s-01 \
  --region blr1 \
  --env ADMIN_PASSWORD=ecolemax2026 \
  --env DB_PATH=/home/app/ecolemax.db

# Vérifier le déploiement
koyeb app status ecolemax
```

#### 4. Accéder à l'application
- URL : https://ecolemax-[random].koyeb.app
- Health : https://ecolemax-[random].koyeb.app/health
- Admin API : https://ecolemax-[random].koyeb.app/api/admin/stats

#### 5. Configurer le domaine custom (gratuit)
- Dans Koyeb dashboard → App → Settings
- Ajouter un domain custom

### Déploiement alternative : Fly.io

```bash
# Installer la CLI Fly.io
curl -L https://fly.io/install | sh

# Se connecter
fly auth login

# Créer une app
fly init --name ecolemax

# Déployer
fly deploy \
  --image ecolemax:latest \
  --env ADMIN_PASSWORD=ecolemax2026 \
  --env DB_PATH=/data/ecolemax.db

# Vérifier
fly status
```

### Déploiement alternative : Railway

```bash
# Installer la CLI Railway
npm install -g railway

# Se connecter
railway login

# Créer une app
railway init

# Déployer
railway up
```

### ⚠️ PythonAnywhere ❌
PythonAnywhere bloque les appels réseau sortants → IA externe (Pollinations, OVH AI) NE FONCTIONNERA PAS.
Ne pas utiliser pour cette application.

## Validation post-déploiement :
```bash
# Health
curl https://YOUR-APP-URL/health

# Register
curl -X POST https://YOUR-APP-URL/api/register \
  -H "Content-Type: application/json" \
  -d '{"pseudo":"test","mot_de_passe":"Test1234","email":"test@test.com"}'

# Exercises
curl https://YOUR-APP-URL/api/exercises

# Quiz
curl https://YOUR-APP-URL/api/quiz

# Admin
curl https://YOUR-APP-URL/api/admin/stats -H "X-Admin-Password: ecolemax2026"
```

## Configuration Koyeb recommandée :
- Instance type : s-01 (free tier)
- Region : blr1 (Mumbai) ou sfo1 (San Francisco)
- Réplicas : 1 (pour free tier)
- Port : 8000
- Health check : /health
- Env vars :
  - ADMIN_PASSWORD=ecolemax2026
  - DB_PATH=/home/app/ecolemax.db
  - PORT=8000
