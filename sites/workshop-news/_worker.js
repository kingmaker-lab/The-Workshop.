// Workshop News | Cloudflare Pages Advanced Mode | no third-party client scripts.
const SOURCE_LIMIT = 500_000;
const SECURITY = Object.freeze({
  'X-Content-Type-Options':'nosniff',
  'X-Frame-Options':'DENY',
  'Referrer-Policy':'no-referrer',
  'Permissions-Policy':'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
  'Strict-Transport-Security':'max-age=31536000',
  'Cross-Origin-Resource-Policy':'same-origin',
  'Content-Security-Policy':"default-src 'none'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; upgrade-insecure-requests"
});
const HEADERS_API = {'Content-Type':'application/json; charset=utf-8','Cache-Control':'public, max-age=120, s-maxage=300, stale-while-revalidate=180'};
const GH_COMMITS = 'https://api.github.com/repos/kingmaker-lab/The-Workshop./commits?per_page=10';
const FEEDS = [
  {name:'Cloudflare Blog',url:'https://blog.cloudflare.com/rss/',host:'blog.cloudflare.com',category:'Infra'},
  {name:'GitHub Blog',url:'https://github.blog/feed/',host:'github.blog',category:'Dev'}
];
const HN = 'https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=16';

const text = (value,max=190) => String(value ?? '').replace(/<[^>]*>/g,' ').replace(/[\u0000-\u001f\u007f]/g,' ').replace(/\s+/g,' ').trim().slice(0,max);
function decodeXml(value) {
  return String(value ?? '').replace(/^<!\[CDATA\[|\]\]>$/g,'').replace(/&#(x[0-9a-f]+|\d+);/gi,(_,v)=>{
    const n=v.toLowerCase().startsWith('x')?parseInt(v.slice(1),16):Number(v);
    return n>=32&&n<=0x10ffff?String.fromCodePoint(n):'';
  }).replace(/&(amp|lt|gt|quot|apos|#39);/gi,(_,v)=>({amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",'#39':"'"})[v.toLowerCase()]??'');
}
function safeUrl(raw,hosts=null) {
  try {
    const u=new URL(String(raw||''));
    if(u.protocol!=='https:' || u.username || u.password) return null;
    if(hosts && !hosts.includes(u.hostname.toLowerCase())) return null;
    return u.href;
  } catch { return null; }
}
const field=(block,tag)=>{
  const m=block.match(new RegExp('<(?:[\\w-]+:)?'+tag+'(?:\\s[^>]*)?>([\\s\\S]*?)<\\/(?:[\\w-]+:)?'+tag+'\\s*>','i'));
  return m?decodeXml(m[1].trim()):'';
};
const date=(v)=>{const d=new Date(v);return Number.isNaN(d.getTime())?null:d.toISOString();};
function categorize(value,original='Tech') {
  const q=String(value||'').toLowerCase();
  if(/cve|vulnerab|security|segurança|ransomware|malware|exploit|breach|phishing|zero.day/.test(q)) return 'Segurança';
  if(/\bai\b|artificial intelligence|machine learning|llm|gemini|openai|modelos? de ia|inteligência artificial|neural/.test(q)) return 'IA';
  if(/cloud|dns|server|cloudflare|network|infrastructure|infraestrutura|kubernetes|docker/.test(q)) return 'Infra';
  if(/github|release|developer|programming|python|rust|javascript|linux|ruby|code|software/.test(q)) return 'Dev';
  return original;
}
function parseRss(xml, source, limit=6) {
  const entries=String(xml).match(/<item(?:\s[^>]*)?>[\s\S]*?<\/item>/gi)||[];
  return entries.slice(0,limit*3).map((entry,i)=>{
    const title=text(field(entry,'title'),170);
    const url=safeUrl(field(entry,'link'),[source.host,'www.'+source.host]);
    const published=date(field(entry,'pubDate')||field(entry,'date'));
    if(!title||!url) return null;
    return {id:'rss-'+source.name.toLowerCase().replace(/\W/g,'-')+'-'+i,title,url,source:source.name,category:categorize(title,source.category),published};
  }).filter(Boolean).slice(0,limit);
}
function parseHn(json) {
  return (Array.isArray(json?.hits)?json.hits:[]).slice(0,30).map((hit)=>{
    const title=text(hit.title||hit.story_title,170);
    const url=safeUrl(hit.url||hit.story_url)||safeUrl('https://news.ycombinator.com/item?id='+encodeURIComponent(hit.objectID||''));
    if(!title||!url) return null;
    return {id:'hn-'+text(hit.objectID,24),title,url,source:'Hacker News',category:categorize(title),published:date(hit.created_at),score:Number.isFinite(Number(hit.points))?Math.max(0,Math.floor(Number(hit.points))):0};
  }).filter(Boolean).slice(0,12);
}
function parseCommits(json) {
  return (Array.isArray(json)?json:[]).slice(0,10).map(commit=>{
    const title=text(commit?.commit?.message?.split('\n')[0],130);
    const url=safeUrl(commit?.html_url,['github.com']);
    if(!title||!url) return null;
    return {id:text(commit.sha,40),title,url,source:'The Workshop',category:categorize(title,'Workshop'),published:date(commit?.commit?.committer?.date||commit?.commit?.author?.date),sha:text(commit.sha,7)};
  }).filter(Boolean);
}
async function readLimited(response) {
  const length=Number(response.headers.get('content-length')||0);
  if(!response.ok || length>SOURCE_LIMIT) throw Error('upstream not available');
  if(!response.body) return (await response.text()).slice(0,SOURCE_LIMIT);
  const reader=response.body.getReader();let bytes=0;const decoder=new TextDecoder();let result='';
  try {
    while(true) {
      const {value,done}=await reader.read();if(done)break;
      bytes+=value.byteLength;if(bytes>SOURCE_LIMIT)throw Error('upstream size limit');
      result+=decoder.decode(value,{stream:true});
    }
    return result+decoder.decode();
  } finally { reader.releaseLock(); }
}
async function pull(fetcher,url,accept='application/json'){
  const approvedHost=new URL(url).hostname;
  let current=url;
  for(let hop=0;hop<3;hop++){
    const response=await fetcher(current,{headers:{'Accept':accept,'User-Agent':'Workshop-News/1.0 (+https://github.com/kingmaker-lab/The-Workshop.)'},signal:AbortSignal.timeout(4500),redirect:'manual'});
    if(response.status>=300&&response.status<400){
      const location=response.headers.get('location');
      if(!location)throw Error('upstream redirect missing location');
      const target=new URL(location,current);
      if(target.protocol!=='https:'||target.hostname!==approvedHost||target.port||target.username||target.password)throw Error('untrusted upstream redirect');
      current=target.href;continue;
    }
    return readLimited(response);
  }
  throw Error('upstream redirect limit');
}
async function makeFeed(fetcher=fetch) {
  const tasks=[
    pull(fetcher,HN).then(x=>({type:'hn',data:parseHn(JSON.parse(x))})),
    ...FEEDS.map(s=>pull(fetcher,s.url,'application/rss+xml, application/xml;q=0.9, text/xml;q=0.8').then(x=>({type:s.name,data:parseRss(x,s)}))),
    pull(fetcher,GH_COMMITS).then(x=>({type:'workshop',data:parseCommits(JSON.parse(x))}))
  ];
  const settled=await Promise.allSettled(tasks);
  const articles=[];let updates=[];const available=[];
  for(let i=0;i<settled.length;i++){
    if(settled[i].status!=='fulfilled')continue;
    const {type,data}=settled[i].value;
    available.push(type);
    if(type==='workshop')updates=data;
    else articles.push(...data);
  }
  articles.sort((a,b)=>Date.parse(b.published||0)-Date.parse(a.published||0));
  const unique=Array.from(new Map(articles.map(a=>[a.url,a])).values()).slice(0,24);
  return {generatedAt:new Date().toISOString(),partial:available.length!==tasks.length,available,articles:unique,updates,projectLinks:[
    {name:'Workshop Labs',url:'https://workshop-labs.pages.dev/',tag:'Hub de pesquisa'},
    {name:'Crypto Lab',url:'https://wolfpack-crypto.pages.dev/',tag:'Criptografia e matemática'},
    {name:'WolfPack OS',url:'https://wolfpack.wolfpackworkshop.workers.dev/',tag:'Laboratórios interativos'},
    {name:'Cerberus',url:'https://cerberus.wolfpackworkshop.workers.dev/',tag:'Arquitetura e integração'}
  ]};
}
function json(body,status=200) {return new Response(JSON.stringify(body),{status,headers:{...SECURITY,...HEADERS_API,...(status>=400?{'Cache-Control':'no-store'}:{})}});}
function error(status,allow=false) {
  return new Response(status===404?'Não encontrado':'Método não permitido',{status,headers:{...SECURITY,'Content-Type':'text/plain; charset=utf-8','Cache-Control':'no-store',...(allow?{'Allow':'GET, HEAD'}:{})}});
}
async function handler(request,env={},ctx={}) {
  if(!['GET','HEAD'].includes(request.method))return error(405,true);
  const pathname=new URL(request.url).pathname;
  // Controlled navigation only: the destination is constant, never user-supplied.
  if(pathname==='/jogos'||pathname==='/jogos/'){
    return new Response(null,{status:302,headers:{
      ...SECURITY,
      'Location':'https://wolfpack.wolfpackworkshop.workers.dev/',
      'Cache-Control':'no-store',
      'Content-Type':'text/plain; charset=utf-8'
    }});
  }
  if(pathname==='/api/feed'){
    const cache=typeof caches!=='undefined'?caches.default:null;
    const key=new Request(new URL('/api/feed',request.url),{method:'GET'});
    if(cache) {
      const cached=await cache.match(key);
      if(cached) return request.method==='HEAD'?new Response(null,{status:cached.status,headers:cached.headers}):cached;
    }
    const feed=await makeFeed();
    const response=json(feed,feed.available.length?200:503);
    if(cache&&response.status===200&&typeof ctx.waitUntil==='function')ctx.waitUntil(cache.put(key,response.clone()));
    return request.method==='HEAD'?new Response(null,{status:response.status,headers:response.headers}):response;
  }
  if(pathname.startsWith('/api/'))return error(404);
  if(!['/','/index.html','/styles.css','/app.js','/favicon.svg'].includes(pathname))return error(404);
  if(!env.ASSETS || typeof env.ASSETS.fetch!=='function')return error(404);
  const response=await env.ASSETS.fetch(request);
  const headers=new Headers(response.headers);
  for(const [k,v] of Object.entries(SECURITY))headers.set(k,v);
  headers.set('Cache-Control',response.status===200?(pathname==='/'||pathname==='/index.html'?'public, max-age=120':'public, max-age=3600'):'no-store');
  return new Response(request.method==='HEAD'?null:response.body,{status:response.status,headers});
}
export {makeFeed,parseRss,parseHn,parseCommits,safeUrl,categorize,handler};
export default {fetch:handler};
