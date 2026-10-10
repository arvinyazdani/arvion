const assert = require('node:assert/strict'), vm = require('node:vm'), fs = require('node:fs');
class Element {
  constructor(tag) {this.tagName = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.style = {setProperty() {}}; this.textContent = '';}
  append(...children) {this.children.push(...children);}
  setAttribute(key, value) {this.attributes[key] = value;}
  set innerHTML(value) {throw Error('Untrusted HTML interpolation is forbidden');}
}
const window = {}, document = {createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag)};
vm.runInNewContext(fs.readFileSync(require.resolve('../static/core/js/order-scene-art.js'), 'utf8'), {window, document});
const art = window.RvionOrderArt, flatten = el => [el, ...el.children.flatMap(flatten)];
const say = (_, en) => en, icon = () => new Element('svg');
const ctx = {say, icon, topic: 'restaurant', look: 'modern', name: '<img onerror=bad>', copy: ['A new taste', 'A fictional restaurant', 'Seasonal menu'], palette: 'warm', selected: []};
const signature = {};
for (const look of ['modern', 'industrial', 'cinematic', 'video', 'classic', 'soft']) {
  const tree = art.site({...ctx, look}); signature[look] = flatten(tree).map(n => n.className || n.tagName).join('|');
  assert.equal(flatten(tree).filter(n => n.dataset.osBrand !== undefined).length, 2);
  assert.ok(flatten(tree).some(n => n.tagName === 'h3' && n.children.some(c => c.dataset.osBrand !== undefined)), 'Live brand is also inside the hero heading');
  assert.ok(flatten(tree).some(n => n.textContent === ctx.name), 'Brand is text, never evaluated');
  assert.ok(!/[\u0600-\u06ff]/.test(flatten(tree).map(n => n.textContent).join('')), 'English specimen copy contains no Persian interface text');
  assert.ok(art.lookCode[look].includes('{')); assert.ok(art.looks[look][0]); assert.ok(art.looks[look][1]);
}
assert.equal(new Set(Object.values(signature)).size, 6, 'Six distinct structural trees, not six decorations');
const introPaths = new Set();
for (const topic of ['ecommerce','restaurant','clinic','corporate','portfolio','education','jewelry','crm','other']) {
  const tree = art.intro(topic, icon); const paths = flatten(tree).filter(n => n.tagName === 'path');
  assert.ok(paths.length >= 2); introPaths.add(paths.map(n => n.attributes.d).join('|'));
}
assert.equal(introPaths.size, 9, 'All topics own distinct SVG scenes');
for (const key of ['payment','booking','catalog','membership','blog','multilingual','webapp','support','customers','sales','visits','correspondence','accounting','inventory','automation','security','ai','channels','workflows','mobile','portal']) {
  const section = art.section(key, 'Feature label', ctx); assert.equal(section.dataset.feature, key); assert.ok(section.children.length > 2);
}
console.log('Order art: six structures, nine SVG topics, real feature keys and text-only brand PASS');
