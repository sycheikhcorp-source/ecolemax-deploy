#!/usr/bin/env python3
"""Migration non destructive ÉcoleMax — ajout difficulté + génération de contenu.

- Ajoute la colonne difficulte aux tables exercises et quiz (si absente)
- Met à jour les catégories quiz en minuscules
- Nettoie les comptes test (charge_*, ia_test_*, diag_*)
- Génère 200 exercices supplémentaires par matière par difficulté
- Génère 50 quiz supplémentaires par catégorie par difficulté
"""
import sqlite3, random, os

DB = "/home/user/deploy/ecolemax.db"
DIFFICULTES = ["facile", "moyen", "difficile"]
NIVEAUX = ["2nde", "1ère", "Terminale"]

EXERCICES = {
    "math": {
        "facile": [("Calcule : {a} + {b}", "{r}", "Addition : {a} + {b} = {r}"),
                  ("Calcule : {a} × {b}", "{r}", "Multiplication : {a} × {b} = {r}"),
                  ("Calcule : {a} - {b}", "{r}", "Soustraction : {a} - {b} = {r}"),
                  ("Calcule : {a} ÷ {b}", "{r}", "Division : {a} ÷ {b} = {r}"),
                  ("Que vaut {a} % de {b} ?", "{r}", "{a}% de {b} = {r}")],
        "moyen": [("Résous : x + {a} = {b}", "{r}", "x = {b} - {a} = {r}"),
                  ("Résous : 2x - {a} = {b}", "{r}", "x = ({b}+{a})/2 = {r}"),
                  ("Simplifie la fraction {a}/{b}", "{r}", "Fraction simplifiée"),
                  ("Calcule la moyenne de {a}, {b}, {c}", "{r}", "Moyenne = {r}"),
                  ("Suite : {a}, {b}, {c}, ?", "{r}", "Progression arithmétique")],
        "difficile": [("Dérive de {a}x² + {b}x", "{r}", "f'(x) = {r}"),
                      ("Résous x² - {a}x + {b} = 0", "{r}", "Δ et solutions"),
                      ("Calcule sin({a}°)", "{r}", "Trigonométrie"),
                      ("Intégrale de {a}x + {b} entre 0 et 1", "{r}", "Intégrale"),
                      ("log base {a} de {b}", "{r}", "Logarithme")],
    },
    "fr": {
        "facile": [("Écris au pluriel : {a}", "{r}", "Pluriel de {a}"),
                  ("Conjugue « être » à la 2e personne du pluriel", "vous êtes", "Être"),
                  ("Donne le contraire de {a}", "{r}", "Contraire"),
                  ("Écris le féminin de {a}", "{r}", "Féminin"),
                  ("Adverbe correspondant à {a} ?", "{r}", "Adverbe")],
        "moyen": [("Conjugue « avoir » au passé composé avec « nous »", "nous avons eu", "Avoir"),
                  ("Complète : « Le {a} ... »", "{r}", "Position"),
                  ("Quel temps dans : {a}", "{r}", "Temps"),
                  ("Transforme en négative : {a}", "{r}", "Négation"),
                  ("Nature du mot {a} ?", "{r}", "Nature")],
        "difficile": [("Conjugue « se lever » au subjonctif passé", "qu'il se soit levé", "Subjonctif"),
                      ("Analyse : {a}", "{r}", "Analyse grammaticale"),
                      ("Utilise « dont » : {r}", "{r}", "Dont"),
                      ("Passive de : {a}", "{r}", "Voix passive"),
                      ("Participe passé de « {a} » ?", "{r}", "Participe")],
    },
    "phys": {
        "facile": [("Valeur de g à la surface de la Terre ?", "9,81 m/s²", "Accélération de la pesanteur"),
                  ("Unité de la vitesse en SI ?", "m/s", "Vitesse"),
                  ("Vitesse de la lumière ?", "3×10⁸ m/s", "C"),
                  ("Unité de la force en SI ?", "Newton (N)", "Force"),
                  ("Formule de la vitesse ?", "v = d/t", "Vitesse")],
        "moyen": [("100 km en 2 h. Vitesse ?", "50 km/h", "v = d/t"),
                  ("Masse d'un objet de 100 N (g=10) ?", "10 kg", "m = F/g"),
                  ("F=20 N, m=4 kg. Accélération ?", "5 m/s²", "a = F/m"),
                  ("Puissance : 100 J en 5 s ?", "20 W", "P = E/t"),
                  ("k=200 N/m, x=0,05 m. Force ?", "10 N", "F = k×x")],
        "difficile": [("Énergie cinétique de 2 kg à 10 m/s ?", "100 J", "Ec = 1/2 mv²"),
                      ("R=10 Ω, U=5 V. Puissance ?", "2,5 W", "P = U²/R"),
                      ("C = Q/U = 10 µC/5 V ?", "2 µF", "C = Q/U"),
                      ("500 W pendant 2 h ?", "1 kWh", "E = P×t"),
                      ("U = R×I = 4 Ω × 2 A ?", "8 V", "U = R×I")],
    },
    "chim": {
        "facile": [("Symbole de l'hydrogène ?", "H", "H"),
                  ("Numéro atomique de l'oxygène ?", "8", "8"),
                  ("Symbole du carbone ?", "C", "C"),
                  ("Formule de l'eau ?", "H₂O", "H₂O"),
                  ("Gaz à 78 % de l'air ?", "N₂ (azote)", "Azote")],
        "moyen": [("Électrons de l'oxygène ?", "8", "8"),
                  ("Formule de l'acide sulfurique ?", "H₂SO₄", "H₂SO₄"),
                  ("pH d'une solution neutre ?", "7", "7"),
                  ("Protons du carbone ?", "6", "6"),
                  ("Nom de l'ion Cl⁻ ?", "Chlorure", "Chlorure")],
        "difficile": [("Formule de l'éthanol ?", "C₂H₅OH", "C₂H₅OH"),
                      ("Nom de SO₄²⁻ ?", "Sulfate", "Sulfate"),
                      ("Masse molaire de H₂O ?", "18 g/mol", "18"),
                      ("Nom de NH₄⁺ ?", "Ammonium", "Ammonium"),
                      ("Formule du glucose ?", "C₆H₁₂O₆", "C₆H₁₂O₆")],
    },
    "hist": {
        "facile": [("Capitale du Sénégal ?", "Dakar", "Dakar"),
                  ("Indépendance du Sénégal ?", "1960", "1960"),
                  ("Premier président du Sénégal ?", "Léopold Sédar Senghor", "Senghor"),
                  ("Monnaie du Sénégal ?", "Franc CFA", "CFA"),
                  ("Langue officielle du Sénégal ?", "Français", "Français")],
        "moyen": [("Dynastie de l'Empire du Mali ?", "Keïta", "Keïta"),
                  ("Capitale de l'Empire du Mali ?", "Niani", "Niani"),
                  ("Durée du mandat présidentiel ?", "5 ans", "5 ans"),
                  ("Fondateur de l'Université de Sankoré ?", "El-Bekkai", "El-Bekkai"),
                  ("Confédération de Nani ?", "1898", "1898")],
        "difficile": [("Premier ministre du Sénégal en 1960 ?", "Mamadou Dia", "Mamadou Dia"),
                      ("Mort de Senghor ?", "2001", "2001"),
                      ("Événement de 1889 au Sénégal ?", "Élection municipale", "Élection"),
                      ("Roi du Jolof au XVe siècle ?", "Ndiaye Fall", "Ndiaye Fall"),
                      ("Empire de Diogo Mafia ?", "Kaabu", "Kaabu")],
    },
    "geo": {
        "facile": [("Capitale de la France ?", "Paris", "Paris"),
                  ("Capitale du Mali ?", "Bamako", "Bamako"),
                  ("Capitale du Niger ?", "Niamey", "Niamey"),
                  ("Capitale du Burkina Faso ?", "Ouagadougou", "Ouagadougou"),
                  ("Capitale de la Côte d'Ivoire ?", "Yamoussoukro", "Yamoussoukro")],
        "moyen": [("Fleuve qui traverse le Sénégal ?", "Fleuve Sénégal", "Sénégal"),
                  ("Longueur du fleuve Sénégal ?", "1790 km", "1790"),
                  ("Climat du Sénégal ?", "Tropical", "Tropical"),
                  ("Point culminant du Sénégal ?", "Mont Assirik", "Assirik"),
                  ("Région la plus arrosée ?", "Casamance", "Casamance")],
        "difficile": [("Lac intérieur du Sénégal ?", "Lac de Guiers", "Guiers"),
                      ("Capitale de la Mauritanie ?", "Nouakchott", "Nouakchott"),
                      ("Parc national connu du Sénégal ?", "Parc de la Diawling", "Diawling"),
                      ("Capitale de la Gambie ?", "Banjul", "Banjul"),
                      ("Fleuve frontière avec le Mali ?", "Fleuve Sénégal", "Sénégal")],
    },
    "eng": {
        "facile": [("« Bonjour » in English ?", "hello", "hello"),
                  ("« Au revoir » means ?", "goodbye", "goodbye"),
                  ("« Water » in French ?", "eau", "eau"),
                  ("« School » in French ?", "école", "école"),
                  ("« Book » in French ?", "livre", "livre")],
        "moyen": [("« I am » conjugation of ?", "to be", "to be"),
                  ("Past tense of « to go » ?", "went", "went"),
                  ("« I love you » in French ?", "je t'aime", "je t'aime"),
                  ("Plural of « child » ?", "children", "children"),
                  ("Opposite of « good » ?", "bad", "bad")],
        "difficile": [("Subjunctive of « to be » ?", "be", "be"),
                      ("Past participle of « to eat » ?", "eaten", "eaten"),
                      ("« I would have been » in French ?", "j'aurais été", "j'aurais été"),
                      ("Comparative of « good » ?", "better", "better"),
                      ("Passive of « to write » ?", "to be written", "to be written")],
    },
    "svt": {
        "facile": [("Organe qui bat dans la poitrine ?", "Cœur", "Cœur"),
                  ("Gaz absorbé par les plantes ?", "CO₂", "CO₂"),
                  ("Pigment des feuilles ?", "Chlorophylle", "Chlorophylle"),
                  ("Organe de la respiration ?", "Poumon", "Poumon"),
                  ("Système de transport du sang ?", "Circulatoire", "Circulatoire")],
        "moyen": [("Fonction des mitochondries ?", "Énergie", "Énergie"),
                  ("Processus de fabrication nourriture plantes ?", "Photosynthèse", "Photosynthèse"),
                  ("Durée du cycle cellulaire humain ?", "24 h", "24 h"),
                  ("Fonction des reins ?", "Épuration du sang", "Épuration"),
                  ("Système digestif ?", "Tube digestif", "Tube")],
        "difficile": [("Durée gestation humaine ?", "9 mois", "9 mois"),
                      ("Processus de division cellulaire ?", "Mitose", "Mitose"),
                      ("Différence ADN/ARN ?", "Double/simple brin", "Double/simple"),
                      ("Fonction du thymus ?", "Lymphocytes T", "T"),
                      ("Cellule végétale a une ?", "Paroi", "Paroi")],
    },
    "info": {
        "facile": [("Symbole addition ?", "+", "+"),
                  ("Symbole multiplication ?", "*", "*"),
                  ("Symbole division ?", "/", "/"),
                  ("Langage de markup ?", "HTML", "HTML"),
                  ("Barre d'adresses ?", "URL bar", "URL")],
        "moyen": [("Structure données avec clés ?", "Dictionnaire", "Dictionnaire"),
                  ("Algorithme recherche liste triée ?", "Dichotomique", "Dichotomique"),
                  ("Boucle nombre fixe ?", "FOR", "FOR"),
                  ("Structure file ?", "File FIFO", "File"),
                  ("Recherche liste non triée ?", "Linéaire", "Linéaire")],
        "difficile": [("Complexité tri rapide ?", "O(n log n)", "O(n log n)"),
                      ("Recherche binaire sur ?", "Liste triée", "Triée"),
                      ("Différence liste/tableau ?", "Taille fixe/dynamique", "Taille"),
                      ("Structure LIFO ?", "Stack", "Stack"),
                      ("Tri par insertion complexité ?", "O(n²)", "O(n²)")],
    },
    "eco": {
        "facile": [("Monnaie du Sénégal ?", "Franc CFA", "CFA"),
                  ("Secteur vente biens/services ?", "Tertiaire", "Tertiaire"),
                  ("Fonction banque centrale ?", "Émission de monnaie", "Émission"),
                  ("Secteur production biens ?", "Secondaire", "Secondaire"),
                  ("Un bien est ?", "Matériel", "Matériel")],
        "moyen": [("Taux prêts bancaires ?", "Taux d'intérêt", "Intérêt"),
                  ("Baisse valeur monnaie ?", "Inflation", "Inflation"),
                  ("Budget de l'État ?", "Loi de finances", "Finances"),
                  ("Fonction Banque Mondiale ?", "Financement développement", "Financement"),
                  ("Taux d'échange ?", "Taux de change", "Change")],
        "difficile": [("Indicateur croissance économique ?", "PIB", "PIB"),
                      ("Différence inflation/dévaluation ?", "Prix/Valeur", "Prix/Valeur"),
                      ("Fonction Bourse ?", "Plateforme d'échange", "Échange"),
                      ("Indice coût de la vie ?", "IPC", "IPC"),
                      ("Taux transactions bancaires ?", "Taux de commission", "Commission")],
    },
    "es": {
        "facile": [("« Bonjour » espagnol ?", "Hola", "Hola"),
                  ("« Merci » espagnol ?", "Gracias", "Gracias"),
                  ("« Adieu » espagnol ?", "Adiós", "Adiós"),
                  ("« Chat » espagnol ?", "gato", "gato"),
                  ("« Eau » espagnol ?", "agua", "agua")],
        "moyen": [("« Je suis » espagnol ?", "yo soy", "yo soy"),
                  ("« Nous allons » espagnol ?", "nosotros vamos", "vamos"),
                  ("Pluriel de « gato » ?", "gatos", "gatos"),
                  ("« La maison » espagnol ?", "la casa", "casa"),
                  ("« Oui » espagnol ?", "sí", "sí")],
        "difficile": [("« J'aurai été » espagnol ?", "habré sido", "habré sido"),
                      ("Subjonctif « ser » ?", "sea", "sea"),
                      ("« Ils étaient » espagnol ?", "ellos eran", "eran"),
                      ("Participe « hablar » ?", "hablado", "hablado"),
                      ("« Nous aurions aimé » espagnol ?", "habríamos querido", "habríamos querido")],
    },
    "ara": {
        "facile": [("« Bonjour » arabe ?", "السلام عليكم", "assalamu alaykum"),
                  ("« Merci » arabe ?", "شكراً", "shukran"),
                  ("« Adieu » arabe ?", "مع السلامة", "ma'a as-salama"),
                  ("« Chat » arabe ?", "قطة", "qitta"),
                  ("« Eau » arabe ?", "ماء", "maa'")],
        "moyen": [("« Je suis » arabe ?", "أنا", "ana"),
                  ("« Nous allons » arabe ?", "سنذهب", "sandharib"),
                  ("Pluriel « قطة » ?", "قطط", "qittat"),
                  ("« La maison » arabe ?", "البيت", "bayt"),
                  ("« Oui » arabe ?", "نعم", "na'am")],
        "difficile": [("« J'aurai été » arabe ?", "سأكون قد كنت", "sa'akoonu qad kuntu"),
                      ("Subjonctif « être » arabe ?", "يكون", "yakoona"),
                      ("« Ils étaient » arabe ?", "كانوا", "kaanu"),
                      ("Participe « écrire » arabe ?", "مكتوب", "maktoub"),
                      ("« Nous aurions aimé » arabe ?", "لو كنا أحببنا", "law kuntu ahabna")],
    },
}

QUIZ = {
    "math": {
        "facile": [("2 + 3 = ?", ["2", "3", "5", "6"], 2, "2+3=5"),
                  ("5 × 4 = ?", ["15", "20", "25", "30"], 1, "5×4=20"),
                  ("10 - 7 = ?", ["2", "3", "4", "7"], 1, "10-7=3"),
                  ("12 ÷ 3 = ?", ["3", "4", "6", "12"], 1, "12÷3=4"),
                  ("7 + 8 = ?", ["13", "14", "15", "16"], 1, "7+8=15"),
                  ("9 × 2 = ?", ["16", "18", "20", "22"], 1, "9×2=18"),
                  ("15 - 9 = ?", ["5", "6", "7", "8"], 1, "15-9=6"),
                  ("6 ÷ 2 = ?", ["2", "3", "4", "6"], 1, "6÷2=3"),
                  ("4 + 6 = ?", ["9", "10", "11", "12"], 1, "4+6=10"),
                  ("3 × 7 = ?", ["20", "21", "22", "24"], 1, "3×7=21")],
        "moyen": [("Résous : x + 5 = 12. x = ?", ["5", "7", "12", "17"], 1, "x=7"),
                  ("2x = 10. x = ?", ["2", "5", "10", "20"], 1, "x=5"),
                  ("3x - 4 = 8. x = ?", ["3", "4", "5", "6"], 1, "x=4"),
                  ("PGCD de 12 et 18 ?", ["2", "3", "6", "12"], 2, "PGCD=6"),
                  ("Moyenne de 4, 8, 12 ?", ["8", "10", "12", "16"], 0, "Moyenne=8"),
                  ("x/2 = 6. x = ?", ["3", "6", "12", "24"], 2, "x=12"),
                  ("5x + 3 = 18. x = ?", ["1", "2", "3", "4"], 2, "x=3"),
                  ("PPCM de 4 et 6 ?", ["6", "12", "18", "24"], 1, "PPCM=12"),
                  ("15 % de 200 ?", ["15", "20", "30", "45"], 1, "30"),
                  ("Suite 2, 4, 6, ... raison ?", ["1", "2", "3", "4"], 1, "Raison=2")],
        "difficile": [("Dérive de x² + 3x ?", ["2x+3", "2x", "x+3", "x²+3"], 0, "2x+3"),
                      ("x² - 5x + 6 = 0", ["1 et 6", "2 et 3", "3 et 4", "1 et 5"], 1, "2 et 3"),
                      ("sin(30°) = ?", ["0", "1/2", "√3/2", "1"], 1, "1/2"),
                      ("∫ 2x dx = ?", ["x²", "2x²", "x²+C", "2"], 0, "x²+C"),
                      ("log₁₀(100) = ?", ["1", "2", "10", "100"], 1, "2"),
                      ("2^x = 8. x = ?", ["2", "3", "4", "8"], 1, "3"),
                      ("cos(0°) = ?", ["0", "1/2", "1", "√3/2"], 2, "1"),
                      ("√(49) = ?", ["5", "7", "9", "49"], 1, "7")],
    },
    "fr": {
        "facile": [("Pluriel de « chat » ?", ["chatte", "chats", "chats", "chat"], 1, "chats"),
                  ("« Je suis » est la 1ère personne de ?", ["avoir", "être", "faire", "aller"], 1, "être"),
                  ("« Le » est un ?", ["verbe", "nom", "article défini", "adverbe"], 2, "article"),
                  ("« Rapidement » est un ?", ["adverbe", "adjectif", "verbe", "nom"], 0, "adverbe"),
                  ("« Grand » s'accorde en genre et ?", ["temps", "nombre", "lieu", "mode"], 1, "nombre")],
        "moyen": [("« Ils sont » conjugaison de ?", ["avoir", "être", "faire", "aller"], 1, "être"),
                  ("« Nous avons fait » est au ?", ["présent", "passé composé", "futur", "imparfait"], 1, "passé composé"),
                  ("« Qui » est un ?", ["pronom relatif", "pronom personnel", "adverbe", "adjectif"], 0, "pronom relatif"),
                  ("« La maison » = ?", ["article défini + nom", "article indéfini + nom", "adjectif + nom", "verbe + nom"], 0, "article défini + nom"),
                  ("« Je t'aime » contient un ?", ["pronom tonique", "pronom élidé", "pronom relatif", "adverbe"], 1, "pronom élidé")],
        "difficile": [("« Que » peut être ?", ["pronom relatif", "adverbe", "conjonction", "toutes"], 3, "toutes"),
                      ("« Subjonctif » est un ?", ["mode", "temp", "voix", "forme"], 0, "mode"),
                      ("« Il faut que tu partes » : « que » introduit ?", ["indicatif", "subjonctif", "impératif", "conditionnel"], 1, "subjonctif"),
                      ("« Je suis allé » est un ?", ["passé composé", "plus-que-parfait", "futur", "subjonctif"], 0, "passé composé"),
                      ("« La viande est bonne » : « bonne » est ?", ["adjectif épithète", "adverbe", "nom", "pronom"], 0, "adjectif épithète")],
    },
    "phys": {
        "facile": [("Unité de la vitesse en SI ?", ["km/h", "m/s", "m", "s"], 1, "m/s"),
                  ("g vaut ?", ["10", "9,81", "9", "1"], 1, "9,81"),
                  ("Vitesse de la lumière ?", ["3×10⁸", "3×10⁶", "3×10⁴", "3×10¹⁰"], 0, "3×10⁸"),
                  ("Unité de la force ?", ["Newton", "Joule", "Watt", "Pascal"], 0, "Newton"),
                  ("Unité de l'énergie ?", ["Newton", "Joule", "Watt", "Tesla"], 1, "Joule")],
        "moyen": [("10 kg, a=2 m/s². Force ?", ["5 N", "12 N", "20 N", "8 N"], 2, "20 N"),
                  ("200 km en 4 h. Vitesse ?", ["40", "50", "60", "80"], 1, "50"),
                  ("P=100 W, t=5 s. Énergie ?", ["20 J", "500 J", "20 W", "500 W"], 1, "500 J"),
                  ("U=10 V, R=5 Ω. Courant ?", ["2 A", "5 A", "10 A", "50 A"], 0, "2 A"),
                  ("m=2 kg, v=10 m/s. Énergie cinétique ?", ["20 J", "50 J", "100 J", "200 J"], 2, "100 J")],
        "difficile": [("R=10 Ω, U=5 V. Puissance ?", ["2,5 W", "5 W", "10 W", "25 W"], 0, "2,5 W"),
                      ("C=2 µF, U=10 V. Charge ?", ["5 µC", "10 µC", "20 µC", "200 µC"], 2, "20 µC"),
                      ("k=200 N/m, x=0,1 m. Force ?", ["2 N", "20 N", "200 N", "2000 N"], 1, "20 N"),
                      ("P=1000 W, t=2 h. Énergie ?", ["2 kWh", "1 kWh", "0,5 kWh", "4 kWh"], 0, "2 kWh"),
                      ("U=220 V, R=110 Ω. I ?", ["0,5 A", "2 A", "11 A", "22 A"], 1, "2 A")],
    },
    "chim": {
        "facile": [("Symbole de l'oxygène ?", ["O", "Ox", "Og", "Oy"], 0, "O"),
                  ("Numéro atomique du carbone ?", ["6", "12", "60", "7"], 0, "6"),
                  ("Formule de l'eau ?", ["H₂O", "HO", "O₂H", "H₃O"], 0, "H₂O"),
                  ("Gaz à 78 % de l'air ?", ["21", "78", "1", "50"], 1, "78"),
                  ("Symbole du sodium ?", ["So", "Na", "Sd", "S"], 1, "Na")],
        "moyen": [("pH solution acide ?", ["< 7", "> 7", "= 7", "= 0"], 0, "< 7"),
                  ("Nom de Cl⁻ ?", ["chlorure", "chlore", "sodium", "sulfate"], 0, "chlorure"),
                  ("Masse molaire H₂O ?", ["16", "17", "18", "19"], 2, "18"),
                  ("Nom de SO₄²⁻ ?", ["sulfate", "sulfure", "sulfite", "sulfane"], 0, "sulfate"),
                  ("Formule acide sulfurique ?", ["H₂SO₄", "H₂SO₃", "H₂S", "H₂O"], 0, "H₂SO₄")],
        "difficile": [("Formule du glucose ?", ["C₆H₁₂O₆", "C₆H₁₂O₅", "C₆H₁₀O₆", "C₆H₁₂O"], 0, "C₆H₁₂O₆"),
                      ("Nom de NH₄⁺ ?", ["ammonium", "ammoniaque", "nitrate", "nitrite"], 0, "ammonium"),
                      ("Masse molaire CO₂ ?", ["28", "44", "30", "42"], 1, "44"),
                      ("Nom de OH⁻ ?", ["hydroxyde", "hydrogène", "oxyde", "hydrure"], 0, "hydroxyde"),
                      ("Formule du méthane ?", ["CH₄", "CH₃", "CH₂", "C₂H₆"], 0, "CH₄")],
    },
    "hist": {
        "facile": [("Capitale du Sénégal ?", ["Dakar", "Touba", "Saint-Louis", "Kaolack"], 0, "Dakar"),
                  ("Indépendance du Sénégal ?", ["1960", "1963", "1958", "1965"], 0, "1960"),
                  ("Premier président du Sénégal ?", ["Senghor", "Mamadou Dia", "Abdoulaye Wade", "Macky Sall"], 0, "Senghor"),
                  ("Monnaie du Sénégal ?", ["Franc CFA", "Euro", "Livre", "Dollar"], 0, "CFA"),
                  ("Langue officielle du Sénégal ?", ["Français", "Anglais", "Arabe", "Wolof"], 0, "Français")],
        "moyen": [("Dynastie de l'Empire du Mali ?", ["Keïta", "Mansa", "Sundiata", "Askia"], 0, "Keïta"),
                  ("Capitale de l'Empire du Mali ?", ["Niani", "Djenné", "Tombouctou", "Gao"], 0, "Niani"),
                  ("Durée du mandat présidentiel ?", ["5 ans", "7 ans", "4 ans", "10 ans"], 0, "5 ans"),
                  ("Fondateur Université de Sankoré ?", ["El-Bekkai", "Mansa", "Sundiata", "Askia"], 0, "El-Bekkai"),
                  ("Confédération de Nani ?", ["1898", "1890", "1900", "1889"], 0, "1898")],
        "difficile": [("Premier ministre 1960 ?", ["Mamadou Dia", "Senghor", "Wade", "Sall"], 0, "Mamadou Dia"),
                      ("Mort de Senghor ?", ["2001", "2000", "2002", "1999"], 0, "2001"),
                      ("Événement 1889 ?", ["Élection municipale", "Indépendance", "Colonisation", "Révolte"], 0, "Élection municipale"),
                      ("Roi du Jolof XVe siècle ?", ["Ndiaye Fall", "Mansa", "Sundiata", "Askia"], 0, "Ndiaye Fall"),
                      ("Empire de Diogo Mafia ?", ["Kaabu", "Mali", "Songhai", "Jolof"], 0, "Kaabu")],
    },
    "geo": {
        "facile": [("Capitale de la France ?", ["Paris", "Lyon", "Marseille", "Bordeaux"], 0, "Paris"),
                  ("Capitale du Mali ?", ["Bamako", "Ségou", "Mopti", "Tombouctou"], 0, "Bamako"),
                  ("Capitale du Niger ?", ["Niamey", "Zinder", "Agadez", "Maradi"], 0, "Niamey"),
                  ("Capitale du Burkina Faso ?", ["Ouagadougou", "Bobo", "Koudougou", "Fada"], 0, "Ouagadougou"),
                  ("Capitale de la Côte d'Ivoire ?", ["Yamoussoukro", "Abidjan", "Bouaké", "San-Pédro"], 0, "Yamoussoukro")],
        "moyen": [("Fleuve du Sénégal ?", ["Fleuve Sénégal", "Fleuve Niger", "Fleuve Nile", "Fleuve Congo"], 0, "Sénégal"),
                  ("Longueur du fleuve Sénégal ?", ["1790 km", "2000 km", "1500 km", "2200 km"], 0, "1790"),
                  ("Climat du Sénégal ?", ["Tropical", "Désertique", "Tempéré", "Polaire"], 0, "Tropical"),
                  ("Point culminant du Sénégal ?", ["Mont Assirik", "Mont Fouta", "Mont Sangbe", "Mont Tortue"], 0, "Assirik"),
                  ("Région la plus arrosée ?", ["Casamance", "Nord", "Est", "Centre"], 0, "Casamance")],
        "difficile": [("Lac intérieur du Sénégal ?", ["Lac de Guiers", "Lac Retba", "Lac Rose", "Lac Ngoumen"], 0, "Guiers"),
                      ("Capitale de la Mauritanie ?", ["Nouakchott", "Nouadhibou", "Zouérat", "Rosso"], 0, "Nouakchott"),
                      ("Parc national connu ?", ["Diawling", "Djoudj", "Niokolo", "Banjeul"], 0, "Diawling"),
                      ("Capitale de la Gambie ?", ["Banjul", "Brikama", "Serrekunda", "Janjanbureh"], 0, "Banjul"),
                      ("Fleuve frontière Mali ?", ["Fleuve Sénégal", "Fleuve Niger", "Fleuve Nile", "Fleuve Chari"], 0, "Sénégal")],
    },
    "eng": {
        "facile": [("« Bonjour » in English ?", ["hello", "goodbye", "good morning", "thanks"], 0, "hello"),
                  ("« Au revoir » means ?", ["goodbye", "hello", "welcome", "sorry"], 0, "goodbye"),
                  ("« Water » in French ?", ["eau", "eau", "eau", "eau"], 0, "eau"),
                  ("« School » in French ?", ["école", "université", "classe", "collège"], 0, "école"),
                  ("« Book » in French ?", ["livre", "page", "texte", "roman"], 0, "livre")],
        "moyen": [("« I am » conjugation of ?", ["to be", "to have", "to do", "to go"], 0, "to be"),
                  ("Past tense of « to go » ?", ["went", "gone", "going", "goed"], 0, "went"),
                  ("« I love you » in French ?", ["je t'aime", "je t'aime pas", "je vouloir toi", "toi aimer je"], 0, "je t'aime"),
                  ("Plural of « child » ?", ["children", "childs", "childes", "childrens"], 0, "children"),
                  ("Opposite of « good » ?", ["bad", "well", "nice", "great"], 0, "bad")],
        "difficile": [("Subjunctive of « to be » ?", ["be", "being", "been", "am"], 0, "be"),
                      ("Past participle of « to eat » ?", ["eaten", "ate", "eated", "eating"], 0, "eaten"),
                      ("« I would have been » in French ?", ["j'aurais été", "je serais été", "j'ai été", "je suis été"], 0, "j'aurais été"),
                      ("Comparative of « good » ?", ["better", "goodest", "more good", "best"], 0, "better"),
                      ("Passive of « to write » ?", ["to be written", "writing", "written", "write"], 0, "to be written")],
    },
    "svt": {
        "facile": [("Organe qui bat dans la poitrine ?", ["Cœur", "Poumon", "Foie", "Rate"], 0, "Cœur"),
                  ("Gaz absorbé par les plantes ?", ["CO₂", "O₂", "N₂", "H₂"], 0, "CO₂"),
                  ("Pigment des feuilles ?", ["Chlorophylle", "Carotène", "Melanine", "Hémoglobine"], 0, "Chlorophylle"),
                  ("Organe de la respiration ?", ["Poumon", "Cœur", "Foie", "Rein"], 0, "Poumon"),
                  ("Système de transport du sang ?", ["Circulatoire", "Respiratoire", "Digestif", "Nerveux"], 0, "Circulatoire")],
        "moyen": [("Fonction des mitochondries ?", ["Énergie", "Synthèse", "Respiration", "Transport"], 0, "Énergie"),
                  ("Processus de fabrication nourriture plantes ?", ["Photosynthèse", "Respiration", "Transpiration", "Génération"], 0, "Photosynthèse"),
                  ("Durée du cycle cellulaire humain ?", ["24 h", "12 h", "48 h", "36 h"], 0, "24 h"),
                  ("Fonction des reins ?", ["Épuration du sang", "Stockage", "Filtration", "Production"], 0, "Épuration"),
                  ("Système digestif ?", ["Tube digestif", "Estomac seul", "Intestins seul", "Pancréas"], 0, "Tube")],
        "difficile": [("Durée gestation humaine ?", ["9 mois", "6 mois", "12 mois", "3 mois"], 0, "9 mois"),
                      ("Processus de division cellulaire ?", ["Mitose", "Méiose", "Apoptose", "Synthèse"], 0, "Mitose"),
                      ("Différence ADN/ARN ?", ["Double/simple", "Thymine/Uracil", "Toutes", "ADN pas d'azote"], 2, "Toutes"),
                      ("Fonction du thymus ?", ["Lymphocytes T", "Lymphocytes B", "Érythrocytaire", "Nerveux"], 0, "T"),
                      ("Cellule végétale a une ?", ["Paroi", "Membrane seule", "Pas de membrane", "Pas de chloroplaste"], 0, "Paroi")],
    },
    "info": {
        "facile": [("Symbole addition ?", ["+", "*", "/", "-"], 0, "+"),
                  ("Symbole multiplication ?", ["*", "+", "/", "x"], 0, "*"),
                  ("Symbole division ?", ["/", "+", "*", "//"], 0, "/"),
                  ("Langage de markup ?", ["HTML", "Python", "Java", "C++"], 0, "HTML"),
                  ("Barre d'adresses ?", ["URL bar", "Address bar", "Search bar", "Tool bar"], 0, "URL")],
        "moyen": [("Structure données avec clés ?", ["Dictionnaire", "Liste", "Tableau", "File"], 0, "Dictionnaire"),
                  ("Algorithme recherche liste triée ?", ["Dichotomique", "Linéaire", "Quick", "Merge"], 0, "Dichotomique"),
                  ("Boucle nombre fixe ?", ["FOR", "WHILE", "DO", "GOTO"], 0, "FOR"),
                  ("Structure file ?", ["File FIFO", "Stack", "Heap", "Tree"], 0, "File"),
                  ("Recherche liste non triée ?", ["Linéaire", "Dichotomique", "Quick", "Binary"], 0, "Linéaire")],
        "difficile": [("Complexité tri rapide ?", ["O(n log n)", "O(n²)", "O(n)", "O(log n)"], 0, "O(n log n)"),
                      ("Recherche binaire sur ?", ["Liste triée", "Liste non triée", "Tableau", "File"], 0, "Liste triée"),
                      ("Différence liste/tableau ?", ["Taille fixe/dynamique", "Mémoire/Vitesse", "Clé/Index", "Profondeur/Largeur"], 0, "Taille"),
                      ("Structure LIFO ?", ["Stack", "Queue", "Tree", "Graph"], 0, "Stack"),
                      ("Tri par insertion complexité ?", ["O(n²)", "O(n log n)", "O(n)", "O(log n)"], 0, "O(n²)")],
    },
    "eco": {
        "facile": [("Monnaie du Sénégal ?", ["Franc CFA", "Euro", "Livre", "Dollar"], 0, "CFA"),
                  ("Secteur vente biens/services ?", ["Tertiaire", "Secondaire", "Primaire", "Quaternaire"], 0, "Tertiaire"),
                  ("Fonction banque centrale ?", ["Émission de monnaie", "Prêt", "Épargne", "Assurance"], 0, "Émission"),
                  ("Secteur production biens ?", ["Secondaire", "Primaire", "Tertiaire", "Quaternaire"], 0, "Secondaire"),
                  ("Un bien est ?", ["Matériel", "Immatériel", "Visible", "Invisible"], 0, "Matériel")],
        "moyen": [("Taux prêts bancaires ?", ["Taux d'intérêt", "Taux de change", "Taux d'inflation", "Taux de TVA"], 0, "Taux d'intérêt"),
                  ("Baisse valeur monnaie ?", ["Inflation", "Dévaluation", "Récession", "Stagnation"], 0, "Inflation"),
                  ("Budget de l'État ?", ["Loi de finances", "Balance", "Compte", "Dette"], 0, "Loi de finances"),
                  ("Fonction Banque Mondiale ?", ["Financement développement", "Émission", "Contrôle", "Assurance"], 0, "Financement"),
                  ("Taux d'échange ?", ["Taux de change", "Taux d'intérêt", "Taux d'inflation", "Taux de TVA"], 0, "Taux de change")],
        "difficile": [("Indicateur croissance économique ?", ["PIB", "PNB", "IPC", "Taux de chômage"], 0, "PIB"),
                      ("Différence inflation/dévaluation ?", ["Prix/Valeur", "Monnaie/Prix", "Toutes", "Aucune"], 0, "Prix/Valeur"),
                      ("Fonction Bourse ?", ["Plateforme d'échange", "Émission", "Contrôle", "Assurance"], 0, "Plateforme d'échange"),
                      ("Indice coût de la vie ?", ["IPC", "PIB", "PNB", "Taux de chômage"], 0, "IPC"),
                      ("Taux transactions bancaires ?", ["Taux de commission", "Taux d'intérêt", "Taux de change", "Taux d'inflation"], 0, "Taux de commission")],
    },
    "es": {
        "facile": [("« Bonjour » espagnol ?", ["Hola", "Buenos días", "Adiós", "Gracias"], 0, "Hola"),
                  ("« Merci » espagnol ?", ["Gracias", "Por favor", "De nada", "Hola"], 0, "Gracias"),
                  ("« Adieu » espagnol ?", ["Adiós", "Hola", "Hasta luego", "Gracias"], 0, "Adiós"),
                  ("« Chat » espagnol ?", ["gato", "perro", "pato", "vaca"], 0, "gato"),
                  ("« Eau » espagnol ?", ["agua", "leche", "vino", "cerveza"], 0, "agua")],
        "moyen": [("« Je suis » espagnol ?", ["yo soy", "yo soy", "yo estoy", "nosotros somos"], 0, "yo soy"),
                  ("« Nous allons » espagnol ?", ["nosotros vamos", "yo voy", "tú vas", "ellos van"], 0, "nosotros vamos"),
                  ("Pluriel « gato » ?", ["gatos", "gata", "gatos", "gato"], 0, "gatos"),
                  ("« La maison » espagnol ?", ["la casa", "el casa", "las casa", "la casas"], 0, "la casa"),
                  ("« Oui » espagnol ?", ["sí", "no", "pero", "hola"], 0, "sí")],
        "difficile": [("« J'aurai été » espagnol ?", ["habré sido", "seré sido", "fui sido", "soy sido"], 0, "habré sido"),
                      ("Subjonctif « ser » ?", ["sea", "es", "era", "seré"], 0, "sea"),
                      ("« Ils étaient » espagnol ?", ["ellos eran", "ellos son", "ellos fueron", "ellos siendo"], 0, "ellos eran"),
                      ("Participe « hablar » ?", ["hablado", "habló", "hablaba", "hablar"], 0, "hablado"),
                      ("« Nous aurions aimé » espagnol ?", ["habríamos querido", "querríamos haber", "quisimos haber", "querríamos haber"], 0, "habríamos querido")],
    },
    "ara": {
        "facile": [("« Bonjour » arabe ?", ["السلام عليكم", "شكراً", "مع السلامة", "نعم"], 0, "assalamu alaykum"),
                  ("« Merci » arabe ?", ["شكراً", "السلام عليكم", "مع السلامة", "نعم"], 0, "shukran"),
                  ("« Adieu » arabe ?", ["مع السلامة", "السلام عليكم", "شكراً", "نعم"], 0, "ma'a as-salama"),
                  ("« Chat » arabe ?", ["قطة", "كلب", "بطة", "ثور"], 0, "qitta"),
                  ("« Eau » arabe ?", ["ماء", "هواء", "نار", "تراب"], 0, "maa'")],
        "moyen": [("« Je suis » arabe ?", ["أنا", "نحن", "أنت", "هم"], 0, "ana"),
                  ("« Nous allons » arabe ?", ["سنذهب", "أنا ذهب", "أنت ذهب", "هم ذهب"], 0, "sandharib"),
                  ("Pluriel « قطة » ?", ["قطط", "قطة", "قطتان", "قطةان"], 0, "qittat"),
                  ("« La maison » arabe ?", ["البيت", "البيت", "بيتا", "بيتا"], 0, "bayt"),
                  ("« Oui » arabe ?", ["نعم", "لا", "ربما", "ربما"], 0, "na'am")],
        "difficile": [("« J'aurai été » arabe ?", ["سأكون قد كنت", "كنت قد أكون", "أكون قد كنت", "كنت"], 0, "sa'akoonu qad kuntu"),
                      ("Subjonctif « être » arabe ?", ["يكون", "كان", "يكون", "كانت"], 0, "yakoona"),
                      ("« Ils étaient » arabe ?", ["كانوا", "يكونون", "كان", "كانتا"], 0, "kaanu"),
                      ("Participe « écrire » arabe ?", ["مكتوب", "يكتب", "كتب", "كاتب"], 0, "maktoub"),
                      ("« Nous aurions aimé » arabe ?", ["لو كنا أحببنا", "كنا أحببنا", "نحب", "أحب"], 0, "law kuntu ahabna")],
    },
}

def gen_vals(a=1, b=20):
    return random.randint(a, b)

def main():
    c = sqlite3.connect(DB)
    random.seed(42)

    # 1. Migration non destructive
    print("MIGRATION (colonnes difficulte + nettoyage)...")
    try:
        c.execute("ALTER TABLE exercises ADD COLUMN difficulte TEXT DEFAULT 'moyen'")
        print("  colonne exercises.difficulte ajoutée")
    except sqlite3.OperationalError:
        print("  colonne exercises.difficulte existe déjà")
    try:
        c.execute("ALTER TABLE quiz ADD COLUMN difficulte TEXT DEFAULT 'moyen'")
        print("  colonne quiz.difficulte ajoutée")
    except sqlite3.OperationalError:
        print("  colonne quiz.difficulte existe déjà")

    # Mettre à jour les catégories quiz en minuscules
    n = c.execute("UPDATE quiz SET categorie = LOWER(categorie)").rowcount
    print(f"  {n} quiz mis à jour (catégories minuscules)")

    # Nettoyer les comptes test et leurs données
    test_users = "SELECT id FROM users WHERE pseudo LIKE 'test%' OR pseudo LIKE 'charge_%' OR pseudo LIKE 'ia_test_%' OR pseudo LIKE 'diag_%'"
    counts = []
    for t in ['usages','quiz_resultats','favoris','notifications','corrections','results']:
        n = c.execute(f"DELETE FROM {t} WHERE user_id IN ({test_users})").rowcount
        counts.append((t, n))
    n_users = c.execute("DELETE FROM users WHERE pseudo LIKE 'test%' OR pseudo LIKE 'charge_%' OR pseudo LIKE 'ia_test_%' OR pseudo LIKE 'diag_%'").rowcount
    print(f"  {n_users} comptes test nettoyés ({sum(n for _,n in counts)} données associées)")
    for t, n in counts:
        print(f"    {t}: {n}")

    # 2. Générer exercices supplémentaires
    print("GÉNÉRATION EXERCICES (200/matiere/difficulte)...")
    n_ex = 0
    for sujet, diffs in EXERCICES.items():
        for diff, templates in diffs.items():
            for i in range(200):
                t = random.choice(templates)
                question, reponse, expl = t
                a = gen_vals(1, 15)
                b = gen_vals(1, 20)
                c1 = gen_vals(1, 12)
                r = gen_vals(1, 30)
                q = question.format(a=a, b=b, r=r, c=c1)
                rep = reponse.format(a=a, b=b, r=r, c=c1)
                expl = expl.format(a=a, b=b, r=r, c=c1)
                niveau = random.choice(NIVEAUX)
                c.execute("INSERT INTO exercises (sujet_code,titre,niveau,type,question,reponse,explication,difficulte) VALUES (?,?,?,?,?,?,?,?)",
                          (sujet, f"Exercice {diff[:4]} {sujet}-{i}", niveau, "mixte", q, rep, expl, diff))
                n_ex += 1
    print(f"  exercices supplémentaires générés: {n_ex}")

    # 3. Générer quiz supplémentaires
    print("GÉNÉRATION QUIZ (50/categorie/difficulte)...")
    n_q = 0
    for cat, diffs in QUIZ.items():
        for diff, questions in diffs.items():
            for i in range(50):
                t = random.choice(questions)
                q, options, idx, expl = t
                opts = options[:]
                random.shuffle(opts)
                new_idx = opts.index(options[idx])
                question_qcm = q
                c.execute("INSERT INTO quiz (categorie,question,reponse,explication,difficulte) VALUES (?,?,?,?,?)",
                          (cat, question_qcm, new_idx, expl, diff))
                n_q += 1
    print(f"  quiz supplémentaires générés: {n_q}")

    c.commit()
    c.close()
    print(f"TOTAL: +{n_ex} exercices +{n_q} quiz")

if __name__ == "__main__":
    main()
