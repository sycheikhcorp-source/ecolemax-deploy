# Déploiement ÉcoleMax sur Render (gratuit, stable 24/7)

## Étape 1 : Créer un compte Render
1. Aller sur https://render.com
2. S'inscrire (gratuit, pas de carte bancaire)
3. Connecter GitHub

## Étape 2 : Déployer le service
1. Aller sur https://render.com/dashboard
2. Cliquer "New" → "Blueprint"
3. Sélectionner le repo : `sycheikhcorp-source/ecolemax-deploy`
4. Render détectera automatiquement :
   - Runtime : Python
   - Build : pas de dépendances (Python standard)
   - Start : `python serveur.py` (depuis le Procfile)
5. Cliquer "Deploy"

## Étape 3 : Récupérer l'URL
Après le déploiement :
- URL : `https://ecolemax-xxx.onrender.com`
- Dashboard : `https://ecolemax-xxx.onrender.com/dashboard.html`
- Mot de passe admin : `ecolemax2026` (modifiable dans les settings)

## Étape 4 : Rebuild APK avec l'URL Render
Une fois le service déployé, me dire l'URL. Je rebuilde l'APK avec cette URL stable.
