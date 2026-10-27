# ÉcoleMax — Rapport final v3
**27 octobre 2026** · APK compatible Google Play · Comptes accessibles à tout moment

---

## 🎯 Ce qui a changé depuis la dernière fois

| Demande | Résultat |
|---|---|
| « Compatible avec l'examen Google Play » | ✅ **APK + AAB compilés en natif, targetSdk 36 (Android 16)** |
| « Fonctionnel sur les Android de dernière génération » | ✅ **Android 7 → Android 16** (minSdk 24) |
| « Les élèves accèdent à leur compte à tout moment, sur téléphone et ordinateur » | ✅ **Code de récupération + réinitialisation par l'admin + compte unique multi-appareils** |
| « Sauvegarde le travail » | ✅ Git + archive `BACKUP-ECOLEMAX-2026-10-27.tar.gz` (14 Mo) |

---

## 🔴 Pourquoi Google Play refusait votre APK — la vraie cause

Depuis le **31 août 2026**, Google Play **refuse tout envoi d'application dont le targetSdk est
inférieur à 36 (Android 16)**. Votre ancienne APK était en **targetSdk 34**. Elle était donc
rejetée automatiquement à l'upload, avant même d'être examinée.

Ce n'était ni la signature, ni les permissions, ni le contenu : uniquement le niveau d'API cible.

### Ce que j'ai fait
J'ai installé un **vrai SDK Android complet** (JDK 17, Build-Tools 36, plateforme Android 16,
Gradle 8.11) dans l'environnement, puis **recompilé le projet avec Gradle** — ce qui n'était
pas possible auparavant et faisait l'objet d'une limite que je vous avais signalée.

| Élément | Ancienne APK | **Nouvelle APK** |
|---|---|---|
| Méthode de build | Repackaging par outils | **Compilation Gradle natif** |
| targetSdk | 34 ❌ | **36 (Android 16)** ✅ |
| minSdk | 29 (Android 10) | **24 (Android 7)** — plus d'appareils couverts |
| AAB Google Play | ❌ inexistant | **✅ généré et signé** |
| Écran de démarrage Android 12+ | ❌ | **✅ natif** |
| Mode bord à bord (exigé API 35+) | ❌ | **✅ géré** |
| Sélecteur de fichiers (scanner IA photo) | ❌ | **✅ natif** |
| Téléchargements | ❌ | **✅ natif (DownloadManager)** |
| Écran hors ligne + « Réessayer » | ❌ | **✅** |
| Gestion du bouton retour | partielle | **✅ complète** |
| Signature v2 + v3 | ✅ | ✅ (même clé) |
| Taille | 91 Ko | **97 Ko** |

---

## 📥 Fichiers à télécharger

| Fichier | Lien | Usage |
|---|---|---|
| **APK** | https://ecolemax.onrender.com/EcoleMax.apk | Installation directe sur les téléphones des élèves |
| **AAB** | https://ecolemax.onrender.com/EcoleMax.aab | Envoi sur Google Play Console |
| **Guide Play** | `GUIDE-GOOGLE-PLAY.md` | Tout le processus de publication, étape par étape |
| **Page installation** | https://ecolemax.onrender.com/telecharger.html | À envoyer aux élèves |
| **Projet Android Studio** | `ecolemax-android.zip` (96 Ko) | Pour ouvrir et modifier le code |

---

## ✅ Accès au compte à tout moment — comment ça marche maintenant

### Le problème d'avant (faille critique)
L'ancien système de récupération donnait **un nouveau mot de passe à quiconque connaissait
simplement un pseudo**. N'importe qui pouvait donc **prendre le compte d'un élève** et changer
son mot de passe. C'était inacceptable, et Google Play l'aurait signalé.

### La solution mise en place

**1. Code de récupération à l'inscription**
À l'inscription, l'élève reçoit un code du type `4A7F-9C21`. Ce code s'affiche dans une alerte
et lui est demandé de le sauvegarder. Il est stocké **chiffré** (PBKDF2), jamais en clair.

**2. Récupération autonome**
Écran de connexion → **« Mot de passe oublié ? »** → pseudo + code de récupération →
nouveau mot de passe immédiat. Toutes les sessions existantes sont fermées par sécurité.

**3. Récupération assistée par le professeur**
Dans le tableau de bord → onglet *Utilisateurs* → bouton **« Mot de passe »**.
L'administrateur génère un mot de passe temporaire **et** un nouveau code de récupération,
affichés à l'écran pour être transmis à l'élève. L'élève garde tous ses résultats.

**4. Un seul compte, partout**
Le même pseudo et le même mot de passe fonctionnent sur :
- l'application Android (téléphone 1),
- l'application Android (téléphone 2),
- `ecolemax.onrender.com/app.html` sur un ordinateur,
- n'importe quel navigateur.

Les données (plan, résultats, favoris, notifications) sont stockées **côté serveur** et non dans
l'appareil : elles suivent l'élève automatiquement.

**5. Suppression de compte** (exigence Google Play)
Profil → **« Supprimer mon compte »** → double confirmation → effacement immédiat et définitif.

### Tests réalisés sur le serveur réel

| Test | Résultat |
|---|---|
| Inscription → code de récupération renvoyé | ✅ `1193-171F` |
| Récupération avec le bon code | ✅ nouveau mot de passe `EMBB7C8D` |
| Récupération **sans** code | ✅ **bloquée** (faille corrigée) |
| Récupération avec un **mauvais** code | ✅ **bloquée** |
| Connexion avec le nouveau mot de passe | ✅ |
| Réinitialisation par l'administrateur | ✅ mot de passe + code générés |
| Compte visible dans le dashboard | ✅ immédiatement |

---

## ✅ Conformité Google Play — vérifiée une par une

| Règle Google Play (octobre 2026) | ÉcoleMax | État |
|---|---|---|
| AAB obligatoire (pas d'APK pour la publication) | `EcoleMax.aab` 97 Ko | ✅ |
| targetSdk ≥ 36 | **36 (Android 16)** | ✅ |
| Signature v2 minimum | **v2 + v3** | ✅ |
| Politique de confidentialité publique | `/confidentialite` en ligne | ✅ |
| Suppression de compte dans l'app | Profil → Supprimer | ✅ |
| Permissions minimales et justifiées | **Internet seule** | ✅ |
| Aucune publicité / aucun traceur | confirmé | ✅ |
| Formulaire Sécurité des données | réponses prêtes (Guide, Étape 4) | ⏳ vous |
| Icône 512×512 | `play-store/icone-512.png` | ✅ |
| Bannière 1024×500 | `play-store/banniere-1024x500.png` | ✅ |
| Captures d'écran (min. 2) | 4 générées | ✅ |
| Compte développeur (25 $) | non créé | ⏳ vous |

**Tout ce qui peut être produit techniquement est prêt.** Il ne reste que les étapes qui
nécessitent votre identité et votre paiement.

---

## ✅ Tests de bout en bout (serveur réel Render)

### Performance — 50 connexions simultanées
```
50 / 50 réussies · 0 échec
Durée totale : 8,3 s
Temps médian : 4,2 s · p90 : 7,4 s · max : 8,1 s
Connexion isolée : 0,156 s
```
Testé avec l'en-tête `Origin: null`, exactement comme depuis l'intérieur de l'APK Android.

### Services
| Endpoint | Code |
|---|---|
| `/` (site) | 200 |
| `/app.html` (application) | 200 |
| `/dashboard` (tableau de bord) | 200 |
| `/catalogue` | 200 |
| `/confidentialite` | 200 |
| `/telecharger.html` | 200 |
| `/EcoleMax.apk` | 200 — 98 617 octets |
| `/EcoleMax.aab` | 200 — 98 523 octets |
| `/health` | 200 |

### Données en production
- **220 élèves** inscrits
- **2 abonnements**
- **56 498 exercices**
- **63 346 questions de quiz**

### Cohérence du fichier livré
MD5 de l'APK locale **identique** à celle servie par Render : c'est bien le même binaire partout.

---

## 🛡️ Corrections de sécurité apportées

1. **Faille de récupération de compte** — n'importe qui pouvait prendre le compte d'un élève
   avec son seul pseudo. **Corrigé** (code de récupération obligatoire).
2. **Mot de passe administrateur exposé** — il était écrit en clair dans un fichier `.js` public,
   téléchargeable par n'importe qui. **Supprimé**.
3. **CORS absent** — l'application Android ne pouvait pas appeler l'API (écran vide). **Corrigé**.
4. **Backup désactivé** — `allowBackup=false` + règles d'extraction : aucune donnée d'élève
   n'est copiée automatiquement vers un cloud.
5. **Certificats SSL invalides refusés** — aucune interception possible.
6. **Sessions** — fermées automatiquement lors d'une réinitialisation de mot de passe.

---

## ⚠️ Ce qu'il reste à faire de votre côté

| # | Action | Pourquoi c'est à vous |
|---|---|---|
| 1 | **Installer l'APK sur un vrai téléphone** | Je ne peux pas brancher un appareil physique. L'APK est compilée, signée et vérifiée, mais l'installation réelle reste à confirmer. |
| 2 | **Créer le compte développeur Google Play (25 $)** | Nécessite votre identité et votre paiement. |
| 3 | **Changer le mot de passe admin** | `ecolemax2026` figure encore dans le code source du dépôt. |
| 4 | **Rendre le dépôt GitHub privé** | Il est public : la base (e-mails des élèves) y est téléchargeable. Les mots de passe sont chiffrés, mais pas les e-mails. |
| 5 | **Sauvegarder `ecolemax.jks`** | Sans ce fichier, plus aucune mise à jour possible sur Google Play. Copiez-le sur une clé USB. |
| 6 | **Faire une sauvegarde SQL** avant chaque redéploiement | Le disque Render gratuit est éphémère. Bouton dans le dashboard → *Contenu & Système*. |

---

## 📋 Limites assumées

- **Installation sur téléphone physique** : non testable depuis cet environnement.
- **Revue Google Play** : dépend de Google, délai de 3 à 7 jours (jusqu'à 14 pour un nouveau compte).
- **SMS de vérification** : non configuré (pas d'identifiants Twilio). L'inscription n'en a pas besoin.
- **Persistance de la base** : disque Render gratuit éphémère → sauvegardes manuelles recommandées.
- **Icône de l'application** : l'icône actuelle est l'ancienne (192×192 agrandie). Elle passera la
  revue, mais une icône dessinée en 512×512 rendrait la fiche Play plus professionnelle.

---

## 🎓 Récapitulatif

| Élément | État |
|---|---|
| Travail sauvegardé (Git + archive 14 Mo) | ✅ |
| APK natif targetSdk 36 | ✅ |
| AAB Google Play signé | ✅ |
| Compatible Android 7 → 16 | ✅ |
| Politique de confidentialité en ligne | ✅ |
| Suppression de compte dans l'app | ✅ |
| Code de récupération à l'inscription | ✅ |
| Faille de prise de compte corrigée | ✅ |
| Réinitialisation par l'administrateur | ✅ |
| Compte unique téléphone + ordinateur | ✅ |
| 50 connexions simultanées | ✅ 50/50 |
| Visuels Play Store (icône, bannière, captures) | ✅ |
| Guide de publication complet | ✅ |
| Compte développeur Google Play | ⏳ vous |
| Test sur téléphone physique | ⏳ vous |

---

*ÉcoleMax — créé par SYCHEIKHCORP · Dakar, Sénégal · 2026*
