const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const {filmPosition,filmVoice}=require('../static/core/js/assessment-film.js');
function harness(availableVoices=[],language='en',reduced=false){
 const make=()=>({events:{},attrs:{},classes:new Set(),style:{setProperty(){}},classList:{toggle(k,v){v?this.owner.classes.add(k):this.owner.classes.delete(k)}},addEventListener(k,f){this.events[k]=f},setAttribute(k,v){this.attrs[k]=v}});
 const scenes=Array.from({length:4},make),replay=make(),progress=make(),bar=make(),root=make(),sound=make(),status=make();
 for(const el of [...scenes,root])el.classList.owner=el;
 root.dataset={filmLang:language,narration:'Test skills. Review behaviour. Read your report. Learn from answers.',voiceAvailable:'Available',voiceUnavailable:'Unavailable',voiceOn:'On'};
 root.querySelectorAll=()=>scenes;
 root.querySelector=s=>({'[data-film-replay]':replay,'.af-progress':progress,'[data-film-progress]':bar,'[data-film-sound]':sound,'[data-film-voice-status]':status}[s]);
 let frame=null,intersect;const events={},lifecycle={},voiceEvents={};
 const document={hidden:false,querySelector:()=>root,addEventListener(k,f){events[k]=f}};
 const motion={matches:reduced,addEventListener(k,f){this.changed=f}};
 const speech={spoken:[],cancelled:0,resumed:0,getVoices:()=>availableVoices,speak(u){this.spoken.push(u)},cancel(){this.cancelled++},resume(){this.resumed++},addEventListener(k,f){voiceEvents[k]=f},removeEventListener(k){delete voiceEvents[k]}};
 class Observer{constructor(fn){intersect=fn}observe(){}disconnect(){this.disconnected=true}}
 vm.runInNewContext(fs.readFileSync('core/static/core/js/assessment-film.js','utf8'),{document,window:{speechSynthesis:speech,SpeechSynthesisUtterance:function(text){this.text=text},IntersectionObserver:Observer},IntersectionObserver:Observer,matchMedia:()=>motion,requestAnimationFrame:f=>{frame=f;return 1},cancelAnimationFrame:()=>{frame=null},addEventListener(k,f){lifecycle[k]=f}});
 return{root,scenes,replay,progress,document,events,motion,sound,status,speech,lifecycle,voiceEvents,view:ratio=>intersect([{isIntersecting:ratio>0,intersectionRatio:ratio}]),frame:now=>frame?.(now)};
}
test('four scenes stop at exactly 9.6 seconds, including slow frames',()=>{
 assert.equal(filmPosition(2400).index,1);assert.deepEqual(filmPosition(9999),{index:3,progress:1,ended:true});
 const h=harness();assert.equal(h.root.classes.has('is-playing'),false);h.view(.2);assert.equal(h.root.classes.has('is-playing'),false);
 h.view(.5);h.frame(0);h.frame(2400);assert.equal(h.scenes[1].inert,false);h.frame(9600);
 assert.equal(h.root.classes.has('is-playing'),false);assert.equal(h.progress.attrs['aria-valuenow'],'100');assert.equal(h.replay.hidden,false);
});
test('ended sequence never restarts on scrolling; explicit replay starts again',()=>{
 const h=harness();h.view(1);h.frame(0);h.frame(9600);h.view(0);h.view(1);
 assert.equal(h.root.classes.has('is-playing'),false);h.replay.events.click();assert.equal(h.root.classes.has('is-playing'),true);assert.equal(h.replay.hidden,true);assert.equal(h.scenes[0].inert,false);
});
test('offscreen and hidden pause; return resumes without counting invisible time',()=>{
 const h=harness();h.view(1);h.frame(0);h.frame(1000);h.view(0);h.frame(9000);assert.equal(h.root.classes.has('is-playing'),false);
 h.view(1);h.frame(10000);h.frame(11000);assert.equal(h.scenes[0].inert,false);
 h.document.hidden=true;h.events.visibilitychange();assert.equal(h.root.classes.has('is-playing'),false);
 h.document.hidden=false;h.events.visibilitychange();assert.equal(h.root.classes.has('is-playing'),true);
});
test('English sound click immediately speaks in the same gesture, without another play button',()=>{
 const h=harness([{lang:'en-US',localService:true}]);h.view(1);assert.equal(h.speech.spoken.length,0);
 h.sound.events.click();assert.equal(h.speech.spoken.length,1);assert.equal(h.speech.spoken[0].lang,'en-US');assert.equal(h.speech.resumed,1);
 assert.equal(h.status.textContent,'On');
 h.sound.events.click();assert.equal(h.speech.cancelled,1);assert.equal(h.sound.attrs['aria-pressed'],'false');
});
test('late voice availability is recoverable and never substitutes a foreign or remote voice',()=>{
 const voices=[],h=harness(voices);h.view(1);h.sound.events.click();assert.equal(h.status.textContent,'Unavailable');
 voices.push({lang:'en-GB',localService:true});h.voiceEvents.voiceschanged();h.sound.events.click();assert.equal(h.speech.spoken.length,1);
 assert.equal(filmVoice([{lang:'en-US',localService:false},{lang:'fa-IR',localService:true}],'en'),null);
});
test('sound is cancelled at end, on hidden, offscreen and pagehide',()=>{
 for(const cause of ['end','hidden','offscreen','pagehide']){
  const h=harness([{lang:'en-US',localService:true}]);h.view(1);h.sound.events.click();
  if(cause==='end'){h.frame(0);h.frame(9600)}if(cause==='hidden'){h.document.hidden=true;h.events.visibilitychange()}if(cause==='offscreen')h.view(0);if(cause==='pagehide')h.lifecycle.pagehide();
  assert.equal(h.speech.cancelled,1,cause);assert.equal(h.root.classes.has('is-playing'),false,cause);
  if(cause==='hidden'||cause==='offscreen')assert.equal(h.sound.attrs['aria-pressed'],'false');
 }
});
test('stale speech cancellation cannot disable replay; actual failure gives a useful status',()=>{
 const h=harness([{lang:'en-US',localService:true}]);h.view(1);h.sound.events.click();const old=h.speech.spoken[0];h.replay.events.click();old.onerror();
 assert.equal(h.sound.attrs['aria-pressed'],'true');h.speech.spoken[1].onerror();assert.equal(h.sound.attrs['aria-pressed'],'false');assert.equal(h.status.textContent,'Unavailable');
});
test('reduced motion does not autoplay; explicit replay is available without CSS motion',()=>{
 const h=harness([], 'fa',true);h.view(1);assert.equal(h.root.classes.has('is-playing'),false);assert.equal(h.replay.hidden,false);
 h.replay.events.click();h.frame(0);h.frame(2400);assert.equal(h.scenes[1].inert,false);assert.equal(h.root.classes.has('is-playing'),false);
});
test('pagehide disconnects voice listeners and cannot restart a disposed player',()=>{
 const h=harness();h.view(1);h.lifecycle.pagehide();h.view(1);h.replay.events.click();assert.equal(h.root.classes.has('is-playing'),false);assert.equal(h.voiceEvents.voiceschanged,undefined);
});
