# PROTOCOLE DE TEST ÉCOLEMAX — 50 ÉLÈVES
## Date : 2026-10-26 | Version : 1.0

---

## 1. LIENS DE LIVRAISON

### 🟢 POINT D'ACCÈS PRINCIPAL (code optimisé)
- **Site** : https://freely-priorities-adsl-treasure.trycloudflare.com
- **Dashboard admin** : https://freely-priorities-adsl-treasure.trycloudflare.com/dashboard
- **APK** : https://ecolemax.onrender.com/EcoleMax.apk

### 🟡 BACKUP STABLE (code fonctionnel)
- **Site** : https://ecolemax.onrender.com
- **Dashboard** : https://ecolemax.onrender.com/dashboard
- **APK** : https://ecolemax.onrender.com/EcoleMax.apk

---

## 2. INSCRIPTION PAR L'ÉLÈVE (5 étapes)

1. **Installer l'APK** : Télécharger EcoleMax.apk, cliquer sur « Installer »
2. **Créer le compte** : Pseudo (ex: eleve01) + mot de passe (min 6 chars)
3. **Renseigner le téléphone** : Optionnel mais recommandé (+221XXXXXXXXX)
4. **Se connecter** : Même pseudo + mot de passe
5. **Accéder à l'interface** : Exercices, quiz, IA

---

## 3. TEST SIMULTANÉ (50 élèves)

### Phase 1 — Installation (5 min)
- [ ] Télécharger APK
- [ ] Installer sur Android
- [ ] Ouvrir l'app

### Phase 2 — Inscription (10 min)
- [ ] Créer compte avec pseudo unique
- [ ] Mot de passe valide
- [ ] Phone si demandé

### Phase 3 — Connexion (5 min)
- [ ] Se connecter
- [ ] Voir interface élève
- [ ] Accéder aux exercices

### Phase 4 — Functionnalités (20 min)
- [ ] Exercices de difficulté 1/2/3
- [ ] Quiz 15 questions
- [ ] Assistant IA français
- [ ] Traduction en 10 langues

### Phase 5 — Synchronisation (5 min)
- [ ] Ouvrir le site web
- [ ] Se connecter avec même compte
- [ ] Voir historique synchronisé

---

## 4. CONTRÔLE ADMINISTRATEUR

### Accéder au dashboard :
- URL : https://freely-priorities-adsl-treasure.trycloudflare.com/dashboard
- Mot de passe admin : `ecolemax2026`

### Vérifier dans le dashboard :
- [ ] Liste des 50 inscriptions
- [ ] Activité des utilisateurs
- [ ] Historique des exercices/quiz
- [ ] Statistiques de performance
- [ ] Gestion des comptes (blocage/déblocage)

---

## 5. PROBABLES PROBLÈMES ET CORRECTIONS

| Problème | Cause | Solution |
|----------|-------|----------|
| APK non installable | Version Android trop ancienne | Vérifier Android 5.0+ |
| Inscription échoue | Pseudo déjà utilisé | Choisir un pseudo unique |
| Connexion échoue | Mauvais mot de passe | Vérifier les majuscules |
| IA ne répond pas | Clé API Groq non config | Vérifier dans app.py |
| Dashboard inaccessible | Tunnels instables | Utiliser l'URL Render backup |

---

## 6. RAPPORT DE TEST (à remplir après le test)

Date du test : ____________
Nombre d'installations réussies : ____/50
Nombre d'inscriptions réussies : ____/50
Nombre de connexions réussies : ____/50
Exercices complétés : ____
Quiz complétés : ____
IA utilisée : ____
Erreurs constatées : ______________
Corrections apportées : ______________

---

## 7. ACTIONS NÉCESSITANT INTERVENTION

- **Push GitHub** : Token GitHub requis pour déployer le code optimisé sur Render
- **Tunnel Cloudflare** : Compte Cloudflare requis pour tunnel nommé stable
- **Twilio SMS** : Vérifier les crédits pour SMS d'inscription
- **SendGrid email** : Vérifier les crédits pour emails de contact

---

## 8. CONTACT

- Email : sycheikhcorp@gmail.com
- Téléphone : +221 767 283 959
