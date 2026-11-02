/* Fake Walker. Isolated progressive enhancement; no dependency on News app state. */
(() => {
  'use strict';
  const root=document.getElementById('fake-walker');
  const character=document.getElementById('fw-character');
  const bubble=document.getElementById('fw-bubble');
  const hide=document.getElementById('fw-hide');
  const restore=document.getElementById('fake-walker-toggle');
  if(!root||!character||!bubble||!hide||!restore)return;
  const storageKey='workshop-news-fake-walker-hidden-v1';
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  const phrases=['E aí, galera! Fake na área! 💜','Notícia boa tem fonte! 👀','Tem novidade na bancada!','Bora investigar o que mudou?','Desconfie, pesquise, descubra. ✦'];
  let x=16,direction=1,lastTime=0,frame=0,pauseUntil=0,speakingUntil=0,hover=false,visible=true;
  const isCompact=()=>window.innerWidth<=760;
  const minX=()=>12;
  const maxX=()=>Math.max(minX(),window.innerWidth-root.offsetWidth-12);
  function place(){x=Math.max(minX(),Math.min(maxX(),x));root.style.left=x+'px';}
  function say(message){
    if(!visible)return;
    bubble.textContent=message;
    bubble.hidden=false;
    speakingUntil=performance.now()+3000;
  }
  function stop(){if(frame)cancelAnimationFrame(frame);frame=0;root.dataset.moving='false';lastTime=0;}
  function shouldMove(){return visible&&!reduced.matches&&!isCompact()&&!document.hidden;}
  function tick(time){
    frame=0;
    if(!shouldMove()){stop();return;}
    const dt=lastTime?Math.min(45,time-lastTime):16;
    lastTime=time;
    if(time>=speakingUntil)bubble.hidden=true;
    const paused=hover||time<pauseUntil;
    if(!paused){
      x+=direction*0.052*dt;
      if(x>=maxX()){x=maxX();direction=-1;pauseUntil=time+1200;}
      if(x<=minX()){x=minX();direction=1;pauseUntil=time+1200;}
      place();
    }
    root.dataset.facing=direction<0?'left':'right';
    root.dataset.moving=String(!paused);
    frame=requestAnimationFrame(tick);
  }
  function run(){if(shouldMove()&&!frame)frame=requestAnimationFrame(tick);else if(!shouldMove())stop();}
  function setVisible(next){
    visible=next;root.hidden=!next;restore.hidden=next;
    if(!next){stop();bubble.hidden=true;}else{place();run();}
    try{window.localStorage.setItem(storageKey,next?'0':'1');}catch{}
  }
  try{if(window.localStorage.getItem(storageKey)==='1')setVisible(false);}catch{}
  character.addEventListener('click',()=>{say('Bora pro Fake’s Corner! ✦');document.getElementById('fake-corner')?.scrollIntoView({behavior:reduced.matches?'auto':'smooth',block:'start'});pauseUntil=performance.now()+3000;});
  character.addEventListener('mouseenter',()=>{hover=true;say('Fui pego no flagra! 😼');});
  character.addEventListener('mouseleave',()=>{hover=false;pauseUntil=performance.now()+900;});
  character.addEventListener('focus',()=>{hover=true;});
  character.addEventListener('blur',()=>{hover=false;pauseUntil=performance.now()+700;});
  hide.addEventListener('click',()=>setVisible(false));
  restore.addEventListener('click',()=>{setVisible(true);say('Voltei! Sentiu saudade? 💜');});
  document.addEventListener('visibilitychange',run);
  reduced.addEventListener('change',run);
  window.addEventListener('resize',()=>{place();run();});
  window.setInterval(()=>{
    if(!visible||!shouldMove()||hover)return;
    pauseUntil=performance.now()+2600;
    if(Math.random()>.38)say(phrases[Math.floor(Math.random()*phrases.length)]);
  },11500);
  place();run();
})();
