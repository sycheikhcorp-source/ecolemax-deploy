# 📲 ÉcoleMax — APK, QR code et Play Store

> Ce document explique tout ce qu'il faut pour **installer l'application sur un téléphone**,
> **partager le QR code** et **publier sur Google Play** quand vous aurez les fonds.

---

## ✅ Ce qui est prêt

| Fichier | Rôle | Où |
|---|---|---|
| `EcoleMax-1.0.0.apk` (1,5 Mo) | Installation directe Android | `projet/telechargements/` |
| `EcoleMax-1.0.0.aab` (1,5 Mo) | Soumission Google Play | `projet/telechargements/` |
| `ecolemax.keystore` | Clé de signature (à garder !) | `apk-build/` |
| `qr-apk.svg` | QR code vers l'APK | `projet/` |
| `qr-app.svg` | QR code vers l'app web | `projet/` |
| `construire-apk.sh` | Rebuild APK + AAB | `apk-build/` |
| `publier-apk.sh` | Met à jour l'APK + régénère les QR | racine |

**Identité de l'application** : package `sn.ecolemax.app` · version 1.0.0 · versionCode 1
· Android min 6.0 (API 23) · cible Android 14 (API 34).

---

## 📲 Installer l'APK sur votre téléphone

### Option 1 — par le QR code (le plus simple)
1. Ouvrez `projet/telecharger.html` sur un ordinateur.
2. Affichez le QR code de la section **« 📲 Installer l'APK »**.
3. Sur le téléphone : **Appareil photo** → cadrez le QR → le téléchargement démarre.
4. Paramètres → **Applications** → **Accès aux applications installées** (ou *Sécurité*)
   → choisir **Chrome** ou **WhatsApp** → **Autoriser**.
5. Ouvrez le fichier téléchargé → **Installer** → **Ouvrir**.

> Sur Android 8 et plus, l'option s'appelle « Installer des applications inconnues ».
> Sur certains téléphones : *Paramètres → Sécurité → Applications → Installer des applications
> inconnues*.

### Option 2 — par le lien
```
https://bulk-color-laser-shareware.trycloudflare.com/EcoleMax-1.0.0.apk
```
(le tunnel est temporaire : utilisez plutôt le QR ou le fichier local)

### Option 3 — par câble / Bluetooth
Copiez `EcoleMax-1.0.0.apk` sur le téléphone (câble USB, Bluetooth ou carte SD),
ouvrez-le avec le gestionnaire de fichiers, puis **Installer**.

---

## 🧭 Le QR code que vous partagez à vos élèves

Il y a **deux QR utiles**, ne les confondez pas :

| QR | Contenu | Pour qui |
|---|---|---|
| **`qr-apk.svg`** | le fichier APK lui-même | élèves Android (installation native) |
| **`qr-app.svg`** | l'application web installable | élèves iPhone + test rapide |

Pour iPhone, l'APK ne fonctionne pas (Apple l'interdit). Usez **`qr-app.svg`** :
Safari → Partager → « Sur l'écran d'accueil ».

### Générer un QR vers une nouvelle adresse
```bash
python3 projet/outils/qr.py https://votre-nouvelle-url.com
```
Ça régénère les 5 QR codes. Pour l'APK vers un lien précis :
```bash
python3 projet/outils/qr.py --url https://votre-lien/EcoleMax-1.0.0.apk --sortie projet/qr-apk.svg
```

---

## 🔄 Publier une nouvelle version de l'APK

```bash
bash publier-apk.sh https://votre-serveur.com
```
Le script :
1. copie la PWA à jour dans l'APK ;
2. injecte l'adresse du serveur ;
3. reconstruit l'APK **et** l'AAB ;
4. téléverse l'APK sur un hébergeur gratuit ;
5. régénère tous les QR codes ;
6. met à jour `telecharger.html`.

> ⚠️ **Important** : la clé `apk-build/ecolemax.keystore` (mot de passe `ecolemax2026`)
> **doit être conservée**. Sans elle, Android refusera les mises à jour de l'application
> déjà installée, et le Play Store rejetttera un bundle signé avec une autre clé.

---

## 🛠️ Comment l'APK a été construit (sans Gradle)

Le projet React Native est trop lourd pour une machine 2 Go de RAM. L'APK est donc
construit **directement avec les outils Android** (`apk-build/construire-apk.sh`) :

| Étape | Outil |
|---|---|
| 1. Ressources (icônes, textes) | `aapt2 compile` |
| 2. Manifeste + liaison | `aapt2 link` |
| 3. Code Java | `javac` (Java 17) |
| 4. Classes → DEX | `d8` |
| 5. Assemblage ZIP | `zip` |
| 6. Alignement 4 octets | `zipalign` |
| 7. Signature | `apksigner` (v1+v2+v3) |
| 8. Bundle Play Store | `aapt2 --proto-format` + `bundletool` + `jarsigner` |

L'application est une **WebView native** qui charge l'interface React Native web
embarquée dans `assets/www/`. Avantages : APK de 1,5 Mo seulement, compatible
Android 6 → 14, et le même code que la version web.

**Composants :**
- `apk-build/src/sn/ecolemax/app/MainActivity.java` — activity WebView,
  sélecteur de photo (correction IA), dialogue de réglage du serveur.
- `apk-build/AndroidManifest.xml` — package `sn.ecolemax.app`.
- `apk-build/res/` — icônes de lancement générées depuis `projet/assets/icone-ecolemax.png`.

---

## 🚀 Google Play Store — publication

Le bundle `EcoleMax-1.0.0.aab` est **construit, signé et validé** (bundletool `validate` : OK).

### Étapes restantes (votre part)

| # | Action | Détail |
|---|---|---|
| 1 | Créer le compte développeur | [play.google.com/console](https://play.google.com/console) — **25 $** (carte) |
| 2 | Vérifier l'identité | Carte d'identité / passport + adresse |
| 3 | Créer l'application | Nom « ÉcoleMax », langue fr, gratuit |
| 4 | Remplir la fiche | `projet/play-store.md` (titre, description, mots-clés) |
| 5 | Screenshots | `captures/app-*.png` (2-8 images, 1080×1920) |
| 6 | Politique de confidentialité | `projet/confidentialite.html` → heberger en ligne et donner l'URL |
| 7 | **Envoyer l'AAB** | Production → Nouvelle version → `EcoleMax-1.0.0.aab` |
| 8 | Remplir le questionnaire | Public → CIBLE 3+ · pas de publicité · pas de données personnelles |

### Points d'attention Google
- **Version cible** : Android 14 (API 34) — exigé par Google depuis août 2024. ✅
- **Signature** : Play Store va générer sa propre clé de signature (Play App Signing).
  Conservez la nôtre pour les prochaines versions.
- **Testing interne** : avant la publication publique, faites un test interne
  (20 testeurs maximum, disponible tout de suite) avec vos élèves.
- **Délai** : première publication ≈ 1 à 3 jours (revue Google) + quelques heures.

---

## 🆘 Dépannage

| Problème | Solution |
|---|---|
| « Application non installée » | Autorisez « sources inconnues » pour l'app qui a téléchargé le fichier (Chrome / WhatsApp) |
| « Le fichier ne peut pas être ouvert » | Le téléchargement a été interrompu → recommencez en Wi-Fi |
| L'app ne répond pas | Touchez **⚙** en bas à droite → saisissez l'adresse du serveur |
| « Play Protect a bloqué » | C'est normal pour un APK hors Play Store → **Paramètres → Sécurité → Autoriser** |
| La connexion échoue | Créez un compte (essai 24 h) au lieu du compte de démo |
| Le tunnel est mort | Relancez `bin/cloudflared tunnel --url http://localhost:8000` puis `bash publier-apk.sh <nouvelle_url>` |

---

*ÉcoleMax · APK v1.0.0 · 24/10/2026*
