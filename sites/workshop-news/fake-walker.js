/* Fake 4D. Progressive enhancement; never owns News data or blocks card interaction. */
(() => {
  'use strict';

  const root=document.getElementById('fake-walker');
  const character=document.getElementById('fw-character');
  const bubble=document.getElementById('fw-bubble');
  const hide=document.getElementById('fw-hide');
  const pause=document.getElementById('fw-pause');
  const restore=document.getElementById('fake-walker-toggle');
  if(!root||!character||!bubble||!hide||!pause||!restore)return;

  const hiddenKey='workshop-news-fake-walker-hidden-v1';
  const pausedKey='workshop-news-fake-4d-paused-v1';
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  const plans=[
    {selector:'.news-item',action:'point'},
    {selector:'.highlight-card',action:'climb'},
    {selector:'.activity-item',action:'peek'},
    {selector:'.lab-links a',action:'sit'}
  ];

  let x=18;
  let y=0;
  let direction=1;
  let visible=true;
  let paused=false;
  let hover=false;
  let busy=false;
  let frame=0;
  let lastTime=0;
  let bubbleUntil=0;
  let bubbleTimer=0;
  let scheduleTimer=0;
  let planIndex=0;
  let targetIndex=0;
  let generation=0;
  let anchor=null;
  let scrollFrame=0;

  const compact=()=>window.innerWidth<=760;
  const mainLeft=()=>{
    const shell=document.querySelector('.main-shell');
    return Math.max(8,Math.round(shell?.getBoundingClientRect().left||0)+8);
  };
  const width=()=>root.offsetWidth||116;
  const height=()=>root.offsetHeight||154;
  const minX=()=>mainLeft();
  const maxX=()=>Math.max(minX(),window.innerWidth-width()-8);
  const maxY=()=>Math.max(8,window.innerHeight-height()-6);
  const dockY=()=>maxY();

  function clamp(value,min,max){return Math.max(min,Math.min(max,value));}
  function place(nx=x,ny=y){
    x=clamp(nx,minX(),maxX());
    y=clamp(ny,8,maxY());
    root.style.transform=`translate3d(${Math.round(x)}px,${Math.round(y)}px,0)`;
  }
  function setFacing(next){direction=next<0?-1:1;root.dataset.facing=direction<0?'left':'right';}
  function setAction(action,moving=false){
    root.dataset.action=action;
    root.dataset.moving=String(Boolean(moving));
  }
  function setPassThrough(next){root.dataset.passThrough=String(Boolean(next));}
  function say(message,duration=3100){
    if(!visible)return;
    bubble.textContent=String(message||'').slice(0,110);
    bubble.hidden=false;
    bubbleUntil=performance.now()+duration;
    if(bubbleTimer)window.clearTimeout(bubbleTimer);
    bubbleTimer=window.setTimeout(()=>{bubble.hidden=true;bubbleTimer=0;},duration);
  }
  function updateBubble(now){
    if(!bubble.hidden&&now>=bubbleUntil)bubble.hidden=true;
  }
  function clearSchedule(){if(scheduleTimer)window.clearTimeout(scheduleTimer);scheduleTimer=0;}
  function stopFrame(){if(frame)cancelAnimationFrame(frame);frame=0;lastTime=0;}
  function shouldAnimate(){return visible&&!paused&&!reduced.matches&&!document.hidden;}
  function canInteract(){return shouldAnimate()&&!busy&&!hover;}

  function resetToDock(action=shouldAnimate()?'walk':'idle'){
    anchor=null;
    setPassThrough(false);
    setAction(action,action==='walk');
    place(x,dockY());
  }

  function cancelActive(){
    generation+=1;
    busy=false;
    anchor=null;
    clearSchedule();
    setPassThrough(false);
  }

  function walkTick(time){
    frame=0;
    updateBubble(time);
    if(shouldAnimate()&&!busy&&root.dataset.action==='walk'&&!hover){
      const dt=lastTime?Math.min(48,time-lastTime):16;
      lastTime=time;
      const speed=(compact()?0.025:0.043)*dt;
      x+=direction*speed;
      if(x>=maxX()){x=maxX();setFacing(-1);}
      if(x<=minX()){x=minX();setFacing(1);}
      y=dockY();
      setAction('walk',true);
      place();
    }else{
      lastTime=time;
      if(root.dataset.action==='walk')root.dataset.moving='false';
    }
    if(shouldAnimate()&&!busy)frame=requestAnimationFrame(walkTick);
    else frame=0;
  }
  function ensureFrame(){if(shouldAnimate()&&!frame&&!busy)frame=requestAnimationFrame(walkTick);}

  function visibleTargets(selector){
    return [...document.querySelectorAll(selector)].filter(node=>{
      const r=node.getBoundingClientRect();
      return r.width>80&&r.height>34&&r.bottom>76&&r.top<window.innerHeight-24&&r.right>minX()+20&&r.left<window.innerWidth-20;
    });
  }
  function targetLabel(target){
    const node=target.querySelector?.('.news-title,.highlight-title,.activity-title,strong')||target;
    return String(node?.textContent||'').replace(/\s+/g,' ').trim().slice(0,58);
  }
  function pickPlan(){
    for(let attempt=0;attempt<plans.length;attempt++){
      const plan=plans[planIndex%plans.length];
      planIndex+=1;
      const targets=visibleTargets(plan.selector);
      if(!targets.length)continue;
      const target=targets[targetIndex%targets.length];
      targetIndex+=1;
      return {...plan,target};
    }
    return null;
  }

  function sideFor(rect){
    const roomLeft=rect.left-minX();
    const roomRight=window.innerWidth-rect.right;
    return roomRight>=width()+12||roomRight>=roomLeft?'right':'left';
  }
  function anchorPoint(target,mode){
    const r=target.getBoundingClientRect();
    const w=width(),h=height();
    const side=sideFor(r);
    if(mode==='point'){
      const onRight=side==='right';
      return {
        x:onRight?r.right+5:r.left-w-5,
        y:clamp(r.top+Math.min(44,r.height*.22),8,maxY()),
        facing:onRight?-1:1
      };
    }
    if(mode==='sit'){
      const rawX=r.left+Math.min(Math.max(12,r.width*.58),Math.max(12,r.width-w-8));
      return {x:clamp(rawX,minX(),maxX()),y:clamp(r.top-h+25,8,maxY()),facing:r.left+r.width/2<window.innerWidth/2?1:-1};
    }
    if(mode==='peek'){
      const onRight=side==='right';
      return {
        x:onRight?r.right-w*.36:r.left-w*.64,
        y:clamp(r.top+Math.min(30,r.height*.14),8,maxY()),
        facing:onRight?-1:1
      };
    }
    return {x,y,facing:direction};
  }
  function climbPoints(target){
    const r=target.getBoundingClientRect();
    const side=sideFor(r);
    const onRight=side==='right';
    const edgeX=onRight?r.right-width()*.55:r.left-width()*.45;
    return {
      start:{x:edgeX,y:clamp(r.bottom-height()+18,8,maxY()),facing:onRight?-1:1},
      top:{x:edgeX,y:clamp(r.top-height()+28,8,maxY()),facing:onRight?-1:1}
    };
  }

  function moveTo(nx,ny,duration,token,action='walk'){
    return new Promise(resolve=>{
      const sx=x,sy=y;
      const dx=clamp(nx,minX(),maxX())-sx;
      const dy=clamp(ny,8,maxY())-sy;
      if(Math.abs(dx)>2)setFacing(dx<0?-1:1);
      const start=performance.now();
      setAction(action,true);
      setPassThrough(true);
      const step=now=>{
        if(token!==generation||!visible||paused||reduced.matches){resolve(false);return;}
        const p=clamp((now-start)/Math.max(1,duration),0,1);
        const eased=1-Math.pow(1-p,3);
        place(sx+dx*eased,sy+dy*eased);
        updateBubble(now);
        if(p<1)requestAnimationFrame(step);
        else{root.dataset.moving='false';resolve(true);}
      };
      requestAnimationFrame(step);
    });
  }
  function wait(ms,token){
    return new Promise(resolve=>window.setTimeout(()=>resolve(token===generation&&shouldAnimate()),ms));
  }
  function alive(token,target){return token===generation&&shouldAnimate()&&document.contains(target);}

  async function pointAt(target,token){
    const spot=anchorPoint(target,'point');
    if(!await moveTo(spot.x,spot.y,850,token,'walk')||!alive(token,target))return false;
    setFacing(spot.facing);setAction('point');setPassThrough(true);anchor={target,mode:'point'};
    const label=targetLabel(target);
    say(label?`👀 No radar: ${label}`:'👀 Essa aqui entrou no radar.');
    return wait(compact()?2200:3000,token);
  }
  async function climbCard(target,token){
    const points=climbPoints(target);
    if(!await moveTo(points.start.x,points.start.y,850,token,'walk')||!alive(token,target))return false;
    setFacing(points.start.facing);
    if(!await moveTo(points.top.x,points.top.y,1350,token,'climb')||!alive(token,target))return false;
    const sit=anchorPoint(target,'sit');
    setFacing(sit.facing);place(sit.x,sit.y);setAction('sit');setPassThrough(true);anchor={target,mode:'sit'};
    say('Escalar card conta como jornalismo? 😼');
    return wait(compact()?2400:3400,token);
  }
  async function sitOn(target,token){
    const spot=anchorPoint(target,'sit');
    if(!await moveTo(spot.x,spot.y,950,token,'walk')||!alive(token,target))return false;
    setFacing(spot.facing);setAction('sit');setPassThrough(true);anchor={target,mode:'sit'};
    say('Boa vista daqui. Fonte primeiro, hype depois. ✦');
    return wait(compact()?2300:3300,token);
  }
  async function peekAt(target,token){
    const spot=anchorPoint(target,'peek');
    if(!await moveTo(spot.x,spot.y,900,token,'walk')||!alive(token,target))return false;
    setFacing(spot.facing);setAction('peek');setPassThrough(true);anchor={target,mode:'peek'};
    say('Só conferindo o que saiu da bancada... 👀');
    return wait(compact()?2100:3000,token);
  }

  async function interact(plan){
    if(!plan||!canInteract())return;
    busy=true;
    const token=generation;
    let stayed=false;
    try{
      if(plan.action==='point')stayed=await pointAt(plan.target,token);
      else if(plan.action==='climb')stayed=await climbCard(plan.target,token);
      else if(plan.action==='sit')stayed=await sitOn(plan.target,token);
      else if(plan.action==='peek')stayed=await peekAt(plan.target,token);
      if(token!==generation)return;
      anchor=null;
      if(stayed&&shouldAnimate()){
        setPassThrough(true);
        await moveTo(x,dockY(),compact()?650:900,token,'walk');
      }
    }finally{
      if(token===generation){
        busy=false;
        setPassThrough(false);
        resetToDock();
        scheduleNext();
      }
    }
  }

  function scheduleNext(delay=compact()?12500:8200){
    clearSchedule();
    if(!shouldAnimate())return;
    scheduleTimer=window.setTimeout(()=>{
      scheduleTimer=0;
      if(!canInteract()){scheduleNext(2600);return;}
      const plan=pickPlan();
      if(plan)void interact(plan);
      else scheduleNext(4200);
    },delay);
  }

  function syncAnchor(){
    scrollFrame=0;
    if(!anchor||!visible||paused||reduced.matches||!document.contains(anchor.target))return;
    const spot=anchorPoint(anchor.target,anchor.mode);
    setFacing(spot.facing);place(spot.x,spot.y);
  }
  function queueAnchorSync(){
    if(anchor&&!scrollFrame)scrollFrame=requestAnimationFrame(syncAnchor);
  }

  function setPaused(next,userInitiated=true){
    paused=Boolean(next);
    if(userInitiated){try{localStorage.setItem(pausedKey,paused?'1':'0');}catch{}}
    pause.setAttribute('aria-pressed',String(paused));
    pause.setAttribute('aria-label',paused?'Retomar animações do Fake':'Pausar animações do Fake');
    pause.title=paused?'Retomar Fake':'Pausar Fake';
    pause.textContent=paused?'▶':'Ⅱ';
    cancelActive();
    if(paused||reduced.matches){
      setAction('idle');setPassThrough(false);place(x,dockY());
      if(userInitiated&&paused)say('Modo estátua ativado. Prometo me comportar. 😇',2200);
    }else{
      resetToDock('walk');ensureFrame();scheduleNext(2600);
      if(userInitiated)say('Voltei a circular pela redação! ✦',2200);
    }
  }
  function setVisible(next){
    visible=Boolean(next);
    root.hidden=!visible;restore.hidden=visible;
    cancelActive();
    if(!visible){bubble.hidden=true;if(bubbleTimer)window.clearTimeout(bubbleTimer);bubbleTimer=0;stopFrame();}
    else{place(x,dockY());ensureFrame();if(shouldAnimate()){setAction('walk');scheduleNext(2600);}else setAction('idle');}
    try{localStorage.setItem(hiddenKey,visible?'0':'1');}catch{}
  }

  try{paused=localStorage.getItem(pausedKey)==='1';}catch{}
  try{if(localStorage.getItem(hiddenKey)==='1')visible=false;}catch{}
  pause.setAttribute('aria-pressed',String(paused));
  pause.textContent=paused?'▶':'Ⅱ';
  root.hidden=!visible;restore.hidden=visible;
  place(x,dockY());
  setAction(shouldAnimate()?'walk':'idle');
  ensureFrame();
  scheduleNext(4200);

  character.addEventListener('click',()=>{
    cancelActive();say('Bora pro Fake’s Corner! ✦');
    document.getElementById('fake-corner')?.scrollIntoView({behavior:reduced.matches?'auto':'smooth',block:'start'});
    resetToDock(shouldAnimate()?'walk':'idle');scheduleNext(5200);
  });
  character.addEventListener('mouseenter',()=>{hover=true;if(!busy)say('Fui pego no flagra! 😼',1900);});
  character.addEventListener('mouseleave',()=>{hover=false;if(shouldAnimate()&&!busy)scheduleNext(2600);});
  character.addEventListener('focus',()=>{hover=true;});
  character.addEventListener('blur',()=>{hover=false;if(shouldAnimate()&&!busy)scheduleNext(2400);});
  hide.addEventListener('click',()=>setVisible(false));
  pause.addEventListener('click',()=>setPaused(!paused));
  restore.addEventListener('click',()=>{setVisible(true);say('Voltei! Sentiu saudade? 💜',2400);});

  document.addEventListener('visibilitychange',()=>{
    cancelActive();
    if(document.hidden){setAction('idle');stopFrame();}
    else{resetToDock(shouldAnimate()?'walk':'idle');ensureFrame();scheduleNext(3000);}
  });
  reduced.addEventListener('change',()=>{
    cancelActive();
    resetToDock(reduced.matches?'idle':paused?'idle':'walk');
    if(reduced.matches||paused)stopFrame();
    else{ensureFrame();scheduleNext(3000);}
  });
  window.addEventListener('resize',()=>{
    if(anchor)queueAnchorSync();
    else place(x,dockY());
    if(shouldAnimate()&&!busy)scheduleNext(3200);
  },{passive:true});
  window.addEventListener('scroll',queueAnchorSync,{passive:true});
})();
