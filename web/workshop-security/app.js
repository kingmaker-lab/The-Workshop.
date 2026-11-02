'use strict';
const $ = s => document.querySelector(s);
const state={missions:[],me:null,ranking:[],active:null};
const elem=(tag,cls,txt)=>{let n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=String(txt);return n;};
function say(selector,message,isError=false){let n=$(selector);n.textContent=message;n.classList.toggle('error',isError);}
async function request(path,options={}){
 const res=await fetch(path,{credentials:'same-origin',...options});
 let value;try{value=await res.json();}catch{throw Error('Resposta inesperada do servidor.');}
 if(!res.ok)throw Error(value.error||'Falha ao processar requisição.');
 return value;
}
async function send(path,data){return request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});}
function renderAccount(){
 const guest=!state.me;$('#guestPanel').hidden=!guest;$('#profilePanel').hidden=guest;
 if(!guest){$('#profileNick').textContent=state.me.nickname;$('#profileScore').textContent=state.me.score;}
}
function renderMissions(){
 const grid=$('#missionGrid');grid.replaceChildren();
 state.missions.forEach((c,i)=>{
  const solved=Boolean(state.me?.solved?.includes(c.id));
  const card=elem('article','mission-card'+(solved?' solved':''));
  const top=elem('div','mission-top');top.append(elem('span','mission-num',String(i+1).padStart(2,'0')+' / 07'),elem('span','mission-points','+'+c.points+' XP'));
  const kind=elem('div','mission-category',c.category.toUpperCase());
  const title=elem('h3','',c.title),summary=elem('p','',c.summary);
  const foot=elem('div','mission-foot');foot.append(elem('span','mission-level',solved?'✓ CONCLUÍDO':c.level.toUpperCase()));
  const button=elem('button','',solved?'REVISITAR ↗':'ABRIR MISSÃO ↗');button.type='button';button.addEventListener('click',()=>openMission(c.id));foot.append(button);
  card.append(top,kind,title,summary,foot);grid.append(card);
 });
}
function renderBoard(){
 const body=$('#rankRows');body.replaceChildren();
 if(!state.ranking.length){const row=elem('tr');const c=elem('td','','Nenhum investigador ainda. Seu nome pode ser o primeiro.');c.colSpan=4;row.append(c);body.append(row);return;}
 state.ranking.forEach((r,i)=>{
  const row=elem('tr');[String(i+1).padStart(2,'0'),r.nickname,r.solved,r.score].forEach(value=>row.append(elem('td','',value)));body.append(row);
 });
}
async function refresh(){
 const data=await request('/api/bootstrap');state.missions=data.challenges||[];state.me=data.me||null;state.ranking=data.ranking||[];
 $('#statMissions').textContent=String(state.missions.length).padStart(2,'0');
 $('#statPlayers').textContent=data.totals?.players||0;$('#statSolves').textContent=data.totals?.solves||0;
 renderAccount();renderMissions();renderBoard();
}
async function openMission(id){
 if(!state.me){say('#identityStatus','Escolha seu codinome antes de abrir uma missão.');$('#identidade').scrollIntoView({behavior:'smooth'});$('#nickname').focus();return;}
 const detail=$('#missionDetail');detail.hidden=false;state.active=id;say('#flagStatus','');$('#flagInput').value='';$('#hintText').hidden=true;
 $('#detailTitle').textContent='Carregando...';detail.scrollIntoView({behavior:'smooth',block:'start'});
 try{
  const d=await request('/api/challenge/'+encodeURIComponent(id));
  $('#detailTitle').textContent=d.title;$('#detailCategory').textContent=d.category.toUpperCase()+' / +'+d.points+' XP';
  $('#detailInstruction').textContent=d.artifact.instruction;$('#detailFilename').textContent=d.artifact.file;
  $('#detailArtifact').textContent=d.artifact.content;$('#hintText').textContent=d.hint;
 }catch(e){say('#flagStatus',e.message,true);$('#detailTitle').textContent='Não foi possível abrir a missão.';}
}
$('#closeDetail').addEventListener('click',()=>{$('#missionDetail').hidden=true;state.active=null;});
$('#hintBtn').addEventListener('click',()=>{$('#hintText').hidden=!$('#hintText').hidden;});
$('#toggleRestore').addEventListener('click',()=>{$('#restoreForm').hidden=!$('#restoreForm').hidden;});
$('#dismissRecovery').addEventListener('click',()=>{$('#recoveryPanel').hidden=true;$('#recoveryValue').textContent='';});
$('#registerForm').addEventListener('submit',async e=>{
 e.preventDefault();say('#identityStatus','Criando sua identidade...');
 const button=e.currentTarget.querySelector('button');button.disabled=true;
 try{
  const out=await send('/api/session',{nickname:$('#nickname').value});
  $('#recoveryValue').textContent=out.recovery;$('#recoveryPanel').hidden=false;
  await refresh();say('#identityStatus','Codinome criado! Guarde sua chave de recuperação.');
 }catch(err){say('#identityStatus',err.message,true);}finally{button.disabled=false;}
});
$('#restoreForm').addEventListener('submit',async e=>{
 e.preventDefault();const button=e.currentTarget.querySelector('button');button.disabled=true;
 try{await send('/api/restore',{nickname:$('#recoverNick').value,recovery:$('#recoverKey').value});$('#recoverKey').value='';await refresh();say('#identityStatus','Acesso restaurado. Bem-vindo de volta.');}
 catch(err){say('#identityStatus',err.message,true);}finally{button.disabled=false;}
});
$('#logoutBtn').addEventListener('click',async()=>{
 try{await send('/api/logout',{});$('#missionDetail').hidden=true;$('#recoveryPanel').hidden=true;await refresh();say('#identityStatus','Sessão encerrada. Seu progresso continua guardado.');}
 catch(err){say('#identityStatus',err.message,true);}
});
$('#flagForm').addEventListener('submit',async e=>{
 e.preventDefault();if(!state.active)return;
 const button=e.currentTarget.querySelector('button');button.disabled=true;say('#flagStatus','Validando sua investigação...');
 try{const out=await send('/api/submit',{id:state.active,flag:$('#flagInput').value.trim()});say('#flagStatus',out.message+(out.points?' +'+out.points+' pontos.':''));await refresh();}
 catch(err){say('#flagStatus',err.message,true);}finally{button.disabled=false;}
});
refresh().catch(()=>{say('#identityStatus','A arena está temporariamente indisponível. Recarregue a página.',true);$('#missionGrid').textContent='Não foi possível carregar as missões.';});