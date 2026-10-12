const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {createStudioGestureGate}=require('../static/core/studio/tour.js');
test('one wheel burst stays consumed after landing; a quiet new gesture is admitted',()=>{
 const gate=createStudioGestureGate();
 assert.ok(gate.wheel(0));assert.ok(gate.begin(0));
 for(let t=20;t<=1400;t+=20)assert.equal(gate.wheel(t),false);
 assert.equal(gate.busy(999),true);assert.equal(gate.busy(1000),false);
 assert.ok(gate.wheel(1700));assert.ok(gate.begin(1700));
 gate.cancel();assert.ok(gate.wheel(1701));assert.ok(gate.begin(1701));
});
function scene(initialTop=68){
 const events={},frames=new Map(),media={},htmlClasses=new Set();let time=0,id=0,y=0,height=706;
 const node=()=>({dataset:{},attrs:{},classes:new Set(),events:{},inert:false,
  setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k]},
  addEventListener(k,f){this.events[k]=f},closest(){return null},
  classList:{toggle(){},remove(){}}});
 const root=node(),canvas=node(),button=node(),skip=node(),stops=['workshop','exam','library','reception'].map(stop=>Object.assign(node(),{dataset:{stop}})),chapters=stops.map(()=>node());
 const source={},avif=[],poster={parentElement:{querySelector:()=>source,querySelectorAll:()=>avif}};
 root.dataset.assets='/static/core/studio/';root.getBoundingClientRect=()=>({top:initialTop-y,bottom:initialTop+706*4-y});
 root.querySelector=s=>s==='canvas'?canvas:s==='[data-studio-poster]'?poster:s==='[data-studio-mode]'?button:s==='.st-controls a'?skip:{offsetHeight:height};
 root.querySelectorAll=s=>s==='[data-stop]'?stops:s==='.st-chapters a'?chapters:[];
 const window={get scrollY(){return y},scrollTo({top}){y=top;events.scroll?.()}};
 const context={document:{querySelector:()=>root,readyState:'loading',body:{classList:{contains:()=>false}},documentElement:{classList:{contains:x=>htmlClasses.has(x),add:x=>htmlClasses.add(x),remove:x=>htmlClasses.delete(x)}}},window,navigator:{},history:{replaceState(){}},
  performance:{now:()=>time},matchMedia:q=>media[q]||(media[q]={matches:false,addEventListener(k,fn){this.change=fn}}),getComputedStyle:()=>({getPropertyValue:()=>68}),
  addEventListener:(k,fn)=>events[k]=fn,removeEventListener:(k,fn)=>{if(events[k]===fn)delete events[k]},
  requestAnimationFrame:fn=>{frames.set(++id,fn);return id},cancelAnimationFrame:i=>frames.delete(i),clearInterval(){}};
 vm.runInNewContext(fs.readFileSync('core/static/core/studio/tour.js','utf8'),context);
 const send=(kind,extra={})=>{const event={target:node(),prevented:false,preventDefault(){this.prevented=true},...extra};events[kind]?.(event);return event};
 const advance=ms=>{time+=ms;const pending=[...frames];frames.clear();pending.forEach(([,fn])=>fn(time))};
 return{root,stops,button,skip,events,media,frames,send,advance,resize:()=>{height=600;send('resize')},freeze:ms=>{time+=ms},get y(){return y},set y(value){y=value;send('scroll');advance(0)},get step(){return root.dataset.stop}};
}
test('weak and huge wheel each advance exactly one chapter; transition and inertia block repeats',()=>{
 const s=scene();assert.equal(s.step,'workshop');
 assert.ok(s.send('wheel',{deltaY:.5,deltaX:0}).prevented);assert.equal(s.step,'exam');
 s.advance(50);assert.ok(s.send('wheel',{deltaY:9000,deltaX:0}).prevented);assert.equal(s.step,'exam');
 s.advance(700);assert.equal(s.y,706);assert.equal(s.root.attrs['data-transitioning'],undefined);
 s.advance(300);assert.ok(s.send('wheel',{deltaY:9000,deltaX:0}).prevented);assert.equal(s.step,'library');
 s.advance(1050);assert.equal(s.y,1412);assert.ok(s.send('wheel',{deltaY:-1,deltaX:0}).prevented);assert.equal(s.step,'exam');
 s.advance(1050);assert.equal(s.y,706);
});
test('a slightly taller real header still admits the very first one-pixel wheel',()=>{
 const s=scene(81);assert.ok(s.send('wheel',{deltaY:1,deltaX:0}).prevented);assert.equal(s.step,'exam');
 s.advance(1100);assert.equal(s.y,719);
});
test('a suspended RAF cannot unlock an unfinished transition just because time elapsed',()=>{
 const s=scene();s.send('wheel',{deltaY:1});s.freeze(3000);
 assert.ok(s.send('wheel',{deltaY:9000}).prevented);assert.equal(s.step,'exam');
 s.advance(0);assert.equal(s.y,706);assert.equal(s.root.attrs['data-transitioning'],undefined);
});
test('native scrolling remains available at both boundaries and outside the scene',()=>{
 const s=scene();assert.equal(s.send('wheel',{deltaY:-80,deltaX:0}).prevented,false);
 s.y=2118;assert.equal(s.step,'reception');s.advance(300);
 assert.equal(s.send('wheel',{deltaY:5000,deltaX:0}).prevented,false);
 s.y=4000;assert.equal(s.send('wheel',{deltaY:-100,deltaX:0}).prevented,false);
});
test('one touch contact cannot advance twice even after transition; a new swipe can',()=>{
 const s=scene(),touch=(x,y)=>({clientX:x,clientY:y});
 s.send('touchstart',{touches:[touch(100,400)]});
 assert.ok(s.send('touchmove',{touches:[touch(100,390)]}).prevented);assert.equal(s.step,'exam');
 s.advance(1200);assert.ok(s.send('touchmove',{touches:[touch(100,20)]}).prevented);assert.equal(s.step,'exam');
 s.send('touchend');s.send('touchstart',{touches:[touch(100,400)]});s.send('touchmove',{touches:[touch(100,100)]});assert.equal(s.step,'library');
 s.advance(1200);s.send('touchend');s.send('touchstart',{touches:[touch(100,400)]});s.send('touchmove',{touches:[touch(100,500)]});assert.equal(s.step,'exam');
});
test('horizontal scrolling, pinch zoom, keyboard controls and reduced motion stay safe',()=>{
 const s=scene();assert.equal(s.send('wheel',{deltaX:80,deltaY:4}).prevented,false);
 assert.equal(s.send('wheel',{deltaY:80,ctrlKey:true}).prevented,false);
 s.send('touchstart',{touches:[{clientX:100,clientY:100},{clientX:200,clientY:100}]});
 assert.equal(s.send('touchmove',{touches:[{clientX:100,clientY:0},{clientX:200,clientY:0}]}).prevented,false);
 s.send('keydown',{key:'PageDown'});assert.equal(s.step,'exam');s.advance(1200);
 assert.ok(s.send('keydown',{key:'PageDown',repeat:true}).prevented);assert.equal(s.step,'exam');
 s.media['(prefers-reduced-motion: reduce)'].matches=true;s.media['(prefers-reduced-motion: reduce)'].change();
 assert.equal(s.send('wheel',{deltaY:80}).prevented,false);s.advance(0);assert.equal(s.frames.size,0);
});
test('skip, resize, simple mode and pagehide cancel an in-progress transition',()=>{
 for(const action of ['skip','resize','simple','pagehide','hashchange','popstate','End','Tab']){
  const s=scene();s.send('wheel',{deltaY:1});assert.ok(s.frames.size);
  if(action==='skip')s.skip.events.click();if(action==='simple')s.button.events.click();if(action==='resize')s.resize();if(action==='pagehide')s.send(action);
  if(['hashchange','popstate'].includes(action))s.send(action);
  if(['End','Tab'].includes(action))s.send('keydown',{key:action});
  assert.equal(s.root.attrs['data-transitioning'],undefined);
  if(action==='pagehide'){assert.equal(s.events.wheel,undefined);assert.equal(s.frames.size,0)}
  if(action==='simple')assert.equal(s.send('wheel',{deltaY:80}).prevented,false);
 }
});
test('mobile browser-chrome resize does not interrupt a stable svh stage',()=>{
 const s=scene();s.send('wheel',{deltaY:1});s.send('resize');
 assert.equal(s.root.attrs['data-transitioning'],'');s.advance(1100);assert.equal(s.y,706);
});
