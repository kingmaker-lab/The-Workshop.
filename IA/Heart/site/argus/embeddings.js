"use strict";
// HEART_004 browser demonstration. Tiny fixed public corpus and seeded SGD;
// independent of the locally trained Python model, and no network traffic.
// The original tokenizer defines encode() before this script executes.
(() => {
  const a = document.getElementById("embedding-a");
  const b = document.getElementById("embedding-b");
  const vector = document.getElementById("embedding-vector");
  const score = document.getElementById("embedding-score");
  if (!a || !b || !vector || !score || typeof encode !== "function") return;

  const corpus = [
    "heartai neural heartai",
    "tokens de linguagem neural",
    "modelos aprendem padrões",
    "heartai aprende tokens",
    "pesquisa neural e linguagem",
    "linguagem tem padrões",
    "tokens neural tokens"
  ];
  const rows = corpus.map(encode);
  const size = typeof merges === "undefined"
    ? Math.max(258, ...rows.flat()) + 1
    : 259 + merges.length;
  const dim = 8;
  let seed = 20261030;
  const random = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const table = () => Array.from({ length: size }, () =>
    Array.from({ length: dim }, () => (random() - .5) * .12));
  const input = table();
  const context = table();
  const observed = [...new Set(rows.flat())].sort((x,y) => x-y);
  const negatives = new Map(observed.map(id => [id,observed.filter(x=>x!==id)]));
  const sigmoid = x => x >= 0 ? 1/(1+Math.exp(-x)) : Math.exp(x)/(1+Math.exp(x));
  function update(center,target,label) {
    let dot=0;
    for(let d=0;d<dim;d++) dot+=input[center][d]*context[target][d];
    const gradient=(sigmoid(dot)-label)*.075;
    for(let d=0;d<dim;d++){
      const x=input[center][d], y=context[target][d];
      input[center][d]-=gradient*y;
      context[target][d]-=gradient*x;
    }
  }
  for(let epoch=0;epoch<14;epoch++){
    for(const row of rows){
      for(let i=0;i<row.length;i++){
        for(let j=Math.max(0,i-2);j<Math.min(row.length,i+3);j++){
          if(i===j)continue;
          const center=row[i],target=row[j];
          update(center,target,1);
          const options=negatives.get(target);
          if(options.length)update(center,options[Math.floor(random()*options.length)],0);
        }
      }
    }
  }
  function pool(text){
    // Limit the amount of user input processed even if DOM limits are bypassed.
    const tokens=encode(text.slice(0,180)).filter(id=>id>=0&&id<size);
    if(!tokens.length)return Array(dim).fill(0);
    return Array.from({length:dim},(_,d)=>
      tokens.reduce((sum,id)=>sum+input[id][d],0)/tokens.length);
  }
  function cosine(x,y){
    const dot=x.reduce((sum,v,i)=>sum+v*y[i],0);
    const norm=Math.sqrt(x.reduce((s,v)=>s+v*v,0)*y.reduce((s,v)=>s+v*v,0));
    return norm===0?0:Math.max(-1,Math.min(1,dot/norm));
  }
  function render(){
    const first=pool(a.value),second=pool(b.value);
    vector.textContent="[ "+first.map(n=>n.toFixed(4)).join(", ")+" ]";
    score.textContent="Similaridade de cosseno: "+cosine(first,second).toFixed(4)+
      "  |  Dimensões: "+dim+"  |  Treino: corpus demonstrativo fixo";
  }
  a.addEventListener("input",render);
  b.addEventListener("input",render);
  render();
})();
