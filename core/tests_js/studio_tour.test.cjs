const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {studioEligibility,studioProgress,studioStep}=require('../static/core/studio/tour.js');
test('startup runs at DOM readiness, without Safari one-second or full-load delay',()=>{
 const source=fs.readFileSync(path.join(__dirname,'../static/core/studio/tour.js'),'utf8');
 const schedule=source.slice(source.indexOf(' const idle=()=>'),source.indexOf(' // Initial HTML'));
 for(const readyState of ['loading','interactive','complete'])for(const idleAPI of [false,true]){
  let started=0;const events={};const context={document:{readyState},window:{},boot(){started++},addEventListener(k,f){events[k]=f}};
  if(idleAPI){context.window.requestIdleCallback=true;context.requestIdleCallback=(fn,options)=>{assert.equal(options.timeout,200);fn()};}
  vm.runInNewContext(schedule,context);
  if(readyState==='loading'){assert.equal(started,0);events.DOMContentLoaded();}
  assert.equal(started,1);assert.equal(events.load,undefined);
 }
});
test('unresolved page fonts do not block poster-first boot; pagehide still cancels',async()=>{
 const source=fs.readFileSync(path.join(__dirname,'../static/core/studio/tour.js'),'utf8');
 const boot=source.slice(source.indexOf(' async function boot(){'),source.indexOf(" canvas.addEventListener('webglcontextlost'"));
 for(const disposed of [false,true]){
  const failures=[],frames=[];let decoded=0;
  const context={disposed,booting:false,root:{dataset:{}},short:{matches:false},motion:{matches:false},
   navigator:{},studioEligibility:()=>true,document:{fonts:{ready:new Promise(()=>{})}},
   poster:{decode:()=>{decoded++;return Promise.resolve()}},requestAnimationFrame:fn=>{frames.push(fn)},
   canvas:{},fallback:reason=>failures.push(reason)};
  vm.runInNewContext(boot,context);const pending=context.boot();await Promise.resolve();await Promise.resolve();await Promise.resolve();
  while(frames.length)frames.shift()();await pending;
  assert.equal(decoded,disposed?0:1);assert.deepEqual(failures,disposed?[]:['worker-unsupported']);
 }
});
test('motion, data saving and low device gates prevent engine admission',()=>{
 const good={cores:8,memory:8,reduced:false,saveData:false};
 assert.equal(studioEligibility(good),true);
 for(const change of [{reduced:true},{saveData:true},{cores:2},{memory:1}])assert.equal(studioEligibility({...good,...change}),false);
});
test('four-step navigation selects and holds a room, including resized viewports',()=>{
 assert.equal(studioStep(68,706,68,4),0);
 assert.equal(studioStep(-638,706,68,4),1);
 assert.equal(studioStep(-1344,706,68,4),2);
 assert.equal(studioStep(-2050,706,68,4),3);
 assert.equal(studioStep(-9000,706,68,4),3);
 assert.equal(studioStep(500,706,68,4),0);
 assert.equal(studioStep(-648,724,76,4),1);
});
test('native scroll camera progress is clamped and finite',()=>{
 assert.equal(studioProgress(80,5600,800),0);
 assert.equal(studioProgress(-2400,5600,800),.5);
 assert.equal(studioProgress(-6000,5600,800),1);
 assert.equal(studioProgress(0,0,0),0);
});
test('scroll updates active links, inert panels and poster; short screens expose all routes',()=>{
 const make=()=>({attrs:{},events:{},classes:new Set(),dataset:{},classList:{toggle(k,on){on?this.owner.classes.add(k):this.owner.classes.delete(k)},remove(k){this.owner.classes.delete(k)}},setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k]},addEventListener(k,f){this.events[k]=f}});
 const stops=['workshop','exam','library','reception'].map(stop=>{const n=make();n.dataset.stop=stop;return n}),links=stops.map(make),root=make(),button=make(),canvas=make(),html=make(),source={};
 for(const n of [...stops,...links,root,html])n.classList.owner=n;
 const avif=[{dataset:{studioFormat:'mobile'}},{dataset:{studioFormat:'desktop'}}];
 const poster={parentElement:{querySelector:()=>source,querySelectorAll:()=>avif}},events={},medias={};let top=68,frame,reads=0;
 root.dataset.assets='/static/core/studio/';root.getBoundingClientRect=()=>{reads++;return{top,bottom:top+706*4}};
 root.querySelector=s=>s==='canvas'?canvas:s==='[data-studio-poster]'?poster:s==='[data-studio-mode]'?button:s==='.st-controls a'?null:{offsetHeight:706};
 root.querySelectorAll=s=>s==='[data-stop]'?stops:links;
 const media=q=>medias[q]||(medias[q]={matches:false,addEventListener(k,f){this.change=f}});
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/core/studio/tour.js'),'utf8'),{
  document:{querySelector:()=>root,documentElement:html,readyState:'loading'},window:{},navigator:{},
  matchMedia:media,getComputedStyle:()=>({getPropertyValue:()=>68}),
  addEventListener(k,f){events[k]=f},requestAnimationFrame(f){frame=f;return 1},cancelAnimationFrame(){},clearInterval(){},
 });
 assert.deepEqual(stops.map(s=>s.inert),[false,true,true,true]);assert.equal(links[0].attrs['aria-current'],'step');
 assert.equal(reads,0,'initial keyboard scope must not synchronously force layout');
 top=68-706;events.scroll();frame();
 assert.deepEqual(stops.map(s=>s.inert),[true,false,true,true]);assert.equal(links[1].attrs['aria-current'],'step');assert.equal(links[0].attrs['aria-current'],undefined);
 assert.equal(poster.src,'/static/core/studio/posters/exam-desktop.webp');assert.equal(source.srcset,'/static/core/studio/posters/exam-mobile.webp');
 assert.equal(avif[0].srcset,'/static/core/studio/posters/exam-mobile.avif');assert.equal(avif[1].srcset,'/static/core/studio/posters/exam-desktop.avif');
 const short=medias['(max-height:620px)'];short.matches=true;short.change();
 assert.deepEqual(stops.map(s=>s.inert),[false,false,false,false]);assert.equal(root.dataset.reason,'short-viewport');assert.equal(html.classes.has('st-snap'),false);
});
