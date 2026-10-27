# ÉcoleMax — Activer l'IA et la traduction « premium » (gratuit)

L'application fonctionne **sans aucune clé** : le moteur local répond instantanément
aux questions courantes, le cache sert les questions déjà posées, et les fournisseurs
gratuits prennent le relais.

Pour passer à une qualité et une rapidité maximales (50 élèves en même temps),
il suffit d'ajouter **une seule variable d'environnement** dans Render.
Aucune clé n'est écrite dans le code : tout passe par l'environnement.

---

## 1. Clé Gemini (recommandé pour l'IA — gratuit)

1. Ouvrir <https://aistudio.google.com/apikey>
2. « Create API key » → copier la clé (commence par `AIza…`)
3. Render → service `ecolemax` → onglet **Environment** → *Add Environment Variable*
   - **Key** : `GEMINI_API_KEY`
   - **Value** : la clé copiée
4. *Save Changes* (Render redéploie automatiquement)

Quota gratuit : 15 requêtes/minute, 1 500/jour — largement suffisant pour 50 élèves.
Modèle utilisé par défaut : `gemini-2.0-flash` (réponse en ~1 s).
Variable optionnelle : `GEMINI_MODEL` pour changer de modèle.

---

## 2. Clé DeepL (recommandé pour la traduction — gratuit)

1. Ouvrir <https://www.deepl.com/pro-api> → *DeepL API Free* (500 000 caractères/mois, sans carte)
2. Copier la clé (elle finit par `:fx`)
3. Render → **Environment** → ajouter
   - **Key** : `DEEPL_API_KEY`
   - **Value** : la clé

Dès qu'elle est présente, DeepL devient le moteur n° 1 de traduction
(qualité professionnelle, ~300 ms).

---

## 3. Autres clés acceptées (facultatif)

| Variable | Service | Gratuit |
|---|---|---|
| `GROQ_API_KEY` | Groq (Llama 3.3 70B) | oui, très rapide |
| `OPENAI_API_KEY` | OpenAI | non |
| `TRAD_EMAIL` | adresse de contact MyMemory (quota élargi) | oui |

---

## 4. Ce qui se passe sans clé (état actuel)

| Fonction | Comportement |
|---|---|
| Question de cours (capitale, conjugaison, calcul, date…) | **instantané** (moteur local, 0,01 s) |
| Question déjà posée | **instantané** (cache) |
| Question libre | OVH Qwen (~1–2 s) → Pollinations → moteur local |
| Traduction courte (mot, expression) | **instantané** (dictionnaire local) |
| Traduction d'une phrase | Google / MyMemory (0,4–1,2 s) ou IA (~1,5 s) |

> Les moteurs gratuits (Google, MyMemory) sont parfois limités depuis les IP
> partagées de Render (erreur 429). Le système bascule alors automatiquement
> sur le fournisseur suivant, sans erreur visible pour l'élève.

---

## 5. Vérifier que tout fonctionne

```bash
curl -H "X-Admin-Password: ecolemax2026" \
     https://ecolemax.onrender.com/api/diag/moteurs
```

La réponse indique, pour chaque moteur, s'il répond et en combien de millisecondes.

---

## 🔒 Rendre les clés PERMANENTES (survivent à tous les déploiements)

Render (offre gratuite) n'a **pas de disque permanent** : la base SQLite est réinitialisée à chaque
déploiement. Trois niveaux de protection sont en place :

### Niveau 1 — automatique (déjà actif, aucune action)
Le tableau de bord garde une copie des clés dans le navigateur de l'administrateur.
À chaque ouverture du dashboard, si le serveur a perdu ses clés, elles sont **réinjectées seules**
(`POST /api/admin/reglages/restore`). Message affiché : « Clés restaurées automatiquement ».

### Niveau 2 — recommandé : fichier secret Render (définitif, même sans navigateur)
1. Render → service **ecolemax-flask** → onglet **Environment**
2. Section **Secret Files** → **Add Secret File**
3. Nom du fichier : `cles.env`
4. Contenu :
   ```
   DEEPL_API_KEY=ta_cle_deepl:fx
   GEMINI_API_KEY=ta_cle_gemini
   TRAD_EMAIL=ecolemax.app@gmail.com
   ```
5. **Save** → Render redéploie et le serveur lit `/etc/secrets/cles.env` au démarrage.
   Ce fichier n'est pas dans le dépôt GitHub : il reste privé et persistant.

### Niveau 3 — variables d'environnement Render
Environment → **Add Environment Variable** → `DEEPL_API_KEY`, `GEMINI_API_KEY`.

**Ordre de priorité du code :** variable d'environnement Render > fichier secret > réglages du dashboard.

---

## 📡 Garder le serveur toujours éveillé

| Mécanisme | Fréquence | Rôle |
|---|---|---|
| Cron Render `ecolemax-keepalive` | 5 min | ping externe `/health` |
| Thread interne `keepalive()` | 4 min | auto-ping de `https://ecolemax.onrender.com/health` |
| `GET /api/ping` | à la demande | réponse ultra-légère (« pong ») pour les moniteurs |

**Recommandé en plus (gratuit) :** moniteur sur https://uptimerobot.com
→ type HTTPS, URL `https://ecolemax.onrender.com/api/ping`, intervalle **5 minutes**.
C'est le seul mécanisme qui réveille le service même si Render l'a endormi.
