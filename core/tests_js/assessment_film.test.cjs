const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const {filmPosition}=require('../static/core/js/assessment-film.js');
test('film chapters, progress and end are bounded at the four chapter boundaries',()=>{
 assert.deepEqual(filmPosition(-1),{index:0,progress:0,ended:false});
 assert.equal(filmPosition(8999).index,0);assert.equal(filmPosition(9000).index,1);
 assert.deepEqual(filmPosition(36001),{index:3,progress:1,ended:true});
});
function harness(){
 const make=()=>({events:{},attrs:{},classes:new Set(),style:{setProperty(){}},classList:{toggle(k,v){v?this.owner.classes.add(k):this.owner.classes.delete(k)}},addEventListener(k,f){this.events[k]=f},setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k]}});
 const scenes=Array.from({length:4},make),chapters=Array.from({length:4},make),play=make(),time=make(),progress=make(),bar=make(),root=make();
 for(const el of [...scenes,...chapters,root])el.classList.owner=el;
 root.dataset={playLabel:'Play',pauseLabel:'Pause',replayLabel:'Replay'};
 root.querySelectorAll=s=>s==='[data-film-scene]'?scenes:chapters;
 root.querySelector=s=>({'[data-film-play]':play,'[data-film-time]':time,'.af-progress':progress,'[data-film-progress]':bar}[s]);
 let frame=null;const events={};const document={hidden:false,querySelector:()=>root,addEventListener(k,f){events[k]=f}};
 const motion={matches:false,addEventListener(k,f){this.changed=f}};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/core/js/assessment-film.js'),'utf8'),{document,window:{},matchMedia:()=>motion,requestAnimationFrame:f=>{frame=f;return 1},cancelAnimationFrame:()=>{frame=null},addEventListener(){}});
 return {root,scenes,chapters,play,time,progress,document,events,motion,frame:now=>frame?.(now)};
}
test('player does not autoplay; play, pause and manual chapters keep UI and focus owner coherent',()=>{
 const h=harness();assert.equal(h.play.attrs['aria-pressed'],'false');assert.equal(h.root.classes.has('is-playing'),false);
 h.play.events.click();h.frame(100);h.frame(200);assert.equal(h.play.textContent,'Pause');assert.equal(h.root.classes.has('is-playing'),true);
 h.chapters[2].events.click();assert.equal(h.play.attrs['aria-pressed'],'false');assert.equal(h.chapters[2].attrs['aria-current'],'step');assert.equal(h.scenes[0].inert,true);assert.equal(h.scenes[2].inert,false);assert.equal(h.time.textContent,'00:18 / 00:36');
 h.play.events.click();h.document.hidden=true;h.events.visibilitychange();assert.equal(h.play.textContent,'Play');
});
test('end stops playback and replay restarts; reduced motion pauses running animations',()=>{
 const h=harness();h.chapters[3].events.click();h.play.events.click();for(let t=100;t<=9200;t+=100)h.frame(t);
 assert.equal(h.play.textContent,'Replay');assert.equal(h.progress.attrs['aria-valuenow'],'100');assert.equal(h.play.attrs['aria-pressed'],'false');
 h.play.events.click();assert.equal(h.time.textContent,'00:00 / 00:36');h.motion.matches=true;h.motion.changed();assert.equal(h.root.classes.has('is-playing'),false);
});
