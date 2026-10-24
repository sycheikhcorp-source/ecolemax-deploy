# 🚀 Déployer ÉcoleMax — Play Store / App Store / APK — **sans budget**

> Version : 1.0.0 · Date : 23/10/2026
> Ce guide part du principe que vous ne voulez **payer rien** pour commencer.

---

## 0. Ce qu'il faut savoir (résumé rapide)

| Option | Coût | Délai | Recommandé pour… |
|---|---|---|---|
| **APK + site web** | **0 €** | **quelques heures** | lancement immédiat, partage par lien/QR |
| **PWA** (site installable) | **0 €** | **quelques heures** | iPhone + Android + PC sans store |
| **Google Play Store** | **25 $** (frais unique) | **plusieurs jours** (validation) | distribution officielle Android |
| **Apple App Store** | **99 $/an** (+ Mac obligatoire) | **plusieurs semaines** (validation) | distribution officielle iPhone/iPad |

**Conclusion :** vous pouvez **lancer ÉcoleMax gratuitement dès aujourd'hui** via l'APK + le site web + PWA. Les stores officiels viendront **plus tard**, quand vous aurez des revenus.

> **📱 Essai gratuit : 24 heures, tout débloqué** — 24 questions IA/jour + 1 photo/jour + toutes les matières + téléchargement. Après 24 h, abonnement à partir de 250 FCFA.

---

## 1. Option gratuite : APK téléchargeable + site web (recommandé pour commencer)

### 1.1 Héberger le site + l'API (gratuit)

Le projet a deux parties :
- **Backend** (`backend/serveur.py`) : API + paiements + IA. Python, aucune dépendance lourde (stdlib + `requests` facultatif).
- **App mobile** (`app-expo/`) : Expo React Native, qui se compile en APK.

Hébergez le **backend** sur une plateforme gratuite :

| Plateforme | Modèle gratuit | Limite | Idéal |
|---|---|---|---|
| **PythonAnywhere** | Gratuit permanent | 512 MB RAM, 3 couches/jour | démarrage facile (Python natif) |
| **Render** | Gratuit | 0,1 CPU, 100 h/mois | lancement simple |
| **Koyeb** | Gratuit | 250 h/mois | deploy Python en 1 clic |
| **Fly.io** | 3 $/mois de crédit gratuit | 1 GB | rapide, mais besoin de carte |
| **Clever Cloud** | Gratuit | 100 h/mois | Python natif |

**Étapes PythonAnywhere (le plus simple, gratuit) :**

1. Créer un compte sur pythonanywhere.com
2. `$ pip install requests` (si utilisé) → dans la console Bash
3. Envoyer les fichiers : `scp -r backend/ user@pythonanywhere.com:/home/user/` ou via l'upload web
4. **Web app** → New web app → Python 3.11 → source code : `/home/user/backend`
5. **Startup command** : `python3 serveur.py`
6. **Variables d'environnement** : clés IA (voir §4)
7. Donner l'accès au port 8000 (Afficher → ports → 8000)
8. Votre API est en ligne : `https://tonnom.pythonanywhere.com`

**Le site web** (`projet/` : index.html, dashboard.html, telecharger.html) peut être hébergé :
- Sur **GitHub Pages** (gratuit, 100 % gratuit)
- Sur **Netlify** / **Cloudflare Pages** (gratuit)
- Ou directement dans le backend (déjà servis via `/`)

### 1.2 Construire l'APK (gratuit)

Deux façons de compiler l'app Expo en APK Android :

#### A. EAS Build (service officiel d'Expo — **gratuit pour les builds privés**)

```bash
cd app-expo
npm install
eas login
eas build:configure
# Créer eas.json :
cat > eas.json <<'EOF'
{
  "cli": { "version": ">= 7.0.0", "appVersionSource": "remote" },
  "build": {
    "development": { "developmentClient": true, "distribution": "internal" },
    "preview": { "distribution": "internal", "android": { "buildType": "apk" } },
    "production": { "android": { "buildType": "apk" } }
  }
}
EOF
eas build --platform android --profile production
```
- Coût : **gratuit** (EAS Build a des minutes gratuites mensuelles)
- Résultat : `.apk` téléchargeable → hébergez-le sur votre site
- **Astuce** : le bundled APK doit point vers **votre backend en ligne** : changer `API_BASE` dans `app-expo/api.js` → `https://tonnom.pythonanywhere.com`

#### B. Avantage : **Capacitor + Android Studio** (gratuit, local)

```bash
cd app-expo
npm install @capacitor/core @capacitor/cli
npx cap init ÉcoleMax app.ecolemax --web-dir=dist
# build web :
npx expo export --platform android   # génère dist/
npx cap add android
npx cap copy
npx cap open android                 # ouvre Android Studio
# Android Studio : Build → Build APK(s)
```
- Coût : **0 €** (Android Studio + SDK gratuits)
- Votre PC Windows/Linux suffit ; pas de Mac
- Le APK sort dans `android/app/build/outputs/apk/`

> **Le script `build-apk.sh`** (dans ce dossier) automatise la vérification et génère une page de release.

### 1.3 Page de téléchargement

Une page est déjà prête : **`projet/telecharger.html`** — avec bouton APK + **QR code** (scan pour télécharger) + instructions Android/iOS.

1. Copiez votre APK dans `projet/`
2. Renommez-le `EcoleMax-1.0.0.apk`
3. Hébergez `projet/` sur GitHub Pages / Netlify / votre serveur
4. Lien : `https://votrenom/telecharger.html`

### 1.4 Distribution sans store

- Partagez le **lien** ou le **QR** (groupes WhatsApp/Telegram, page Facebook)
- **Pas de validation**, **pas de frais**, mise à jour par nouveau lien
- L'app demande d'autoriser « sources inconnues » (normal pour tout APK hors Play)

---

## 2. Option PWA (gratuite, iPhone inclus)

La version web est une **PWA** : installable sur Android **et iPhone**.

- iPhone : Safari → Partage → **« Ajouter sur l'écran d'accueil »**
- Android : Chrome → menu → **« Ajouter à l'écran d'accueil »**
- L'app s'ouvre en plein écran comme une vraie app, **pas de store**

Avantages : **gratuit**, mise à jour instantanée, pas de validation.
Idéal pour commencer avant l'App Store.

---

## 3. Play Store (Android) — **25 $ unique, pas d'abonnement**

### Quand passer au Play Store ?
Quand vous avez des milliers d'utilisateurs et que vous voulez :
- une distribution « propre » (pas d'autorisation « sources inconnues »)
- la gestion des mises à jour automatiques
- la possibilité de facturer via **Google Play Billing** (plus tard)

### Étapes

1. **Créer un compte développeur** : https://play.google.com/console
   - Coût : **25 $** (frais de registration **unique**, pas annuel)
   - Reçu : carte cadeau ou virement
2. **Créer une application** : nom, description, logo
3. **Remplir les champs obligatoires** :
   - Rôle : Personal
   - Adresse + numéro de téléphone
   - URL du site
   - Contenu de l'app (résumé + screenshots — les vôtres sont prêts)
4. **Montrer une vidéo / captures** : utilisez les captures de `projet/app.html`
5. **Upload de l'APK** :
   - Copiez l'APK (issu de §1.2)
   - Console → « Créer une nouvelle version » → charger le fichier
   - Version `1.0.0`
6. **Soumettre** : l'app passe en **Examen** (quelques jours à 2 semaines)
7. Une fois approuvée → **Disponible sur Play Store**

**Points à surveiller (causes courantes de rejet) :**
- Demander des permissions excessives (GPS, contacts) → ÉcoleMax n'en a pas
- Collecte de données sans politique de confidentialité → ajoutez une page « Confidentialité » (`projet/securite.html` peut servir)
- Contenu non conforme (pas de contenu pour adultes, pas de violence)

> **Important** : l'APK hébergé (§1) et l'APK du Play Store peuvent être le même fichier. Vous n'avez pas besoin d'avoir un compte Play pour distribuer l'APK — les deux options sont indépendantes.

---

## 4. App Store (Apple) — **99 $ par an + Mac obligatoire**

### Quand passer à l'App Store ?
Quand une partie de votre public est sur **iPhone/iPad**.

### Étapes

1. **Créer un compte développeur Apple** : https://developer.apple.com/programs/
   - Coût : **99 $ par an** (renouvelable)
   - **Obligatoire** : posséder un **Mac** (macOS) pour générer les certificats
   - Alternative : **macOS sur une machine virtuelle** (pas simple) — ou demander à un proche
2. **App Store Connect** → nouveau projet iOS
3. **Générer les certificats** (sur le Mac) : Xcode → settings → certificates
4. **Générer l'IPA** :
   - `app-expo/` → `eas build --platform ios --profile production` (EAS sur Mac)
   - ou Xcode + Capacitor sur Mac
5. **Soumettre** : remplir la fiche app (description, screenshots iPad/iPhone, prix « Gratuit »)
6. **Examen Apple** : souvent **1 à 3 semaines** (parfois plusieurs rejets)

### Rejets fréquents et comment les éviter
- **Guidelines 4.0 Performance** : l'app doit être utile, pas un site web « wrapper » → ÉcoleMax est une vraie app, OK
- **Test de qualité** : éviter les bugs, les plantages — testez bien avant soumission
- **Confidentialité** : listez les données collectées (ÉcoleMax : pseudo, mot de passe haché, usage IA)
- **Pas de contenu IA non modéré** : l'app doit avoir une modération (le serveur limite déjà le contenu)

> **Alternative sans Mac ni 99 $** : la **PWA** (§2) ou **TestFlight** (il faut aussi un compte développeur). Pour lancer gratuitement, **la PWA est la solution iPhone**.

---

## 4b. App Store SANS frais — solutions (0 €)

Apple exige 99 $/an + Mac pour l'App Store officiel. **Sans payer, les seules vraies solutions pour iPhone :**

### ✅ Solution 1 : PWA (la seule 100 % gratuite & mondiale)
La version web est une **PWA installable** :
- iPhone : Safari → Partage → **« Ajouter sur l'écran d'accueil »**
- L'app s'ouvre en plein écran, reçoit les notifications, pas de store, **0 €**
- C'est **la façon officielle « sans frais »** de distribuer sur iPhone.

### ✅ Solution 2 : AltStore PAL (UE) — sideloading iPhone gratuit
- Depuis l'**UE** (iOS 17.4+), les apps peuvent être installées hors App Store
- **AltStore PAL** (altstore.io) est gratuit : l'app est signée avec un certificat **gratuit**
- Contrainte : l'app doit être compilée en **IPA** (il faut un Mac pour le build initial, ou confier le build)
- Noter : fonctionne **uniquement dans l'UE**

### ✅ Solution 3 : stores alternatifs (Android — 0 €)
En plus de l'APK direct, soumettez l'app sur des **stores alternatifs gratuits** :
| Store | Coût | Notes |
|---|---|---|
| **Amazon Appstore** | 0 € | compte développeur gratuit, accepte les APK |
| **Aptoide** | 0 € | store alternatif Android populaire en Afrique |
| **Uptodown** | 0 € | téléchargements directs, très utilisé |
| **Microsoft Store** | 0 € | version Windows (PWA/desktop) |

### ⚠️ Ce qui n'est PAS possible gratuitement
- **App Store officiel** : 99 $/an minimum, **sans exception** (même les apps gratuites)
- **TestFlight** : nécessite aussi un compte développeur (99 $/an)
- **Sideloading iPhone hors UE** : impossible sans Apple (ou ordinateur Mac avec compte)

**Recommandation sans budget :**
1. **Lancement** : APK (Android) + **PWA (iPhone)** → 0 €
2. **Ensuite**, si les revenus arrivent : Play Store 25 $ → App Store 99 $/an

---

## 5. Clés IA gratuites (augmenter les réponses IA sans payer)

L'app fonctionne **sans aucune clé** (repli Pollinations gratuit). Pour améliorer :

| Service | Clé gratuite | Limite | Vision (photo) | Notes |
|---|---|---|---|---|
| **Groq** | `https://console.groq.com/keys` | 30 RPM, gratuit | oui (llama-3.2-vision) | **le meilleur choix gratuit** |
| **Google Gemini** | `https://aistudio.google.com/app/apikey` | 15 RPM, gratuit | oui (gemini-2.0-flash) | **le meilleur choix gratuit** |
| **Pollinations** | `https://text.pollinations.ai/` (openai) | ~1/30 s par IP sans clé | oui | déjà intégrée |
| **OpenAI** | payant | — | oui | pas nécessaire |

**À placer dans les variables d'environnement du backend :**

```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# POLLINATIONS_KEY=pollen_xxxxxx (optionnel, pour lever la limite 30 s)
```

Le serveur essaie automatiquement : **OpenAI → Groq → Gemini → Pollinations → repli**.
Plus une clé est ajoutée, plus les réponses sont rapides et correctes.

> **« Acheter une API key avec plus d'abonnés »** (futur) : Groq / Gemini / OpenAI / DeepSeek ont des offres payantes. Ajoutez la clé dans le même variable — l'app n'a pas besoin de changer.

---

## 6. Ordre recommandé (plan sans budget)

1. **Héberger le backend gratuitement** (§1.1)
2. **Changer `API_BASE` dans `app-expo/api.js`** → URL en ligne
3. **Construire l'APK gratuitement** (§1.2)
4. **Héberger la page de téléchargement** (§1.3) + QR
5. **Ajouter les clés gratuites** Groq + Gemini (§5)
6. **Tester avec 50 étudiants** (groupes WhatsApp)
7. **Quand les revenus arrivent** → Play Store 25 $ (§3)
8. **Ensuite**, si l'audience iPhone est forte → App Store 99 $/an (§4)

---

## 7. Fichiers associés

| Fichier | Rôle |
|---|---|
| `projet/telecharger.html` | Page de téléchargement APK + QR + instructions |
| `projet/deployement.md` | Ce guide |
| `projet/build-apk.sh` | Script de build APK + vérification |
| `projet/.env.exemple` | Variables d'environnement (clés IA) |
| `app-expo/api.js` | Adresse de l'API (changer pour la version en ligne) |
| `backend/serveur.py` | API + paiements + IA |

---

## 8. Sécurité des paiements en production

- **Wave** : clé de production remplaçant la sandbox
- **Orange Money** : demander la **production** à Orange Sonatel (`DemandeOMB2B@orange-sonatel.com`)
- **Webhooks** : vérifier les signatures (déjà implémenté HMAC)
- **HTTPS obligatoire** en production (les clés API ne transitent jamais côté client)


---

## 9. Tester l'application (comment et quand)

### 🧪 Tester MAINTENANT (0 €, immédiat)
1. **Sur smartphone (Expo Go)** :
   ```bash
   cd /home/user/app-expo
   npm install
   npx expo start
   ```
   - Installer **Expo Go** sur le téléphone
   - Scanner le **QR code** affiché → l'app s'ouvre
   - Elle se connecte au backend (démo : **fatimatou / fatimatou**)
2. **Sur navigateur (prototype)** : `http://localhost:8000/app.html`
3. **Dashboard** : `http://localhost:8000/dashboard.html`

### 📱 Tester le APK (dès qu'il est build)
- `bash build-apk.sh --eas` → APK en ~15-30 min
- Envoyer le APK par WhatsApp/USB → installer (autoriser « sources inconnues »)

### ✅ Ce qu'on peut tester dès aujourd'hui
| Fonction | Statut |
|---|---|
| 18 matières, 52 chapitres, 33 exercices | ✅ prêt |
| IA questions (24/jour gratuit) | ✅ prêt (réel via Groq/Gemini/Pollinations) |
| Correction photo (1/jour gratuit) | ✅ prêt |
| Paiements Wave/Orange (sandbox) | ✅ prêt |
| Sécurité (anti-plagiat, anti-capture) | ✅ prêt |
| Page de téléchargement + QR | ✅ prêt |
