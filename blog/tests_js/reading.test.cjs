const assert = require('node:assert/strict');
const test = require('node:test');
const {progress, activeHeading, showContents, bindSheet} = require('../static/blog/js/reading.js');

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
