/* Read-only enhancement. No tracking, persistence or third-party requests. */
(function () {
  'use strict';
  var article = document.querySelector('[data-reader]');
  if (!article) return;
  var toc = article.querySelector('.journal-toc');
  var media = window.matchMedia('(min-width: 701px)');
  function adapt() { if (toc) toc.open = media.matches; }
  adapt();
  if (media.addEventListener) media.addEventListener('change', adapt);
  var body = article.querySelector('.journal-prose');
  var progress = document.querySelector('.journal-progress');
  var headings = Array.from(body.querySelectorAll('h2[id],h3[id]'));
  var links = toc ? Array.from(toc.querySelectorAll('a')) : [];
  var queued = false;
  function update() {
    queued = false;
    var rect = body.getBoundingClientRect();
    var distance = rect.height - (window.innerHeight - 120);
    var percent = Math.round(Math.max(0, Math.min(100, distance > 0 ? (120 - rect.top) / distance * 100 : rect.top < window.innerHeight ? 100 : 0)));
    if (progress) {
      progress.setAttribute('aria-valuenow', String(percent));
      progress.firstElementChild.style.transform = 'scaleX(' + percent / 100 + ')';
    }
    var active = null;
    headings.forEach(function (h) { if (h.getBoundingClientRect().top <= 160) active = h.id; });
    links.forEach(function (link) {
      if (decodeURIComponent(link.hash.slice(1)) === active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
  function queue() { if (!queued) { queued = true; requestAnimationFrame(update); } }
  window.addEventListener('scroll', queue, {passive: true});
  window.addEventListener('resize', queue);
  update();
  var button = article.querySelector('[data-copy-article]');
  var status = article.querySelector('.journal-copy-status');
  var fallback = article.querySelector('.journal-copy-fallback');
  button.addEventListener('click', async function () {
    button.disabled = true;
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(fallback.value);
      status.textContent = button.dataset.success;
      fallback.hidden = true;
    } catch (_) {
      status.textContent = button.dataset.failure;
      fallback.hidden = false;
      fallback.focus();
      fallback.select();
    } finally { button.disabled = false; }
  });
  // No inactive-looking action before enhancement has actually initialized.
  button.disabled = false;
})();
