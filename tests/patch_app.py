import re

path = '/home/user/deploy/projet/app.html'
content = open(path, 'r').read()

# 1. Ajouter variables et selectDiff
content = content.replace(
    '// ── Quiz Universel ──\nasync function loadQuiz',
    '''// ── Quiz Universel ──
let QUIZ_DIFF = "Toutes";
let QUIZ_START = 0;
let QUIZ_TIMER = null;
function selectDiff(diff, el) {
  QUIZ_DIFF = diff;
  document.querySelectorAll("#quizDiffs .quick-btn").forEach(b => b.classList.remove("active"));
  el.classList.add("active");
}
async function loadQuiz'''
)

# 2. Modifier loadQuiz pour ajouter difficile
content = content.replace(
    'if(categorie && categorie!=="Toutes") params.set("categorie",categorie);',
    'if(categorie && categorie!=="Toutes") params.set("categorie",categorie);\n    if(QUIZ_DIFF!=="Toutes") params.set("difficulte",QUIZ_DIFF);'
)

# 3. Ajouter lancerSession après loadQuiz
content = content.replace(
    '} catch(err){showAlert("quizAlert","⚠️ Erreur réseau: "+err.message,false);}\n}\n\nfunction renderQuizQuestion(){',
    '''} catch(err){showAlert("quizAlert","⚠️ Erreur réseau: "+err.message,false);}
}

async function lancerSession() {
  const q = document.getElementById("quizAlert");
  showAlert("quizAlert", "🎲 Session en cours... 15 questions", true);
  try {
    const params = new URLSearchParams();
    if (QUIZ_DIFF !== "Toutes") params.set("difficulte", QUIZ_DIFF);
    const r = await fetch(API + "/api/quiz?limite=15&" + params, {headers: {"Authorization": "Bearer " + TOKEN}});
    const d = await r.json();
    QUIZ_DATA = d.quiz || [];
    if (QUIZ_DATA.length < 15) {
      showAlert("quizAlert", "⚠️ Seulement " + QUIZ_DATA.length + " questions disponibles", false);
      return;
    }
    QUIZ_SCORE = 0; QUIZ_TOTAL = 0; QUIZ_CURRENT = 0;
    QUIZ_START = Date.now();
    document.getElementById("quizScore").textContent = "0";
    document.getElementById("quizTotal").textContent = "0";
    startTimer();
    renderQuizQuestion();
    showAlert("quizAlert", "✅ Session lancée !", true);
  } catch (err) { showAlert("quizAlert", "⚠️ Erreur: " + err.message, false); }
}

function startTimer() {
  clearInterval(QUIZ_TIMER);
  QUIZ_TIMER = setInterval(() => {
    const sec = Math.floor((Date.now() - QUIZ_START) / 1000);
    const m = Math.floor(sec / 60), s = sec % 60;
    const el = document.getElementById("quizTimer");
    if (el) el.textContent = "⏱️ " + m + ":" + (s < 10 ? "0" : "") + s;
  }, 1000);
}

function stopTimer() { clearInterval(QUIZ_TIMER); }

function renderQuizQuestion(){'''
)

# 4. Modifier renderQuizQuestion pour ajouter chrono
old_end = 'document.getElementById("quizList").innerHTML=`<div class="card"><h3>🎯 Quiz terminé !</h3><p>Bonne réponses : <strong>${QUIZ_SCORE}</strong> / ${QUIZ_TOTAL} (${Math.round(QUIZ_SCORE/QUIZ_TOTAL*100)}%)</p></div>`;'
new_end = 'stopTimer();\n    const sec=Math.floor((Date.now()-QUIZ_START)/1000);\n    document.getElementById("quizList").innerHTML=`<div class="card"><h3>🎯 Session terminée !</h3><p>Bonne réponses : <strong>${QUIZ_SCORE}</strong> / ${QUIZ_TOTAL} (${Math.round(QUIZ_SCORE/QUIZ_TOTAL*100)}%)</p><p>Temps : ${Math.floor(sec/60)}m ${sec%60}s</p></div>`;'
content = content.replace(old_end, new_end)

# 5. Ajouter difficile dans q-cat
content = content.replace(
    '<div class="q-cat">${q.categorie}</div>',
    '<div class="q-cat">${q.categorie} · ${q.difficulte||""}</div>'
)

open(path, 'w').write(content)
print('✅ app.html modifié')
