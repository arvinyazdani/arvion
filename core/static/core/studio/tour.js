/* Native scrolling: no scroll hijack, no application/session requests. */
function studioEligibility({reduced,saveData,cores,memory}) {
  return !reduced&&!saveData&&!(cores&&cores<=2)&&!(memory&&memory<=2);
}
function studioProgress(top,height,viewport){return Math.max(0,Math.min(1,-top/Math.max(1,height-viewport)));}
function studioStep(top,stepHeight,header,count){return Math.max(0,Math.min(count-1,Math.round((header-top)/Math.max(1,stepHeight))));}
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
if(typeof module!=='undefined')module.exports={studioEligibility,studioProgress,studioStep,createStudioWorker};
if(typeof document!=='undefined')(()=>{
 const root=document.querySelector('[data-studio-tour]');if(!root)return;
 const canvas=root.querySelector('canvas'),poster=root.querySelector('[data-studio-poster]'),picture=poster.parentElement;
 const stops=[...root.querySelectorAll('[data-stop]')],button=root.querySelector('[data-studio-mode]');
 const chapters=[...root.querySelectorAll('.st-chapters a')];
 const motion=matchMedia('(prefers-reduced-motion: reduce)'),short=matchMedia('(max-height:620px)'),asset=root.dataset.assets;
 let engine=null,connection=null,disposed=false,booting=false,lastStop=0,scrollFrame=0,governor=0,started=0,lowWindows=0;
 function update(){scrollFrame=0;const rect=root.getBoundingClientRect(),h=root.querySelector('.st-viewport').offsetHeight,header=parseFloat(getComputedStyle(root).getPropertyValue('--st-header'))||0;
  if(short.matches){stops.forEach(stop=>{stop.inert=false});document.documentElement.classList.remove('st-snap');return;}
  const index=studioStep(rect.top,h,header,stops.length);
  engine?.setP(index/(stops.length-1));
  document.documentElement.classList.toggle('st-snap',rect.top<=header+h/2&&rect.bottom>header+h&&!motion.matches);
  stops.forEach((stop,i)=>{stop.inert=i!==index;stop.classList.toggle('is-current',i===index)});
  chapters.forEach((link,i)=>{if(i===index)link.setAttribute('aria-current','step');else link.removeAttribute('aria-current')});
  if(index!==lastStop){lastStop=index;root.dataset.stop=stops[index].dataset.stop;
   poster.src=asset+'posters/'+stops[index].dataset.stop+'-desktop.webp';picture.querySelector('[data-studio-mobile]').srcset=asset+'posters/'+stops[index].dataset.stop+'-mobile.webp';
   picture.querySelectorAll('[data-studio-format]').forEach(source=>{source.srcset=asset+'posters/'+stops[index].dataset.stop+'-'+source.dataset.studioFormat+'.avif'});}
 }
 const scroll=()=>{if(!disposed&&!scrollFrame)scrollFrame=requestAnimationFrame(update)};
 addEventListener('scroll',scroll,{passive:true});addEventListener('resize',scroll);
 function fallback(reason){root.dataset.engine='static';root.dataset.reason=reason;clearInterval(governor);connection?.dispose();button.hidden=true;}
 button.addEventListener('click',()=>fallback('user'));
 motion.addEventListener('change',()=>{if(motion.matches)fallback('reduced-motion')});
 short.addEventListener('change',()=>{if(short.matches)fallback('short-viewport');update()});
 async function boot(){
  if(disposed||booting||root.dataset.reason||short.matches||!studioEligibility({reduced:motion.matches,saveData:navigator.connection?.saveData,cores:navigator.hardwareConcurrency,memory:navigator.deviceMemory}))return;
  // Do not construct/animate two scenes while the entry overlay owns the screen.
  if(document.querySelector('#rvion-entry')||document.documentElement.hasAttribute('data-entry-pending')){document.addEventListener('rvion:entry-closed',boot,{once:true});return;}
  booting=true;
  try{
   // Let the already-loaded poster and fonts paint before GPU work can compete.
   await document.fonts?.ready;await poster.decode?.().catch(()=>{});
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
 addEventListener('pagehide',()=>{disposed=true;clearInterval(governor);cancelAnimationFrame(scrollFrame);document.documentElement.classList.remove('st-snap');connection?.dispose();},{once:true});
 addEventListener('pageshow',event=>{if(event.persisted)fallback('restored-page')});
 const idle=()=>{if('requestIdleCallback'in window)requestIdleCallback(boot,{timeout:2500});else setTimeout(boot,1000)};
 if(document.readyState==='complete')idle();else addEventListener('load',idle,{once:true});
 // Initial HTML already presents workshop. Establish keyboard scope without
 // forcing a full layout while deferred scripts/fonts are still arriving.
 root.dataset.stop='workshop';
 stops.forEach((stop,i)=>{stop.inert=!short.matches&&i!==0});
 chapters[0]?.setAttribute('aria-current','step');
 if(document.readyState==='complete')scroll();else addEventListener('load',scroll,{once:true});
})();
