const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('core/static/core/js/site-shell.js','utf8');
const block = source.slice(source.indexOf('  const welcome ='),source.indexOf('  const revealItems ='));
function environment(reduced=false){
 const attrs=new Map(),classes=new Set(),listeners={},timers=new Map();let id=0,locked=false;
 const loader={setAttribute:(k,v)=>attrs.set(k,v),classList:{remove(){}}};
 const main={setAttribute:(k,v)=>attrs.set(k,v),toggleAttribute:(k,v)=>{locked=v;}};
 const context={URL,location:{href:'https://rvionai.com/fa/',origin:'https://rvionai.com',pathname:'/fa/',search:''},
  document:{querySelector:s=>s==='main'?main:loader,querySelectorAll:s=>s==='[data-route-shell]'?[main]:[],getElementById:()=>null,
   documentElement:{classList:{add:x=>classes.add(x),remove:x=>classes.delete(x)}},addEventListener:(name,fn)=>{listeners[name]=fn;}},
  window:{matchMedia:()=>({matches:reduced,addEventListener(){}}),setTimeout:(fn,delay)=>{timers.set(++id,{fn,delay});return id;},clearTimeout:i=>timers.delete(i),addEventListener:(name,fn)=>{listeners[name]=fn;}},HTMLFormElement:class {}
 };
 vm.runInNewContext(block,context);
 return {attrs,classes,listeners,timers,get locked(){return locked;},fire(delay){const [key,timer]=[...timers].find(([,t])=>t.delay===delay);timers.delete(key);timer.fn();},click(link){listeners.click({target:{closest:()=>link},button:0});}};
}
const link={href:'https://rvionai.com/fa/start/',target:'',dataset:{},hasAttribute:()=>false};
let e=environment();
assert.equal(e.attrs.get('aria-hidden'),'true');
e.click(link);
assert.equal(e.attrs.get('aria-busy'),'true');
assert.equal(e.timers.size,2);
e.fire(160);
assert.equal(e.attrs.get('aria-hidden'),'false');assert.ok(e.locked);assert.ok(e.classes.has('navigation-pending'));
e.listeners.pageshow();assert.equal(e.attrs.get('aria-hidden'),'true');assert.equal(e.locked,false);assert.equal(e.timers.size,0);
e.click(link);e.fire(8000);assert.equal(e.attrs.get('aria-busy'),'false');assert.equal(e.locked,false);
e=environment(true);e.click(link);assert.equal(e.timers.size,1);assert.equal(e.attrs.get('aria-hidden'),'true');
for(const change of [{href:'https://outside.example/'},{dataset:{noLoader:''}},{target:'_blank'},{href:'https://rvionai.com/fa/#main'}]){const n=environment();n.click({...link,...change});assert.equal(n.timers.size,0);}
console.log('Navigation loader: delayed reveal, background lock, pageshow/failsafe recovery, reduced-motion and link exclusions passed.');
