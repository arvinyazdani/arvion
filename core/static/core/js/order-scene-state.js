/* Pure, testable state; no storage, identity or DOM dependencies. */
(function (host) {
  'use strict';
  function create(catalogue) {
    const c = catalogue.initial || {};
    return {step: 0, visited: 0, editing: false, palette: c.palette || '', look: c.look || '',
      topic: c.type || '', brand: '', features: (c.modules || '').split(',').filter(Boolean),
      extensions: (c.extensions || '').split(',').filter(Boolean), addons: (c.addons || '').split(',').filter(Boolean),
      consult: c.consult === '1'};
  }
  function transition(state, action, catalogue) {
    const s = {...state, features: [...state.features], extensions: [...state.extensions], addons: [...state.addons]};
    if (action.type === 'choose') {
      const lists = {palette: catalogue.palettes, look: catalogue.looks, topic: catalogue.topics.map(t => [t.key])};
      if (!lists[action.field]?.some(row => row[0] === action.value)) return state;
      if (action.field === 'topic' && s.topic !== action.value) {s.features = []; s.extensions = [];}
      s[action.field] = action.value;
    } else if (action.type === 'toggle') {
      const topic = catalogue.topics.find(t => t.key === s.topic);
      const allowed = action.field === 'addons' ? catalogue.addons : topic?.[action.field];
      if (!allowed?.some(row => row[0] === action.value)) return state;
      const list = new Set(s[action.field]); list.has(action.value) ? list.delete(action.value) : list.add(action.value);
      s[action.field] = [...list].sort();
    } else if (action.type === 'brand') {s.brand = String(action.value).slice(0, 40);
    } else if (action.type === 'consult') {s.consult = !s.consult;
    } else if (action.type === 'edit' && action.step >= 0 && action.step < 4 && s.visited === 4) {
      s.step = action.step; s.editing = true; s.editTopic = s.topic;
    } else if (action.type === 'go' && action.step >= 0 && action.step <= s.visited) {s.step = action.step;
    } else if (action.type === 'next') {
      if (s.step === 0 && !s.palette || s.step === 1 && !s.look || s.step === 2 && !s.topic) return state;
      // A topic change always revisits its modules; edits of other steps return to final.
      s.step = s.editing && (s.step !== 2 || s.editTopic === s.topic) ? 4 : Math.min(4, s.step + 1);
      s.visited = Math.max(s.visited, s.step); if (s.step === 4) s.editing = false;
    }
    return s;
  }
  function choices(s) {
    const result = {type: s.topic, palette: s.palette, look: s.look};
    if (s.addons.length) result.addons = s.addons.join(',');
    if (s.consult) result.consult = '1';
    if (s.topic === 'crm') {
      if (s.features.length) result.modules = s.features.join(',');
      if (s.extensions.length) result.extensions = s.extensions.join(',');
    }
    return result;
  }
  const api = {create, transition, choices};
  if (typeof module !== 'undefined') module.exports = api; else host.RvionOrderState = api;
})(typeof window === 'undefined' ? {} : window);
