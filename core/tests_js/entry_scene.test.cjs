const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const scene = fs.readFileSync('core/static/core/js/entry.js', 'utf8');
const css = fs.readFileSync('core/static/core/css/entry.css', 'utf8');
assert.match(css, /@media\(max-width:760px\)[\s\S]*?\.paths\{grid-template-columns:minmax\(0,1fr\)/);
assert.doesNotMatch(css, /\.path span\{/,'nested translated CTA text must inherit its title/button colour');
assert.match(css,/\.world\{[^}]*contain:layout paint/);
assert.match(css,/\.room\{[^}]*contain:layout paint/);
assert.match(css,/\.cap\{height:5em/,'caption height must be reserved before copy changes');
const element = () => ({style: {setProperty() {}}, classList: {toggle() {}, add() {}, remove() {}}, setAttribute() {}, innerHTML: '', textContent: '# idea → design → code → launch'});
const nodes = new Map();
const root = element();
root.querySelector = selector => {
  if (!nodes.has(selector)) nodes.set(selector, element());
  return nodes.get(selector);
};
root.querySelector('[data-entry-id="captions"]').children = [
  {innerHTML: 'Every website starts as an idea on a desk.'},
  {innerHTML: 'Let’s step inside.<small>See how your project gets built</small>'}
];
root.querySelector('[data-entry-id="fx"]').getContext = () => new Proxy({}, {get: () => () => {}, set: () => true});
root.querySelectorAll = () => Array.from({length: 5}, element);
const context = {window: {}, innerWidth: 390, innerHeight: 844, devicePixelRatio: 2};
vm.runInNewContext(scene, context);
const timeline = context.window.RvionEntry.mount(root);
timeline.measure();
assert.ok(Math.abs(timeline.T_FINAL - 11.1) < 0.001);
assert.ok(Math.abs(timeline.T_END - 12.5) < 0.001);
for (const time of [0, 0.8, 3.6, 5.1, 7.5, 10.4, 12.5]) {
  const first = JSON.stringify(timeline.camera(time));
  timeline.render(time);
  timeline.render(12.5);
  timeline.render(time);
  assert.equal(JSON.stringify(timeline.camera(time)), first, 'seek must not depend on previous frames');
  assert.ok(Object.values(timeline.camera(time)).every(Number.isFinite));
}
assert.doesNotMatch(scene, /\b(fetch|XMLHttpRequest|sendBeacon|Audio|AudioContext)\b/);
assert.doesNotMatch(scene, /[\u0600-\u06ff]/);
assert.doesNotMatch(scene, /style\.(filter|width)\s*=/);
// Structural projection regression: geometry reads only on measure, stable
// parent bounds, deterministic seek and restoration before a resize measurement.
// Browser/Lighthouse separately verifies real native DOMMatrix geometry and CLS.
class MatrixTrace {
  constructor(value=[]){this.ops=[value];}
  append(op){const m=new MatrixTrace();m.ops=[...this.ops,op];return m;}
  translate(...v){return this.append(['translate',v]);}
  rotateAxisAngle(...v){return this.append(['rotate',v]);}
  multiply(m){return this.append(['multiply',m.ops]);}
  inverse(){return this.append(['inverse']);}
  toString(){return JSON.stringify(this.ops);}
}
context.DOMMatrix=MatrixTrace;
let reads=0;
context.getComputedStyle=node=>{reads++;return {transform:node.style.transform||'none',transformOrigin:'0px 0px 0px'};};
for(const node of nodes.values()){node.parentElement=root;node.offsetLeft=10;node.offsetTop=20;}
const oldAll=root.querySelectorAll;
root.querySelectorAll=()=>oldAll().map(node=>Object.assign(node,{parentElement:root,offsetLeft:10,offsetTop:20}));
const projected=context.window.RvionEntry.mount(root);
const parentTransform=root.querySelector('[data-entry-id="world"]').style.transform;
projected.measure();
const measuredReads=reads;
projected.render(.8);
const firstProjection=root.querySelector('[data-entry-id="scr"]').style.transform;
projected.render(7.5);projected.render(.8);
assert.equal(root.querySelector('[data-entry-id="scr"]').style.transform,firstProjection);
assert.equal(reads,measuredReads,'no per-frame layout/style reads');
assert.equal(root.querySelector('[data-entry-id="world"]').style.transform,parentTransform,'camera must not move a scene parent');
projected.measure();projected.render(.8);
assert.equal(root.querySelector('[data-entry-id="scr"]').style.transform,firstProjection,'resize must not compound a previously projected transform');
async function codecChecks(){
  Object.assign(context,{DecompressionStream,Blob,Response,Uint8Array,atob});
  const html='<div id="rvion-entry">فارسی & English</div>';
  const payload={scene_gzip:require('node:zlib').gzipSync(html).toString('base64')};
  assert.equal((await context.window.RvionEntry.decode(payload)).html,html);
  await assert.rejects(context.window.RvionEntry.decode({scene_gzip:'invalid'}));
  delete context.DecompressionStream;
  await assert.rejects(context.window.RvionEntry.decode(payload),/unavailable/);
}
codecChecks().then(()=>console.log('Entry scene: timeline/projection/resize and UTF-8 gzip success/failure contracts passed.')).catch(error=>{console.error(error);process.exitCode=1;});
