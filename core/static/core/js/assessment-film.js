/* A user-started, silent code animation. No media download or autoplay. */
function filmPosition(elapsed,count=4,duration=9000){
 const total=count*duration,ms=Math.max(0,Math.min(total,elapsed));
 return {index:Math.min(count-1,Math.floor(ms/duration)),progress:ms/total,ended:ms===total};
}
if(typeof module!=='undefined')module.exports={filmPosition};
if(typeof document!=='undefined')(()=>{
 const root=document.querySelector('[data-assessment-film]');if(!root)return;
 const scenes=[...root.querySelectorAll('[data-film-scene]')],chapters=[...root.querySelectorAll('[data-film-chapter]')];
 const play=root.querySelector('[data-film-play]'),time=root.querySelector('[data-film-time]'),progress=root.querySelector('.af-progress'),bar=root.querySelector('[data-film-progress]');
 const motion=matchMedia('(prefers-reduced-motion: reduce)');let elapsed=0,playing=false,last=0,raf=0;
 const format=ms=>'00:'+String(Math.floor(ms/1000)).padStart(2,'0');
 function paint(){const state=filmPosition(elapsed,scenes.length);scenes.forEach((s,i)=>{s.classList.toggle('is-active',state.index===i);s.inert=state.index!==i});chapters.forEach((b,i)=>{if(i===state.index)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current')});bar.style.setProperty('--af-progress',state.progress);progress.setAttribute('aria-valuenow',String(Math.round(state.progress*100)));time.textContent=format(elapsed)+' / 00:36';play.textContent=playing?root.dataset.pauseLabel:state.ended?root.dataset.replayLabel:root.dataset.playLabel;play.setAttribute('aria-pressed',String(playing));root.classList.toggle('is-playing',playing&&!motion.matches);}
 function pause(){playing=false;cancelAnimationFrame(raf);last=0;paint();}
 function tick(now){if(!playing)return;if(last)elapsed+=Math.min(100,now-last);last=now;if(filmPosition(elapsed,scenes.length).ended){elapsed=scenes.length*9000;pause();return}paint();raf=requestAnimationFrame(tick);}
 play.addEventListener('click',()=>{if(playing){pause();return}if(filmPosition(elapsed,scenes.length).ended)elapsed=0;playing=true;last=0;paint();raf=requestAnimationFrame(tick)});
 chapters.forEach((b,i)=>b.addEventListener('click',()=>{pause();elapsed=i*9000;paint()}));
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pause()});
 const observer='IntersectionObserver'in window?new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)pause()}):null;observer?.observe(root);
 motion.addEventListener('change',()=>{if(motion.matches)pause()});
 addEventListener('pagehide',()=>{pause();observer?.disconnect()},{once:true});paint();
})();
