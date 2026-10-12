const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('core/static/core/js/site-shell.js','utf8');
const block = source.slice(source.indexOf('  const welcome ='),source.indexOf('  const revealItems ='));
function environment(reduced=false,arrival=false){
 const attrs=new Map(),htmlAttrs=new Set(arrival?['data-arrival-loading']:[]),classes=new Set(arrival?['navigation-pending']:[]),listeners={},timers=new Map(),frames=new Map();let id=0,locked=false;
 const loader={setAttribute:(k,v)=>attrs.set(k,v),classList:{remove(){},add(){}}};
 const main={setAttribute:(k,v)=>attrs.set(k,v),toggleAttribute:(k,v)=>{locked=v;}};
 const context={URL,location:{href:'https://rvionai.com/fa/',origin:'https://rvionai.com',pathname:'/fa/',search:''},
  document:{querySelector:s=>s==='main'?main:loader,querySelectorAll:s=>s==='[data-route-shell]'?[main]:[],getElementById:()=>null,
   documentElement:{hasAttribute:x=>htmlAttrs.has(x),removeAttribute:x=>htmlAttrs.delete(x),classList:{add:x=>classes.add(x),remove:x=>classes.delete(x)}},addEventListener:(name,fn)=>{listeners[name]=fn;}},
  window:{matchMedia:()=>({matches:reduced,addEventListener(){}}),requestAnimationFrame:fn=>{frames.set(++id,fn);return id},cancelAnimationFrame:i=>frames.delete(i),setTimeout:(fn,delay)=>{timers.set(++id,{fn,delay});return id;},clearTimeout:i=>timers.delete(i),addEventListener:(name,fn)=>{listeners[name]=fn;}},HTMLFormElement:class {}
 };
 vm.runInNewContext(block,context);
 return {attrs,classes,listeners,timers,htmlAttrs,get locked(){return locked;},paint(){const pending=[...frames];frames.clear();pending.forEach(([,fn])=>fn())},fire(delay){const [key,timer]=[...timers].find(([,t])=>t.delay===delay);timers.delete(key);timer.fn();},click(link){listeners.click({target:{closest:()=>link},button:0});}};
}
const link={href:'https://rvionai.com/fa/start/',target:'',dataset:{},hasAttribute:()=>false};
let e=environment();
assert.equal(e.attrs.get('aria-hidden'),'true');
e.click(link);
assert.equal(e.attrs.get('aria-busy'),'true');
assert.equal(e.timers.size,2);
e.fire(160);
assert.equal(e.attrs.get('aria-hidden'),'false');assert.ok(e.locked);assert.ok(e.classes.has('navigation-pending'));
e.listeners.pageshow({persisted:false});assert.equal(e.attrs.get('aria-hidden'),'true');assert.equal(e.locked,false);assert.equal(e.timers.size,0);
e.click(link);e.fire(8000);assert.equal(e.attrs.get('aria-busy'),'false');assert.equal(e.locked,false);
e=environment(true);e.click(link);assert.equal(e.timers.size,2);e.fire(160);assert.equal(e.attrs.get('aria-hidden'),'false');e.fire(8000);assert.equal(e.locked,false);
for(const change of [{href:'https://outside.example/'},{dataset:{noLoader:''}},{target:'_blank'},{href:'https://rvionai.com/fa/#main'}]){const n=environment();n.click({...link,...change});assert.equal(n.timers.size,0);}
console.log('Navigation loader: delayed reveal, background lock, pageshow/failsafe recovery, reduced-motion and link exclusions passed.');
e=environment(false,true);assert.equal(e.attrs.get('aria-hidden'),'false');e.listeners.pageshow({persisted:false});assert.ok(e.classes.has('navigation-pending'));
e.paint();e.paint();e.fire(240);assert.equal(e.classes.has('navigation-pending'),false);assert.equal(e.htmlAttrs.has('data-arrival-loading'),false);
e=environment(false,true);e.paint();e.paint();e.click(link);assert.equal([...e.timers.values()].some(t=>t.delay===240),false);e.fire(160);assert.ok(e.locked);e.fire(8000);assert.equal(e.locked,false);
e=environment(false,true);e.listeners.pageshow({persisted:true});assert.equal(e.classes.has('navigation-pending'),false);
console.log('Home arrival: two-paint exit, reload, bfcache and immediate navigation recovery passed.');
const arrivalSource=fs.readFileSync('core/templates/core/includes/arrival_loader.html','utf8').split('<script>')[1].split('</script>')[0];
for(const reduced of [false,true]){
 const flags=new Set(),classes=new Set();let recover;
 vm.runInNewContext(arrivalSource,{matchMedia:()=>({matches:reduced}),setTimeout:(fn,ms)=>{assert.equal(ms,1500);recover=fn},document:{documentElement:{setAttribute:k=>flags.add(k),hasAttribute:k=>flags.has(k),removeAttribute:k=>flags.delete(k),classList:{add:k=>classes.add(k),remove:k=>classes.delete(k)}}}});
 assert.equal(flags.has('data-arrival-loading'),true);assert.equal(classes.has('navigation-pending'),true);
 recover();assert.equal(flags.size,0);assert.equal(classes.size,0);
}
console.log('Arrival bootstrap: same static reduced-motion feedback and independent failed-script recovery passed.');
