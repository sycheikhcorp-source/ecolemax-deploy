#!/usr/bin/env python3
"""Test de charge ÉcoleMax — 50 utilisateurs simultanés.

Scénarios :
1. Inscription simultanée
2. Connexion simultanée
3. Quiz + réponses
4. Exercices
5. IA conversation
6. Correction texte
7. Traduction
8. Favoris
9. /api/me

Mesure : taux réussite, temps moyen, P95/P99, erreurs HTTP.
"""
import json, time, random, urllib.request, urllib.error, concurrent.futures, statistics, sys

BASE = "https://ecolemax.onrender.com"
N = 50

def req(method, url, data=None, token=None, timeout=60):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = "Bearer " + token
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                               headers=h, method=method)
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        code, body = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        code, body = e.code, e.read()
    except Exception as e:
        code, body = 0, str(e).encode()
    dt = (time.time() - t0) * 1000
    return code, dt, body

def parse(body):
    try: return json.loads(body)
    except Exception: return {}

results = []  # (scenario, code, dt_ms)

def scenario_register(i):
    code, dt, body = req("POST", BASE + "/api/register", {
        "pseudo": f"charge_{i}", "mot_de_passe": "Test@123",
        "email": f"c{i}@test.com", "niveau": "3ème"})
    return ("register", code, dt)

def scenario_login(i):
    code, dt, body = req("POST", BASE + "/api/login", {
        "pseudo": f"charge_{i}", "mot_de_passe": "Test@123"})
    d = parse(body)
    return ("login", code, dt, d.get("token"))

def scenario_quiz(token, i):
    code, dt, body = req("POST", BASE + "/api/quiz/reponse",
                         {"quiz_id": 1, "reponse": i % 4}, token=token)
    return ("quiz", code, dt)

def scenario_exercise(token, i):
    code, dt, body = req("POST", BASE + "/api/exercise/reponse",
                         {"exercise_id": 1, "reponse": f"reponse_{i}"}, token=token)
    return ("exercise", code, dt)

def scenario_ai_ask(token, i):
    code, dt, body = req("POST", BASE + "/api/ai/ask",
                         {"question": f"Question {i}: explique la fraction 1/2"}, token=token, timeout=90)
    return ("ai_ask", code, dt)

def scenario_ai_correct(token, i):
    code, dt, body = req("POST", BASE + "/api/ai/correct",
                         {"texte": "je vei a lekole"}, token=token, timeout=90)
    return ("ai_correct", code, dt)

def scenario_translate(token, i):
    code, dt, body = req("POST", BASE + "/api/ai/translate",
                         {"texte": "bonjour", "langue": "en"}, token=token, timeout=90)
    return ("translate", code, dt)

def scenario_favoris(token, i):
    code, dt, body = req("POST", BASE + "/api/favoris/add",
                         {"type": "cours", "ref_id": 1, "label": f"fav_{i}"}, token=token)
    return ("favoris", code, dt)

def scenario_me(token, i):
    code, dt, body = req("GET", BASE + "/api/me", token=token)
    return ("me", code, dt)

def run():
    all_times = {}
    all_codes = {}
    errors = []

    print(f"=== TEST DE CHARGE {N} UTILISATEURS — {BASE} ===\n")

    # Phase 1 : inscription simultanée
    print(f"[Phase 1] Inscriptions simultanées ({N})...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as ex:
        futs = [ex.submit(scenario_register, i) for i in range(N)]
        for f in concurrent.futures.as_completed(futs):
            sc, code, dt = f.result()
            results.append((sc, code, dt))
            all_times.setdefault(sc, []).append(dt)
            all_codes.setdefault(sc, {}).setdefault(code, 0)
            all_codes[sc][code] += 1
            if code != 200:
                errors.append((sc, code))

    # Phase 2 : connexion simultanée
    print(f"[Phase 2] Connexions simultanées ({N})...")
    tokens = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as ex:
        futs = [ex.submit(scenario_login, i) for i in range(N)]
        for f in concurrent.futures.as_completed(futs):
            sc, code, dt, tok = f.result()
            results.append((sc, code, dt))
            all_times.setdefault(sc, []).append(dt)
            all_codes.setdefault(sc, {}).setdefault(code, 0)
            all_codes[sc][code] += 1
            if code == 200 and tok:
                tokens[sc] = tok
            if code != 200:
                errors.append((sc, code))

    # Phase 3 : quiz + exercices + /api/me simultanés
    print(f"[Phase 3] Quiz + exercices + profil simultanés ({N})...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as ex:
        futs = []
        for i in range(N):
            tok = tokens.get("login") or None
            if tok:
                futs.append(ex.submit(scenario_quiz, tok, i))
                futs.append(ex.submit(scenario_exercise, tok, i))
                futs.append(ex.submit(scenario_me, tok, i))
        for f in concurrent.futures.as_completed(futs):
            sc, code, dt = f.result()
            results.append((sc, code, dt))
            all_times.setdefault(sc, []).append(dt)
            all_codes.setdefault(sc, {}).setdefault(code, 0)
            all_codes[sc][code] += 1
            if code != 200:
                errors.append((sc, code))

    # Phase 4 : IA (plus lent) — 20 utilisateurs
    print(f"[Phase 4] IA (ask/correct/traduction) — 20 utilisateurs...")
    ia_tokens = list(tokens.values()) or [None]
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futs = []
        for i in range(20):
            tok = ia_tokens[i % len(ia_tokens)]
            futs.append(ex.submit(scenario_ai_ask, tok, i))
            futs.append(ex.submit(scenario_ai_correct, tok, i))
            futs.append(ex.submit(scenario_translate, tok, i))
            futs.append(ex.submit(scenario_favoris, tok, i))
        for f in concurrent.futures.as_completed(futs):
            sc, code, dt = f.result()
            results.append((sc, code, dt))
            all_times.setdefault(sc, []).append(dt)
            all_codes.setdefault(sc, {}).setdefault(code, 0)
            all_codes[sc][code] += 1
            if code != 200:
                errors.append((sc, code))

    # Rapport
    print("\n" + "="*70)
    print("RAPPORT DU TEST DE CHARGE")
    print("="*70)
    total = 0
    succ = 0
    for sc in sorted(all_times.keys()):
        times = all_times[sc]
        codes = all_codes[sc]
        total += sum(codes.values())
        ok = codes.get(200, 0)
        succ += ok
        mean = statistics.mean(times)
        p95 = sorted(times)[int(len(times) * 0.95) - 1] if len(times) >= 20 else max(times)
        p99 = sorted(times)[int(len(times) * 0.99) - 1] if len(times) >= 100 else p95
        print(f"{sc:14s} | n={len(times):3d} | OK={ok:3d}/{sum(codes.values()):3d} | "
              f"moyen={mean:7.0f}ms | P95={p95:7.0f}ms | P99={p99:7.0f}ms | codes={codes}")

    print("-"*70)
    print(f"TOTAL : {succ}/{total} requêtes réussies ({100*succ/total:.1f}%)")
    if errors:
        print(f"ERREURS : {len(errors)} — exemples : {errors[:5]}")
    else:
        print("ERREURS : aucune")
    print("="*70)
    return succ, total

if __name__ == "__main__":
    run()
