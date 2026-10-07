const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/assessments/js/copy-warning.js'), 'utf8');

function fixture({count=0, fa=true, selected=true, protectedText=true, failFirst=false, noCsrf=false}={}) {
  const message={}, counter={}, dismiss={hidden:true, addEventListener() {}};
  const panel={dataset:{count:String(count),lang:fa?'fa':'en'},
    querySelector(s) {return s==='[data-copy-message]'?message:s==='[data-copy-counter]'?counter:dismiss;}};
  const content={dataset:{copyQuestion:'123'}};
  const requests=[];
  let sequence=0;
  let handler;
  const document={querySelector(s) {
    if(s==='[data-copy-warning]')return panel;
    if(s==='[data-integrity-url]')return {dataset:{integrityUrl:'/events/'}};
    return noCsrf ? null : {value:'csrf'};
  }, querySelectorAll() {return [content];}, getElementById(){return null;},
  addEventListener(type, fn){assert.equal(type,'copy'); handler=fn;}};
  vm.runInNewContext(source, {document, window:{getSelection:()=>({isCollapsed:!selected,
    rangeCount:1,getRangeAt:()=>({intersectsNode:()=>protectedText})})},
    navigator:{onLine:true},crypto:{randomUUID:()=>`event-${++sequence}`},URLSearchParams,
    AbortController,setTimeout,clearTimeout,fetch:async (url,opts)=>{
      requests.push(Object.fromEntries(opts.body));
      if(failFirst&&requests.length===1)throw new Error('network');
      return {ok:true,json:async()=>({copy_count:count+1,integrity_score:98})};
    }});
  const event={isTrusted:true, prevented:false,preventDefault(){this.prevented=true;}};
  return {handler,event,requests,message,counter,panel};
}

test('question copy is blocked and displays only the server-confirmed count', async()=>{
  const f=fixture(); f.handler(f.event);
  await new Promise(setImmediate);
  assert.equal(f.event.prevented,true);
  assert.equal(f.requests.length,1);
  assert.equal(f.requests[0].item_id,'123');
  assert.equal(f.requests[0].copy_scope,'question');
  assert.match(f.counter.textContent,/۱$/);
});
test('an incomplete snapshot without an answer form does not crash',()=>{
  const f=fixture({noCsrf:true});
  assert.equal(f.handler,undefined);
  assert.equal(f.requests.length,0);
});
test('review text, empty selection and synthetic events never count',()=>{
  for(const options of [{protectedText:false},{selected:false}]){
    const f=fixture(options); f.handler(f.event);
    assert.equal(f.requests.length,0); assert.equal(f.event.prevented,false);
  }
  const f=fixture(); f.event.isTrusted=false; f.handler(f.event);
  assert.equal(f.requests.length,0);
});
test('retry keeps the same identifier and does not inflate the count',async()=>{
  const f=fixture({failFirst:true}); f.handler(f.event);
  await new Promise(setImmediate);
  assert.equal(f.requests.length,2);
  assert.equal(f.requests[0].copy_event_id,f.requests[1].copy_event_id);
  assert.match(f.counter.textContent,/۱$/);
});
test('rapid copies are sent sequentially with distinct identifiers',async()=>{
  const f=fixture();
  f.handler(f.event); f.handler(f.event); f.handler(f.event);
  await new Promise(setImmediate);
  assert.equal(f.requests.length,3);
  assert.equal(new Set(f.requests.map(r=>r.copy_event_id)).size,3);
});
test('a restored English fourth warning has Latin count and a serious warning',()=>{
  const f=fixture({count:4,fa:false});
  assert.equal(f.panel.dataset.stage,'4');
  assert.match(f.message.textContent,/Serious warning/);
  assert.match(f.counter.textContent,/4$/);
});
