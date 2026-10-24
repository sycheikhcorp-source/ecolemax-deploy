# 📱 Installer ÉcoleMax sur iPhone — les 3 méthodes (dont 2 gratuites)

> Apple ne permet pas d'installer une application hors App Store sans compte développeur à 99 $/an.
> **Mais il existe deux méthodes 100 % gratuites et légales** pour avoir ÉcoleMax sur iPhone, avec icône sur l'écran d'accueil.

---

## ✅ Méthode 1 — PWA (RECOMMANDÉE, gratuite, immédiate)

C'est un vrai raccourci : l'app s'ouvre en plein écran, avec son icône, sans passer par l'App Store.

### Ce qu'il faut faire, côté vous (10 minutes)
1. **Héberger le dossier `projet/pwa/`** (fourni, prêt à l'emploi) :
   - aller sur **app.netlify.com/drop**
   - glisser-déposer le **contenu** du dossier `pwa/` (ou le fichier `EcoleMax-iPhone-PWA.zip` décompressé)
   - Netlify donne immédiatement une adresse du type `https://ecolemax.netlify.app`
   - **gratuit, sans carte bancaire, HTTPS inclus**
2. Envoyer ce lien à vos élèves (WhatsApp, Facebook, SMS).

### Ce qu'ils font, côté élève (3 gestes)
1. Ouvrir le lien dans **Safari** (obligatoire, pas Chrome).
2. Toucher le bouton **Partager** (le carré avec la flèche vers le haut).
3. Choisir **« Sur l'écran d'accueil »** → **Ajouter**.

➡️ L'icône ÉcoleMax apparaît sur l'iPhone. En l'ouvrant : **plein écran, sans barre d'adresse**, comme une vraie app. Elle fonctionne aussi **hors ligne** pour l'interface (le contenu des cours déjà chargé).

### Ce que la PWA sait faire
| Fonction | Disponible |
|---|---|
| Icône sur l'écran d'accueil | ✅ |
| Plein écran (pas de barre Safari) | ✅ |
| Écran de démarrage vert ÉcoleMax | ✅ |
| Fonctionne hors ligne (interface) | ✅ |
| Mise à jour automatique | ✅ (il suffit de rouvrir) |
| Notifications push | ⚠️ iPhone : nécessite iOS 16.4+ et l'app ajoutée à l'écran d'accueil |
| Apparaître dans l'App Store | ❌ (réservé au compte à 99 $/an) |

**Coût total : 0 FCFA.**

---

## 🟡 Méthode 2 — AltStore PAL (gratuite, mais seulement dans l'UE)

Depuis iOS 17.4, l'Europe autorise les magasins alternatifs. **AltStore PAL** installe des apps hors App Store avec un certificat gratuit.

- ✅ Gratuit
- ✅ Vraie app native (IPA)
- ❌ **Fonctionne uniquement si l'iPhone est enregistré dans l'Union européenne**
- ❌ Le Sénégal n'est pas concerné → **ce n'est pas la solution pour vos élèves**
- ❌ Nécessite un Mac pour compiler l'IPA

➡️ À garder en tête seulement si vous ciblez un jour l'Europe.

---

## 🔴 Méthode 3 — App Store officiel (payant)

| Élément | Détail |
|---|---|
| Compte développeur Apple | **99 $/an** (renouvelable) |
| Matériel obligatoire | un **Mac** (ou un service de build cloud) |
| Délai de validation | 1 à 3 semaines |
| Build | `eas build --platform ios --profile production` |

**Aucune astuce ne permet d'éviter les 99 $/an** : Apple vérifie chaque app. Je préfère vous le dire clairement plutôt que de vous vendre une fausse solution.

**Stratégie conseillée :**
1. Aujourd'hui : **Play Store (Android, 25 $)** + **PWA (iPhone, 0 $)**
2. Quand les revenus rentrent : **App Store (99 $/an)**

---

## 🎯 Ce que voit l'élève au final

| Son téléphone | Comment il installe | Prix pour vous |
|---|---|---|
| Android | Play Store → « Installer » | 25 $ une fois |
| Android (avant publication) | APK + QR code | 0 FCFA |
| iPhone | Safari → « Sur l'écran d'accueil » | 0 FCFA |
| Ordinateur | site web | 0 FCFA |

---

## 🧪 Tester la PWA tout de suite (avant hébergement)

Sur ce serveur de développement, elle est déjà accessible :
```
http://localhost:8000/pwa/index.html
```
Sur iPhone connecté au même Wi-Fi : `http://VOTRE-IP-LOCAL:8000/pwa/index.html`
(l'installation « écran d'accueil » exige **HTTPS** → elle ne marchera qu'après l'hébergement Netlify.)

---

## 📋 Fichiers fournis

| Fichier | Utilité |
|---|---|
| `projet/pwa/` | La PWA complète (HTML + JS + icônes + manifest + service worker) |
| `EcoleMax-iPhone-PWA.zip` | Le même dossier zippé → à glisser sur Netlify Drop |
| `projet/pwa/manifest.json` | Nom, icône, couleurs, mode plein écran |
| `projet/pwa/sw.js` | Service worker (mode hors ligne) |
