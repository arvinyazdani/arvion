/* One viewport-started sequence. Sound is always an explicit user action. */
const FILM_CHAPTER_MS=2400;
function filmPosition(elapsed,count=4,duration=FILM_CHAPTER_MS){
 const total=count*duration,ms=Math.max(0,Math.min(total,elapsed));
 return {index:Math.min(count-1,Math.floor(ms/duration)),progress:ms/total,ended:ms===total};
}
function filmVoice(voices,language){return voices.find(v=>v.localService&&v.lang.toLowerCase().split(/[-_]/)[0]===language)||null;}
if(typeof module!=='undefined')module.exports={filmPosition,filmVoice};
if(typeof document!=='undefined')(()=>{
 const root=document.querySelector('[data-assessment-film]');if(!root)return;
 const scenes=[...root.querySelectorAll('[data-film-scene]')];
 const replay=root.querySelector('[data-film-replay]'),progress=root.querySelector('.af-progress'),bar=root.querySelector('[data-film-progress]');
 const sound=root.querySelector('[data-film-sound]'),status=root.querySelector('[data-film-voice-status]');
 const motion=matchMedia('(prefers-reduced-motion: reduce)'),synth=window.speechSynthesis;
 let elapsed=0,playing=false,last=null,raf=0,entered=false,visible=false,disposed=false;
 const audioSource=root.dataset.narrationAudio;
 let voice=null,soundOn=false,utterance=null,audio=null,audioGeneration=0;
 function stopVoice(){
  audioGeneration++;
  if(audio){audio.pause();audio.currentTime=0;}
  if(utterance){utterance=null;synth?.cancel();}
 }
 function soundAvailable(){return Boolean(audioSource||voice);}
 function soundFailed(){stopVoice();soundOn=false;sound.setAttribute('aria-pressed','false');status.textContent=root.dataset.voiceUnavailable;}
 function voices(){
  voice=synth&&window.SpeechSynthesisUtterance?filmVoice(synth.getVoices(),root.dataset.filmLang):null;
  if(!soundAvailable()){stopVoice();soundOn=false;sound.setAttribute('aria-pressed','false');}
  status.textContent=soundAvailable()?(soundOn?root.dataset.voiceOn:root.dataset.voiceAvailable):root.dataset.voiceUnavailable;
 }
 function speak(){
  if(!soundOn||!soundAvailable()||!visible||document.hidden||disposed)return;
  stopVoice();
  try{
   if(audioSource){
    if(!audio){audio=new window.Audio(audioSource);audio.preload='none';}
    const generation=audioGeneration;
    audio.onerror=()=>{if(generation===audioGeneration&&soundOn)soundFailed();};
    // Static same-origin narration works without an installed Persian voice.
    // Start in this click, not after a fetch/voiceschanged callback (iOS).
    audio.play()?.catch(()=>{if(generation===audioGeneration&&soundOn)soundFailed();});
    return;
   }
   const current=new window.SpeechSynthesisUtterance(root.dataset.narration);utterance=current;
   current.voice=voice;current.lang=voice.lang;current.rate=1.15;
   current.onend=()=>{if(utterance===current)utterance=null};
   current.onerror=()=>{if(utterance!==current)return;stopVoice();soundOn=false;sound.setAttribute('aria-pressed','false');status.textContent=root.dataset.voiceUnavailable;};
   // Called synchronously from sound/replay click: mobile requires a gesture.
   synth.resume?.();synth.speak(current);
  }catch{stopVoice();soundOn=false;sound.setAttribute('aria-pressed','false');status.textContent=root.dataset.voiceUnavailable;}
 }
 function paint(){
  const state=filmPosition(elapsed,scenes.length);
  scenes.forEach((s,i)=>{s.classList.toggle('is-active',state.index===i);s.inert=state.index!==i});
  bar.style.setProperty('--af-progress',state.progress);progress.setAttribute('aria-valuenow',String(Math.round(state.progress*100)));
  root.classList.toggle('is-playing',playing&&!motion.matches);
  replay.hidden=playing||(!state.ended&&!motion.matches);
 }
 function pause(disableSound=false){
  playing=false;cancelAnimationFrame(raf);last=null;stopVoice();
  if(disableSound){soundOn=false;sound.setAttribute('aria-pressed','false');status.textContent=soundAvailable()?root.dataset.voiceAvailable:root.dataset.voiceUnavailable;}
  paint();
 }
 function tick(now){
  if(!playing||disposed)return;
  if(last!==null)elapsed+=Math.max(0,now-last);last=now;
  if(filmPosition(elapsed,scenes.length).ended){elapsed=scenes.length*FILM_CHAPTER_MS;pause();return}
  paint();raf=requestAnimationFrame(tick);
 }
 function start(){if(disposed||document.hidden||!visible||playing)return;playing=true;last=null;paint();raf=requestAnimationFrame(tick);}
 sound.addEventListener('click',()=>{
  voices();if(!soundAvailable())return;
  soundOn=!soundOn;sound.setAttribute('aria-pressed',String(soundOn));
  status.textContent=soundOn?root.dataset.voiceOn:root.dataset.voiceAvailable;
  if(!soundOn){stopVoice();return;}
  // Immediate sound, with the full introduction rather than only its tail.
  elapsed=0;pause();start();speak();
 });
 replay.addEventListener('click',()=>{elapsed=0;pause();start();speak();});
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pause(true);else if(visible&&entered&&!filmPosition(elapsed,scenes.length).ended&&!motion.matches)start();});
 const observer='IntersectionObserver'in window?new IntersectionObserver(entries=>{
  visible=entries[0].isIntersecting&&entries[0].intersectionRatio>=.35;
  if(!visible){pause(true);return;}
  if(!entered){entered=true;if(!motion.matches)start();}
  else if(!filmPosition(elapsed,scenes.length).ended&&!motion.matches)start();
 },{threshold:[0,.35]}):null;
 // Without IntersectionObserver, keep an explicit replay/start alternative.
 if(observer)observer.observe(root);else{visible=true;elapsed=scenes.length*FILM_CHAPTER_MS;}
 motion.addEventListener('change',()=>{if(motion.matches)pause();});
 addEventListener('pagehide',()=>{disposed=true;pause();observer?.disconnect();synth?.removeEventListener('voiceschanged',voices)},{once:true});
 voices();synth?.addEventListener('voiceschanged',voices);paint();
})();
