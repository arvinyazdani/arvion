/* User-started 9.6-second animation; optional device-local narration. */
const FILM_CHAPTER_MS=2400;
function filmPosition(elapsed,count=4,duration=FILM_CHAPTER_MS){
 const total=count*duration,ms=Math.max(0,Math.min(total,elapsed));
 return {index:Math.min(count-1,Math.floor(ms/duration)),progress:ms/total,ended:ms===total};
}
function filmVoice(voices,language){return voices.find(v=>v.localService&&v.lang.toLowerCase().split(/[-_]/)[0]===language)||null;}
if(typeof module!=='undefined')module.exports={filmPosition,filmVoice};
if(typeof document!=='undefined')(()=>{
 const root=document.querySelector('[data-assessment-film]');if(!root)return;
 const scenes=[...root.querySelectorAll('[data-film-scene]')],chapters=[...root.querySelectorAll('[data-film-chapter]')];
 const play=root.querySelector('[data-film-play]'),time=root.querySelector('[data-film-time]'),progress=root.querySelector('.af-progress'),bar=root.querySelector('[data-film-progress]');
 const motion=matchMedia('(prefers-reduced-motion: reduce)');let elapsed=0,playing=false,last=0,raf=0;
 const sound=root.querySelector('[data-film-sound]'),status=root.querySelector('[data-film-voice-status]');
 const synth=window.speechSynthesis;let voice=null,soundOn=false,utterance=null;
 function stopVoice(){if(utterance){utterance=null;synth?.cancel();}}
 function voices(){voice=synth&&window.SpeechSynthesisUtterance?filmVoice(synth.getVoices(),root.dataset.filmLang):null;if(sound){sound.disabled=!voice;sound.hidden=false;}if(!voice){soundOn=false;sound?.setAttribute('aria-pressed','false');}if(status)status.textContent=voice?root.dataset.voiceAvailable:root.dataset.voiceUnavailable;}
 function speak(){if(!soundOn||!voice)return;stopVoice();try{const current=new window.SpeechSynthesisUtterance(root.dataset.narration);utterance=current;current.voice=voice;current.lang=voice.lang;current.rate=1.15;current.onend=()=>{if(utterance===current)utterance=null;};current.onerror=()=>{if(utterance!==current)return;stopVoice();soundOn=false;sound?.setAttribute('aria-pressed','false');if(status)status.textContent=root.dataset.voiceUnavailable;};synth.speak(current);}catch{stopVoice();soundOn=false;sound?.setAttribute('aria-pressed','false');if(status)status.textContent=root.dataset.voiceUnavailable;}}
 sound?.addEventListener('click',()=>{soundOn=!soundOn;sound.setAttribute('aria-pressed',String(soundOn));if(!soundOn)stopVoice();});
 voices();synth?.addEventListener('voiceschanged',voices);
 const format=ms=>(ms/1000).toFixed(1)+'s';
 function paint(){const state=filmPosition(elapsed,scenes.length);scenes.forEach((s,i)=>{s.classList.toggle('is-active',state.index===i);s.inert=state.index!==i});chapters.forEach((b,i)=>{if(i===state.index)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current')});bar.style.setProperty('--af-progress',state.progress);progress.setAttribute('aria-valuenow',String(Math.round(state.progress*100)));time.textContent=format(elapsed)+' / 9.6s';play.textContent=playing?root.dataset.pauseLabel:state.ended?root.dataset.replayLabel:root.dataset.playLabel;play.setAttribute('aria-pressed',String(playing));root.classList.toggle('is-playing',playing&&!motion.matches);}
 function pause(){playing=false;cancelAnimationFrame(raf);last=0;stopVoice();paint();}
 function tick(now){if(!playing)return;if(last)elapsed+=Math.max(0,now-last);last=now;if(filmPosition(elapsed,scenes.length).ended){elapsed=scenes.length*FILM_CHAPTER_MS;pause();return}paint();raf=requestAnimationFrame(tick);}
 play.addEventListener('click',()=>{if(playing){pause();return}if(filmPosition(elapsed,scenes.length).ended)elapsed=0;playing=true;last=0;paint();if(elapsed===0)speak();raf=requestAnimationFrame(tick)});
 chapters.forEach((b,i)=>b.addEventListener('click',()=>{pause();elapsed=i*FILM_CHAPTER_MS;paint()}));
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pause()});
 const observer='IntersectionObserver'in window?new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)pause()}):null;observer?.observe(root);
 motion.addEventListener('change',()=>{if(motion.matches)pause()});
 addEventListener('pagehide',()=>{pause();observer?.disconnect();synth?.removeEventListener('voiceschanged',voices)},{once:true});paint();
})();
