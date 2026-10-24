# 🧪 Tester ÉcoleMax localement & avec vos élèves — sans dépenser un franc

> Objectif : **tout tester maintenant**, envoyer le QR/lien à quelques élèves, et garder le Play Store pour plus tard.
> Coût total de cette phase : **0 FCFA**.

---

## ✅ 1. Le plus rapide : le lien public déjà en ligne

Une adresse de test est active. Vos élèves l'ouvrent sur leur téléphone, sans rien installer de compliqué :

| Quoi | Lien |
|---|---|
| **Application élève** | `https://bulk-color-laser-shareware.trycloudflare.com/pwa/index.html` |
| **APK Android (vrai fichier)** | `https://bulk-color-laser-shareware.trycloudflare.com/EcoleMax-1.0.0.apk` |
| Page récapitulative de test | `.../tester.html` |
| Site vitrine | `.../` |
| Tableau de bord | `.../dashboard.html` |

**Compte de démonstration :** `fatimatou` / `fatimatou`
**Nouveau compte :** essai gratuit 24 h automatique.

### Envoyer à un élève (Android) — deux options

**A. L'APK (vraie application, recommandée)**
1. Il scanne le QR `qr-apk.svg` → le fichier `EcoleMax-1.0.0.apk` se télécharge.
2. Paramètres → Sécurité → « Installer des applications inconnues » → autoriser.
3. Ouvrir le fichier → Installer → Ouvrir.

**B. La version web (sans rien autoriser)**
1. Il ouvre le lien **dans Chrome** (pas dans WhatsApp).
2. Menu **⋮** → **« Installer l'application »**.
3. L'icône 🎓 apparaît sur son écran, l'app s'ouvre en plein écran.

### Sur iPhone
Safari → **Partager** → **« Sur l'écran d'accueil »** → Ajouter.
(Apple interdit l'installation d'un APK : la PWA est la seule option gratuite.)

> ⚠️ **Important :** ce lien est un *tunnel gratuit* (trycloudflare). Il ne dépend pas de vous, il peut s'arrêter ou changer d'adresse à tout moment, et il est lent pour de grands fichiers. Il est parfait pour **quelques jours de test**, pas pour une mise en production.
> Fortune de l'APK : même si le tunnel tombe, l'application continue de fonctionner (mode autonome, l'IA est interrogée directement depuis le téléphone).

## 💻 2. Tout tester sur votre propre ordinateur

### Lancer en une commande
```bash
bash demarrer.sh
```
Puis ouvrir :
- **http://localhost:8000** → site vitrine
- **http://localhost:8000/pwa/index.html** → l'application
- **http://localhost:8000/dashboard.html** → votre tableau de bord
- **http://localhost:8000/telecharger.html** → la page de test

Le script affiche aussi l'adresse IP de votre ordinateur : un téléphone **connecté au même Wi-Fi** peut ouvrir l'app avec cette adresse.

### Tester l'application native (Expo Go)
```bash
cd app-expo
npm install
npx expo start
```
Installez **Expo Go** sur le téléphone (gratuit, Play Store / App Store) puis scannez le QR affiché.
L'app détecte automatiquement l'adresse de votre ordinateur pour joindre l'API.

---

## 📱 3. Pourquoi pas un APK tout de suite ?

Un APK doit être **compilé**. Deux possibilités, toutes deux gratuites :

| Méthode | Ce qu'il faut | Durée |
|---|---|---|
| **EAS Build** (recommandé) | un compte **Expo gratuit** (expo.dev), aucune carte bancaire | ~15-30 min de file d'attente |
| **Build local Android** | Android Studio + Java sur un PC | 1-2 h d'installation |

Commandes, une fois le compte Expo créé :
```bash
cd app-expo
npm install -g eas-cli
eas login
eas build:configure
eas build --platform android --profile preview   # → APK
```

> Le fichier `app-expo/eas.json` est déjà configuré : `preview` produit un **APK installable**, `production` produit un **AAB** pour le Play Store.

**En attendant l'APK, la PWA est équivalente pour un élève** : même écran, même icône, mêmes fonctions. C'est ce que je recommande pour la phase de test.

---

## 🗣️ 4. Ce que vos élèves doivent vous rapporter

Donnez-leur ces 3 consignes :

1. **Créer un compte** → est-ce que ça marche en moins d'une minute ?
2. **Poser une question à l'IA** en français, puis en wolof → la réponse est-elle claire ? assez lente/rapide ?
3. **Photographier un exercice** → l'IA lit-elle bien la photo ?

Et notez pour chaque retour :
| Élève | Téléphone | Action | Résultat | Ce qui bloque |
|---|---|---|---|---|
| | | | | |

Les questions les plus utiles : *« As-tu compris l'explication ? »*, *« Qu'est-ce qui manque ? »*, *« L'utiliserais-tu tous les jours ? »*.

---

## 🔒 5. Limites à connaître pendant la phase de test

| Limite | Explication |
|---|---|
| Liens de l'IA | Les fournisseurs gratuits (Pollinations) limitent à ~1 réponse / 30 s par adresse IP. Quelques élèves en même temps → réponses plus lentes. Ajouter une clé **Groq gratuite** règle le problème (voir `.env.exemple`). |
| Le tunnel peut s'arrêter | Un simple redémarrage le relance, mais l'adresse change → il faudra renvoyer le nouveau lien. |
| Données de test | Les comptes créés sont dans `backend/ecolemax.db`. Pour repartir proprement : supprimez ce fichier, il se recrée au démarrage. |
| Pas de paiement réel | Wave/Orange sont en mode **sandbox** : aucun argent n'est prélevé. |

---

## 💡 6. Comment obtenir une adresse stable (gratuit) quand vous voudrez

Pour arrêter de dépendre du tunnel, hébergez le backend gratuitement :

| Service | Gratuit | Remarque |
|---|---|---|
| **Render** | oui | HTTPS automatique, mise en veille après 15 min d'inactivité |
| **Koyeb** | 250 h/mois | pas de mise en veille prolongée |
| **PythonAnywhere** | oui | très simple, HTTPS inclus |

Le backend est **prêt pour ces services** : `requirements.txt`, `Procfile`, et il écoute sur le port fourni par la plateforme (`$PORT`).

Guide détaillé : `projet/play-store.md` §1.

---

## 📅 7. Feuille de route conseillée

| Quand | Quoi | Coût |
|---|---|---|
| **Aujourd'hui** | test local + lien public aux élèves | 0 FCFA |
| **Cette semaine** | corrections selon les retours, backend sur Render | 0 FCFA |
| **Quand vous avez les fonds** | compte Google Play 25 $ → build AAB → publication | 25 $ |
| **Plus tard** | App Store iPhone (99 $/an) — la PWA suffit en attendant | 99 $/an |

---

*ÉcoleMax · phase de test · 23/10/2026*
