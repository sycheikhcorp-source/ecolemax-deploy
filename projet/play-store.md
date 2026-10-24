# 🟢 Publier ÉcoleMax sur le Google Play Store — guide pas-à-pas

> Version 1.0.0 · package `sn.ecolemax.app` · Frais : **25 $ une seule fois** (compte développeur à vie)
> Durée totale réaliste : **3 à 10 jours** (dont 1 à 7 jours de validation Google)

---

## 0. Ce qui est déjà prêt dans le dossier

| Élément | Fichier | État |
|---|---|---|
| Configuration Play Store | `app-expo/app.json` (package, versionCode, icône, permissions) | ✅ |
| Profils de build | `app-expo/eas.json` | ✅ |
| Icône 1024×1024 | `app-expo/assets/icon.png` | ✅ |
| Icône adaptative Android | `app-expo/assets/adaptive-icon.png` | ✅ |
| Écran de démarrage | `app-expo/assets/splash.png` | ✅ |
| Validation Expo (18 contrôles) | — | ✅ 18/18 |
| Bundle Android compilé | 556 modules, 0 erreur | ✅ |

**Il ne manque que 3 choses, qui exigent VOS comptes :**
1. votre compte Google Play (25 $),
2. votre compte Expo (gratuit),
3. l'URL de votre backend en ligne (gratuit).

---

## 1. Mettre le backend en ligne (gratuit) — 20 min

Sans API en ligne, l'app installée depuis le Play Store ne pourra pas répondre (elle chercherait `localhost`, qui n'existe pas sur le téléphone du client).

### Option recommandée : Render (gratuit, HTTPS automatique)
1. Créer un compte sur **render.com** (gratuit, sans carte).
2. **New → Web Service** → connecter votre dépôt GitHub contenant `backend/`.
3. Paramètres :
   - **Runtime** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `python serveur.py`
   - **Port** : le serveur doit écouter sur `0.0.0.0` et lire `$PORT`
4. Render donne une URL du type `https://ecolemax-api.onrender.com`.
5. **Important** : ajouter dans `backend/requirements.txt` (à créer) :
   ```
   requests
   ```
   et faire écouter le serveur sur le port fourni par Render.

> ⚠️ Render gratuit met le service en veille après 15 min d'inactivité : le premier appel après une pause prend ~30 s. Pour un lancement sérieux, prévoir Render Starter (7 $/mois) ou PythonAnywhere payant plus tard.

### Alternatives gratuites
| Plateforme | Gratuit | Remarque |
|---|---|---|
| **PythonAnywhere** | oui | pas de veille, mais HTTPS + domaine perso limités |
| **Koyeb** | 250 h/mois | déploiement en 1 clic |
| **Railway** | crédit d'essai | très simple |
| **Fly.io** | petit quota | plus technique |

---

## 2. Pointer l'application vers l'API en ligne — 2 min

Dans `app-expo/api.js`, ligne 11 :

```js
const URL_PRODUCTION = 'https://ecolemax-api.onrender.com'; // ← votre URL Render
```

C'est tout : l'app utilisera cette adresse partout (Android, iOS, web).

---

## 3. Créer le compte développeur Google — 15 min + 25 $

1. Aller sur **play.google.com/console** → **Créer un compte développeur**.
2. Choisir **Particulier** (25 $ une fois, pas d'abonnement).
3. Vérifier l'identité : pièce d'identité + adresse (Google vérifie, 1 à 3 jours).
4. Accepter l'accord développeur.

> 💡 Le compte est **à vie** : les 25 $ ne se repaient jamais, même avec 50 applications.

---

## 4. Construire le fichier pour le Play Store (AAB) — 20 à 40 min

Le Play Store n'accepte **pas** un APK, mais un **AAB** (Android App Bundle). C'est déjà configuré (`eas.json → production → buildType: app-bundle`).

```bash
cd app-expo
npm install -g eas-cli     # une seule fois
eas login                  # créer un compte gratuit sur expo.dev
eas build:configure        # génère le projectId
eas build --platform android --profile production
```

- Le build se fait **sur les serveurs d'Expo** (votre PC peut être éteint).
- Quota gratuit : builds illimités en file d'attente lente ; file rapide prioritaire payante (~15 $/mois, optionnel).
- À la fin : un lien de téléchargement `.aab`.

**Pour tester sur un téléphone avant publication** (APK, pas AAB) :
```bash
eas build --platform android --profile preview
```
→ donne un `.apk` installable directement.

---

## 5. Créer la fiche Play Store — 45 min

Dans la Play Console : **Créer une application**.

| Champ | Ce qu'il faut mettre pour ÉcoleMax |
|---|---|
| Nom | `ÉcoleMax` (30 caractères max) |
| Description courte | `Ton tuteur IA : 18 matières, exercices corrigés, photo, wolof.` |
| Description complète | voir modèle ci-dessous |
| Catégorie | Éducation |
| Type | Application |
| Gratuit / payant | **Gratuit** (obligatoire pour rester gratuit ensuite) |
| Coordonnées | votre e-mail + site web |
| Politique de confidentialité | **obligatoire** — voir §6 |

### Modèle de description complète
```
ÉcoleMax est le tuteur scolaire intelligent pensé pour les élèves du Sénégal,
du collège au lycée.

📚 18 MATIÈRES
Mathématiques, Physique-Chimie, SVT, Français, Anglais, Histoire-Géographie,
Philosophie, Économie, Informatique et plus encore — programme sénégalais.

🤖 TUTEUR IA QUI EXPLIQUE
Pose ta question en français ou en wolof : ÉcoleMax répond pas-à-pas, avec
la méthode et le raisonnement, pas seulement le résultat.

📷 CORRECTION PAR PHOTO
Prends une photo de ton exercice : l'IA lit l'énoncé et corrige.

✍️ EXERCICES ET RÉDACTION
Des exercices par chapitre, une aide à la rédaction avec contrôle anti-plagiat.

🔒 SÉCURITÉ
Pas de contenu recopié sans comprendre : l'app t'apprend à faire seul.

🎁 ESSAI GRATUIT 24 HEURES
Toutes les fonctionnalités, sans payer. Ensuite à partir de 250 FCFA.

Paiement Wave et Orange Money.
```

### Visuels obligatoires
| Élément | Format | Comment le faire |
|---|---|---|
| Icône | 512×512 PNG | `app-expo/assets/icon.png` (déjà en 1024, réduisez) |
| Image de présentation | 1024×500 PNG/JPG | capture d'écran de l'app + logo |
| Captures téléphone | **2 minimum** | 2 à 8 images, 1080×1920 |
| Captures tablette | optionnel | — |

> ✅ **Les captures sont déjà prêtes** dans `captures/` :
> `store-1-accueil.png` · `store-2-ia.png` (réponse IA avec wolof) · `store-3-exercice.png` · `store-4-profil.png`
>
> Elles sont au format 390×844 (téléphone). Pour le Play Store, rognez-les ou refaites-les en **1080×1920** depuis votre téléphone (ouvrez l'app, capture d'écran). Ne mettez **pas** de texte trompeur ni de faux boutons Play Store sur les visuels (motif de rejet classique).
>
> 📎 **Le fichier à envoyer au Play Store** : `projet/telechargements/EcoleMax-1.0.0.aab` (déjà signé et validé).

---

## 6. Politique de confidentialité (obligatoire, gratuit)

Google la vérifie. Sans elle, **impossible de publier**.

Hébergement gratuit de 2 pages : **pages.github.com** ou **netlify.com/drop**.

Contenu minimal à inclure :
- quelles données sont collectées (pseudo, mot de passe chiffré, niveau, ville) ;
- pourquoi (fournir les cours et l'IA) ;
- où elles sont stockées et combien de temps ;
- **la photo envoyée à l'IA est transmise à un fournisseur d'IA** (Groq/Gemini/OpenAI) et non conservée ;
- comment demander la suppression de son compte ;
- contact : votre e-mail.

Un modèle prêt à remplir est dans `projet/confidentialite.md`.

---

## 7. Questionnaire « Data safety » — 20 min

Dans la Play Console : **Sécurité des données**. Réponses pour ÉcoleMax :

| Question | Réponse |
|---|---|
| Collectez-vous des données ? | **Oui** |
| Données collectées | Nom/pseudo, adresse e-mail, identifiants, photos, historique d'utilisation |
| Données partagées avec des tiers ? | **Oui** (fournisseur d'IA pour les réponses) |
| Chiffrées en transit ? | **Oui** (HTTPS) |
| Suppression possible ? | **Oui** (par e-mail / dans l'app) |

⚠️ Une déclaration inexacte = **suspension du compte développeur**. Restez précis et honnête.

---

## 8. Envoyer la version — 10 min

1. **Production → Créer une version**.
2. Envoyer le fichier `.aab`.
3. Remplir les notes de version : `Première version d'ÉcoleMax : tuteur IA, 18 matières, correction photo.`
4. **Tests fermés d'abord** (recommandé) : 20 testeurs pendant 14 jours — Google l'impose désormais aux comptes particuliers récents.
   - Créer un test fermé, inviter 20 e-mails, publier.
5. Après les tests : **Promouvoir en production**.

---

## 9. Validation Google — 1 à 7 jours

Google vérifie : sécurité, politique de confidentialité, captures, permissions.

### Motifs de rejet les plus fréquents (et comment les éviter)
| Motif | Solution ÉcoleMax |
|---|---|
| Politique de confidentialité absente / inaccessible | héberger la page et mettre le lien public |
| Permissions non justifiées (caméra) | justifier : « photographier un exercice pour le corriger » |
| Data safety inexact | déclarer le partage avec le fournisseur d'IA |
| Contenu ou visuels trompeurs | captures réelles, pas de faux boutons |
| App qui plante au démarrage | tester l'APK `preview` avant |
| Compte de test manquant | fournir `fatimatou / fatimatou` dans les notes de validation |
| Public cible enfants | si vous ciblez les moins de 13 ans → programme « Families » plus strict |

---

## 10. Après la publication

- Lien public : `https://play.google.com/store/apps/details?id=sn.ecolemax.app`
- À mettre sur `projet/telecharger.html` et dans le QR code.
- Mises à jour : augmenter `versionCode` dans `app.json`, relancer `eas build`, envoyer.

---

## 💰 Récapitulatif des coûts

| Poste | Coût |
|---|---|
| Compte développeur Google | **25 $ une fois** |
| Build EAS (file lente) | 0 $ |
| Backend Render (gratuit) | 0 $ |
| Hébergement PWA (Netlify/GitHub Pages) | 0 $ |
| Politique de confidentialité | 0 $ |
| **Total pour être sur le Play Store** | **25 $ (~15 000 FCFA)** |

---

## ✅ Checklist finale

- [ ] Backend en ligne (URL HTTPS testée dans un navigateur)
- [ ] `URL_PRODUCTION` rempli dans `api.js`
- [ ] `eas build --profile production` terminé → `.aab`
- [ ] APK `preview` testé sur un vrai téléphone Android
- [ ] Icône 512×512 (`projet/assets/icone-ecolemax.png`) + 4 captures (`captures/store-*.png`)
- [ ] **AAB téléversé** : `projet/telechargements/EcoleMax-1.0.0.aab`
- [ ] Politique de confidentialité publiée (URL publique)
- [ ] Questionnaire Data safety rempli
- [ ] Compte de test fourni aux valideurs (`fatimatou / fatimatou`)
- [ ] Version envoyée → test fermé → production
