/* Optional scroll enhancement only. No state, requests, animation loop or tracking. */
function studioStaticMode({reduced = false, saveData = false, memory = 8, cores = 8} = {}) {
  return reduced || saveData || memory <= 2 || cores <= 2;
}
if (typeof module !== 'undefined') module.exports = {studioStaticMode};
if (typeof document !== 'undefined') {
  const studio = document.querySelector('.hs-home');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const connection = navigator.connection;
  const update = () => studio?.toggleAttribute('data-static-studio', studioStaticMode({
    reduced: motion.matches, saveData: Boolean(connection?.saveData),
    memory: navigator.deviceMemory, cores: navigator.hardwareConcurrency,
  }));
  update();
  motion.addEventListener?.('change', update);
  connection?.addEventListener?.('change', update);
}
