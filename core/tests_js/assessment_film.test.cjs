const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const {filmPosition,filmVoice}=require('../static/core/js/assessment-film.js');
test('film chapters, progress and end are bounded at the four chapter boundaries',()=>{
 assert.deepEqual(filmPosition(-1),{index:0,progress:0,ended:false});
 assert.equal(filmPosition(2399).index,0);assert.equal(filmPosition(2400).index,1);
 assert.deepEqual(filmPosition(9600),{index:3,progress:1,ended:true});
 assert.deepEqual(filmPosition(9999),{index:3,progress:1,ended:true});
});
function harness(availableVoices=[]){
 const make=()=>({events:{},attrs:{},classes:new Set(),style:{setProperty(){}},classList:{toggle(k,v){v?this.owner.classes.add(k):this.owner.classes.delete(k)}},addEventListener(k,f){this.events[k]=f},setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k]}});
 const scenes=Array.from({length:4},make),chapters=Array.from({length:4},make),play=make(),time=make(),progress=make(),bar=make(),root=make(),sound=make(),status=make();
 for(const el of [...scenes,...chapters,root])el.classList.owner=el;
 root.dataset={playLabel:'Play',pauseLabel:'Pause',replayLabel:'Replay',filmLang:'fa',narration:'Narration',voiceAvailable:'Available',voiceUnavailable:'Unavailable'};
 root.querySelectorAll=s=>s==='[data-film-scene]'?scenes:chapters;
 root.querySelector=s=>({'[data-film-play]':play,'[data-film-time]':time,'.af-progress':progress,'[data-film-progress]':bar,'[data-film-sound]':sound,'[data-film-voice-status]':status}[s]);
 let frame=null;const events={};const document={hidden:false,querySelector:()=>root,addEventListener(k,f){events[k]=f}};
 const motion={matches:false,addEventListener(k,f){this.changed=f}};
 const speech={spoken:[],cancelled:0,getVoices:()=>availableVoices,speak(u){this.spoken.push(u)},cancel(){this.cancelled++},addEventListener(){},removeEventListener(){}};
 const lifecycle={};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/core/js/assessment-film.js'),'utf8'),{document,window:{speechSynthesis:speech,SpeechSynthesisUtterance:function(text){this.text=text}},matchMedia:()=>motion,requestAnimationFrame:f=>{frame=f;return 1},cancelAnimationFrame:()=>{frame=null},addEventListener(k,f){lifecycle[k]=f}});
 return {root,scenes,chapters,play,time,progress,document,events,motion,sound,status,speech,lifecycle,frame:now=>frame?.(now)};
}
test('player does not autoplay; play, pause and manual chapters keep UI and focus owner coherent',()=>{
 const h=harness();assert.equal(h.play.attrs['aria-pressed'],'false');assert.equal(h.root.classes.has('is-playing'),false);
 h.play.events.click();h.frame(100);h.frame(200);assert.equal(h.play.textContent,'Pause');assert.equal(h.root.classes.has('is-playing'),true);
 h.chapters[2].events.click();assert.equal(h.play.attrs['aria-pressed'],'false');assert.equal(h.chapters[2].attrs['aria-current'],'step');assert.equal(h.scenes[0].inert,true);assert.equal(h.scenes[2].inert,false);assert.equal(h.time.textContent,'4.8s / 9.6s');
 h.play.events.click();h.document.hidden=true;h.events.visibilitychange();assert.equal(h.play.textContent,'Play');
});
test('end stops playback and replay restarts; reduced motion pauses running animations',()=>{
 const h=harness();h.chapters[3].events.click();h.play.events.click();for(let t=100;t<=9200;t+=100)h.frame(t);
 assert.equal(h.play.textContent,'Replay');assert.equal(h.progress.attrs['aria-valuenow'],'100');assert.equal(h.play.attrs['aria-pressed'],'false');
 h.play.events.click();assert.equal(h.time.textContent,'0.0s / 9.6s');h.motion.matches=true;h.motion.changed();assert.equal(h.root.classes.has('is-playing'),false);
});
test('slow frames do not stretch a full film beyond 9.6 seconds',()=>{
 const h=harness();h.play.events.click();h.frame(100);h.frame(2500);assert.equal(h.scenes[1].inert,false);h.frame(9700);assert.equal(h.play.textContent,'Replay');assert.equal(h.time.textContent,'9.6s / 9.6s');
});
test('only matching local voices are eligible, never remote or another language',()=>{
 const fa={lang:'fa-IR',localService:true},en={lang:'en-US',localService:true};
 assert.equal(filmVoice([{lang:'fa-IR',localService:false},en],'fa'),null);
 assert.equal(filmVoice([en,fa],'fa'),fa);assert.equal(filmVoice([fa,en],'en'),en);
 const h=harness();assert.equal(h.sound.disabled,true);assert.equal(h.status.textContent,'Unavailable');
});
test('voice requires explicit opt-in and is cancelled on pause, end and pagehide',()=>{
 const h=harness([{lang:'fa-IR',localService:true}]);
 assert.equal(h.speech.spoken.length,0);h.play.events.click();assert.equal(h.speech.spoken.length,0);h.play.events.click();
 h.sound.events.click();h.play.events.click();assert.equal(h.speech.spoken.length,1);assert.equal(h.speech.spoken[0].lang,'fa-IR');
 h.frame(100);h.frame(9700);assert.equal(h.speech.cancelled,1);
 h.play.events.click();h.lifecycle.pagehide();assert.equal(h.speech.cancelled,2);assert.equal(h.play.attrs['aria-pressed'],'false');
});
test('late cancellation errors cannot turn off the chosen voice or cancel a replay',()=>{
 const h=harness([{lang:'fa-IR',localService:true}]);h.sound.events.click();h.play.events.click();const old=h.speech.spoken[0];h.play.events.click();h.play.events.click();old.onerror();
 assert.equal(h.sound.attrs['aria-pressed'],'true');assert.equal(h.status.textContent,'Available');assert.equal(h.speech.cancelled,1);
 h.speech.spoken[1].onerror();assert.equal(h.sound.attrs['aria-pressed'],'false');assert.equal(h.status.textContent,'Unavailable');
});
