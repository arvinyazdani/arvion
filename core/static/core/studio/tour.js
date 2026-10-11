/* Native scrolling: no scroll hijack, no application/session requests. */
function studioEligibility({reduced,saveData,cores,memory}) {
  return !reduced&&!saveData&&!(cores&&cores<=2)&&!(memory&&memory<=2);
}
function studioProgress(top,height,viewport){return Math.max(0,Math.min(1,-top/Math.max(1,height-viewport)));}
function studioStep(top,stepHeight,header,count){return Math.max(0,Math.min(count-1,Math.round((header-top)/Math.max(1,stepHeight))));}
if(typeof module!=='undefined')module.exports={studioEligibility,studioProgress,studioStep};
if(typeof document!=='undefined')(()=>{
 const root=document.querySelector('[data-studio-tour]');if(!root)return;
 const canvas=root.querySelector('canvas'),poster=root.querySelector('[data-studio-poster]'),picture=poster.parentElement;
 const stops=[...root.querySelectorAll('[data-stop]')],button=root.querySelector('[data-studio-mode]');
 const chapters=[...root.querySelectorAll('.st-chapters a')];
 const motion=matchMedia('(prefers-reduced-motion: reduce)'),short=matchMedia('(max-height:620px)'),asset=root.dataset.assets;
 let engine=null,disposed=false,lastStop=0,scrollFrame=0,governor=0,started=0,lowWindows=0;
 function update(){scrollFrame=0;const rect=root.getBoundingClientRect(),h=root.querySelector('.st-viewport').offsetHeight,header=parseFloat(getComputedStyle(root).getPropertyValue('--st-header'))||0;
  if(short.matches){stops.forEach(stop=>{stop.inert=false});document.documentElement.classList.remove('st-snap');return;}
  const index=studioStep(rect.top,h,header,stops.length);
  engine?.setP(index/(stops.length-1));
  document.documentElement.classList.toggle('st-snap',rect.top<=header+h/2&&rect.bottom>header+h&&!motion.matches);
  stops.forEach((stop,i)=>{stop.inert=i!==index;stop.classList.toggle('is-current',i===index)});
  chapters.forEach((link,i)=>{if(i===index)link.setAttribute('aria-current','step');else link.removeAttribute('aria-current')});
  if(index!==lastStop){lastStop=index;root.dataset.stop=stops[index].dataset.stop;
   poster.src=asset+'posters/'+stops[index].dataset.stop+'-desktop.webp';picture.querySelector('source').srcset=asset+'posters/'+stops[index].dataset.stop+'-mobile.webp';}
 }
 const scroll=()=>{if(!scrollFrame)scrollFrame=requestAnimationFrame(update)};
 addEventListener('scroll',scroll,{passive:true});addEventListener('resize',scroll);
 function fallback(reason){root.dataset.engine='static';root.dataset.reason=reason;clearInterval(governor);engine?.stop();button.hidden=true;}
 button.addEventListener('click',()=>fallback('user'));
 motion.addEventListener('change',()=>{if(motion.matches)fallback('reduced-motion')});
 short.addEventListener('change',()=>{if(short.matches)fallback('short-viewport');update()});
 const load=src=>new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=reject;document.head.append(s)});
 async function boot(){
  if(disposed||short.matches||!studioEligibility({reduced:motion.matches,saveData:navigator.connection?.saveData,cores:navigator.hardwareConcurrency,memory:navigator.deviceMemory}))return;
  // Do not construct/animate two scenes while the entry overlay owns the screen.
  if(document.querySelector('#rvion-entry')){document.addEventListener('rvion:entry-closed',boot,{once:true});return;}
  try{
   await load(asset+'vendor/three-r128.min.js');await load(asset+'vendor/post-r128.js');await load(asset+'engine.js?v=3');
   if(disposed||motion.matches)return;
   const covers={};root.querySelectorAll('[data-studio-cover]').forEach(a=>{const u=new URL(a.dataset.studioCover,location.href);if(u.origin===location.origin)covers[a.dataset.coverKey]=u.href});
   engine=await window.RvionStudioEngine.create(canvas,{lite:matchMedia('(max-width:760px)').matches,rtl:document.documentElement.dir==='rtl',covers,shotIndices:[1,2,3,6]});
   if(disposed||motion.matches||root.dataset.reason==='context-lost'){engine.dispose();fallback('interrupted');return;}
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
 addEventListener('pagehide',()=>{disposed=true;clearInterval(governor);cancelAnimationFrame(scrollFrame);document.documentElement.classList.remove('st-snap');engine?.dispose();},{once:true});
 addEventListener('pageshow',event=>{if(event.persisted)fallback('restored-page')});
 const idle=()=>{if('requestIdleCallback'in window)requestIdleCallback(boot,{timeout:2500});else setTimeout(boot,1000)};
 if(document.readyState==='complete')idle();else addEventListener('load',idle,{once:true});
 root.dataset.stop='workshop';update();
})();
