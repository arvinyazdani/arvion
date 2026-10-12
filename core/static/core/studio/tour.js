/* Bounded chapter gestures; native scrolling everywhere outside this scene. */
function studioEligibility({reduced,saveData,cores,memory}) {
  return !reduced&&!saveData&&!(cores&&cores<=2)&&!(memory&&memory<=2);
}
function studioProgress(top,height,viewport){return Math.max(0,Math.min(1,-top/Math.max(1,height-viewport)));}
function studioStep(top,stepHeight,header,count){return Math.max(0,Math.min(count-1,Math.round((header-top)/Math.max(1,stepHeight))));}
function createStudioGestureGate(duration=1000,quiet=220){
 let until=0,lastWheel=-Infinity;
 return {
  busy:now=>now<until,
  begin(now){if(now<until)return false;until=now+duration;return true},
  wheel(now){const continuing=now-lastWheel<quiet;lastWheel=now;return now>=until&&!continuing},
  cancel(){until=0;lastWheel=-Infinity},
 };
}
function createStudioWorker(canvas,asset,options,onFailure){
 const worker=new Worker(asset+'render-worker.js?v=1');
 let closed=false,settled=false,intersecting=true,latest={fps:0,frames:0,quality:0},rejectReady;
 const send=(message,transfer=[])=>{if(!closed)worker.postMessage(message,transfer)};
 const viewport=()=>({width:canvas.clientWidth,height:canvas.clientHeight,dpr:devicePixelRatio||1});
 const size=()=>send({type:'size',viewport:viewport()});
 const visible=()=>send({type:'visible',value:intersecting&&!document.hidden});
 const pointer=event=>{if(event.pointerType==='touch')return;const r=canvas.getBoundingClientRect();send({type:'pointer',x:(event.clientX-r.left)/r.width-.5,y:(event.clientY-r.top)/r.height-.5});};
 const observer=typeof IntersectionObserver!=='undefined'?new IntersectionObserver(entries=>{intersecting=entries[0].isIntersecting;visible()}):null;
 const dispose=()=>{if(closed)return;closed=true;clearTimeout(timer);observer?.disconnect();removeEventListener('resize',size);document.removeEventListener('visibilitychange',visible);canvas.parentElement.removeEventListener('pointermove',pointer);worker.terminate();if(!settled){settled=true;rejectReady(new Error('renderer-cancelled'));}};
 const fail=()=>{if(closed)return;const wasReady=settled;dispose();if(wasReady)onFailure();};
 const timer=setTimeout(fail,20000);
 const ready=new Promise((resolve,reject)=>{
  rejectReady=reject;
  worker.onerror=event=>{event.preventDefault?.();fail();};
  worker.onmessage=({data})=>{
   if(closed)return;
   if(data.type==='failed'){fail();return;}
   if(data.stats)latest=data.stats;
   if(data.type==='ready'&&!settled){settled=true;clearTimeout(timer);size();visible();resolve({
    start:()=>send({type:'start'}),playIntro(){},setP:value=>send({type:'progress',value}),
    setQuality:value=>send({type:'quality',value}),stats:()=>latest,dispose,
   });}
  };
  try{const offscreen=canvas.transferControlToOffscreen();send({type:'init',canvas:offscreen,viewport:viewport(),options},[offscreen]);}
  catch(error){reject(error);settled=true;dispose();}
 });
 // Only the canvas is transferable; preferences/account data never enter this worker.
 if(!closed){observer?.observe(canvas);addEventListener('resize',size);document.addEventListener('visibilitychange',visible);canvas.parentElement.addEventListener('pointermove',pointer);}
 return{ready,dispose};
}
if(typeof module!=='undefined')module.exports={studioEligibility,studioProgress,studioStep,createStudioGestureGate,createStudioWorker};
if(typeof document!=='undefined')(()=>{
 const root=document.querySelector('[data-studio-tour]');if(!root)return;
 const canvas=root.querySelector('canvas'),poster=root.querySelector('[data-studio-poster]'),picture=poster.parentElement;
 const stops=[...root.querySelectorAll('[data-stop]')],button=root.querySelector('[data-studio-mode]');
 const chapters=[...root.querySelectorAll('.st-chapters a')];
 const motion=matchMedia('(prefers-reduced-motion: reduce)'),short=matchMedia('(max-height:620px)'),asset=root.dataset.assets;
 let engine=null,connection=null,disposed=false,booting=false,lastStop=0,scrollFrame=0,governor=0,started=0,lowWindows=0;
 const gate=createStudioGestureGate();
 let transitionFrame=0,transitionTarget=null,transitionSize=null,touch=null;
 const geometry=()=>{const rect=root.getBoundingClientRect(),height=root.querySelector('.st-viewport').offsetHeight,header=parseFloat(getComputedStyle(root).getPropertyValue('--st-header'))||0;return{rect,height,header,start:window.scrollY+rect.top-header}};
 const enabled=()=>!disposed&&!motion.matches&&!short.matches&&root.dataset.reason!=='user';
 // The real header can be a few pixels taller than its nominal CSS offset
 // after fonts/theme load. Admit the first tiny gesture, not just later ones.
 const inScene=g=>g.rect.top<=g.header+24&&g.rect.bottom>=g.header+g.height-24;
 function cancelTransition(){cancelAnimationFrame(transitionFrame);transitionFrame=0;transitionTarget=null;gate.cancel();document.documentElement.classList.remove('st-stepping');root.removeAttribute('data-transitioning');}
 function goTo(index){
  if(!enabled()||transitionTarget!==null||index<0||index>=stops.length||!gate.begin(performance.now()))return false;
  const g=geometry(),from=window.scrollY,to=Math.max(0,g.start+index*g.height),start=performance.now();
  transitionSize={height:g.height,width:root.clientWidth};
  transitionTarget=index;root.setAttribute('data-transitioning','');document.documentElement.classList.add('st-stepping');update();
  const tick=now=>{
   const t=Math.min(1,(now-start)/750),ease=t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
   window.scrollTo({top:from+(to-from)*ease,behavior:'instant'});
   if(t<1)transitionFrame=requestAnimationFrame(tick);
   else {transitionFrame=0;transitionTarget=null;document.documentElement.classList.remove('st-stepping');root.removeAttribute('data-transitioning');update();}
  };
  transitionFrame=requestAnimationFrame(tick);return true;
 }
 const ignored=target=>target.closest?.('input,textarea,select,dialog,[contenteditable="true"],[role="slider"]')||document.body.classList.contains('menu-open')||document.documentElement.classList.contains('navigation-pending');
 function wheel(event){
  if(!enabled()||event.ctrlKey||event.metaKey||event.defaultPrevented||ignored(event.target)||Math.abs(event.deltaX)>Math.abs(event.deltaY)||!event.deltaY)return;
  const g=geometry();if(!inScene(g)&&!gate.busy(performance.now()))return;
  const now=performance.now(),direction=Math.sign(event.deltaY),index=studioStep(g.rect.top,g.height,g.header,stops.length),next=index+direction;
  const admitted=gate.wheel(now);
  // Consume inertia even after the camera lands, until the gesture is quiet.
  if(!admitted||transitionTarget!==null){event.preventDefault();return;}
  if(next<0||next>=stops.length)return;
  event.preventDefault();goTo(next);
 }
 function touchStart(event){touch=event.touches.length===1&&!ignored(event.target)?{x:event.touches[0].clientX,y:event.touches[0].clientY,used:false}:null;}
 function touchMove(event){
  if(!touch||event.touches.length!==1||!enabled()||event.defaultPrevented)return;
  const dx=event.touches[0].clientX-touch.x,dy=touch.y-event.touches[0].clientY;
  if(Math.abs(dx)>Math.abs(dy)||Math.abs(dy)<8)return;
  const g=geometry();if(!inScene(g)&&!gate.busy(performance.now()))return;
  const next=studioStep(g.rect.top,g.height,g.header,stops.length)+Math.sign(dy);
  if(!touch.used&&!gate.busy(performance.now())&&(next<0||next>=stops.length))return;
  event.preventDefault();
  if(!touch.used){touch.used=true;goTo(next);}
 }
 function key(event){
  if(['Home','End','Tab'].includes(event.key)){cancelTransition();return;}
  if(!enabled()||event.defaultPrevented||event.ctrlKey||event.metaKey||event.altKey||ignored(event.target)||event.target.closest?.('button,a,summary'))return;
  const direction=({ArrowDown:1,PageDown:1,ArrowUp:-1,PageUp:-1,' ':event.shiftKey?-1:1})[event.key];if(!direction)return;
  const g=geometry();if(!inScene(g))return;
  if(gate.busy(performance.now())||event.repeat){event.preventDefault();return;}
  const next=studioStep(g.rect.top,g.height,g.header,stops.length)+direction;
  if(next>=0&&next<stops.length){event.preventDefault();goTo(next);}
 }
 addEventListener('wheel',wheel,{passive:false});addEventListener('touchstart',touchStart,{passive:true});addEventListener('touchmove',touchMove,{passive:false});
 addEventListener('hashchange',cancelTransition);addEventListener('popstate',cancelTransition);
 addEventListener('touchend',()=>{touch=null},{passive:true});addEventListener('touchcancel',()=>{touch=null},{passive:true});addEventListener('keydown',key);
 chapters.forEach((link,index)=>link.addEventListener('click',event=>{if(!enabled()||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||event.button)return;event.preventDefault();if(goTo(index))history.replaceState(null,'',link.getAttribute('href'));}));
 root.querySelector('.st-controls a')?.addEventListener('click',cancelTransition);
 function update(){scrollFrame=0;const rect=root.getBoundingClientRect(),h=root.querySelector('.st-viewport').offsetHeight,header=parseFloat(getComputedStyle(root).getPropertyValue('--st-header'))||0;
  if(short.matches){stops.forEach(stop=>{stop.inert=false});return;}
  const index=transitionTarget??studioStep(rect.top,h,header,stops.length);
  engine?.setP(index/(stops.length-1));
  stops.forEach((stop,i)=>{stop.inert=i!==index;stop.classList.toggle('is-current',i===index)});
  chapters.forEach((link,i)=>{if(i===index)link.setAttribute('aria-current','step');else link.removeAttribute('aria-current')});
  if(index!==lastStop){lastStop=index;root.dataset.stop=stops[index].dataset.stop;
   poster.src=asset+'posters/'+stops[index].dataset.stop+'-desktop.webp';picture.querySelector('[data-studio-mobile]').srcset=asset+'posters/'+stops[index].dataset.stop+'-mobile.webp';
   picture.querySelectorAll('[data-studio-format]').forEach(source=>{source.srcset=asset+'posters/'+stops[index].dataset.stop+'-'+source.dataset.studioFormat+'.avif'});}
 }
 const scroll=()=>{if(!disposed&&!scrollFrame)scrollFrame=requestAnimationFrame(update)};
 addEventListener('scroll',scroll,{passive:true});addEventListener('resize',()=>{
  // Safari's browser chrome can resize the visual viewport during a swipe.
  // Only a real stage resize/orientation change invalidates the destination.
  if(transitionTarget!==null&&(geometry().height!==transitionSize.height||root.clientWidth!==transitionSize.width))cancelTransition();
  scroll();
 });
 function fallback(reason){root.dataset.engine='static';root.dataset.reason=reason;clearInterval(governor);connection?.dispose();button.hidden=true;}
 button.addEventListener('click',()=>{cancelTransition();fallback('user')});
 motion.addEventListener('change',()=>{cancelTransition();if(motion.matches)fallback('reduced-motion')});
 short.addEventListener('change',()=>{cancelTransition();if(short.matches)fallback('short-viewport');update()});
 async function boot(){
  if(disposed||booting||root.dataset.reason||short.matches||!studioEligibility({reduced:motion.matches,saveData:navigator.connection?.saveData,cores:navigator.hardwareConcurrency,memory:navigator.deviceMemory}))return;
  booting=true;
  try{
   // Paint the poster first; worker fonts load independently. Unrelated page
   // fonts/images must not delay scene startup, especially on mobile Safari.
   await poster.decode?.().catch(()=>{});
   await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
   if(disposed||motion.matches||short.matches)return;
   if(typeof Worker==='undefined'||!canvas.transferControlToOffscreen){fallback('worker-unsupported');return;}
   const covers={};root.querySelectorAll('[data-studio-cover]').forEach(a=>{const u=new URL(a.dataset.studioCover,location.href);if(u.origin===location.origin)covers[a.dataset.coverKey]=u.href});
   connection=createStudioWorker(canvas,asset,{lite:matchMedia('(max-width:760px)').matches,rtl:document.documentElement.dir==='rtl',covers,fonts:[root.dataset.fontRegular,root.dataset.fontBold,root.dataset.fontBlack],shotIndices:[1,2,3,6]},()=>fallback('worker-failed'));
   engine=await connection.ready;
   if(disposed||motion.matches||short.matches||root.dataset.reason){engine.dispose();fallback('interrupted');return;}
   engine.playIntro();engine.start();started=performance.now();root.dataset.engine='ready';button.hidden=false;update();
   root.studioMetrics=()=>engine.stats();
   governor=setInterval(()=>{if(document.hidden||performance.now()-started<5000)return;const rect=canvas.getBoundingClientRect();if(rect.bottom<=0||rect.top>=innerHeight)return;
    const stats=engine.stats(),minimum=matchMedia('(max-width:760px)').matches?30:45;
    lowWindows=stats.fps>0&&stats.fps<minimum?lowWindows+1:0;
    if(lowWindows>=2){lowWindows=0;if(stats.quality<2)engine.setQuality(stats.quality+1);else fallback('frame-budget');}
   },3000);
  }catch(error){fallback('unavailable');}
 }
 canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();fallback('context-lost')});
 addEventListener('pagehide',()=>{disposed=true;cancelTransition();clearInterval(governor);cancelAnimationFrame(scrollFrame);removeEventListener('wheel',wheel);removeEventListener('touchstart',touchStart);removeEventListener('touchmove',touchMove);removeEventListener('keydown',key);removeEventListener('hashchange',cancelTransition);removeEventListener('popstate',cancelTransition);connection?.dispose();},{once:true});
 addEventListener('pageshow',event=>{if(event.persisted)fallback('restored-page')});
 const idle=()=>{if('requestIdleCallback'in window)requestIdleCallback(boot,{timeout:200});else boot()};
 if(document.readyState==='loading')addEventListener('DOMContentLoaded',idle,{once:true});else idle();
 // Initial HTML already presents workshop. Establish keyboard scope without
 // forcing a full layout while deferred scripts/fonts are still arriving.
 root.dataset.stop='workshop';
 stops.forEach((stop,i)=>{stop.inert=!short.matches&&i!==0});
 chapters[0]?.setAttribute('aria-current','step');
 if(document.readyState==='complete')scroll();else addEventListener('load',scroll,{once:true});
})();
