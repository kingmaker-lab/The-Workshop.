import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
test('Argus is linked without removing the CTF or Oni',async()=>{
 const html=(await readFile(path.join(base,'index.html'))).toString();
 const css=(await readFile(path.join(base,'styles.css'))).toString();
 assert.match(html,/id="argus"/);
 assert.match(html,/src="\/assets\/argus\.avif"/);
 assert.match(html,/alt="Arte oficial do Argus/);
 for(const marker of ['id="missoes"','id="ranking"','id="flagForm"','class="host-card"'])assert.ok(html.includes(marker),marker);
 assert.match(css,/\.argus-figure img/);
});
test('The asset exists in AVIF format, and build handles same-origin route',async()=>{
 const raw=await readFile(path.join(base,'assets/argus.avif'));
 assert.ok(raw.length>30000);
 assert.equal(raw.subarray(4,12).toString('ascii'),'ftypavif');
 const source=(await readFile(path.join(base,'worker.mjs'))).toString();
 assert.match(source,/p==='\/assets\/argus\.avif'/);
 assert.match(source,/img-src 'self'/);
 execFileSync(process.execPath,[path.join(base,'build.mjs')],{stdio:'pipe'});
 const dist=(await readFile(path.join(base,'dist/worker.mjs'))).toString();
 assert.ok(!dist.includes('__INLINE_'));
 assert.match(dist,/image\/avif/);
});
