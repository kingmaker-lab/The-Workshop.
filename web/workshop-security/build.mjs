// Build source files into a single Cloudflare module Worker.
// npm dependencies are intentionally not required.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root=path.dirname(fileURLToPath(import.meta.url));
const read=name=>readFile(path.join(root,name));
let code=(await read('worker.mjs')).toString('utf8');
const items=[
 ['__INLINE_HTML__','index.html'],
 ['__INLINE_CSS__','styles.css'],
 ['__INLINE_JS__','app.js']
];
for(const [token,file] of items){
 if(!code.includes(token))throw Error('Missing placeholder '+token);
 code=code.replace(token,JSON.stringify((await read(file)).toString('utf8')));
}
const asset=await read('assets/argus.avif');
if(asset.length<1000||asset.subarray(4,12).toString('ascii')!=='ftypavif')throw Error('Invalid AVIF asset');
code=code.replace('__INLINE_ARGUS_AVIF__',JSON.stringify(asset.toString('base64')));
if(code.includes('__INLINE_'))throw Error('Unresolved build tokens');
const dist=path.join(root,'dist');
await mkdir(dist,{recursive:true});
await writeFile(path.join(dist,'worker.mjs'),code);
console.log('Security Division worker built, with Argus AVIF ('+asset.length+' bytes).');
