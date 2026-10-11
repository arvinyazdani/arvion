const {test} = require('node:test');
const assert = require('node:assert/strict');
const {studioStaticMode} = require('../static/core/js/studio-motion.js');
test('ordinary devices may use CSS scroll enhancement', () => assert.equal(studioStaticMode(), false));
test('reduced motion stays static', () => assert.equal(studioStaticMode({reduced:true}), true));
test('data saving stays static', () => assert.equal(studioStaticMode({saveData:true}), true));
test('low memory or core count stays static', () => {
  assert.equal(studioStaticMode({memory:2}), true);
  assert.equal(studioStaticMode({cores:2}), true);
  assert.equal(studioStaticMode({memory:undefined, cores:undefined}), false);
});
