import {test} from 'node:test';
import assert from 'node:assert/strict';
import {initialState, updateChoice, activeChapter, addItem} from './model.mjs';

test('invalid URL choices never become DOM values', () => {
  assert.deepEqual(initialState(new URLSearchParams('palette=__proto__&style=<script>&features=unknown')), {palette:'olive',style:'editorial',features:[]});
});
test('URL state restores only allowlisted choices', () => {
  assert.deepEqual(initialState(new URLSearchParams('palette=cobalt&style=industrial&features=basket,newsletter,basket')), {palette:'cobalt',style:'industrial',features:['basket','newsletter']});
});
test('explicitly empty features stays empty on reload', () => assert.deepEqual(initialState(new URLSearchParams('features=')).features, []));
test('default reset is deterministic', () => assert.deepEqual(initialState(), {palette:'olive',style:'editorial',features:['catalog','basket']}));
test('choice updates preserve other settings without mutation', () => {
  const before = initialState(); const after = updateChoice(before,'style','minimal');
  assert.equal(before.style,'editorial'); assert.equal(after.style,'minimal'); assert.equal(after.palette,'olive');
});
test('unknown choices and keys do not change state', () => {
  const state = initialState(); assert.equal(updateChoice(state,'palette','bad'),state); assert.equal(updateChoice(state,'owner','x'),state);
});
test('features are deduplicated in canonical order', () => assert.deepEqual(updateChoice(initialState(),'features',['newsletter','basket','basket','other']).features,['basket','newsletter']));
test('forward and backwards scroll choose the chapter at the reading point', () => {
  assert.equal(activeChapter([{top:-500,bottom:0},{top:0,bottom:500},{top:500,bottom:1000}],800),1);
  assert.equal(activeChapter([{top:0,bottom:700},{top:700,bottom:1400}],800),0);
});
test('outside story picks closest end rather than looping', () => {
  assert.equal(activeChapter([{top:-1400,bottom:-700},{top:-700,bottom:0}],800),1);
  assert.equal(activeChapter([{top:700,bottom:1400},{top:1400,bottom:2100}],800),0);
});
test('basket is immutable, bounded and allowlisted', () => {
  const before = {chair:8}; assert.deepEqual(addItem(before,'chair'),{chair:9}); assert.deepEqual(addItem({chair:9},'chair'),{chair:9}); assert.deepEqual(before,{chair:8}); assert.equal(addItem(before,'unknown'),before);
});
