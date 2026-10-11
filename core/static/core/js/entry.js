/* Owner reference timeline: P=1100, 2.2/4.4/4.8 seconds, five 1.3s beats; gateway at 11.1s. */
(() => {
"use strict";
function mount(root) {
 const $=id=>root.querySelector(`[data-entry-id="${id}"]`);
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const sm=(a,b,x)=>{const t=clamp((x-a)/(b-a));return t*t*(3-2*t)};
const eio=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const eo=t=>1-Math.pow(1-t,3);
const lerp=(a,b,t)=>a+(b-a)*t;
const P=1100;
/* timeline (seconds) */
const A_END=2.2,B_END=4.4,SWAP=4.4,P0=4.8,PER=1.3,HOLD=.8,NP=5,Z0=-600,ZSTEP=650;
const T_FINAL=P0+(NP-1)*PER+HOLD+.3, T_END=T_FINAL+1.4;
const captions=[...$('captions').children];
const CAPSX=[[.3,2,captions[0].innerHTML],[2.3,4.1,captions[1].innerHTML]];
const el={entry:root,world:$('world'),room:$('room'),scr:$('scr'),glass:$('glass'),bloom:$('bloom'),cap:$('cap'),fin:$('final'),prog:$('progbar'),fx:$('fx'),wall:$('wall'),lamp:$('lamp'),char:$('char'),mug:$('mug')};
const panels=[...root.querySelectorAll('.panel')];
panels.forEach((panel,i)=>{panel.style.zIndex=String(NP-i);});
let vw=innerWidth,vh=innerHeight,W=560,Hs=350,y0=-40,fzFill=600,ez=254,Wp=0,Hp=0;
let projection=[];
const leaves=[el.wall,$('desk'),el.lamp,el.char,el.scr,root.querySelector('.base'),el.mug,...panels].filter(Boolean);
const originalStyles=leaves.map(node=>({node,transform:node.style.transform,origin:node.style.transformOrigin}));
const canProject=typeof DOMMatrix!=='undefined';
const fzOf=i=>ez-(Z0-ZSTEP*i);

function measure(){
  vw=innerWidth;vh=innerHeight;
  W=Math.min(vw*.62,560,vh*.72);Hs=W*.625;y0=-vh*.08;
  const s=el.entry.style;s.setProperty('--W',W+'px');s.setProperty('--Hs',Hs+'px');s.setProperty('--y0',y0+'px');s.setProperty('--yb',(y0+Hs/2)+'px');
  const inner=W*(1-.048),innerH=Hs*(1-.048);
  const fill=Math.max(vw/inner,vh/innerH)*1.03;
  fzFill=P*(1-1/fill);
  const pw=Math.min(vw*.86,640);ez=P*(1-1/Math.min(1.5,Math.max(1,vw*.92/pw)));
  const dpr=Math.min(devicePixelRatio||1,2);el.fx.width=vw*dpr;el.fx.height=vh*dpr;
  if(canProject)measureProjection();
}

// Bake the shared camera into each visual plane. Static viewport/room parents
// no longer acquire changing projected bounds; the original scene coordinates
// and vanishing point are retained. Geometry is read only on mount/resize.
function localMatrix(node){
  const style=getComputedStyle(node),origin=style.transformOrigin.split(' ').map(Number.parseFloat);
  const transform=style.transform==='none'?new DOMMatrix():new DOMMatrix(style.transform);
  return {origin,matrix:new DOMMatrix().translate(...origin).multiply(transform).translate(...origin.map(v=>-v))};
}
function ancestorMatrix(node){
  if(node===root)return new DOMMatrix();
  return ancestorMatrix(node.parentElement).translate(node.offsetLeft,node.offsetTop).multiply(localMatrix(node).matrix);
}
function measureProjection(){
  for(const saved of originalStyles){saved.node.style.transform=saved.transform;saved.node.style.transformOrigin=saved.origin;}
  projection=leaves.map(node=>{
    const local=localMatrix(node),anchor=ancestorMatrix(node.parentElement).translate(node.offsetLeft,node.offsetTop);
    node.style.transformOrigin='0 0';
    return {node,anchor,inverse:anchor.inverse(),local:local.matrix,anchored:anchor.multiply(local.matrix),origin:local.origin};
  });
}
function project(c,t){
  const perspective=new DOMMatrix([1,0,0,0,0,1,0,0,0,0,1,-1/P,0,0,0,1]);
  const view=new DOMMatrix().translate(vw/2,vh/2).multiply(perspective)
    .translate(-c.cx,-c.cy,c.fz).rotateAxisAngle(1,0,0,c.pitch)
    .rotateAxisAngle(0,1,0,c.yaw).translate(-vw/2,-vh/2);
  for(const plane of projection){
    // Invisible planes retain their geometry but need no matrix/style work.
    // Recompute on re-entry (including deterministic backwards seek).
    if(panels.includes(plane.node) ? t<B_END-.4 : t>=B_END+.8)continue;
    let local=plane.local;
    if(plane.node===el.scr){const origin=plane.origin;
      local=new DOMMatrix().translate(...origin).rotateAxisAngle(1,0,0,c.tilt).translate(...origin.map(v=>-v));
    }
    const anchored=plane.node===el.scr?plane.anchor.multiply(local):plane.anchored;
    plane.node.style.transform=plane.inverse.multiply(view).multiply(anchored).toString();
  }
}

/* typed code on the laptop screen */
let LINES=[],PLAIN=[];
function buildLines(){
  LINES=['<span class="k">from</span> django.db <span class="k">import</span> models','','<span class="k">class</span> <span class="f">Site</span>(models.Model):','    brand = models.<span class="f">CharField</span>(<span class="s">"..."</span>)','    goal  = models.<span class="f">TextField</span>()','','<span class="c">'+$('code-comment').textContent+'</span>','<span class="k">def</span> <span class="f">build</span>(idea):','    design = sketch(idea)','    <span class="k">return</span> ship(test(code(design)))'];
  PLAIN=LINES.map(l=>l.replace(/<[^>]+>/g,''));
}
buildLines();
let lastTyped=-1;
function typed(t){
  const total=PLAIN.join('\n').length;
  const n=Math.floor(clamp((t-.2)/(3.8-.2))*total);
  if(n===lastTyped)return;lastTyped=n;
  let left=n,out='<div class="tb"><i></i><i></i><i></i></div>';
  for(let i=0;i<LINES.length;i++){
    const len=PLAIN[i].length+1;
    if(left<=0){out+='<div class="ln"></div>';continue}
    if(left>=len){out+='<div class="ln">'+LINES[i]+'</div>';left-=len;continue}
    // partial line: re-highlight the visible slice plainly
    out+='<div class="ln cur">'+PLAIN[i].slice(0,left).replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</div>';left=0;
  }
  el.glass.innerHTML=out;
}


/* camera as a pure function of time */
function camera(t){
  let fz=0,cx=0,cy=0,yaw=0,pitch=0,tilt=8;
  if(t<A_END){const k=eo(t/A_END);fz=lerp(0,150,k);yaw=lerp(-9,-3,k);pitch=lerp(2.5,1.5,k);cy=0;tilt=8}
  else if(t<B_END){const k=eio((t-A_END)/(B_END-A_END));fz=lerp(150,fzFill,k);cy=lerp(0,y0,k);yaw=lerp(-3,0,k);pitch=lerp(1.5,0,k);tilt=lerp(8,0,k)}
  else if(t<P0){const k=eio((t-B_END)/(P0-B_END));fz=lerp(fzFill,fzOf(0),k);cy=y0;tilt=0}
  else{
    tilt=0;cy=y0*(1-sm(P0,P0+1.2,t));
    const u=t-P0;let i=Math.min(NP-1,Math.floor(u/PER)),r=u-i*PER;
    if(u>=NP*PER){fz=fzOf(NP-1)+sm(0,1,(t-(P0+(NP-1)*PER+HOLD))/1.4)*260}
    else if(r<HOLD||i===NP-1){fz=fzOf(i)+(r<HOLD?(r/HOLD)*30:30)}
    else{const k=eio((r-HOLD)/(PER-HOLD));fz=lerp(fzOf(i)+30,fzOf(i+1),k)}
    const k=clamp(vw/1100,.12,1);yaw=Math.sin(t*.7)*1.6*k;pitch=Math.cos(t*.6)*.9*k;cx=Math.sin(t*.5)*22*k;
  }
  return {fz,cx,cy,yaw,pitch,tilt};
}

/* particles */
const ctx=el.fx.getContext('2d');
let seed=7;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647};
const PT=Array.from({length:200},()=>({x:(rnd()-.5)*2200,y:(rnd()-.5)*1500,z:-rnd()*4600+150,c:rnd()<.5?'255,150,70':rnd()<.5?'255,190,90':'140,180,255',r:rnd()*1.6+.6}));
const DUST=Array.from({length:50},()=>({x:rnd(),y:rnd(),r:rnd()*1.8+.4,v:rnd()*.012+.003}));

function fx(t,c){
  const dpr=Math.min(devicePixelRatio||1,2);
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,vw,vh);
  if(t<SWAP){ // floating dust in the room
    for(const d of DUST){const x=((d.x+t*d.v*.4)%1)*vw,y=(1-((d.y+t*d.v)%1))*vh;ctx.fillStyle='rgba(255,200,130,'+(.25*(1-sm(3.5,5.5,t)))+')';ctx.beginPath();ctx.arc(x,y,d.r,0,6.3);ctx.fill()}
  }
  if(t>SWAP-.2){
    const a=sm(SWAP-.2,SWAP+.5,t);
    const dz=Math.abs(c.fz-camera(Math.max(0,t-1/60)).fz);
    for(const p of PT){
      const e=p.z+c.fz;if(e>P-60)continue;
      const s=P/(P-e),X=vw/2+(p.x-c.cx)*s,Y=vh/2+(p.y-c.cy)*s;
      if(X<-50||X>vw+50||Y<-50||Y>vh+50)continue;
      const al=a*clamp(1-Math.abs(e)/4200+.25,0,1)*(.35+.65*clamp(s/2,0,1));
      if(dz>2){const s2=P/(P-(e-dz)),X2=vw/2+(p.x-c.cx)*s2,Y2=vh/2+(p.y-c.cy)*s2;ctx.strokeStyle='rgba('+p.c+','+(al*.55)+')';ctx.lineWidth=p.r;ctx.beginPath();ctx.moveTo(X2,Y2);ctx.lineTo(X,Y);ctx.stroke()}
      ctx.fillStyle='rgba('+p.c+','+al+')';ctx.beginPath();ctx.arc(X,Y,p.r*Math.min(s,2.2),0,6.3);ctx.fill();
    }
  }

}

function render(t){
  const c=camera(t);
  if(canProject)project(c,t);
  else{el.world.style.transform='translate3d('+(-c.cx)+'px,'+(-c.cy)+'px,'+c.fz+'px) rotateX('+c.pitch+'deg) rotateY('+c.yaw+'deg)';el.scr.style.setProperty('--tilt',c.tilt+'deg');}
  typed(t);
  // Reference screen dissolve; hide the room leaves without flattening preserve-3d.
  el.room.classList.toggle('inside',t>=B_END-.05);el.scr.style.opacity=(1-sm(B_END-.1,B_END+.7,t)).toFixed(3);el.room.style.display=t<B_END+.8?'':'none';
  // Leaf depth blur omitted: owner requires transform/opacity-only motion.
  // dissolve (no flash) while passing through the screen
  el.bloom.style.opacity=0;
  // panels
  panels.forEach((p,i)=>{
    const z=Z0-ZSTEP*i,e=z+c.fz;
    const near=P*.62,far=-2500;
    let o=sm(far,far+1300,e)*(1-sm(near-120,near+120,e));
    if(t<B_END-.4)o=0;
    p.style.opacity=o.toFixed(3);
  });
  fx(t,c);
  // captions
  let cap=null;for(const k of CAPSX)if(t>=k[0]&&t<k[1])cap=k;
  if(cap){if(el.cap.innerHTML!==cap[2])el.cap.innerHTML=cap[2];el.cap.classList.add('on')}else el.cap.classList.remove('on');
  // final card
  const fa=sm(T_FINAL,T_FINAL+.9,t);el.fin.style.opacity=fa.toFixed(3);el.fin.classList.toggle('on',fa>.5);el.fin.inert=fa<=.5;el.fin.setAttribute('aria-hidden',fa>.5?'false':'true');
  el.prog.style.transform='scaleX('+clamp(t/T_FINAL)+')';
  clockLeaves(t);
}


const phases=[[".grain",0],[".forearm",0],[".hand2",0],[".head",0],[".mug i:first-child",0],[".mug i:nth-child(2)",.9]]
 .map(([selector,offset])=>({leaf:root.querySelector(selector),offset,room:selector!=='.grain'}));
function clockLeaves(t){
 for(const {leaf,offset,room} of phases){if(leaf&&(!room||t<B_END+.8))leaf.style.animationDelay=(offset-t)+"s";}
 const cursor=root.querySelector(".cur");if(cursor)cursor.style.setProperty("--entry-cursor-time",(-t)+"s");
}
return {measure,render,T_END,T_FINAL,camera};
}
function start(payload) {
 if(typeof DOMMatrix==='undefined')return false;
 const holder=document.createElement('template');
 holder.innerHTML=payload.html;
 const root=holder.content.firstElementChild;
 if(!root||root.id!=='rvion-entry'||document.getElementById(root.id))return false;
 root.dir=document.documentElement.dir;
 root.dataset.entryTheme=document.documentElement.dataset.theme || (window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
 const previous=document.activeElement;
 const background=[...document.body.children].filter(node=>!['SCRIPT','STYLE','LINK'].includes(node.tagName));
 const saved=background.map(node=>({node,inert:node.inert,hidden:node.getAttribute('aria-hidden')}));
 let closed=false,frame=0,time=0,paused=false,last=0,timeline;
 const skip=root.querySelector('[data-entry-id="skip"]');
 const pp=root.querySelector('[data-entry-id="pp"]');
 const close=()=>{
   if(closed)return;closed=true;cancelAnimationFrame(frame);
   document.removeEventListener('keydown',keyboard,true);
   document.removeEventListener('visibilitychange',visibility);
   window.removeEventListener('resize',resize);
   window.removeEventListener('pagehide',close);
   motion.removeEventListener?.('change',motionChange);
   root.remove();
   for(const state of saved){state.node.inert=state.inert;if(state.hidden===null)state.node.removeAttribute('aria-hidden');else state.node.setAttribute('aria-hidden',state.hidden);}
   if(previous?.isConnected)previous.focus({preventScroll:true});
   document.dispatchEvent(new Event('rvion:entry-closed'));
 };
 const keyboard=event=>{
   if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();close();return;}
   if(event.key!=='Tab')return;
   const controls=[...root.querySelectorAll('button:not([disabled]),a[href]')].filter(node=>!node.closest('[inert]')&&node.getClientRects().length);
   const first=controls[0],lastControl=controls[controls.length-1];
   if(event.shiftKey&&(document.activeElement===first||!root.contains(document.activeElement))){event.preventDefault();lastControl?.focus();}
   else if(!event.shiftKey&&(document.activeElement===lastControl||!root.contains(document.activeElement))){event.preventDefault();first?.focus();}
 };
 const tick=now=>{
   if(closed||paused||document.hidden)return;
   time=Math.min(timeline.T_END,time+Math.min(.05,(now-last)/1000));last=now;
   try{timeline.render(time);}catch(error){close();return;}
   if(time<timeline.T_END)frame=requestAnimationFrame(tick);else pp.disabled=true;
 };
 const resume=()=>{last=performance.now();if(!closed&&!paused&&time<timeline.T_END&&!document.hidden)frame=requestAnimationFrame(tick);};
 const visibility=()=>{cancelAnimationFrame(frame);resume();};
 const resize=()=>{if(!closed){timeline.measure();timeline.render(time);}};
 const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
 const motionChange=()=>{if(motion.matches)close();};
 skip.addEventListener('click',close);
 root.querySelector('[data-entry-id="enter"]').addEventListener('click',close);
 root.querySelectorAll('a[href]').forEach(link=>link.addEventListener('click',close));
 pp.addEventListener('click',()=>{paused=!paused;pp.textContent=paused?pp.dataset.resume:pp.dataset.pause;pp.setAttribute('aria-pressed',String(paused));cancelAnimationFrame(frame);if(!paused)resume();});
 root.addEventListener('wheel',event=>{if(!event.target.closest('.final'))event.preventDefault();},{passive:false});
 root.addEventListener('touchmove',event=>{if(!event.target.closest('.final'))event.preventDefault();},{passive:false});
 document.body.append(root);
 try{
   timeline=mount(root);timeline.measure();
   const seek=new URLSearchParams(location.search).get('entry_seek');
   if(['localhost','127.0.0.1','[::1]'].includes(location.hostname)&&seek!==null&&Number.isFinite(Number(seek))){time=Math.min(timeline.T_END,Math.max(0,Number(seek)));paused=true;pp.textContent=pp.dataset.resume;pp.setAttribute('aria-pressed','true');}
   timeline.render(time);
   for(const state of saved){state.node.inert=true;state.node.setAttribute('aria-hidden','true');}
   document.addEventListener('keydown',keyboard,true);
   document.addEventListener('visibilitychange',visibility);
   window.addEventListener('resize',resize);
   window.addEventListener('pagehide',close);
   motion.addEventListener?.('change',motionChange);
   skip.focus({preventScroll:true});resume();return true;
 }catch(error){close();return false;}
}
async function decode(payload){
 if(typeof DecompressionStream==='undefined')throw new Error('Scene decompression unavailable');
 const bytes=Uint8Array.from(atob(payload.scene_gzip),c=>c.charCodeAt(0));
 const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
 return {...payload,html:await new Response(stream).text()};
}
window.RvionEntry={mount,start,decode};
})();
