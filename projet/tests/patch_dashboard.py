#!/usr/bin/env python3
import re

with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ajouter le bouton nav "Contenus"
old_nav = '<div class="nav-item" data-view="matieres" onclick="goView(\'matieres\')"><span class="ic">📚</span> Matières & Cours</div>'
new_nav = old_nav + '\n      <div class="nav-item" data-view="contenus" onclick="goView(\'contenus\')"><span class="ic">✍️</span> Contenus & IA</div>'
if old_nav in content:
    content = content.replace(old_nav, new_nav)
    nav_ok = True
else:
    nav_ok = False

# 2. Ajouter la vue contents dans VIEWS
old_views = '  matieres:{title:"📚 Matières & Cours",render:renderMatieres},'
new_views = old_views + '\n  contenus:{title:"✍️ Contenus & IA",render:renderContenus},'
if old_views in content:
    content = content.replace(old_views, new_views)
    views_ok = True
else:
    views_ok = False

# 3. Ajouter la fonction renderContenus avant renderAdmins
marker = 'async function renderAdmins(){'
func_contenus = r'''async function renderContenus(){
  const c=document.getElementById("viewContent");
  c.innerHTML="<div class='loading'>Chargement...</div>";
  try{
    // Comptes
    const ex=await apiAdmin("/api/admin/exercises?limite=200");
    const qz=await apiAdmin("/api/admin/quiz?limite=200");
    const exN=ex.exercices?ex.exercices.length:0;
    const qzN=qz.quiz?qz.quiz.length:0;
    c.innerHTML=`
      <div class="card-grid">
        <div class="card">
          <h3>📊 Statistiques</h3>
          <div class="stat-box"><div class="stat-val">${exN}</div><div class="stat-lb">Exercices récents</div></div>
          <div class="stat-box"><div class="stat-val">${qzN}</div><div class="stat-lb">Quiz récents</div></div>
        </div>
        <div class="card">
          <h3>🤖 Génération IA</h3>
          <div class="field"><label>Sujet exercice</label><select id="genExSujet">
            <option value="math">Maths</option><option value="fr">Français</option><option value="phys">Physique</option><option value="chim">Chimie</option><option value="svt">SVT</option><option value="hist">Histoire</option><option value="geo">Géographie</option><option value="eng">Anglais</option><option value="eco">Économie</option><option value="info">Informatique</option><option value="es">Espagnol</option><option value="ara">Arabe</option>
          </select></div>
          <div class="field"><label>Difficulté</label><select id="genExDiff"><option>facile</option><option selected>moyen</option><option>difficile</option></select></div>
          <div class="field"><label>Nombre</label><input id="genExNb" type="number" value="5" min="1" max="50"></div>
          <button class="btn btn-primary btn-block" onclick="genExercices()">✨ Générer exercices IA</button>
          <div class="field" style="margin-top:12px"><label>Catégorie quiz</label><select id="genQzCat">
            <option>Maths</option><option>Français</option><option>Physique</option><option>Chimie</option><option>SVT</option><option>Histoire</option><option>Géographie</option><option>Anglais</option><option>Économie</option><option>Informatique</option>
          </select></div>
          <button class="btn btn-primary btn-block" onclick="genQuiz()">✨ Générer quiz IA</button>
          <div id="genResult" style="margin-top:12px"></div>
        </div>
        <div class="card">
          <h3>✏️ Exercices récents</h3>
          <div id="exList" style="max-height:400px;overflow-y:auto"></div>
        </div>
        <div class="card">
          <h3>📝 Quiz récents</h3>
          <div id="qzList" style="max-height:400px;overflow-y:auto"></div>
        </div>
      </div>
      <div class="field" style="margin-top:12px"><input id="exSearch" class="input" placeholder="Recherche exercice..." oninput="renderExList()"><button class="btn btn-danger" onclick="supprEx()">Supprimer</button></div>
    `;
    // Liste exercices
    const el=document.getElementById("exList");
    el.innerHTML=(ex.exercices||[]).map(e=>`<div class="list-item" onclick="selectEx(${e.id})"><div class="li-main">${e.question.substring(0,80)}</div><div class="li-meta">${e.sujet_code} · ${e.difficulte}</div></div>`).join("")||"<div class='empty'>Aucun</div>";
    window._exList=ex.exercices||[];
    window._selEx=null;
    // Liste quiz
    const ql=document.getElementById("qzList");
    ql.innerHTML=(qz.quiz||[]).map(q=>`<div class="list-item" onclick="selectQz(${q.id})"><div class="li-main">${q.question.substring(0,80)}</div><div class="li-meta">${q.categorie} · ${q.difficulte}</div></div>`).join("")||"<div class='empty'>Aucun</div>";
    window._qzList=qz.quiz||[];
    window._selQz=null;
  }catch(e){ c.innerHTML="<div class='alert err'>Erreur: "+e.message+"</div>"; }
}
async function genExercices(){
  const sujet=document.getElementById("genExSujet").value;
  const diff=document.getElementById("genExDiff").value;
  const nb=document.getElementById("genExNb").value;
  showAlert("genResult","Génération en cours...","ok");
  try{
    const r=await fetch(API+"/api/admin/exercises/generate",{method:"POST",headers:{"Content-Type":"application/json","X-Admin-Password":ADMIN_PW},body:JSON.stringify({sujet,difficulte:diff,nb})});
    const d=await r.json();
    showAlert("genResult","✅ "+(d.generes||0)+" générés, "+(d.ecartes||0)+" écartés","ok");
    renderContenus();
  }catch(e){ showAlert("genResult","❌ "+e.message,"err"); }
}
async function genQuiz(){
  const cat=document.getElementById("genQzCat").value;
  const diff=document.getElementById("genExDiff").value;
  const nb=document.getElementById("genExNb").value;
  showAlert("genResult","Génération en cours...","ok");
  try{
    const r=await fetch(API+"/api/admin/quiz/generate",{method:"POST",headers:{"Content-Type":"application/json","X-Admin-Password":ADMIN_PW},body:JSON.stringify({categorie:cat,difficulte:diff,nb})});
    const d=await r.json();
    showAlert("genResult","✅ "+(d.generes||0)+" générés, "+(d.ecartes||0)+" écartés","ok");
    renderContenus();
  }catch(e){ showAlert("genResult","❌ "+e.message,"err"); }
}
function selectEx(id){ window._selEx=id; const ex=window._exList.find(e=>e.id===id); if(ex){ const el=document.getElementById("exList"); el.innerHTML="<div class='list-item active'><div class='li-main'>"+ex.question+"</div><div class='li-meta'>"+ex.sujet_code+" · "+ex.difficulte+"</div><textarea class='input' rows='3'>"+(ex.explication||"")+"</textarea></div>"; } }
function selectQz(id){ window._selQz=id; const q=window._qzList.find(q=>q.id===id); if(q){ const el=document.getElementById("qzList"); el.innerHTML="<div class='list-item active'><div class='li-main'>"+q.question+"</div><div class='li-meta'>"+q.categorie+" · "+q.difficulte+"</div><textarea class='input' rows='3'>"+(q.explication||"")+"</textarea></div>"; } }
async function supprEx(){
  if(!window._selEx){ showAlert("genResult","Sélectionner un exercice","err"); return; }
  if(!confirm("Supprimer cet exercice?")) return;
  try{
    const r=await fetch(API+"/api/admin/exercises",{method:"DELETE",headers:{"Content-Type":"application/json","X-Admin-Password":ADMIN_PW},body:JSON.stringify({id:window._selEx})});
    showAlert("genResult","✅ Exercice supprimé","ok");
    renderContenus();
  }catch(e){ showAlert("genResult","❌ "+e.message,"err"); }
}
'''
if marker in content:
    content = content.replace(marker, func_contenus + "\n" + marker)
    func_ok = True
else:
    func_ok = False

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"PATCH OK - nav={nav_ok}, views={views_ok}, func={func_ok}")
