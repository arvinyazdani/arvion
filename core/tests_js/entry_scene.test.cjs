const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const scene = fs.readFileSync('core/static/core/js/entry.js', 'utf8');
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
console.log('Entry scene: timing, deterministic seek, finite mobile camera, silent/no-network contracts passed.');
