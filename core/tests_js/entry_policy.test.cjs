const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {rvionEntryAdmission: admit} = require('../static/core/js/site-shell.js');
const base = {path: '/fa/', type: 'navigate', referrer: '', origin: 'https://rvionai.com', reduced: false, now: 1000000, state: null};
assert.ok(admit(base).show);
assert.ok(admit({...base, path: '/en/'}).show);
assert.ok(admit({...base, referrer: 'https://google.com/'}).show);
assert.ok(admit({...base, type: 'reload', referrer: base.origin + '/fa/start/'}).show);
for (const change of [{path:'/fa/start/'},{type:'back_forward'},{reduced:true},{referrer:base.origin+'/en/contact/'}]) assert.equal(admit({...base,...change}).show,false);
let state = null;
for(let i=0;i<3;i++){const result=admit({...base,now:base.now+i*10000,state});assert.ok(result.show);state=result.state;}
const fourth=admit({...base,now:base.now+30000,state});
assert.equal(fourth.show,false);
assert.equal(fourth.state.blockedUntil,base.now+330000);
assert.equal(admit({...base,now:base.now+329999,state:fourth.state}).show,false);
assert.ok(admit({...base,now:base.now+330000,state:fourth.state}).show);
assert.ok(admit({...base,now:base.now+91000,state:{starts:[base.now],blockedUntil:0}}).show);
assert.ok(admit({...base,state:{starts:['bad',Infinity],blockedUntil:'forever'}}).show);
// Exercise the real loader, including persistence of the fourth-start cooldown.
const source=fs.readFileSync('core/static/core/js/site-shell.js','utf8');
const boot=source.slice(source.indexOf("  const entryPayload ="),source.indexOf('  const setMainBusy ='));
function run(saved, unavailable=false){
 const writes=[],assets=[];
 const context={URL,URLSearchParams,Date:{now:()=>base.now+30000},rvionEntryAdmission:admit,
  localStorage:{getItem(){if(unavailable)throw Error('disabled');return JSON.stringify(saved);},setItem(k,v){writes.push(JSON.parse(v));}},
  location:{pathname:'/fa/',origin:base.origin,hostname:'rvionai.com',search:''},
  performance:{getEntriesByType:()=>[{type:'reload'}]},prefersReducedMotion:()=>false,navigationScheduled:false,
  window:{setTimeout:()=>1,clearTimeout(){},RvionEntry:{start:()=>true}},
  document:{readyState:'complete',referrer:'',getElementById:()=>({textContent:JSON.stringify({html:'x',css:'/static/core/css/entry.css?v=1',js:'/static/core/js/entry.js?v=1'})}),createElement:()=>({remove(){}}),head:{append(asset){assets.push(asset);asset.onload();}}}
 };
 vm.runInNewContext(boot,context);return {writes,assets};
}
assert.equal(run(state).assets.length,0);
assert.equal(run(state).writes[0].blockedUntil,fourth.state.blockedUntil);
assert.equal(run(null).assets.length,2);
assert.equal(run(null,true).assets.length,2);
console.log('Entry admission: direct/reload/internal/back/reduced, 4th-start cooldown, expiry, denied persistence, unavailable storage and two-asset loader passed.');
