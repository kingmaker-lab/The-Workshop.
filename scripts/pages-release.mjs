import {mkdir,readFile,writeFile,copyFile,rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';

const apps={
  'workshop-news':{
    project:'workshop-news',
    root:'sites/workshop-news',
    files:['_worker.js','index.html','styles.css','app.js','favicon.svg','fake.svg','fake-walker.css','fake-walker.js','fake-3d.svg']
  },
  'workshop-labs':{
    project:'workshop-labs',
    root:'web/workshop-labs',
    files:['_worker.js']
  },
  'wolfpack-crypto':{
    project:'wolfpack-crypto',
    root:'sites/wolfpack-crypto',
    files:[['worker.mjs','_worker.js']]
  }
};

const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const app=process.argv[2];
if(!apps[app])throw Error('Unknown app: '+app);
const meta=apps[app],releaseSha=process.env.RELEASE_SHA||process.env.GITHUB_SHA||'local';
const root=path.join('release',app),deploy=path.join(root,'deploy');
await rm(root,{recursive:true,force:true});
await mkdir(deploy,{recursive:true});

const files=[];
for(const item of meta.files){
  const [srcName,destName]=Array.isArray(item)?item:[item,item];
  const src=path.join(meta.root,srcName),dest=path.join(deploy,destName);
  const bytes=await readFile(src);
  if(!bytes.length)throw Error('Empty source: '+src);
  await copyFile(src,dest);
  files.push({source:src,dest:destName,bytes:bytes.length,sha256:sha256(bytes)});
}
files.sort((a,b)=>a.dest.localeCompare(b.dest));
const aggregate=sha256(Buffer.from(files.map(x=>x.dest+':'+x.sha256).join('\n')));
const manifest={schema:2,app,project:meta.project,commit:releaseSha,aggregate_sha256:aggregate,files};
await writeFile(path.join(root,'release-manifest.json'),JSON.stringify(manifest,null,2)+'\n');

for(const file of files){
 const current=await readFile(path.join(deploy,file.dest));
 if(sha256(current)!==file.sha256)throw Error('Artifact verification failed: '+file.dest);
}
console.log(JSON.stringify(manifest));
