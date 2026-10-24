# -*- coding: utf-8 -*-
"""
ÉcoleMax — Bibliothèque de réponses locales
============================================
Répond sans Internet, sans clé API et sans limite, aux questions les plus
fréquentes du programme sénégalais (collège / lycée).

Utilisée en secours quand les fournisseurs d'IA gratuits sont saturés.
Chaque entrée renvoie une réponse pédagogique structurée : réponse,
explication, étapes.
"""

import re
import unicodedata


# ------------------------------------------------------------------
# Normalisation de la question
# ------------------------------------------------------------------
def normaliser(texte):
    """minuscule, sans accents, espaces simplifiés."""
    t = (texte or "").lower()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _contient(q, *mots):
    return any(m in q for m in mots)


# ------------------------------------------------------------------
# Base de connaissances
# (mots-clés, réponse, explication, étapes)
# ------------------------------------------------------------------
BASE = [
    # ---------- MATHÉMATIQUES ----------
    {
        "mots": ["derivee", "deriver", "derivation"],
        "titre": "La dérivée",
        "reponse": (
            "La **dérivée** mesure la vitesse à laquelle une fonction change. "
            "Graphiquement, c'est la pente de la tangente à la courbe en un point."
        ),
        "explication": (
            "Si f(x) = x², alors f'(x) = 2x. En x = 3, la pente vaut 6 : "
            "quand x augmente un peu, f augmente environ 6 fois plus vite."
        ),
        "etapes": [
            "Formules de base : (xⁿ)' = n·xⁿ⁻¹ · (k)' = 0 · (kx)' = k",
            "Somme : (u + v)' = u' + v'",
            "Produit : (u·v)' = u'·v + u·v'",
            "Quotient : (u/v)' = (u'·v − u·v') / v²",
            "Composée : (u∘v)' = v' × u'(v)",
            "Application : f(x) = 3x² + 2x − 1 → f'(x) = 6x + 2",
        ],
    },
    {
        "mots": ["fonction affine", "affine", "y = ax + b", "droite"],
        "titre": "La fonction affine",
        "reponse": (
            "Une **fonction affine** s'écrit f(x) = ax + b. "
            "Sa représentation graphique est une **droite**."
        ),
        "explication": (
            "• **a** = coefficient directeur (la pente) : si a > 0 la droite monte, "
            "si a < 0 elle descend.\n"
            "• **b** = ordonnée à l'origine : c'est là où la droite coupe l'axe des y."
        ),
        "etapes": [
            "Exemple : f(x) = 2x + 3 → a = 2, b = 3",
            "f(0) = 3 : la droite passe par (0 ; 3)",
            "Pour tracer : il suffit de 2 points, par exemple (0 ; 3) et (1 ; 5)",
            "Pour trouver a entre deux points A et B : a = (yB − yA) / (xB − xA)",
        ],
    },
    {
        "mots": ["pythagore", "hypotenuse", "triangle rectangle"],
        "titre": "Théorème de Pythagore",
        "reponse": (
            "Dans un triangle **rectangle**, le carré de l'hypoténuse est égal "
            "à la somme des carrés des deux autres côtés : **a² + b² = c²** "
            "(c = hypoténuse, le côté face à l'angle droit)."
        ),
        "explication": "Si les côtés de l'angle droit mesurent 3 et 4, alors c² = 9 + 16 = 25, donc c = 5.",
        "etapes": [
            "Repérer l'angle droit et l'hypoténuse (le plus long côté)",
            "Écrire : (côté1)² + (côté2)² = (hypoténuse)²",
            "Calculer les carrés puis additionner",
            "Prendre la racine carrée du résultat",
            "Réciproque : si a² + b² = c², alors le triangle est rectangle",
        ],
    },
    {
        "mots": ["thales", "thalès"],
        "titre": "Théorème de Thalès",
        "reponse": (
            "Si deux droites sont **parallèles** et coupent deux sécantes, alors "
            "les rapports de longueurs sont égaux : **AM/AB = AN/AC = MN/BC**."
        ),
        "explication": "Cela permet de calculer une longueur inconnue dans une configuration de triangles emboîtés.",
        "etapes": [
            "Vérifier que les droites (MN) et (BC) sont parallèles",
            "Écrire l'égalité des trois rapports",
            "Remplacer par les valeurs connues",
            "Faire un produit en croix pour trouver l'inconnue",
        ],
    },
    {
        "mots": ["second degre", "discriminant", "delta", "equation du second"],
        "titre": "Équation du second degré",
        "reponse": (
            "Pour **ax² + bx + c = 0**, on calcule le discriminant "
            "**Δ = b² − 4ac**, puis x = (−b ± √Δ) / (2a)."
        ),
        "explication": (
            "• Δ > 0 : deux solutions distinctes\n"
            "• Δ = 0 : une solution double x = −b/2a\n"
            "• Δ < 0 : aucune solution réelle"
        ),
        "etapes": [
            "Identifier a, b et c",
            "Calculer Δ = b² − 4ac",
            "Si Δ ≥ 0, appliquer x = (−b ± √Δ) / (2a)",
            "Exemple : x² − 5x + 6 = 0 → Δ = 25 − 24 = 1 → x = 3 ou x = 2",
        ],
    },
    {
        "mots": ["pourcentage", "pourcent", " %", "remise", "augmentation"],
        "titre": "Les pourcentages",
        "reponse": "Un pourcentage est une proportion sur 100 : **t % de N = N × t / 100**.",
        "explication": "15 % de 200 = 200 × 15/100 = 30.",
        "etapes": [
            "Pour calculer t % d'un nombre : multiplier par t puis diviser par 100",
            "Augmenter de t % : multiplier par (1 + t/100)",
            "Diminuer de t % : multiplier par (1 − t/100)",
            "Retrouver le prix initial : diviser par le coefficient",
        ],
    },
    {
        "mots": ["pgcd", "ppcm", "plus grand commun diviseur"],
        "titre": "PGCD et PPCM",
        "reponse": "Le **PGCD** est le plus grand nombre qui divise deux entiers ; le **PPCM** est le plus petit multiple commun.",
        "explication": "PGCD(12, 18) = 6 et PPCM(12, 18) = 36.",
        "etapes": [
            "Décomposer chaque nombre en facteurs premiers",
            "PGCD = produit des facteurs communs avec le plus petit exposant",
            "PPCM = produit de tous les facteurs avec le plus grand exposant",
            "Astuce : PGCD × PPCM = a × b",
        ],
    },
    {
        "mots": ["suite arithmetique", "suite geometrique", "suites"],
        "titre": "Les suites",
        "reponse": (
            "**Arithmétique** : on ajoute toujours la même raison r → uₙ = u₀ + n·r.\n"
            "**Géométrique** : on multiplie toujours par la même raison q → uₙ = u₀ × qⁿ."
        ),
        "explication": "Suite arithmétique 2, 5, 8, 11 (r = 3). Suite géométrique 2, 6, 18, 54 (q = 3).",
        "etapes": [
            "Calculer u₁ − u₀ : si c'est constant → arithmétique",
            "Calculer u₁ / u₀ : si c'est constant → géométrique",
            "Appliquer la formule du terme général",
            "Somme arithmétique : n × (premier + dernier) / 2",
        ],
    },
    {
        "mots": ["probabilite", "proba", "hasard", "chance"],
        "titre": "Les probabilités",
        "reponse": "La probabilité d'un événement = **nombre de cas favorables / nombre de cas possibles**.",
        "explication": "Obtenir un 6 avec un dé : 1 cas favorable sur 6 → P = 1/6 ≈ 0,167.",
        "etapes": [
            "Lister tous les résultats possibles (l'univers)",
            "Compter les cas favorables",
            "Diviser : P = favorables / possibles (toujours entre 0 et 1)",
            "P(contraire) = 1 − P(événement)",
        ],
    },
    {
        "mots": ["aire", "perimetre", "surface", "volume"],
        "titre": "Aires, périmètres et volumes",
        "reponse": "Voici les formules essentielles à retenir.",
        "explication": (
            "• Rectangle : aire = L × l, périmètre = 2(L + l)\n"
            "• Triangle : aire = (base × hauteur) / 2\n"
            "• Cercle : aire = πr², périmètre = 2πr\n"
            "• Sphère : volume = (4/3)πr³"
        ),
        "etapes": [
            "Identifier la figure et les dimensions données",
            "Choisir la formule correspondante",
            "Convertir toutes les longueurs dans la même unité",
            "Écrire le résultat avec l'unité correcte (cm², m³…)",
        ],
    },

    # ---------- PHYSIQUE-CHIMIE ----------
    {
        "mots": ["loi d'ohm", "loi dohm", "ohm", "resistance", "tension", "intensite"],
        "titre": "La loi d'Ohm",
        "reponse": "**U = R × I** : la tension (volts) est égale à la résistance (ohms) multipliée par l'intensité (ampères).",
        "explication": "Un résistor de 100 Ω traversé par 0,05 A subit une tension U = 100 × 0,05 = 5 V.",
        "etapes": [
            "Repérer les grandeurs connues (U, R ou I)",
            "Appliquer U = R·I, ou I = U/R, ou R = U/I",
            "Vérifier les unités : V, Ω, A",
            "Contrôler l'ordre de grandeur du résultat",
        ],
    },
    {
        "mots": ["vitesse", "v = d/t", "mouvement", "acceleration"],
        "titre": "Vitesse et mouvement",
        "reponse": "**v = d / t** : la vitesse est la distance divisée par le temps.",
        "explication": "120 km en 2 h → v = 60 km/h. Pour convertir : 1 m/s = 3,6 km/h.",
        "etapes": [
            "Convertir les unités (m et s, ou km et h)",
            "Appliquer v = d / t",
            "Pour la distance : d = v × t",
            "Pour le temps : t = d / v",
        ],
    },
    {
        "mots": ["poids", "masse", "gravite", "pesanteur"],
        "titre": "Poids et masse",
        "reponse": "Le **poids** est une force (en newtons) : **P = m × g**. La **masse** est en kilogrammes et ne change pas selon le lieu.",
        "explication": "Sur Terre g ≈ 9,8 N/kg : une masse de 50 kg a un poids de 490 N.",
        "etapes": [
            "Convertir la masse en kg",
            "Utiliser g ≈ 9,8 N/kg sur Terre (1,6 sur la Lune)",
            "Calculer P = m × g",
            "Écrire le résultat en newtons (N)",
        ],
    },
    {
        "mots": ["mole", "avogadro", "quantite de matiere"],
        "titre": "La mole",
        "reponse": "Une mole contient **6,02 × 10²³ entités** (nombre d'Avogadro). n = N / Nₐ.",
        "explication": "2 moles d'eau contiennent 12,04 × 10²³ molécules.",
        "etapes": [
            "Identifier ce qui est compté (atomes, molécules, ions)",
            "Utiliser n = N / 6,02×10²³",
            "Pour une masse : n = m / M (masse molaire)",
            "Toujours préciser l'unité : mol",
        ],
    },

    # ---------- FRANÇAIS / LITTÉRATURE ----------
    {
        "mots": ["figure de style", "figures de style", "metaphore", "comparaison", "personnification"],
        "titre": "Les figures de style",
        "reponse": "Une figure de style est un procédé d'écriture qui rend l'expression plus expressive.",
        "explication": (
            "• **Comparaison** : « fort comme un lion » (avec un outil de comparaison)\n"
            "• **Métaphore** : « cet homme est un lion » (sans outil)\n"
            "• **Personnification** : « le vent murmure »\n"
            "• **Hyperbole** : « je meurs de faim »\n"
            "• **Anaphore** : répétition en début de phrase"
        ),
        "etapes": [
            "Repérer le mot ou l'expression qui sort de l'ordinaire",
            "Chercher l'image utilisée",
            "Identifier l'outil de comparaison (comme, tel que, ressembler à)",
            "Nommer la figure et expliquer son effet",
        ],
    },
    {
        "mots": ["subjonctif", "conjugaison", "temps", "imparfait", "passe simple"],
        "titre": "Le subjonctif",
        "reponse": "Le subjonctif exprime le souhait, le doute, l'obligation ou l'émotion. Il est presque toujours précédé de **« que »**.",
        "explication": "« Il faut que je **parte** » (subjonctif) ≠ « Je **pars** » (indicatif).",
        "etapes": [
            "Repérer un verbe de volonté, de doute ou une conjonction (pour que, bien que, avant que)",
            "Prendre le radical de la 3ᵉ personne du pluriel au présent",
            "Ajouter les terminaisons : -e, -es, -e, -ions, -iez, -ent",
            "Exceptions à mémoriser : être (que je sois), avoir (que j'aie), aller (que j'aille)",
        ],
    },
    {
        "mots": ["dissertation", "commentaire", "introduction", "plan"],
        "titre": "Méthode de la dissertation",
        "reponse": "Une dissertation = **introduction + développement en 2 ou 3 parties + conclusion**.",
        "explication": "L'introduction contient : l'amorce, la problématique, l'annonce du plan.",
        "etapes": [
            "Analyser le sujet et définir les mots-clés",
            "Formuler une problématique claire",
            "Construire un plan (thèse / antithèse / synthèse)",
            "Rédiger : 1 idée = 1 paragraphe = argument + exemple",
            "Conclure en répondant à la problématique",
        ],
    },
    {
        "mots": ["resume", "resumer un texte"],
        "titre": "Le résumé de texte",
        "reponse": "Un résumé reformule les idées essentielles du texte, **sans les commenter**, avec un nombre de mots imposé.",
        "explication": "On garde les idées, on supprime les exemples et les répétitions.",
        "etapes": [
            "Lire le texte deux fois",
            "Repérer l'idée directrice et les idées secondaires",
            "Supprimer exemples, citations et redondances",
            "Reformuler avec ses propres mots",
            "Compter les mots et respecter l'écart autorisé (±10 %)",
        ],
    },

    # ---------- SVT / HISTOIRE / GÉOGRAPHIE ----------
    {
        "mots": ["photosynthese", "chlorophylle", "plante verte"],
        "titre": "La photosynthèse",
        "reponse": "La photosynthèse permet aux plantes vertes de fabriquer de la matière organique à partir de **CO₂, d'eau et de lumière**, grâce à la **chlorophylle**.",
        "explication": "Bilan simplifié : 6 CO₂ + 6 H₂O + lumière → C₆H₁₂O₆ + 6 O₂.",
        "etapes": [
            "Les racines absorbent l'eau et les sels minéraux",
            "Les feuilles captent le CO₂ par les stomates",
            "La chlorophylle capte l'énergie lumineuse",
            "Le glucose est fabriqué et l'oxygène rejeté",
        ],
    },
    {
        "mots": ["cellule", "adn", "chromosome", "gene", "mitose"],
        "titre": "La cellule et l'ADN",
        "reponse": "La cellule est l'unité de base du vivant. L'**ADN** porte l'information génétique, organisée en **chromosomes**.",
        "explication": "Chez l'humain : 46 chromosomes (23 paires) dans chaque cellule.",
        "etapes": [
            "La cellule = membrane + cytoplasme + noyau",
            "Le noyau contient les chromosomes (ADN)",
            "Un gène = un segment d'ADN qui code un caractère",
            "La mitose = division qui donne 2 cellules identiques",
        ],
    },
    {
        "mots": ["traite negriere", "esclavage", "colonisation", "independance", "1960"],
        "titre": "Colonisation et indépendances",
        "reponse": "La plupart des pays d'Afrique de l'Ouest deviennent indépendants en **1960** ; le Sénégal le 4 avril 1960.",
        "explication": "La traite atlantique (XVᵉ–XIXᵉ s.) a déporté des millions d'Africains vers les Amériques ; Gorée en est un symbole mémoriel.",
        "etapes": [
            "Situer la période (XVᵉ–XIXᵉ s. pour la traite, 1885–1960 pour la colonisation)",
            "Identifier les causes (économiques, politiques, idéologiques)",
            "Décrire les conséquences (démographiques, culturelles, frontières)",
            "Retenir les dates-clés : 1885 (Berlin), 1946 (Union française), 1960 (indépendances)",
        ],
    },
    {
        "mots": ["climat", "sahélien", "desertification", "secheresse", "sahel"],
        "titre": "Le climat sahélien",
        "reponse": "Le Sahel a un climat **tropical semi-aride** : une saison des pluies courte (juin-octobre) et une longue saison sèche.",
        "explication": "La désertification vient de la sécheresse combinée à la pression humaine (déboisement, surpâturage).",
        "etapes": [
            "Caractériser : précipitations faibles et irrégulières (300-600 mm/an)",
            "Expliquer : anticyclone saharien, mousson atlantique",
            "Conséquences : sécheresses, exode rural, baisse des rendements",
            "Solutions : reboisement, zai, cordons pierreux, irrigation maîtrisée",
        ],
    },
    {
        "mots": ["economie", "pib", "inflation", "chomage", "offre et demande"],
        "titre": "Notions d'économie",
        "reponse": "Le **PIB** mesure la richesse produite dans un pays ; l'**inflation** est la hausse générale des prix.",
        "explication": "Si les prix augmentent de 3 % par an, ce qui coûtait 1 000 F coûte 1 030 F un an plus tard.",
        "etapes": [
            "PIB = somme des valeurs ajoutées produites",
            "Inflation = variation de l'indice des prix à la consommation",
            "Chômage = population active sans emploi et en recherchant un",
            "Offre > demande → prix baissent ; demande > offre → prix montent",
        ],
    },
    {
        "mots": ["philosophie", "conscience", "liberte", "verite", "morale"],
        "titre": "Notions de philosophie",
        "reponse": "En philosophie, on ne « récite » pas : on **problématise**. Toute réponse doit passer par une question bien posée.",
        "explication": "Exemple sur la liberté : suis-je libre quand je fais ce que je veux, ou seulement quand je comprends pourquoi je le veux ?",
        "etapes": [
            "Définir les termes du sujet",
            "Formuler le problème (la tension entre deux réponses possibles)",
            "Présenter une thèse avec un argument et un auteur",
            "Présenter l'objection, puis dépasser la contradiction",
            "Conclure de façon nuancée",
        ],
    },

    # ---------- MÉTHODE / ORIENTATION ----------
    {
        "mots": ["methode", "comment apprendre", "reviser", "memoriser", "concentration"],
        "titre": "Méthode de travail",
        "reponse": "Pour retenir durablement, il faut **espacer les révisions** et **se tester** plutôt que relire.",
        "explication": "Relire donne l'impression de savoir ; se poser des questions force le cerveau à récupérer l'information.",
        "etapes": [
            "Découper la leçon en petites parties",
            "Réviser à J+1, J+3, J+7 (répétition espacée)",
            "Se tester à voix haute ou par écrit, sans regarder",
            "Faire des exercices, pas seulement lire",
            "Dormir suffisamment : la mémoire se consolide la nuit",
        ],
    },
    {
        "mots": ["orientation", "serie", "filiere", "universite", "metier"],
        "titre": "Choisir sa filière",
        "reponse": "Le bon choix dépend de **3 éléments** : ce que tu aimes, ce dans quoi tu es bon, et les débouchés.",
        "explication": "Un élève fort en maths mais passionné de biologie peut viser médecine (S) ou ingénierie ; mieux vaut croiser les trois critères.",
        "etapes": [
            "Lister tes 3 matières préférées et tes 3 meilleures notes",
            "Renseigne-toi sur les métiers qui recrutent au Sénégal",
            "Renseigne-toi sur les séries requises pour chaque formation",
            "Parle à des étudiants déjà dans la filière visée",
        ],
    },
    {
        "mots": ["fonction exponentielle", "exponentielle", "puissance", "exposant"],
        "titre": "La fonction exponentielle",
        "reponse": "Une fonction exponentielle est de la forme **f(x) = a · bˣ** avec b > 0 et b ≠ 1. Si b > 1, elle est croissante ; si 0 < b < 1, elle est décroissante.",
        "explication": "La fonction 2ˣ est croissante : 2⁰=1, 2¹=2, 2²=4, 2³=8. Chaque pas de +1 double le résultat.",
        "etapes": [
            "Identifier a (ordonnée à l'origine) et b (base)",
            "Si b > 1 → croissante ; si 0 < b < 1 → décroissante",
            "Propriété : bˣ⁺ʸ = bˣ · bʸ",
            "Équation bˣ = k → x = log_b(k)",
        ],
    },
    {
        "mots": ["logarithme", "log", "népérien", "décimal"],
        "titre": "Le logarithme",
        "reponse": "Le **logarithme** est la fonction réciproque de l'exponentielle. log_b(x) = y ssi bʸ = x.",
        "explication": "Exemple : log₁₀(100) = 2 car 10² = 100. logₑ = ln (népérien).",
        "etapes": [
            "log_b(b) = 1, log_b(1) = 0",
            "Propriété : log_b(x·y) = log_b(x) + log_b(y)",
            "Changement de base : log_b(x) = log_c(x) / log_c(b)",
            "Résoudre bˣ = k → x = log_b(k)",
        ],
    },
    {
        "mots": ["trigonométrie", "sinus", "cosinus", "tangente", "angle"],
        "titre": "Trigonométrie dans le triangle rectangle",
        "reponse": "Dans un triangle rectangle : **sinus** = côté opposé / hypoténuse, **cosinus** = côté adjacent / hypoténuse, **tangente** = opposé / adjacent.",
        "explication": "Pour un angle de 30° : sin(30°) = 1/2, cos(30°) = √3/2, tan(30°) = 1/√3.",
        "etapes": [
            "Identifier l'angle α dans le triangle rectangle",
            "sin α = opposé / hypoténuse",
            "cos α = adjacent / hypoténuse",
            "tan α = opposé / adjacent = sin α / cos α",
        ],
    },
    {
        "mots": ["mécanique", "force", "newton", "masse", "accélération"],
        "titre": "Loi de Newton : F = ma",
        "reponse": "La **deuxième loi de Newton** : **F = m · a** (force = masse × accélération).",
        "explication": "Une masse de 2 kg subissant une accélération de 3 m/s² subit une force de 6 N.",
        "etapes": [
            "Identifier la masse m (en kg) et l'accélération a (en m/s²)",
            "Calculer F = m × a (en newtons)",
            "Si la force et la masse doublent, l'accélération doit doubler",
            "Unités : F en N, m en kg, a en m/s²",
        ],
    },
    {
        "mots": ["optique", "réflexion", "réfraction", "miroir", "lentille"],
        "titre": "Optique : réflexion et réfraction",
        "reponse": "La **réflexion** : un rayon frappe une surface et repart (angle de réflexion = angle d'incidence). La **réfraction** : le rayon change de direction en traversant un milieu.",
        "explication": "Un rayon frappe un miroir plan : l'angle entre le rayon et la normale est identique avant et après.",
        "etapes": [
            "Réflexion : angle de réflexion = angle d'incidence",
            "Réfraction : loi de Snell-Descartes n₁·sin(i) = n₂·sin(r)",
            "Miroir plan : image virtuelle, droite, même taille, symétrique",
            "Lentille convergente : rayons parallèles convergent au foyer",
        ],
    },
    {
        "mots": ["atome", "électron", "proton", "neutron", "noyau"],
        "titre": "Structure de l'atome",
        "reponse": "L'**atome** est composé d'un **noyau** (protons + neutrons) et d'**électrons** qui tournent autour.",
        "explication": "Le noyau est petit, dense et chargé positivement. Les électrons, chargés négativement, occupent des couches autour.",
        "etapes": [
            "Noyau : protons (+) et neutrons (neutres)",
            "Électrons (-) dans des couches (K, L, M, N...)",
            "Nombre de protons = numéro atomique Z",
            "Nombre d'électrons = nombre de protons (atome neutre)",
        ],
    },
    {
        "mots": ["sang", "cœur", "vaisseau", "circulation", "sanguine"],
        "titre": "Le système cardio-vasculaire",
        "reponse": "Le **cœur** est une pompe qui propulse le sang dans les **vaisseaux**. Le sang circule : cœur → artères → capillaires → veines → cœur.",
        "explication": "Le sang rouge riche en O₂ part du cœur gauche vers le corps, revient bleu pauvre en O₂ vers le cœur droit puis les poumons.",
        "etapes": [
            "Circulation pulmonaire : cœur droit → poumons → cœur gauche",
            "Circulation générale : cœur gauche → corps → cœur droit",
            "Artères : sang riche en O₂ (sauf artère pulmonaire)",
            "Veines : sang pauvre en O₂ (sauf veine pulmonaire)",
        ],
    },
    {
        "mots": ["nerveux", "neurone", "synapse", "nerf", "réflexe"],
        "titre": "Le système nerveux",
        "reponse": "Le **système nerveux** transmet des informations via les **neurones**. Un **réflexe** est une réponse rapide et involontaire.",
        "explication": "Un neurone transmit l'influx nerveux. À la synapse, un message chimique passe d'un neurone à l'autre.",
        "etapes": [
            "Neurone = cellule nerveuse (dendrites, axone, synapse)",
            "Système somatique : volontaire (marche, parole)",
            "Système végétatif : involontaire (respiration, digestion)",
            "Réflexe : circuit court stimulus → réponse",
        ],
    },
    {
        "mots": ["hérédité", "gène", "chromosome", "darwin", "évolution"],
        "titre": "Hérédité et génétique",
        "reponse": "L'**hérédité** transmet les caractères des parents aux enfants via les **gènes** portés par les **chromosomes**.",
        "explication": "Chaque gène existe sous plusieurs formes (allèles). Un enfant hérite d'un allèle de chaque parent.",
        "etapes": [
            "Chromosomes : 23 paires chez l'humain (46 chromosomes)",
            "Gène : segment d'ADN qui code un caractère",
            "Allèle : version différente d'un gène",
            "Génotype : combinaison d'allèles ; Phénomène : expression visible",
        ],
    },
    {
        "mots": ["sénégal", "dakar", "capitale", "histoire sénégal", "indépendance", "senghor"],
        "titre": "Le Sénégal : capitale et indépendance",
        "reponse": "Le Sénégal est un pays d'Afrique de l'Ouest. Sa capitale est **Dakar**. Il a obtenu son indépendance le **20 juin 1960**.",
        "explication": "Le Sénégal est membre de l'Union africaine, de la Francophonie et de l'UEMOA. Sa langue officielle est le français.",
        "etapes": [
            "Capitale : Dakar (située sur la côte atlantique)",
            "Indépendance : 20 juin 1960 (de la France)",
            "Premier président : Léopold Sédar Senghor",
            "Langues : français (officiel), wolof, peul, sérère...",
        ],
    },
    {
        "mots": ["afrique", "colonisation", "décolonisation", "berlin", "impérialisme"],
        "titre": "Colonisation et décolonisation",
        "reponse": "La **colonisation** est l'établissement d'un contrôle politique et économique d'un pays sur un autre. Les décolonisations africaines ont eu lieu principalement en **1960**.",
        "explication": "La conférence de Berlin (1885) a partagé l'Afrique entre les puissances européennes. Après la Seconde Guerre mondiale, les peuples africains ont réclamé leur indépendance.",
        "etapes": [
            "1885 : conférence de Berlin — partage de l'Afrique",
            "1946 : Union française — statut des colonies",
            "1958 : référendum — Républiques membres de la Communauté",
            "1960 : année des indépendances africaines",
        ],
    },
    {
        "mots": ["anglais", "grammaire", "present", "passed", "verbe", "present perfect"],
        "titre": "Grammaire anglaise de base",
        "reponse": "En anglais, le **present** décrit une habitude, le **past** une action terminée, le **present perfect** une action passée avec lien au présent.",
        "explication": "\"I have eaten\" (present perfect) = j'ai mangé (lien au présent). \"I ate\" (past simple) = j'ai mangé (action terminée).",
        "etapes": [
            "Present simple : I eat (habitude)",
            "Past simple : I ate (action terminée)",
            "Present perfect : I have eaten (passé + présent)",
            "Be, have, do sont les auxiliaires principaux",
        ],
    },
    {
        "mots": ["arabe", "alphabet", "salutation", "salam", "arabie"],
        "titre": "L'arabe : alphabet et salutations",
        "reponse": "L'**arabe** s'écrit de **droite à gauche**. La salutation courante est **salam** (سلام) qui signifie « paix ».",
        "explication": "L'arabe est une langue sémitique parlée dans le monde arabe. L'alphabet comprend 28 lettres.",
        "etapes": [
            "Écriture : de droite à gauche",
            "Salutation : As-salamu ʻalaykum = que la paix soit sur vous",
            "Réponse : Wa ʻalaykumus salam",
            "Alphabet : 28 lettres, le point change le sens",
        ],
    },
    {
        "mots": ["wolof", "alphabet", "salutation", "sutu", "jangle"],
        "titre": "Le wolof : salutations et bases",
        "reponse": "Le **wolof** est une langue parlée au Sénégal. La salutation courante est **sutu** (salut) et **waabé** (au revoir).",
        "explication": "Le wolof est une langue africaine dont l'alphabet utilise l'latin. C'est la langue la plus parlée au Sénégal.",
        "etapes": [
            "Salut : Sutub / Naungufi",
            "Comment ça va : Ki nga def? / Ki feebar?",
            "Au revoir : Waabé / Njuree",
            "Merci : Jeere jeere (jere jere)",
        ],
    },
    {
        "mots": ["liberté", "égalité", "fraternité", "citoyen", "citoyenneté"],
        "titre": "Liberté, égalité, fraternité",
        "reponse": "« **Liberté, égalité, fraternité** » est la devise de la République française. La **liberté** est le droit de faire ce que la loi autorise.",
        "explication": "Ces valeurs sont inscrites dans la Déclaration des droits de l'homme et du citoyen (1789).",
        "etapes": [
            "Liberté : droit de faire ce que la loi autorise",
            "Égalité : tous devant la loi, sans privilèges",
            "Fraternité : solidarité entre citoyens",
            "1789 : Déclaration des droits de l'homme et du citoyen",
        ],
    },
    {
        "mots": ["monnaie", "euro", "fcfa", "inflation", "prix"],
        "titre": "La monnaie et ses fonctions",
        "reponse": "La **monnaie** sert à **acheter**, à **stocker** de la valeur et à **mesurer** les prix. Le **CFA** est la monnaie de l'Afrique francophone.",
        "explication": "1 euro = 656 francs CFA (taux fixe). L'inflation est la hausse générale des prix.",
        "etapes": [
            "Acheter : moyen de paiement",
            "Stocker : épargne, conservation de la valeur",
            "Mesurer : étalon de valeur (prix)",
            "1 euro = 656 FCFA (taux fixe)",
        ],
    },
    {
        "mots": ["internet", "navigateur", "email", "site web", "url"],
        "titre": "Bases de l'informatique et d'Internet",
        "reponse": "**Internet** est un réseau mondial d'ordinateurs. Un **navigateur** (Chrome, Firefox) permet d'accéder aux sites web via une **URL**.",
        "explication": "Une URL comme https://ecolemax.onrender.com indique le protocole (https), le domaine et le chemin.",
        "etapes": [
            "Internet : réseau mondial d'ordinateurs",
            "Navigateur : logiciel pour consulter les sites web",
            "URL : adresse d'une page web (ex: https://site.com)",
            "Email : courrier électronique (ex: user@domaine.com)",
        ],
    }
]


# ------------------------------------------------------------------
# Recherche
# ------------------------------------------------------------------
def chercher(question):
    """Retourne une réponse locale, ou None si rien ne correspond."""
    q = normaliser(question)
    if not q:
        return None

    meilleur, score_max = None, 0
    for entree in BASE:
        score = sum(1 for m in entree["mots"] if normaliser(m) in q)
        if score > score_max:
            meilleur, score_max = entree, score

    if not meilleur:
        return None

    return {
        "reponse": meilleur["reponse"],
        "explication": meilleur["explication"],
        "etapes": meilleur["etapes"],
        "confiance": 0.85,
        "source": "Bibliothèque locale",
        "titre": meilleur["titre"],
    }


def suggestions():
    """Thèmes couverts localement (affichés en cas d'échec total)."""
    return [e["titre"] for e in BASE]


if __name__ == "__main__":
    for essai in ["explique moi la dérivée", "c'est quoi le théorème de Pythagore",
                  "loi d'ohm", "les figures de style", "comment réviser ?",
                  "blabla sans rapport"]:
        r = chercher(essai)
        print(f"{essai:40s} → {r['titre'] if r else 'aucune correspondance'}")
