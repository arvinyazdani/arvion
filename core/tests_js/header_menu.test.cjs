const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('core/static/core/js/site-shell.js', 'utf8');
const block = source.slice(source.indexOf('  if (menuButton && nav && scrim)'), source.indexOf('  if ("serviceWorker"'));
function element() {
  const classes = new Set(), attrs = new Map(), listeners = {};
  return {classes, attrs, listeners, dataset: {openLabel: 'Open menu', closeLabel: 'Close menu'},
    classList: {add: v => classes.add(v), remove: v => classes.delete(v), contains: v => classes.has(v)},
    setAttribute: (k,v) => attrs.set(k,v), getAttribute: k => attrs.get(k),
    toggleAttribute: (k,v) => v ? attrs.set(k,'') : attrs.delete(k),
    addEventListener: (k,v) => {listeners[k] = v;}, querySelectorAll: () => [], focus() {this.focused = true;}};
}
const menuButton = element(), nav = element(), scrim = element(), main = element(), body = element();
const windowListeners = {}, documentListeners = {};
let display = 'grid';
vm.runInNewContext(block, {menuButton, nav, scrim, closePreferences() {},
  getComputedStyle: () => ({display}),
  document: {body, querySelectorAll: () => [main], addEventListener: (k,v) => {documentListeners[k] = v;}},
  window: {requestAnimationFrame: () => 1, cancelAnimationFrame() {}, addEventListener: (k,v) => {windowListeners[k] = v;}}});
menuButton.listeners.click();
assert.equal(menuButton.attrs.get('aria-expanded'), 'true');
assert.ok(main.attrs.has('inert'));
windowListeners.resize();
assert.ok(nav.classes.has('is-open'), 'A still-visible tablet toggle must keep its menu open after resize');
documentListeners.keydown({key: 'Escape'});
assert.equal(menuButton.attrs.get('aria-expanded'), 'false');
assert.equal(main.attrs.has('inert'), false);
assert.equal(menuButton.focused, true);
menuButton.listeners.click();
display = 'none';
windowListeners.resize();
assert.equal(menuButton.attrs.get('aria-expanded'), 'false');
assert.equal(main.attrs.has('inert'), false);
console.log('Header menu: CSS-owned breakpoint, resize unlock and Escape focus restoration passed.');
