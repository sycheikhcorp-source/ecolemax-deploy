#!/usr/bin/env python3
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter un générateur local de quiz/exercices avant les routes
generator_local = r'''
# === GÉNÉRATOR LOCAL DE CONTENUS (fallback sans IA) ===

def generate_exercice_local(sujet, difficulte):
    """Génère un exercice local basique."""
    cat_name = {"math":"Maths","fr":"Français","phys":"Physique","chim":"Chimie","svt":"SVT","hist":"Histoire","geo":"Géographie","eng":"Anglais","eco":"Économie","info":"Informatique","es":"Espagnol","ara":"Arabe"}.get(sujet,sujet)
    import random as _r
    templates = {
        "math": [
            ("Calculez {a} + {b} [{s1}/{s2}/{s3}/{s4}]", "{a} + {b} = {a}+{b}"),
            ("Simplifiez {a} × {b} [{s1}/{s2}/{s3}/{s4}]", "{a} × {b} = {a}×{b}"),
            ("Calculez {a} − {b} [{s1}/{s2}/{s3}/{s4}]", "{a} − {b} = {a}-{b}"),
            ("Calculez {a} ÷ {b} [{s1}/{s2}/{s3}/{s4}]", "{a} ÷ {b} = {a}/{b}"),
        ],
        "fr": [
            ("Conjuguez le verbe 'manger' au présent : je ___ [mange/manges/mange/mange]", "je mange"),
            ("Quelle est la forme correcte ? 'Les enfants ___' [joue/jouent/joues/jouant]", "jouent"),
            ("Complétez : 'Il est ___ grand' [très/trop/tellement/assez]", "très"),
            ("Synonyme de 'rapide' : [véloce/lent/paresseux/calme]", "véloce"),
        ],
        "phys": [
            ("Un objet de 5 kg est soumis à une force de 20 N. Calculez l'accélération [4 m/s²/5 m/s²/0.25 m/s²/25 m/s²]", "a = F/m = 20/5 = 4 m/s²"),
            ("La vitesse de la lumière est environ [300 000 km/s/30 000 km/s/3 000 km/s/3 000 000 km/s]", "300 000 km/s"),
            ("L'unité de la force est [Newton/Joule/Watt/Pascal]", "Newton"),
            ("La vitesse est égale à [distance / temps/temps × distance/force × masse/énergie × masse]", "distance / temps"),
        ],
        "chim": [
            ("Formule de l'eau est [H₂O/CO₂/O₂/N₂]", "H₂O"),
            ("Le pH d'une solution neutre est [7/0/14/1]", "7"),
            ("Atome le plus réactif du tableau périodique : [Fluor/Oxygène/Hydrogène/Azote]", "Fluor"),
            ("Nombre d'électrons de l'oxygène : [8/6/10/16]", "8"),
        ],
        "svt": [
            ("Le cœur pompe le sang vers [le corps/les poumons/le cerveau/tout le corps]", "tout le corps"),
            ("La photosynthèse se produit dans [les feuilles/les racines/les fleurs/les fruits]", "les feuilles"),
            ("L'ADN est situé dans [le noyau/la membrane/le cytoplasme/les mitochondries]", "le noyau"),
            ("Les cellules nerveuses sont appelées [neurones/leucocytes/erythrocytes/myocytes]", "neurones"),
        ],
        "hist": [
            ("La capitale du royaume du Tekrour était [Tomboctou/Gao/Djenné/Ségou]", "Tomboctou"),
            ("L'indépendance du Sénégal a été proclamée en [1960/1958/1965/1970]", "1960"),
            ("Premier président du Sénégal : [Léopold Sédar Senghor/Abdoulaye Wade/Macky Sall/Diouf]", "Léopold Sédar Senghor"),
            ("La ville de Saint-Louis fut la capitale de l'Afrique-Occidentale française en [1895/1902/1860/1920]", "1895"),
        ],
        "geo": [
            ("Capitale du Sénégal : [Dakar/Touba/Thiès/Saint-Louis]", "Dakar"),
            ("Le fleuve le plus long d'Afrique est [le Nil/le Niger/le Sénégal/le Congo]", "le Nil"),
            ("Le Mont Everest se situe dans [l'Asie/l'Afrique/l'Amérique/l'Europe]", "l'Asie"),
            ("Le Sahara est situé en [Afrique/Asie/Amérique/Europe]", "Afrique"),
        ],
        "eng": [
            ("How are you? [Comment allez-vous/Comment tu es/Qui es-tu/Où vas-tu]", "Comment allez-vous"),
            ("I ___ a student [am/is/are/be]", "am"),
            ("The plural of 'child' is [children/childs/childes/child]", "children"),
            ("Good morning means [Bonjour/Bonsoir/Au revoir/Merci]", "Bonjour"),
        ],
        "eco": [
            ("La monnaie du Sénégal est [XOF/FCFA/EUR/USD]", "XOF"),
            ("La banque centrale de l'UMOA est [BCEAO/BCE/Banque de France/BRI]", "BCEAO"),
            ("L'inflation est [la hausse des prix/la baisse des prix/la stabilité des prix/l'équilibre budgétaire]", "la hausse des prix"),
            ("Le PIB mesure [la richesse d'un pays/la population/le taux d'intérêt/l'inflation]", "la richesse d'un pays"),
        ],
        "info": [
            ("HTML signifie [HyperText Markup Language/HyperTransfer/HighText/HyperLanguage]", "HyperText Markup Language"),
            ("CSS signifie [Cascading Style Sheets/Creative Style Sheets/Computer Style Sheets/Code Style Sheets]", "Cascading Style Sheets"),
            ("Le langage de programmation le plus populaire pour le web est [Python/Java/JavaScript/C++]", "JavaScript"),
            ("Une adresse IP est composée de [4 nombres/3 nombres/6 nombres/2 nombres]", "4 nombres"),
        ],
    }
    templates_default = [
        ("Question de " + cat_name + " : [Option A/Option B/Option C/Option D]", "Explication pédagogique"),
    ]
    tpls = templates.get(sujet, templates_default)
    tpl = _r.choice(tpls)
    if "{a}" in tpl[0]:
        a = _r.randint(2,20)
        b = _r.randint(2,20)
        s1 = a+b
        wrong = _r.sample([s1+1, s1-1, s1+2], 3)
        q = tpl[0].format(a=a,b=b,s1=s1,s2=wrong[0],s3=wrong[1],s4=wrong[2])
        exp = tpl[1].format(a=a,b=b)
        return sujet, q, exp, difficulte, ""
    else:
        q = tpl[0]
        exp = tpl[1]
        return sujet, q, exp, difficulte, ""

def generate_quiz_local(categorie, difficulte):
    """Génère un quiz local basique."""
    import random as _r
    templates = {
        "Maths": [
            ("Quel est le résultat de 7 × 8 ?", 3, "7 × 8 = 56", "facile"),
            ("La racine carrée de 25 est :", 2, "√25 = 5", "facile"),
            ("Un triangle avec 3 côtés égaux est un :", 1, "Triangle équilatéral", "moyen"),
            ("La valeur de π est environ :", 0, "π ≈ 3.1416", "moyen"),
        ],
        "Français": [
            ("Quelle est la capitale de la France ?", 2, "Paris", "facile"),
            ("Le pluriel de 'cheval' est :", 0, "chevaux", "facile"),
            ("Conjuguer 'être' à la 1ère personne :", 0, "je suis", "moyen"),
            ("Un synonyme de 'joli' est :", 1, "beau", "facile"),
        ],
        "Physique": [
            ("La force est mesurée en :", 0, "Newton (N)", "facile"),
            ("La vitesse de la lumière est :", 2, "300 000 km/s", "moyen"),
            ("L'unité de la température est :", 1, "Kelvin (K)", "moyen"),
            ("La loi de Newton est liée à :", 0, "la force et l'accélération", "difficile"),
        ],
        "Chimie": [
            ("La formule de l'eau est :", 0, "H₂O", "facile"),
            ("Le pH d'un acide est :", 0, "inférieur à 7", "facile"),
            ("Le nombre atomique de l'oxygène est :", 2, "8", "moyen"),
            ("Un atome stable a :", 1, "des électrons en couches complètes", "difficile"),
        ],
        "SVT": [
            ("Le cœur est situé dans :", 1, "la poitrine", "facile"),
            ("La photosynthèse transforme :", 0, "la lumière en énergie", "moyen"),
            ("Les cellules nerveuses sont appelées :", 1, "neurones", "facile"),
            ("Le système circulatoire transporte :", 0, "le sang", "facile"),
        ],
        "Histoire": [
            ("L'indépendance du Sénégal date de :", 3, "1960", "facile"),
            ("Le premier président du Sénégal est :", 2, "Léopold Sédar Senghor", "facile"),
            ("La capitale historique du Mali est :", 1, "Tombouctou", "moyen"),
        ],
        "Géographie": [
            ("Capitale du Sénégal :", 0, "Dakar", "facile"),
            ("Le fleuve le plus long d'Afrique :", 1, "le Nil", "facile"),
            ("La plus grande ville d'Afrique est :", 2, "Le Caire", "moyen"),
            ("Le Sahara est un :", 0, "désert", "facile"),
        ],
        "Anglais": [
            ("How are you?", 0, "Comment allez-vous", "facile"),
            ("I ___ a book", 0, "am", "facile"),
            ("The plural of 'child' is :", 1, "children", "moyen"),
            ("Goodbye means :", 2, "Au revoir", "facile"),
        ],
        "Économie": [
            ("La monnaie du Sénégal est :", 1, "XOF", "facile"),
            ("La BCEAO est :", 0, "la banque centrale de l'UMOA", "moyen"),
            ("L'inflation est :", 1, "la hausse des prix", "facile"),
        ],
        "Informatique": [
            ("HTML signifie :", 0, "HyperText Markup Language", "facile"),
            ("CSS est utilisé pour :", 1, "styliser les pages web", "facile"),
            ("Une adresse IP v4 comporte :", 3, "4 nombres", "moyen"),
            ("Le langage du web par défaut est :", 2, "JavaScript", "moyen"),
        ],
    }
    templates_default = [
        ("Question de " + categorie + " :", 0, "Explication pédagogique", "moyen"),
    ]
    tpls = templates.get(categorie, templates_default)
    q, rep, exp, _ = _r.choice(tpls)
    return categorie, q, rep, exp, difficulte

'''

# Ajouter les fonctions locales avant les routes admin
marker = "# === ROUTES ADMIN : GÉNÉRATION IA ET CRUD CONTENUS ==="
pos = content.find(marker)
if pos == -1:
    pos = len(content)

content = content[:pos] + generator_local + "\n" + content[pos:]

# Modifier la route de génération d'exercices pour utiliser le fallback local
old_gen_ex = '''        ok, text, src = get_pollinations(q_prompt, max_tokens=500, silent=True)
        if not ok:
            ok, text, src = get_local_reponse(q_prompt), "", "Local"
        try:
            m = re.search(r'\\{[^{}]*"question"[^{}]*\\}', text, re.DOTALL)
            if m:
                j = json.loads(m.group(0))
                question = j.get("question","")
                explication = j.get("explication","")
                if question and len(question) > 10:
                    generated.append((sujet, question, explication, difficulte, niveau))
        except:
            pass'''

new_gen_ex = '''        ok, text, src = get_pollinations(q_prompt, max_tokens=500, silent=True)
        if ok and text and "402" not in text and "Payment" not in text:
            try:
                m = re.search(r'\\{[^{}]*"question"[^{}]*\\}', text, re.DOTALL)
                if m:
                    j = json.loads(m.group(0))
                    question = j.get("question","")
                    explication = j.get("explication","")
                    if question and len(question) > 10:
                        generated.append((sujet, question, explication, difficulte, niveau))
                        continue
            except:
                pass
        # Fallback local
        try:
            cat, q, exp, diff, niv = generate_exercice_local(sujet, difficulte)
            generated.append((cat, q, exp, diff, niv))
        except:
            pass'''

if old_gen_ex in content:
    content = content.replace(old_gen_ex, new_gen_ex)
    patched_ex = True
else:
    patched_ex = False

# Modifier la route de génération de quiz
old_gen_q = '''        ok, text, src = get_pollinations(q_prompt, max_tokens=400, silent=True)
        if not ok: continue
        try:
            m = re.search(r'\\{[^{}]*"question"[^{}]*\\}', text, re.DOTALL)
            if m:
                j = json.loads(m.group(0))
                q = j.get("question","")
                rep = j.get("reponse",0)
                exp = j.get("explication","")
                if rep < 0 or rep > 3: rep = 0
                if q and len(q) > 10:
                    generated.append((categorie, q, rep, exp, difficulte))
        except:
            pass'''

new_gen_q = '''        ok, text, src = get_pollinations(q_prompt, max_tokens=400, silent=True)
        if ok and text and "402" not in text and "Payment" not in text:
            try:
                m = re.search(r'\\{[^{}]*"question"[^{}]*\\}', text, re.DOTALL)
                if m:
                    j = json.loads(m.group(0))
                    q = j.get("question","")
                    rep = j.get("reponse",0)
                    exp = j.get("explication","")
                    if rep < 0 or rep > 3: rep = 0
                    if q and len(q) > 10:
                        generated.append((categorie, q, rep, exp, difficulte))
                        continue
            except:
                pass
        # Fallback local
        try:
            cat, q, rep, exp, diff = generate_quiz_local(categorie, difficulte)
            generated.append((cat, q, rep, exp, diff))
        except:
            pass'''

if old_gen_q in content:
    content = content.replace(old_gen_q, new_gen_q)
    patched_q = True
else:
    patched_q = False

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"PATCH OK - ex={patched_ex}, quiz={patched_q}")
