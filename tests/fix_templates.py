#!/usr/bin/env python3
"""Corrige les templates ES/ARA difficile dans generer_contenu.py."""
with open('/home/user/deploy/tests/generer_contenu.py') as f:
    content = f.read()

# 1. EXERCICES ES difficile (4 → 3 éléments)
old_es_ex = '''        "difficile": [("« J'aurai été » espagnol ?", ["habré sido", "seré sido", "fui sido", "soy sido"], 0, "habré sido"),
                      ("Subjonctif « ser » ?", ["sea", "es", "era", "seré"], 0, "sea"),
                      ("« Ils étaient » espagnol ?", ["ellos eran", "ellos son", "ellos fueron", "ellos sido"], 0, "ellos eran"),
                      ("Participe « hablar » ?", ["hablado", "habló", "hablaba", "hablar"], 0, "hablado"),
                      ("« Nous aurions aimé » espagnol ?", ["habríamos querido", "querríamos haber", "quisimos haber", "querríamos haber"], 0, "habríamos querido")],
    },
    "ara": {'''
new_es_ex = '''        "difficile": [("« J'aurai été » espagnol ?", "habré sido", "habré sido"),
                      ("Subjonctif « ser » ?", "sea", "sea"),
                      ("« Ils étaient » espagnol ?", "ellos eran", "eran"),
                      ("Participe « hablar » ?", "hablado", "hablado"),
                      ("« Nous aurions aimé » espagnol ?", "habríamos querido", "habríamos querido")],
    },
    "ara": {'''
if old_es_ex in content:
    content = content.replace(old_es_ex, new_es_ex, 1)
    print("✅ EXERCICES ES difficile corrigé")
else:
    print("⚠️ EXERCICES ES difficile non trouvé")

# 2. QUIZ ES difficile (3 → 4 éléments)
old_es_q = '''        "difficile": [("« J'aurai été » espagnol ?", "habré sido", "habré sido"),
                      ("Subjonctif « ser » ?", "sea", "sea"),
                      ("« Ils étaient » espagnol ?", "ellos eran", "eran"),
                      ("Participe « hablar » ?", "hablado", "hablado"),
                      ("« Nous aurions aimé » espagnol ?", "habríamos querido", "habríamos querido")],'''
new_es_q = '''        "difficile": [("« J'aurai été » espagnol ?", ["habré sido", "seré sido", "fui sido", "soy sido"], 0, "habré sido"),
                      ("Subjonctif « ser » ?", ["sea", "es", "era", "seré"], 0, "sea"),
                      ("« Ils étaient » espagnol ?", ["ellos eran", "ellos son", "ellos fueron", "ellos sido"], 0, "ellos eran"),
                      ("Participe « hablar » ?", ["hablado", "habló", "hablaba", "hablar"], 0, "hablado"),
                      ("« Nous aurions aimé » espagnol ?", ["habríamos querido", "querríamos haber", "quisimos haber", "querríamos haber"], 0, "habríamos querido")],'''
if old_es_q in content:
    content = content.replace(old_es_q, new_es_q, 1)
    print("✅ QUIZ ES difficile corrigé")
else:
    print("⚠️ QUIZ ES difficile non trouvé")

# 3. EXERCICES ARA difficile (4 → 3 éléments)
old_ara_ex = '''        "difficile": [("« J'aurai été » arabe ?", ["سأكون قد كنت", "كنت قد أكون", "أكون قد كنت", "كنت"], 0, "sa'akoonu qad kuntu"),
                      ("Subjonctif « être » arabe ?", ["يكون", "كان", "يكون", "كانت"], 0, "yakoona"),
                      ("« Ils étaient » arabe ?", ["كانوا", "يكونون", "كان", "كانتا"], 0, "kaanu"),
                      ("Participe « écrire » arabe ?", ["مكتوب", "يكتب", "كتب", "كاتب"], 0, "maktoub"),
                      ("« Nous aurions aimé » arabe ?", ["لو كنا أحببنا", "كنا أحببنا", "نحب", "أحب"], 0, "law kuntu ahabna")],
    },
    "ara": {'''
new_ara_ex = '''        "difficile": [("« J'aurai été » arabe ?", "سأكون قد كنت", "sa'akoonu qad kuntu"),
                      ("Subjonctif « être » arabe ?", "يكون", "yakoona"),
                      ("« Ils étaient » arabe ?", "كانوا", "kaanu"),
                      ("Participe « écrire » arabe ?", "مكتوب", "maktoub"),
                      ("« Nous aurions aimé » arabe ?", "لو كنا أحببنا", "law kuntu ahabna")],
    },
    "ara": {'''
if old_ara_ex in content:
    content = content.replace(old_ara_ex, new_ara_ex, 1)
    print("✅ EXERCICES ARA difficile corrigé")
else:
    print("⚠️ EXERCICES ARA difficile non trouvé")

# 4. QUIZ ARA difficile (3 → 4 éléments)
old_ara_q = '''        "difficile": [("« J'aurai été » arabe ?", "سأكون قد كنت", "sa'akoonu qad kuntu"),
                      ("Subjonctif « être » arabe ?", "يكون", "yakoona"),
                      ("« Ils étaient » arabe ?", "كانوا", "kaanu"),
                      ("Participe « écrire » arabe ?", "مكتوب", "maktoub"),
                      ("« Nous aurions aimé » arabe ?", "لو كنا أحببنا", "law kuntu ahabna")],'''
new_ara_q = '''        "difficile": [("« J'aurai été » arabe ?", ["سأكون قد كنت", "كنت قد أكون", "أكون قد كنت", "كنت"], 0, "sa'akoonu qad kuntu"),
                      ("Subjonctif « être » arabe ?", ["يكون", "كان", "يكون", "كانت"], 0, "yakoona"),
                      ("« Ils étaient » arabe ?", ["كانوا", "يكونون", "كان", "كانتا"], 0, "kaanu"),
                      ("Participe « écrire » arabe ?", ["مكتوب", "يكتب", "كتب", "كاتب"], 0, "maktoub"),
                      ("« Nous aurions aimé » arabe ?", ["لو كنا أحببنا", "كنا أحببنا", "نحب", "أحب"], 0, "law kuntu ahabna")],'''
if old_ara_q in content:
    content = content.replace(old_ara_q, new_ara_q, 1)
    print("✅ QUIZ ARA difficile corrigé")
else:
    print("⚠️ QUIZ ARA difficile non trouvé")

with open('/home/user/deploy/tests/generer_contenu.py', 'w') as f:
    f.write(content)

print("✅ Corrections terminées")
