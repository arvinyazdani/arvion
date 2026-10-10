/* One cancellable clock per visible studio scene. No state or transport ownership. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.RvionOrderMotion = factory();
})(typeof window === 'undefined' ? globalThis : window, function () {
  'use strict';
  function create(env) {
    let generation = 0;
    const timers = new Set(), frames = new Set();
    function stop() {
      generation++;
      timers.forEach(id => env.clearTimeout(id)); frames.forEach(id => env.cancelAnimationFrame(id));
      timers.clear(); frames.clear();
    }
    function after(ms, callback) {
      const run = generation;
      const id = env.setTimeout(() => {timers.delete(id); if (run === generation) callback();}, ms);
      timers.add(id); return id;
    }
    function animate(duration, update, done) {
      const run = generation; let start;
      const tick = time => {
        frames.delete(id);
        if (run !== generation) return;
        if (start === undefined) start = time;
        const fraction = Math.min(1, (time - start) / duration);
        update(fraction);
        if (fraction < 1) {id = env.requestAnimationFrame(tick); frames.add(id);}
        else if (done) done();
      };
      let id = env.requestAnimationFrame(tick); frames.add(id);
    }
    function cycle(ms, eligible, callback) {
      if (eligible()) after(ms, () => {if (eligible()) callback();});
    }
    return {stop, after, animate, cycle, pending: () => timers.size + frames.size};
  }
  return {create};
});
