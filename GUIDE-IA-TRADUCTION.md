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
