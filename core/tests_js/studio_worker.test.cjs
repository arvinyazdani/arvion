const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function harness(transferFailure=false){
 const workers=[],timers=new Map(),listeners={},docListeners={};let timerId=0;
 class Worker{constructor(url){this.url=url;this.messages=[];this.terminated=0;workers.push(this);}postMessage(data,transfer){this.messages.push({data,transfer});}terminate(){this.terminated++;}emit(data){this.onmessage({data});}}
 const parent={addEventListener(k,f){listeners[k]=f;},removeEventListener(k){delete listeners[k];}},offscreen={};
 const canvas={clientWidth:390,clientHeight:706,parentElement:parent,transferControlToOffscreen:()=>{if(transferFailure)throw new Error('transfer-failed');return offscreen;},getBoundingClientRect:()=>({left:0,top:0,width:390,height:706})};
 const document={hidden:false,querySelector:()=>null,addEventListener(k,f){docListeners[k]=f;},removeEventListener(k){delete docListeners[k];}};
 const context={module:{exports:{}},Worker,document,devicePixelRatio:2,
  setTimeout(fn,ms){timers.set(++timerId,{fn,ms});return timerId;},clearTimeout(id){timers.delete(id);},
  addEventListener(k,f){listeners[k]=f;},removeEventListener(k){delete listeners[k];}};
 vm.runInNewContext(fs.readFileSync('core/static/core/studio/tour.js','utf8'),context);
 let failures=0;
 const bridge=context.module.exports.createStudioWorker(canvas,'/static/core/studio/',{lite:true,rtl:true,covers:{a:'/media/cover.jpg'},shotIndices:[1,2,3,6]},()=>failures++);
 return{bridge,worker:workers[0],timers,listeners,docListeners,document,canvas,offscreen,get failures(){return failures;}};
}
test('renderer receives transferable canvas, preserves camera controls and releases all listeners',async()=>{
 const h=harness(),init=h.worker.messages[0];
 assert.equal(init.data.type,'init');assert.equal(init.transfer[0],h.offscreen);assert.equal(init.data.viewport.width,390);
 h.worker.emit({type:'ready',stats:{fps:60,quality:0}});const engine=await h.bridge.ready;
 assert.equal(h.timers.size,0);engine.start();engine.setP(.5);engine.setQuality(1);
 assert.equal(engine.stats().fps,60);assert.ok(h.worker.messages.some(m=>m.data.type==='progress'&&m.data.value===.5));
 h.document.hidden=true;h.docListeners.visibilitychange();assert.equal(h.worker.messages.at(-1).data.value,false);
 h.canvas.clientWidth=800;h.listeners.resize();assert.equal(h.worker.messages.at(-1).data.viewport.width,800);
 engine.dispose();engine.dispose();assert.equal(h.worker.terminated,1);assert.deepEqual(Object.keys(h.listeners),[]);assert.deepEqual(Object.keys(h.docListeners),[]);
});
test('startup timeout rejects promptly, terminates rendering and cannot resurrect',async()=>{
 const h=harness();const rejected=assert.rejects(h.bridge.ready,/renderer-cancelled/);
 const timer=[...h.timers.values()][0];assert.equal(timer.ms,20000);timer.fn();await rejected;
 h.worker.emit({type:'ready',stats:{fps:60}});assert.equal(h.worker.terminated,1);assert.equal(h.failures,0);
});
test('worker failure after readiness requests safe poster fallback exactly once',async()=>{
 const h=harness();h.worker.emit({type:'ready',stats:{fps:60}});await h.bridge.ready;
 h.worker.emit({type:'failed'});h.worker.emit({type:'failed'});assert.equal(h.failures,1);assert.equal(h.worker.terminated,1);
 h.worker.onerror({});assert.equal(h.failures,1);
});
test('cancellation during construction rejects and leaves no timers',async()=>{
 const h=harness();const rejected=assert.rejects(h.bridge.ready,/renderer-cancelled/);h.bridge.dispose();await rejected;assert.equal(h.timers.size,0);assert.equal(h.worker.terminated,1);
});
test('failed canvas transfer never installs listeners after disposing',async()=>{
 const h=harness(true);await assert.rejects(h.bridge.ready,/transfer-failed/);assert.equal(h.worker.terminated,1);assert.deepEqual(Object.keys(h.listeners),[]);assert.deepEqual(Object.keys(h.docListeners),[]);assert.equal(h.timers.size,0);
});
test('worker reuses the same engine with matching fonts and fails safely without required APIs',async()=>{
 const source=fs.readFileSync('core/static/core/studio/render-worker.js','utf8');
 const messages=[],faces=[];let closed=0,started=0,disposed=0;
 const engine={renderOnce(){},stats:()=>({fps:60}),playIntro(){},start(){started++;},stop(){},dispose(){disposed++;},size(){},setP(){},setVisible(){}};
 const context={self:{fonts:{add:f=>faces.push(f)},RvionStudioEngine:{create:async()=>engine}},location:{href:'https://rvionai.com/static/core/studio/render-worker.js'},URL,
  FontFace:class{constructor(name,src,options){this.name=name;this.src=src;this.options=options;}async load(){return this;}},
  importScripts(...paths){assert.equal(paths[2],'engine.js?v=5');},requestAnimationFrame(){},postMessage:m=>messages.push(m),setInterval:()=>1,clearInterval(){},close(){closed++;}};
 vm.runInNewContext(source,context);await context.onmessage({data:{type:'init',canvas:{},viewport:{width:390,height:706,dpr:2},options:{}}});
 assert.equal(faces.length,3);assert.ok(faces.every(f=>f.src.includes('/static/core/fonts/Vazirmatn-')));assert.equal(messages[0].type,'ready');
 await context.onmessage({data:{type:'start'}});assert.equal(started,1);await context.onmessage({data:{type:'dispose'}});assert.equal(disposed,1);assert.equal(closed,1);
 const unsupported={...context,self:{fonts:null}};vm.runInNewContext(source,unsupported);await unsupported.onmessage({data:{type:'init'}});assert.equal(messages.at(-1).type,'failed');
});
