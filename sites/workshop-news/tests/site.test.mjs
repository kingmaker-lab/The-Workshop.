import test from 'node:test';
import assert from 'node:assert/strict';
import worker,{handler,makeFeed,parseRss,parseHn,parseCommits,parseGitHubAtom,fetchGitHubCommits,safeUrl,categorize} from '../_worker.js';

const base='https://workshop-news.pages.dev/';
const rss='<?xml version="1.0"?><rss><channel><item><title><![CDATA[Cloudflare security update &amp; fixes]]></title><link>https://blog.cloudflare.com/security-update/</link><pubDate>Fri, 30 Oct 2026 08:00:00 GMT</pubDate></item><item><title>Bad link</title><link>http://evil.invalid/</link></item></channel></rss>';
const github=[{sha:'1234567890abcdef',html_url:'https://github.com/kingmaker-lab/The-Workshop./commit/123456',commit:{message:'feat: update Crypto Lab\nlong body',committer:{date:'2026-10-30T13:00:00Z'}}}];
const hn={hits:[{title:'Ruby security announcement',url:'https://ruby-lang.org/en/news/',objectID:'123',points:19,created_at:'2026-10-30T14:00:00Z'}, {title:'Unsafe',url:'javascript:alert(1)',objectID:'999',created_at:'2026-10-30T14:01:00Z'}]};
const fixtures=url=>{
  if(url.includes('algolia.com'))return new Response(JSON.stringify(hn),{status:200,headers:{'content-type':'application/json'}});
  if(url.includes('api.github.com')){
    const branch=url.includes('sha=feature')?'ruby':url.includes('sha=exp-008')?'ouroboros':'main';
    const commits=github.map(c=>({...c,sha:branch+'-1234567890abcdef',html_url:'https://github.com/kingmaker-lab/The-Workshop./commit/'+branch+'123456',commit:{...c.commit,message:branch+': '+c.commit.message}}));
    return new Response(JSON.stringify(commits),{status:200});
  }
  if(url.includes('blog.cloudflare.com'))return new Response(rss,{status:200});
  if(url.includes('github.blog'))return new Response('<rss><channel><item><title>GitHub developer update</title><link>https://github.blog/changelog/</link><pubDate>Fri, 30 Oct 2026 08:00:00 GMT</pubDate></item></channel></rss>',{status:200});
  throw Error('unexpected URL '+url);
};

const githubAtom = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Fix GitHub status &amp; diagnostics</title><link rel="alternate" type="text/html" href="https://github.com/kingmaker-lab/The-Workshop./commit/abcdef1234567890"/><updated>2026-10-30T16:30:00Z</updated></entry><entry><title>Unsafe link</title><link href="https://evil.invalid/commit/333"/><updated>2026-10-30T16:00:00Z</updated></entry></feed>';
const fakeAssets={ASSETS:{fetch:async req=>{
  const u=new URL(req.url);
  return new Response(u.pathname.endsWith('.css')?'body{}':'<!doctype html>',{status:200,headers:{'Content-Type':u.pathname.endsWith('.css')?'text/css':'text/html'}});
}}};

test('safeURL is HTTPS-only and refuses credentials',()=>{
  for(const x of ['javascript:alert(1)','http://bad.invalid/','https://name:password@github.com/','/relative','data:text/html,a'])assert.equal(safeUrl(x),null);
  assert.equal(safeUrl('https://blog.cloudflare.com/a',['blog.cloudflare.com']),'https://blog.cloudflare.com/a');
  assert.equal(safeUrl('https://other.example/a',['blog.cloudflare.com']),null);
});
test('rss is allowlisted and strips unwanted content',()=>{
 const articles=parseRss(rss,{name:'Cloudflare Blog',host:'blog.cloudflare.com',category:'Infra'});
 assert.equal(articles.length,1);
 assert.match(articles[0].title,/Cloudflare security update/);
 assert.equal(articles[0].url,'https://blog.cloudflare.com/security-update/');
 assert.equal(articles[0].category,'Segurança');
});
test('parses Hacker News and GitHub without reflecting scripts into links',()=>{
 const hnParsed=parseHn(hn);
 assert.equal(hnParsed[0].score,19);
 assert.equal(hnParsed[1].url,'https://news.ycombinator.com/item?id=999');
 assert.equal(parseCommits(github)[0].title,'feat: update Crypto Lab');
 assert.equal(categorize('Introducing a machine learning LLM'),'IA');
});
test('aggregator reports real data and partial upstream failure',async()=>{
 const data=await makeFeed(async url=>fixtures(url));
 assert.equal(data.available.length,4);
 assert.equal(data.partial,false);
 assert.equal(data.updates.length,3);
 assert.equal(data.highlights.length,4);
 assert.equal(data.branchSourcesAvailable,2);
 assert.ok(data.updates.some(x=>x.branch==='Protocolo Ruby'));
 assert.ok(data.updates.some(x=>x.branch==='Ouroboros EXP-008'));
 assert.ok(data.highlights.every(x=>x.url.startsWith('https://')&&x.status&&x.summary));
 assert.equal(data.articles.length,4);
 const partial=await makeFeed(async url=>{if(url.includes('github.blog'))throw Error('offline');return fixtures(url);});
 assert.equal(partial.available.length,3);
 assert.equal(partial.partial,true);
 assert.ok(partial.articles.length>0);
});
test('aggregator limits oversized feeds and marks source unavailable',async()=>{
 const data=await makeFeed(async url=>url.includes('algolia.com')?new Response('x'.repeat(501000),{status:200,headers:{'content-length':'501000'}}):fixtures(url));
 assert.ok(!data.available.includes('hn'));
 assert.equal(data.partial,true);
});
test('all unsupported methods denied, including OPTIONS',async()=>{
 for(const method of ['POST','PUT','DELETE','PATCH','OPTIONS']){
   const r=await worker.fetch(new Request(base,{method}),fakeAssets);
   assert.equal(r.status,405,method);assert.equal(r.headers.get('allow'),'GET, HEAD');
   assert.equal(r.headers.get('cache-control'),'no-store');
   assert.equal(r.headers.get('access-control-allow-origin'),null);
 }
});
test('sensitive paths and unknown API endpoints never reach ASSETS',async()=>{
 for(const path of ['/.env','/.git/config','/api/other','/%2e%2e/%2e%2e/private','/uploads/private.txt']){
   const r=await worker.fetch(new Request(new URL(path,base)),fakeAssets);
   assert.equal(r.status,404,path);
   assert.equal(r.headers.get('cache-control'),'no-store');
 }
});
test('static assets preserve security headers and HEAD semantics',async()=>{
 for(const path of ['/','/index.html','/styles.css','/app.js','/favicon.svg']){
   const r=await handler(new Request(new URL(path,base)),fakeAssets);
   assert.equal(r.status,200,path);
   assert.equal(r.headers.get('x-frame-options'),'DENY');
   assert.equal(r.headers.get('x-content-type-options'),'nosniff');
   assert.match(r.headers.get('content-security-policy'),/script-src 'self'/);
   assert.match(r.headers.get('content-security-policy'),/object-src 'none'/);
   assert.match(r.headers.get('strict-transport-security'),/max-age=\d+/);
   assert.equal(r.headers.get('access-control-allow-origin'),null);
   const head=await handler(new Request(new URL(path,base),{method:'HEAD'}),fakeAssets);
   assert.equal(head.status,200);assert.equal(await head.text(),'');
 }
});

test('feed follows only same-host HTTPS redirects (not arbitrary hosts)',async()=>{
 const hostile=await makeFeed(async url=>{
   if(url.includes('blog.cloudflare.com'))return new Response(null,{status:302,headers:{location:'https://127.0.0.1/private'}});
   return fixtures(url);
 });
 assert.ok(!hostile.available.includes('Cloudflare Blog'));
 assert.equal(hostile.partial,true);
 let redirected=false;
 const trusted=await makeFeed(async url=>{
   if(url==='https://blog.cloudflare.com/rss/'){redirected=true;return new Response(null,{status:301,headers:{location:'/rss'}});}
   return fixtures(url);
 });
 assert.ok(redirected);
 assert.ok(trusted.available.includes('Cloudflare Blog'));
});

test('games entry is a fixed redirect to WolfPack OS with no open redirect',async()=>{
 for(const method of ['GET','HEAD']){
   for(const path of ['/jogos','/jogos/?next=https://evil.invalid','/jogos?url=https://evil.invalid']){
     const response=await handler(new Request(new URL(path,base),{method}),fakeAssets);
     assert.equal(response.status,302,path);
     assert.equal(response.headers.get('location'),'https://wolfpack.wolfpackworkshop.workers.dev/');
     assert.equal(response.headers.get('cache-control'),'no-store');
     assert.equal(response.headers.get('x-content-type-options'),'nosniff');
     assert.equal(await response.text(),'');
   }
 }
 for(const method of ['POST','OPTIONS']){
   const response=await handler(new Request(new URL('/jogos',base),{method}),fakeAssets);
   assert.equal(response.status,405);
   assert.equal(response.headers.get('allow'),'GET, HEAD');
 }
});

test('editorial updates survive total upstream outage and never impersonate releases',async()=>{
 const data=await makeFeed(async()=>{throw Error('all sources down')});
 assert.equal(data.partial,true);
 assert.equal(data.available.length,0);
 assert.equal(data.updates.length,3);
 assert.equal(data.sourceStatus.fallbackUsed,true);
 assert.equal(data.sourceStatus.githubMode,'snapshot');
 assert.equal(data.highlights.length,4);
 const byId=Object.fromEntries(data.highlights.map(x=>[x.id,x]));
 assert.equal(byId['ouroboros-exp008'].status,'PESQUISA');
 assert.equal(byId['ruby-20261030'].status,'DESENVOLVIMENTO');
 assert.equal(byId['security-20261030'].status,'EM REVISÃO');
 assert.equal(byId['games-20261030'].status,'NO AR');
 for(const x of data.highlights)assert.equal(new URL(x.url).protocol,'https:');
});


test('GitHub repository health stays online when GitHub Blog RSS is offline',async()=>{
  const data=await makeFeed(async url=>{
    if(url.includes('github.blog'))throw Error('RSS source blocked');
    return fixtures(url);
  });
  assert.equal(data.partial,true);
  assert.equal(data.sourceStatus.githubCommits,true);
  assert.equal(data.sourceStatus.githubBranches,2);
  assert.equal(data.sourceStatus.githubBlog,false);
  assert.equal(data.sourceStatus.cloudflareBlog,true);
  assert.ok(data.updates.length>0);
  assert.ok(data.available.includes('workshop'));
  assert.ok(!data.available.includes('GitHub Blog'));
});
test('GitHub repository errors do not masquerade as RSS feed failures',async()=>{
  const data=await makeFeed(async url=>{
    if(url.includes('api.github.com'))throw Error('GitHub API rate-limited');
    return fixtures(url);
  });
  assert.equal(data.sourceStatus.githubCommits,false);
  assert.equal(data.sourceStatus.githubBranches,0);
  assert.equal(data.sourceStatus.githubBlog,true);
  assert.equal(data.updates.length,3);
 assert.equal(data.sourceStatus.fallbackUsed,true);
 assert.equal(data.sourceStatus.githubMode,'snapshot');
  assert.equal(data.partial,true);
});

test('Atom fallback parses only safe public GitHub commits',async()=>{
  const parsed=parseGitHubAtom(githubAtom);
  assert.equal(parsed.length,1);
  assert.equal(parsed[0].title,'Fix GitHub status & diagnostics');
  assert.equal(parsed[0].url,'https://github.com/kingmaker-lab/The-Workshop./commit/abcdef1234567890');
  const result=await fetchGitHubCommits(async url=>{
    if(url.includes('api.github.com'))return new Response('rate limit',{status:403});
    if(url.includes('github.com/kingmaker-lab/'))return new Response(githubAtom,{status:200});
    throw Error('Unexpected upstream '+url);
  },'main',5);
  assert.equal(result.mode,'atom');
  assert.equal(result.data.length,1);
});
test('all GitHub API requests may fail while the Atom alternative remains live',async()=>{
  const data=await makeFeed(async url=>{
    if(url.includes('api.github.com'))return new Response('rate limited',{status:429});
    if(url.includes('github.com/kingmaker-lab/'))return new Response(githubAtom,{status:200});
    return fixtures(url);
  });
  assert.equal(data.sourceStatus.githubCommits,true);
  assert.equal(data.sourceStatus.githubMode,'atom');
  assert.equal(data.sourceStatus.fallbackUsed,false);
  assert.ok(data.updates.length>=1);
  assert.ok(data.available.includes('workshop'));
});
