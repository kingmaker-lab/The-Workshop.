// Workshop News: untrusted headlines are always rendered with textContent.
const $=id=>document.getElementById(id);
const state={articles:[],updates:[],highlights:[],sourceStatus:null,filter:'Tudo',search:'',loaded:false};
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
function renderHighlights(){
  const wrap=$('highlights-list');
  if(!wrap)return;
  wrap.replaceChildren();
  if(!state.loaded){
    for(let i=0;i<2;i++)wrap.append(el('div','skeleton'));
    return;
  }
  if(!state.highlights.length){
    wrap.append(emptyMessage('Nenhum destaque neste ciclo','Os destaques editoriais serão publicados após revisão das fontes.'));
    return;
  }
  for(const item of state.highlights.slice(0,6)){
    const a=external(item.url,'highlight-card');if(!a)continue;
    const top=el('span','highlight-top');
    top.append(el('span','highlight-topic',item.category||'The Workshop'),el('span','highlight-state',item.status||'EM PESQUISA'));
    const title=el('strong','highlight-title',item.title);
    const description=el('span','highlight-description',item.summary||'');
    const bottom=el('span','highlight-footer');
    bottom.append(el('span','',age(item.published)),el('span','','LER FONTE ↗'));
    a.append(top,title,description,bottom);
    wrap.append(a);
  }
}
function renderActivity(){
  const wrap=$('activity-list');wrap.replaceChildren();
  if(!state.loaded){wrap.append(el('div','activity-loading','Lendo o repositório...'));return;}
  if(!state.updates.length){
    const connected=state.sourceStatus&&(state.sourceStatus.githubCommits||state.sourceStatus.githubBranches>0);
    wrap.append(emptyMessage(connected?'Nenhum commit recente nas fontes consultadas':'Atividade GitHub temporariamente indisponível',
      connected?'Nenhum commit novo encontrado nesta atualização.':'Não conseguimos recuperar commits neste ciclo. Confira diretamente o repositório.',
      [{name:'Ver repositório no GitHub',url:'https://github.com/kingmaker-lab/The-Workshop.'}]));
    return;
  }
  for(const item of state.updates.slice(0,6)){
    const a=external(item.url,'activity-item');if(!a)continue;
    a.append(el('span','activity-tag',(item.branch||'main').toUpperCase()+' / '+(item.sha||'COMMIT')),el('span','activity-title',item.title),el('span','activity-meta',age(item.published)));
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
    state.highlights=(Array.isArray(data.highlights)?data.highlights:[]).filter(x=>x&&typeof x.title==='string'&&trustedLink(x.url));
    const source=data.sourceStatus&&typeof data.sourceStatus==='object'?data.sourceStatus:{};
    state.sourceStatus={
      githubCommits:source.githubCommits===true||data.available.includes('workshop'),
      githubBranches:Number(source.githubBranches??data.branchSourcesAvailable)||0,
      hackerNews:source.hackerNews===true||data.available.includes('hn'),
      githubBlog:source.githubBlog===true||data.available.includes('GitHub Blog'),
      cloudflareBlog:source.cloudflareBlog===true||data.available.includes('Cloudflare Blog')
    };
    const githubOnline=state.sourceStatus.githubCommits||state.sourceStatus.githubBranches>0;
    const statusText=(name,ok)=>name+': '+(ok?'conectado':'indisponível neste ciclo');
    $('source-diagnostics').textContent=[
      statusText('Repositório GitHub',githubOnline),
      statusText('GitHub Blog',state.sourceStatus.githubBlog),
      statusText('Cloudflare Blog',state.sourceStatus.cloudflareBlog),
      statusText('Hacker News',state.sourceStatus.hackerNews)
    ].join(' · ');
    $('github-status').textContent=githubOnline?'GITHUB CONECTADO':'GITHUB INDISPONÍVEL';
    $('metric-news').textContent=state.articles.length;
    $('metric-updates').textContent=state.updates.length;
    $('metric-sources').textContent=data.available.length+' / 4';
    $('metric-sync').textContent=data.generatedAt?new Intl.DateTimeFormat('pt-BR',{hour:'2-digit',minute:'2-digit'}).format(new Date(data.generatedAt)):'—';
    $('connection-state').textContent=!githubOnline?'GITHUB INDISPONÍVEL':data.partial?'GITHUB OK · FEEDS PARCIAIS':'FONTES SINCRONIZADAS';
    $('sync-hint').textContent=data.partial?'Status de cada fonte logo abaixo':'Atualizado automaticamente';
  }catch{
    $('connection-state').textContent='DADOS NÃO VERIFICADOS';
    $('github-status').textContent='GITHUB: STATUS DESCONHECIDO';
    $('source-diagnostics').textContent='Não foi possível consultar o status neste momento. Confira os commits diretamente no GitHub.';
    $('sync-hint').textContent='Tente recarregar a página';
    // Preserve previously fetched articles rather than replacing them with unverified fallback headlines.
  }finally{
    state.loaded=true;renderNews();renderActivity();renderHighlights();
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
