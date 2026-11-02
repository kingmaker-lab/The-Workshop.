// The Workshop Security Division. Compiled HTML/CSS/JS placeholders below.
const HTML=__INLINE_HTML__, CSS=__INLINE_CSS__, JS=__INLINE_JS__, ARGUS_B64=__INLINE_ARGUS_AVIF__;
const ENC=new TextEncoder();
const MISSIONS=[
{id:'base64',title:'Primeiro sinal',category:'Encoding',level:'Iniciante',points:50,summary:'Decodifique um telegrama Base64.',hint:'Base64 é codificação, não criptografia. Decodifique o texto completo.'},
{id:'rot13',title:'A cifra do corredor',category:'Criptografia',level:'Iniciante',points:70,summary:'Desfaça a substituição ROT13.',hint:'Aplique ROT13 novamente: cada letra se desloca 13 posições.'},
{id:'html',title:'O segredo no HTML',category:'Web',level:'Iniciante',points:90,summary:'Investigue o código-fonte de uma página simulada.',hint:'Procure um atributo data-flag no trecho fornecido.'},
{id:'logs',title:'Rastro no log',category:'Forense',level:'Intermediário',points:110,summary:'Ache uma evidência no cabeçalho HTTP de um log fictício.',hint:'O cabeçalho X-Workshop-Flag registra a evidência.'},
{id:'xor',title:'Oficina XOR',category:'Criptografia',level:'Intermediário',points:130,summary:'Reverta um XOR de um byte sobre valores hexadecimais.',hint:'Converta hex para bytes e aplique XOR com 0x23.'},
{id:'js',title:'A trilha do JavaScript',category:'Código',level:'Intermediário',points:150,summary:'Reconstitua uma string a partir dos códigos numéricos de seus caracteres.',hint:'String.fromCharCode recebe códigos de caracteres e produz um texto.'},
{id:'json',title:'Arquivo 07',category:'Análise de dados',level:'Avançado',points:170,summary:'Interprete um JSON e desfaça duas transformações.',hint:'Inverta a sequência de payload, depois aplique Base64 decode.'}
];
const BY_ID=new Map(MISSIONS.map(x=>[x.id,x]));
const HEAD={'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer','Permissions-Policy':'geolocation=(),camera=(),microphone=()','Cross-Origin-Resource-Policy':'same-origin','Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"};
const reply=(v,status=200,extra={})=>new Response(JSON.stringify(v),{status,headers:{...HEAD,'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store',...extra}});
const error=(message,status=400)=>reply({error:message},status);
const asset=(body,contentType)=>new Response(body,{headers:{...HEAD,'Content-Type':contentType,'Cache-Control':'public, max-age=300'}});
const hex=a=>[...new Uint8Array(a)].map(x=>x.toString(16).padStart(2,'0')).join('');
async function hash(s){return hex(await crypto.subtle.digest('SHA-256',ENC.encode(s)));}
function token(n=32){let b=crypto.getRandomValues(new Uint8Array(n));return btoa(String.fromCharCode(...b)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
const setCookie=(s,age=2592000)=>'ws_ctf_session='+s+'; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age='+age;
function cookie(req){let m=(req.headers.get('Cookie')||'').match(/(?:^|;\s*)ws_ctf_session=([A-Za-z0-9_-]{43})(?:;|$)/);return m?m[1]:null;}
async function player(req,env){const t=cookie(req);return t?env.DB.prepare('SELECT * FROM players WHERE session_hash=?').bind(await hash(t)).first():null;}
async function flag(env,id,mission){
  if(!env.FLAG_SECRET||env.FLAG_SECRET.length<32)throw Error('FLAG_SECRET unavailable');
  const key=await crypto.subtle.importKey('raw',ENC.encode(env.FLAG_SECRET),{name:'HMAC',hash:'SHA-256'},false,['sign']);
  const signed=await crypto.subtle.sign('HMAC',key,ENC.encode(id+':'+mission));
  return 'WS{'+hex(signed).slice(0,18).toUpperCase()+'}';
}
const r13=s=>s.replace(/[A-Za-z]/g,c=>String.fromCharCode(c.charCodeAt(0)+(c.toLowerCase()<='m'?13:-13)));
function puzzle(id,f){
  const map={
    base64:{file:'telegrama.base64',language:'text',instruction:'Decodifique Base64 e envie a flag encontrada.',content:btoa(f)},
    rot13:{file:'bilhete.rot13',language:'text',instruction:'Aplique ROT13 para encontrar a mensagem original.',content:r13(f)},
    html:{file:'amostra.html',language:'html',instruction:'Leia este HTML simulado. Não ataque nenhum site real.',content:'<!doctype html>\n<section class="laboratorio" data-stage="local" data-flag="'+f+'">\n  <h1>Veja além da interface.</h1>\n</section>'},
    logs:{file:'acesso-local.log',language:'http',instruction:'Inspecione o cabeçalho da resposta 401 simulada.',content:'GET /health 200 192.0.2.4\nPOST /login 401 192.0.2.44\n--- resposta simulada ---\nHTTP/1.1 401 Unauthorized\nX-Workshop-Flag: '+f+'\n--- fim ---\nGET /help 200 192.0.2.4'},
    xor:{file:'xor-23.hex',language:'hex',instruction:'Desfaça XOR com a chave hexadecimal 23 em cada byte.',content:[...ENC.encode(f)].map(b=>(b^0x23).toString(16).padStart(2,'0')).join(' ')},
    js:{file:'rastreamento.js',language:'javascript',instruction:'Recupere a string pelo código abaixo.',content:'// Simulação local, sem rede\nconst codes = ['+[...f].map(c=>c.charCodeAt(0)).join(', ')+'];\nconsole.log(String.fromCharCode(...codes));'},
    json:{file:'incidente-07.json',language:'json',instruction:'Reverta o payload: primeiro inverta a sequência, depois decodifique Base64.',content:JSON.stringify({incident:{id:'CASE-07',scope:'training-only',evidence:{payload:btoa(f).split('').reverse().join(''),transformations:['base64','reverse']}}},null,2)}
  };return map[id];
}
function missionMeta(x){const {id,title,category,level,points,summary}=x;return {id,title,category,level,points,summary};}
async function me(req,env){
  const p=await player(req,env);if(!p)return null;
  const r=await env.DB.prepare('SELECT challenge_id,points FROM solves WHERE player_id=?').bind(p.id).all();
  const sols=r.results||[];
  return {nickname:p.nickname,score:sols.reduce((s,x)=>s+x.points,0),solved:sols.map(x=>x.challenge_id)};
}
async function board(env){
 const [r,s]=await Promise.all([
 env.DB.prepare('SELECT p.nickname,COUNT(s.challenge_id) AS solved,COALESCE(SUM(s.points),0) AS score FROM players p LEFT JOIN solves s ON p.id=s.player_id GROUP BY p.id ORDER BY score DESC,solved DESC,p.created_at ASC LIMIT 30').all(),
 env.DB.prepare('SELECT (SELECT COUNT(*) FROM players) AS players,(SELECT COUNT(*) FROM solves) AS solves').first()
 ]);return {ranking:r.results||[],totals:s};
}
function allowed(req){const o=req.headers.get('Origin');return (!o||o===new URL(req.url).origin)&&req.headers.get('Sec-Fetch-Site')!=='cross-site'&&/^application\/json(?:;|$)/i.test(req.headers.get('Content-Type')||'');}
async function readBody(req){if(Number(req.headers.get('Content-Length')||0)>1000)throw Error();let s=await req.text();if(s.length>1000)throw Error();let o=JSON.parse(s);if(!o||typeof o!=='object'||Array.isArray(o))throw Error();return o;}
const validNick=n=>typeof n==='string'&&/^[\p{L}\p{N}_-]{3,20}$/u.test(n);
async function api(req,env,path){
 if(!env.DB)return error('Arena temporariamente indisponível.',503);
 if(req.method==='GET'){
   if(path==='/api/health'){await env.DB.prepare('SELECT 1').first();return reply({status:'ok'});}
   if(path==='/api/bootstrap'){const [b,u]=await Promise.all([board(env),me(req,env)]);return reply({...b,me:u,challenges:MISSIONS.map(missionMeta)});}
   if(path==='/api/me')return reply({me:await me(req,env)});
   if(path==='/api/leaderboard')return reply(await board(env));
   const m=path.match(/^\/api\/challenge\/([a-z0-9-]+)$/);
   if(m){let p=await player(req,env);if(!p)return error('Crie um codinome para acessar a missão.',401);
      let x=BY_ID.get(m[1]);if(!x)return error('Missão não encontrada.',404);
      return reply({...missionMeta(x),hint:x.hint,artifact:puzzle(x.id,await flag(env,p.id,x.id))});}
   return error('Rota não encontrada.',404);
 }
 if(req.method!=='POST')return error('Método não permitido.',405);
 if(!allowed(req))return error('Requisição não permitida.',403);
 let body;try{body=await readBody(req);}catch{return error('JSON inválido ou muito grande.',400);}
 if(path==='/api/session'){
   if(await player(req,env))return error('Você já tem um codinome nesta sessão.',409);
   const nick=typeof body.nickname==='string'?body.nickname.trim():'';
   if(!validNick(nick))return error('Use 3 a 20 caracteres: letras, números, _ ou -.',400);
   let s=token(),recovery=token(24);
   try{await env.DB.prepare('INSERT INTO players(id,nickname,nickname_key,session_hash,recovery_hash,created_at) VALUES(?,?,?,?,?,?)').bind(crypto.randomUUID(),nick,nick.toLocaleLowerCase('pt-BR'),await hash(s),await hash(recovery),Date.now()).run();}
   catch(e){if(String(e).includes('UNIQUE'))return error('Codinome já utilizado.',409);throw e;}
   return reply({ok:true,nickname:nick,recovery},201,{'Set-Cookie':setCookie(s)});
 }
 if(path==='/api/restore'){
   let n=typeof body.nickname==='string'?body.nickname.trim():'',recovery=body.recovery;
   if(!validNick(n)||typeof recovery!=='string'||!/^[A-Za-z0-9_-]{32}$/.test(recovery))return error('Dados inválidos.',400);
   const p=await env.DB.prepare('SELECT id FROM players WHERE nickname_key=? AND recovery_hash=?').bind(n.toLocaleLowerCase('pt-BR'),await hash(recovery)).first();
   if(!p)return error('Codinome ou código de recuperação incorreto.',401);
   const s=token();await env.DB.prepare('UPDATE players SET session_hash=? WHERE id=?').bind(await hash(s),p.id).run();
   return reply({ok:true},200,{'Set-Cookie':setCookie(s)});
 }
 if(path==='/api/logout'){
   const p=await player(req,env);
   if(p)await env.DB.prepare('UPDATE players SET session_hash=? WHERE id=?').bind(await hash(token()),p.id).run();
   return reply({ok:true},200,{'Set-Cookie':setCookie('',0)});
 }
 if(path==='/api/submit'){
   const p=await player(req,env);if(!p)return error('Você precisa entrar na arena.',401);
   const x=BY_ID.get(body.id);
   if(!x||typeof body.flag!=='string'||body.flag.length>120)return error('Flag ou missão inválida.',400);
   if(!/^WS\{[0-9A-Fa-f]{18}\}$/.test(body.flag.trim()))return error('Use o formato WS{18 caracteres hexadecimais}.',400);
   const now=Math.floor(Date.now()/1000);
   const counter=await env.DB.prepare('UPDATE players SET attempt_count=CASE WHEN ?-attempt_window>600 THEN 1 ELSE attempt_count+1 END,attempt_window=CASE WHEN ?-attempt_window>600 THEN ? ELSE attempt_window END WHERE id=? RETURNING attempt_count').bind(now,now,now,p.id).first();
   if(counter.attempt_count>30)return error('Limite temporário de tentativas atingido.',429);
   if(body.flag.trim().toUpperCase()!==(await flag(env,p.id,x.id)))return error('Flag incorreta. Revise sua investigação.',422);
   const res=await env.DB.prepare('INSERT OR IGNORE INTO solves(player_id,challenge_id,points,solved_at) VALUES(?,?,?,?)').bind(p.id,x.id,x.points,Date.now()).run();
   const points=res.meta?.changes===1?x.points:0;
   return reply({ok:true,points,message:points?'Flag aceita. Missão concluída!':'Esta missão já foi concluída.'});
 }
 return error('Rota não encontrada.',404);
}
export default {async fetch(req,env){
 const p=new URL(req.url).pathname;
 if(req.method==='GET'&&(p==='/'||p==='/index.html'))return asset(HTML,'text/html; charset=utf-8');
 if(req.method==='GET'&&p==='/styles.css')return asset(CSS,'text/css; charset=utf-8');
 if(req.method==='GET'&&p==='/app.js')return asset(JS,'text/javascript; charset=utf-8');
 if(req.method==='GET'&&p==='/assets/argus.avif')return new Response(Uint8Array.from(atob(ARGUS_B64),c=>c.charCodeAt(0)),{headers:{...HEAD,'Content-Type':'image/avif','Cache-Control':'public, max-age=604800'}});
 if(p.startsWith('/api/'))try{return await api(req,env,p);}catch(e){console.error('arena API failure',String(e).slice(0,120));return error('Serviço temporariamente indisponível.',503);}
 return error('Página não encontrada.',404);
}};
