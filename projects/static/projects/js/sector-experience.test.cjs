const assert = require('node:assert/strict');
const {renderSectorExperience} = require('./demo-configurator.js');

function fixture(keys) {
  const panels = keys.map(key => ({dataset: {sectorPanel: key}, hidden: false}));
  const buttons = keys.map(key => ({dataset: {sectorGoal: key}, disabled: true, attrs: {}, setAttribute(name, value) {this.attrs[name] = value;}}));
  const note = {hidden: false};
  const experience = {
    querySelectorAll(selector) {return selector === '[data-sector-panel]' ? panels : buttons;},
    querySelector() {return note;},
  };
  return {experience, panels, buttons, note};
}

for (const keys of [
  ['tables','takeaway','menu'], ['enquiries','work','profile'], ['consult','services','clients'],
  ['appointments','care','education'], ['courses','webinars','learning'], ['collection','custom','shop'],
]) {
  const f = fixture(keys);
  assert.equal(renderSectorExperience(f.experience, ''), null);
  assert.deepEqual(f.panels.map(p => p.hidden), [false,true,true]);
  assert.ok(f.buttons.every(b => !b.disabled && b.attrs['aria-pressed'] === 'false'));
  assert.equal(f.note.hidden, false); // An illustrative default must not silently choose an enquiry goal.
  for (const [index, key] of keys.entries()) {
    assert.equal(renderSectorExperience(f.experience, key), f.panels[index]);
    assert.deepEqual(f.panels.map(p => p.hidden), keys.map((_, i) => i !== index));
    assert.equal(f.buttons.filter(b => b.attrs['aria-pressed'] === 'true').length, 1);
    assert.equal(f.note.hidden, true);
  }
  renderSectorExperience(f.experience, 'foreign');
  assert.deepEqual(f.panels.map(p => p.hidden), [false,true,true]);
  assert.ok(f.buttons.every(b => b.attrs['aria-pressed'] === 'false'));
  renderSectorExperience(f.experience, keys[1]);
  renderSectorExperience(f.experience, ''); // Settings/reset clears selection without leaving stale UI.
  assert.equal(f.note.hidden, false);
}
console.log('Sector renderer: six domains, all goals, invalid/empty/reset and accessibility states passed.');
