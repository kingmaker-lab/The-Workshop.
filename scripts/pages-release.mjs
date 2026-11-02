import {mkdir,readFile,writeFile,copyFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';

const apps={
  'workshop-news':{project:'workshop-news',source:'web/workshop-news/_worker.js'},
  'workshop-labs':{project:'workshop-labs',source:'web/workshop-labs/_worker.js'},
  'wolfpack-crypto':{project:'wolfpack-crypto',source:'sites/wolfpack-crypto/worker.mjs'}
};
const app=process.argv[2];
if(!apps[app])throw Error('Unknown app: '+app);
const meta=apps[app],releaseSha=process.env.RELEASE_SHA||process.env.GITHUB_SHA||'local';
const source=await readFile(meta.source);
if(!source.length)throw Error('Empty source: '+meta.source);
const hash=createHash('sha256').update(source).digest('hex');
const root=path.join('release',app),deploy=path.join(root,'deploy');
await mkdir(deploy,{recursive:true});
await copyFile(meta.source,path.join(deploy,'_worker.js'));
const manifest={schema:1,app,project:meta.project,source:meta.source,commit:releaseSha,sha256:hash,bytes:source.length};
await writeFile(path.join(root,'release-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify(manifest));
