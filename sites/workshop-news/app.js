// Workshop News: untrusted headlines are always rendered with textContent.
const $=id=>document.getElementById(id);
const state={articles:[],updates:[],filter:'Tudo',search:'',loaded:false};
const relative=new Intl.RelativeTimeFormat('pt-BR',{numeric:'auto'});
const labels={'Segurança':'SECURITY','IA':'ARTIFICIAL INTELLIGENCE','Dev':'DEVELOPMENT','Infra':'INFRASTRUCTURE','Tech':'TECHNOLOGY'};
function age(iso){
  if(!iso)return 'Data não informada';
  const n=Date.parse(iso);if(!Number.isFinite(n))return 'Data não informada';
  const delta=Math.round((n-Date.now())/60000);
  if(Math.abs(delta)<60)return relative.format(delta,'minute');
  const hrs=Math.round(delta/60);if(Math.abs(hrs)<24)return relative.format(hrs,'hour');
  return relative.format(Math.round(hrs/24),'day');
}
function el(tag,className,text){
  const node=document.createElement(tag);
  if(className)node.className=className;
  if(text!==undefined)node.textContent=String(text);
  return node;
}
function trustedLink(link){
  try{
    const url=new URL(link);
    return url.protocol==='https:'&&!url.username&&!url.password?url.href:null;
  }catch{return null;}
}
function external(link,className){
  const safe=trustedLink(link);if(!safe)return null;
  const a=el('a',className);a.href=safe;a.target='_blank';a.rel='noopener noreferrer';
  a.referrerPolicy='no-referrer';return a;
}
function emptyMessage(title,message,links=[]){
  const box=el('div','empty');box.append(el('strong','',title),document.createTextNode(message));
  for(const item of links){const a=external(item.url);if(a){a.textContent=item.name;a.style.display='block';a.style.marginTop='10px';box.append(a);}}
  return box;
}
function renderNews(){
  const wrap=$('news-list');wrap.replaceChildren();
  if(!state.loaded){
    for(let i=0;i<3;i++)wrap.append(el('div','skeleton'));return;
  }
  const filtered=state.articles.filter(item=>(state.filter==='Tudo'||item.category===state.filter)&&(!state.search||(item.title+' '+item.source+' '+item.category).toLocaleLowerCase('pt-BR').includes(state.search)));
  if(!filtered.length){
    wrap.append(emptyMessage(state.articles.length?'Nenhuma notícia encontrada':'Fontes temporariamente indisponíveis',state.articles.length?'Tente outra busca ou categoria.':'O radar não recebeu manchetes neste ciclo. Consulte diretamente as fontes originais.',[{name:'Hacker News',url:'https://news.ycombinator.com/'},{name:'GitHub Blog',url:'https://github.blog/'},{name:'Cloudflare Blog',url:'https://blog.cloudflare.com/'}]));
    return;
  }
  for(const [i,item] of filtered.slice(0,14).entries()){
    const a=external(item.url,'news-item');if(!a)continue;
    const number=el('span','news-number',String(i+1).padStart(2,'0'));
    const body=el('span','news-body');
    const category=el('span','news-category cat-'+String(item.category||'tech').toLowerCase(),labels[item.category]||'TECHNOLOGY');
    const title=el('span','news-title',item.title);
    const meta=el('span','news-meta');
    meta.append(el('span','',item.source||'Fonte externa'),el('span','','·'),el('span','',age(item.published)));
    body.append(category,title,meta);
    a.append(number,body,el('span','news-arrow','↗'));
    a.setAttribute('aria-label',item.title+' (abre fonte externa)');
    wrap.append(a);
  }
}
function renderActivity(){
  const wrap=$('activity-list');wrap.replaceChildren();
  if(!state.loaded){wrap.append(el('div','activity-loading','Lendo o repositório...'));return;}
  if(!state.updates.length){wrap.append(emptyMessage('GitHub indisponível','O histórico não pôde ser consultado agora. Confira os commits diretamente no repositório.'));return;}
  for(const item of state.updates.slice(0,6)){
    const a=external(item.url,'activity-item');if(!a)continue;
    a.append(el('span','activity-tag',item.sha?'COMMIT / '+item.sha:'COMMIT'),el('span','activity-title',item.title),el('span','activity-meta',age(item.published)));
    wrap.append(a);
  }
}
function updateClock(){
  $('clock').textContent=new Intl.DateTimeFormat('pt-BR',{hour:'2-digit',minute:'2-digit'}).format(new Date());
}
async function refresh(){
  try{
    const response=await fetch('/api/feed',{headers:{Accept:'application/json'},cache:'no-store'});
    if(!response.ok)throw Error('feed unavailable');
    const data=await response.json();
    if(!Array.isArray(data.articles)||!Array.isArray(data.updates)||!Array.isArray(data.available))throw Error('invalid feed');
    state.articles=data.articles.filter(x=>x&&typeof x.title==='string'&&trustedLink(x.url));
    state.updates=data.updates.filter(x=>x&&typeof x.title==='string'&&trustedLink(x.url));
    $('metric-news').textContent=state.articles.length;
    $('metric-updates').textContent=state.updates.length;
    $('metric-sources').textContent=data.available.length+' / 4';
    $('metric-sync').textContent=data.generatedAt?new Intl.DateTimeFormat('pt-BR',{hour:'2-digit',minute:'2-digit'}).format(new Date(data.generatedAt)):'—';
    $('connection-state').textContent=data.partial?'FONTES PARCIAIS':'FONTES SINCRONIZADAS';
    $('sync-hint').textContent=data.partial?'Algumas fontes não responderam':'Atualizado automaticamente';
  }catch{
    $('connection-state').textContent='SEM CONEXÃO COM FEEDS';
    $('sync-hint').textContent='Tente recarregar a página';
    // Preserve previously fetched articles rather than replacing them with unverified fallback headlines.
  }finally{
    state.loaded=true;renderNews();renderActivity();
  }
}
for(const button of document.querySelectorAll('[data-filter]')){
  button.addEventListener('click',()=>{
    state.filter=button.dataset.filter;
    for(const other of document.querySelectorAll('[data-filter]')){
      const active=other===button;other.classList.toggle('active',active);other.setAttribute('aria-pressed',String(active));
    }
    renderNews();
  });
}
$('search').addEventListener('input',e=>{state.search=String(e.target.value||'').trim().toLocaleLowerCase('pt-BR');renderNews();});
updateClock();setInterval(updateClock,30_000);
refresh();setInterval(refresh,300_000);
