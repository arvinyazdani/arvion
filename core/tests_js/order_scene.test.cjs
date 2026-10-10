const assert = require('node:assert/strict');
const api = require('../static/core/js/order-scene-state.js');
const catalogue = {initial: {}, palettes: [['warm'], ['gold']], looks: [['modern'], ['soft']], addons: [['support']],
  topics: [{key: 'ecommerce', features: [['payment'], ['catalog']], extensions: []}, {key: 'crm', features: [['sales']], extensions: [['ai']]}]};
let state = api.create(catalogue);
const send = action => {state = api.transition(state, action, catalogue);};
assert.deepEqual(state.features, []); send({type: 'next'}); assert.equal(state.step, 0);
send({type: 'go', step: 4}); assert.equal(state.step, 0);
for (const [field, value] of [['palette', 'warm'], ['look', 'modern'], ['topic', 'ecommerce']]) {send({type: 'choose', field, value}); send({type: 'next'});}
send({type: 'toggle', field: 'features', value: 'payment'});
send({type: 'toggle', field: 'features', value: 'foreign'}); assert.deepEqual(state.features, ['payment']);
send({type: 'brand', value: '<script>' + 'x'.repeat(100)}); assert.equal(state.brand.length, 40);
send({type: 'next'}); assert.equal(state.step, 4);
send({type: 'edit', step: 0}); send({type: 'choose', field: 'palette', value: 'gold'}); send({type: 'next'}); assert.equal(state.step, 4);
send({type: 'edit', step: 2}); send({type: 'next'}); assert.equal(state.step, 4);
send({type: 'edit', step: 2}); send({type: 'choose', field: 'topic', value: 'crm'}); assert.deepEqual(state.features, []); send({type: 'next'}); assert.equal(state.step, 3);
send({type: 'toggle', field: 'features', value: 'sales'}); send({type: 'toggle', field: 'extensions', value: 'ai'}); send({type: 'toggle', field: 'addons', value: 'support'}); send({type: 'next'});
assert.deepEqual(api.choices(state), {type: 'crm', palette: 'gold', look: 'modern', modules: 'sales', extensions: 'ai', addons: 'support'});
assert.ok(!JSON.stringify(api.choices(state)).includes('script'));
send({type: 'choose', field: 'palette', value: 'http://foreign/'}); assert.equal(state.palette, 'gold');
console.log('Order scene state: selection, editing, topic reset and payload contracts PASS');
