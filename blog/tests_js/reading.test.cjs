const assert = require('node:assert/strict');
const test = require('node:test');
const {progress, activeHeading, showContents, bindSheet, bindOpener} = require('../static/blog/js/reading.js');

test('progress is bounded and follows the reading body, including short text', () => {
  assert.equal(progress(1000, 2000, 800), 0);
  assert.equal(progress(120, 2000, 800), 0);
  assert.equal(progress(-540, 2000, 800), 50);
  assert.equal(progress(-2000, 2000, 800), 100);
  assert.equal(progress(120, 100, 800), 100);
});
test('scrollspy chooses the last reached heading and clears above the body', () => {
  assert.equal(activeHeading([{id:'a',top:200}]), null);
  assert.equal(activeHeading([{id:'a',top:-100},{id:'b',top:150},{id:'c',top:400}]), 'b');
});
test('mobile TOC disappears above and below article and on desktop', () => {
  assert.equal(showContents(1000, 4000, 844, true), false);
  assert.equal(showContents(200, 3000, 844, true), true);
  assert.equal(showContents(-2000, 100, 844, true), false);
  assert.equal(showContents(200, 3000, 800, false), false);
});
test('sheet opens, closes, traps focus, supports Escape and restores focus', () => {
  const listeners = {}, buttonListeners = {}, attrs = {};
  let focused = null, locked = false;
  const closeButton = {addEventListener: (n,f) => listeners['button-'+n] = f, focus: () => focused = closeButton};
  const last = {focus: () => focused = last};
  const button = {addEventListener: (n,f) => buttonListeners[n] = f, setAttribute: (n,v) => attrs[n] = v, focus: () => focused = button};
  const doc = {activeElement:button, documentElement:{classList:{add:()=>locked=true, remove:()=>locked=false}}};
  const sheet = {open:false, showModal(){this.open=true;}, close(){this.open=false;listeners.close();},
    querySelector:()=>closeButton, querySelectorAll:()=>[closeButton,last], addEventListener:(n,f)=>listeners[n]=f};
  bindSheet(sheet,button,doc);
  buttonListeners.click();
  assert.equal(sheet.open,true);assert.equal(attrs['aria-expanded'],'true');assert.equal(locked,true);
  doc.activeElement=last;
  let prevented=false;
  listeners.keydown({key:'Tab',shiftKey:false,preventDefault:()=>prevented=true});
  assert.equal(focused,closeButton);assert.equal(prevented,true);
  doc.activeElement=closeButton;
  listeners.keydown({key:'Tab',shiftKey:true,preventDefault(){}});assert.equal(focused,last);
  listeners.keydown({key:'Escape',preventDefault(){}});
  assert.equal(sheet.open,false);assert.equal(attrs['aria-expanded'],'false');assert.equal(locked,false);assert.equal(focused,button);
  buttonListeners.click();listeners['button-click']();assert.equal(sheet.open,false);
});

function openerFixture({seen=false, reduce=false, blocked=false}={}) {
  const events={}, controls={}, timers=new Map(), classes=new Set();
  let next=0, stored=seen;
  const buttons={};
  ['skip','replay'].forEach(name=>buttons[name]={hidden:true,addEventListener:(key,fn)=>controls[name]=fn});
  const media={matches:reduce,addEventListener:(key,fn)=>events.reduce=fn};
  const opener={offsetWidth:600,style:{setProperty(){}},classList:{add:x=>classes.add(x),remove:x=>classes.delete(x)},
    querySelectorAll:()=>[1,2,3].map(()=>({style:{setProperty(){}}})),
    querySelector:s=>buttons[s.includes('skip')?'skip':'replay'],addEventListener:(name,fn)=>events.click=fn};
  const win={matchMedia:()=>media,sessionStorage:{getItem(){if(blocked)throw Error();return stored;},setItem(){stored=true;}},
    setTimeout(fn){timers.set(++next,fn);return next;},clearTimeout:id=>timers.delete(id),addEventListener:(key,fn)=>events[key]=fn};
  const doc={hidden:false,addEventListener:(key,fn)=>events[key]=fn};
  bindOpener(opener,win,doc);
  return {events,controls,timers,classes,buttons,media,doc};
}
test('opener autoplays once per session, can skip/replay, and clears pending timers',()=>{
  const f=openerFixture();assert.equal(f.classes.has('play'),true);assert.equal(f.buttons.skip.hidden,false);
  f.controls.skip();assert.equal(f.timers.size,0);assert.equal(f.classes.has('play'),false);assert.equal(f.buttons.replay.hidden,false);
  f.controls.replay();assert.equal(f.timers.size,1);f.controls.replay();assert.equal(f.timers.size,1);
  f.events.pagehide();assert.equal(f.timers.size,0);
  const second=openerFixture({seen:true});assert.equal(second.classes.size,0);assert.equal(second.timers.size,0);
});
test('reduced motion and unavailable storage never autoplay; preference change stops motion',()=>{
  for(const options of [{reduce:true},{blocked:true}]) {const f=openerFixture(options);assert.equal(f.classes.size,0);assert.equal(f.timers.size,0);}
  const f=openerFixture();f.media.matches=true;f.events.reduce();assert.equal(f.timers.size,0);assert.equal(f.buttons.replay.hidden,true);
});
test('completion and navigation restore final state; hidden document clears timer',()=>{
  const f=openerFixture();[...f.timers.values()][0]();assert.equal(f.classes.size,0);assert.equal(f.buttons.replay.hidden,false);
  f.controls.replay();f.events.click({target:{closest:()=>({})}});assert.equal(f.timers.size,0);
  f.controls.replay();f.doc.hidden=true;f.events.visibilitychange();assert.equal(f.timers.size,0);
});
