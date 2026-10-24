# ÉcoleMax — Application scolaire par IA (Sénégal) — Projet complet

## 📦 Contenu

| Dossier | Description |
|---|---|
| `projet/DOSSIER-PROJET.md` | Dossier complet (v3) : programmes, multilinguisme, modèle économique, sécurité, objectif 3 millions. |
| `projet/index.html` | Page de présentation (landing). |
| `projet/app.html` | Prototype de l'application élève (écran téléphone). |
| `projet/dashboard.html` | Tableau de bord **connecté à l'API** (données réelles). |
| `projet/telecharger.html` | **Page de téléchargement APK + QR + instructions** (Android/iOS/PWA). |
| `projet/securite.html` | Page dédiée à la sécurité (démo interactive). |
| `projet/deployement.md` | **Guide complet : APK / PWA / Play Store / App Store — sans budget**. |
| `projet/build-apk.sh` | Script de build APK (EAS / Capacitor) + vérifications. |
| `projet/.env.exemple` | Variables d'environnement (clés IA gratuites). |
| `projet/css/style.css` | Design system v2. |
| `backend/` | **Backend API** (Python, SQLite) : users, abonnements, paiements, IA, **correction photo**, sécurité. |
| `app-expo/` | **Application Expo React Native** connectée à l'API (avec bouton photo dans l'IA). |
| `sauvegarder.sh` | Script de sauvegarde (appelé après chaque étape). |
| `sauvegardes/` | Copies de sauvegarde du projet. |

## 🚀 Lancer le projet (dans l'ordre)

1. **Backend** :
   ```bash
   python3 /home/user/backend/serveur.py
   ```
   → `http://localhost:8000` (API + dashboard + static)

2. **Dashboard** : ouvrir `http://localhost:8000/dashboard.html` (données en temps réel)

3. **Application mobile** :
   ```bash
   cd /home/user/app-expo
   npm install
   npx expo start
   ```
   (connecte automatiquement au backend en démo : `fatimatou / fatimatou`)

4. **IA réelle** (optionnel) : ajouter des clés gratuites dans `.env` (voir `projet/.env.exemple`) avant de lancer le backend.
   - **Groq** (gratuit, recommandé) : `https://console.groq.com/keys`
   - **Gemini** (gratuit) : `https://aistudio.google.com/app/apikey`

## 📲 Mettre en ligne (sans budget)

1. Héberger le backend gratuitement (PythonAnywhere / Render / Koyeb) — guide : `deployement.md §1.1`
2. Changer `API_BASE` dans `app-expo/api.js` → URL en ligne
3. `bash build-apk.sh --eas` (ou `--capacitor`) → APK gratuit
4. Héberger `telecharger.html` + l'APK → QR/lien de partage
5. **Play Store** : 25 $ unique → `deployement.md §3`
6. **App Store** : 99 $/an + Mac → `deployement.md §4`

## 🔒 Sécurité implémentée

Anti-plagiat · anti-capture d'écran · anti-partage · anti-téléchargement hors ligne · limites par plan côté serveur (IA + photo) · contenu protégé.

## 📋 Contenu pédagogique

**18 matières** · 52 chapitres · 33 exercices (Maths, Français, Physique, SVT, Hist-Géo, Anglais, Espagnol, Arabe, Wolof, Philo, Latin, Économie, Technologie, Arts, EPS, EMC, Peul, Sèrer).
