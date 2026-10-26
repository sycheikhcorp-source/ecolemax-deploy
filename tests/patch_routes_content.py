#!/usr/bin/env python3
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_routes = r'''
# === ROUTES ADMIN : GÉNÉRATION IA ET CRUD CONTENUS ===

@app.route("/api/admin/exercises/generate", methods=["POST"])
def api_admin_exercises_generate():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Authentification requise"}), 403
    data = request.get_json(silent=True) or {}
    sujet = data.get("sujet","math")
    niveau = data.get("niveau","")
    difficulte = data.get("difficulte","moyen")
    nb = min(int(data.get("nb",10)),50)
    cat_name = {"math":"Maths","fr":"Français","phys":"Physique","chim":"Chimie","svt":"SVT","hist":"Histoire","geo":"Géographie","eng":"Anglais","eco":"Économie","info":"Informatique","es":"Espagnol","ara":"Arabe"}.get(sujet,sujet)

    c = db()
    generated = []
    for i in range(nb):
        q_prompt = "Génère un exercice de " + cat_name + " de niveau " + difficulte + " pour un élève. Format JSON strict:\n{\"question\": \"énoncé avec [option1/option2/option3/option4]\", \"explication\": \"solution détaillée\", \"difficulte\": \"" + difficulte + "\"}\nUnique, sans doublon. Réponse dans l'explication."
        ok, text, src = get_pollinations(q_prompt, max_tokens=500, silent=True)
        if not ok:
            ok, text, src = get_local_reponse(q_prompt), "", "Local"
        try:
            m = re.search(r'\{[^{}]*"question"[^{}]*\}', text, re.DOTALL)
            if m:
                j = json.loads(m.group(0))
                question = j.get("question","")
                explication = j.get("explication","")
                if question and len(question) > 10:
                    generated.append((sujet, question, explication, difficulte, niveau))
        except:
            pass

    inserted = 0
    for cat, q, exp, diff, niv in generated:
        dup = c.execute("SELECT id FROM exercises WHERE question=? AND sujet_code=?",(q[:100],cat)).fetchone()
        if dup: continue
        c.execute("INSERT INTO exercises (sujet_code,question,explication,difficulte,niveau) VALUES (?,?,?,?,?)",(cat,q,exp,diff,niv))
        inserted += 1
    c.commit()
    c.close()
    return jsonify({"ok":True,"generes":inserted,"ecartes":len(generated)-inserted,"source":src})

@app.route("/api/admin/quiz/generate", methods=["POST"])
def api_admin_quiz_generate():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Authentification requise"}), 403
    data = request.get_json(silent=True) or {}
    categorie = data.get("categorie","Maths")
    difficulte = data.get("difficulte","moyen")
    nb = min(int(data.get("nb",10)),50)

    c = db()
    generated = []
    for i in range(nb):
        q_prompt = "Génère un QCM de " + categorie + " de niveau " + difficulte + ". Format JSON strict:\n{\"question\": \"question\", \"reponse\": 0, \"explication\": \"explication pédagogique\"}\nreponse: index 0-3 de la bonne réponse. Réponse dans l'explication."
        ok, text, src = get_pollinations(q_prompt, max_tokens=400, silent=True)
        if not ok: continue
        try:
            m = re.search(r'\{[^{}]*"question"[^{}]*\}', text, re.DOTALL)
            if m:
                j = json.loads(m.group(0))
                q = j.get("question","")
                rep = j.get("reponse",0)
                exp = j.get("explication","")
                if rep < 0 or rep > 3: rep = 0
                if q and len(q) > 10:
                    generated.append((categorie, q, rep, exp, difficulte))
        except:
            pass

    inserted = 0
    for cat, q, rep, exp, diff in generated:
        dup = c.execute("SELECT id FROM quiz WHERE question=? AND categorie=?",(q[:100],cat)).fetchone()
        if dup: continue
        c.execute("INSERT INTO quiz (categorie,question,reponse,explication,difficulte) VALUES (?,?,?,?,?)",(cat,q,rep,exp,diff))
        inserted += 1
    c.commit()
    c.close()
    return jsonify({"ok":True,"generes":inserted,"ecartes":len(generated)-inserted,"source":src})

@app.route("/api/admin/exercises", methods=["GET","POST","DELETE"])
def api_admin_exercises():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Authentification requise"}), 403
    c = db()
    if request.method == "GET":
        sujet = request.args.get("sujet","")
        difficulte = request.args.get("difficulte","")
        limite = int(request.args.get("limite",50))
        q = "SELECT * FROM exercises WHERE 1=1"
        params = []
        if sujet: q += " AND sujet_code=?"; params.append(sujet)
        if difficulte: q += " AND difficulte=?"; params.append(difficulte)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limite)
        rows = c.execute(q, params).fetchall()
        c.close()
        return jsonify({"exercices":[dict(r) for r in rows]})
    data = request.get_json(silent=True) or {}
    if request.method == "POST":
        sujet = data.get("sujet_code","math")
        question = data.get("question","")
        explication = data.get("explication","")
        difficulte = data.get("difficulte","moyen")
        niveau = data.get("niveau","")
        if not question: return jsonify({"erreur":"Question requise"}), 400
        c.execute("INSERT INTO exercises (sujet_code,question,explication,difficulte,niveau) VALUES (?,?,?,?,?)",(sujet,question,explication,difficulte,niveau))
        c.commit()
        c.close()
        return jsonify({"ok":True})
    if request.method == "DELETE":
        eid = data.get("id")
        if not eid: return jsonify({"erreur":"ID requis"}), 400
        c.execute("DELETE FROM exercises WHERE id=?",(eid,))
        c.commit()
        c.close()
        return jsonify({"ok":True})

@app.route("/api/admin/quiz", methods=["GET","POST","DELETE"])
def api_admin_quiz():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Authentification requise"}), 403
    c = db()
    if request.method == "GET":
        categorie = request.args.get("categorie","")
        difficulte = request.args.get("difficulte","")
        limite = int(request.args.get("limite",50))
        q = "SELECT * FROM quiz WHERE 1=1"
        params = []
        if categorie: q += " AND categorie=?"; params.append(categorie)
        if difficulte: q += " AND difficulte=?"; params.append(difficulte)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limite)
        rows = c.execute(q, params).fetchall()
        c.close()
        return jsonify({"quiz":[dict(r) for r in rows]})
    data = request.get_json(silent=True) or {}
    if request.method == "POST":
        categorie = data.get("categorie","Maths")
        question = data.get("question","")
        reponse = int(data.get("reponse",0))
        explication = data.get("explication","")
        difficulte = data.get("difficulte","moyen")
        if not question: return jsonify({"erreur":"Question requise"}), 400
        c.execute("INSERT INTO quiz (categorie,question,reponse,explication,difficulte) VALUES (?,?,?,?,?)",(categorie,question,reponse,explication,difficulte))
        c.commit()
        c.close()
        return jsonify({"ok":True})
    if request.method == "DELETE":
        qid = data.get("id")
        if not qid: return jsonify({"erreur":"ID requis"}), 400
        c.execute("DELETE FROM quiz WHERE id=?",(qid,))
        c.commit()
        c.close()
        return jsonify({"ok":True})

'''

marker = "# Keepalive"
pos = content.find(marker)
if pos == -1:
    pos = content.find("if __name__")
if pos == -1:
    pos = len(content)

content = content[:pos] + new_routes + "\n" + content[pos:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH ROUTES OK")
