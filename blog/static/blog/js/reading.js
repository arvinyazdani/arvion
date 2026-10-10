/* Read-only progressive enhancement: no requests, tracking, storage or animation. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else if (root.document) api.init(root.document, root);
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';
  function progress(top, height, viewport) {
    var distance = height - (viewport - 120);
    return Math.round(Math.max(0, Math.min(100,
      distance > 0 ? (120 - top) / distance * 100 : top <= 120 ? 100 : 0)));
  }
  function activeHeading(headings) {
    var active = null;
    headings.forEach(function (heading) { if (heading.top <= 160) active = heading.id; });
    return active;
  }
  function showContents(top, bottom, viewport, mobile) {
    return mobile && top < viewport * .65 && bottom > 160;
  }
  function bindSheet(dialog, button, doc) {
    var returnFocus = button;
    function close() { if (dialog.open) dialog.close(); }
    function open() {
      returnFocus = doc.activeElement;
      dialog.showModal();
      button.setAttribute('aria-expanded', 'true');
      doc.documentElement.classList.add('ar-sheet-open');
    }
    button.addEventListener('click', open);
    dialog.querySelector('[data-toc-close]').addEventListener('click', close);
    dialog.addEventListener('close', function () {
      button.setAttribute('aria-expanded', 'false');
      doc.documentElement.classList.remove('ar-sheet-open');
      if (returnFocus) returnFocus.focus({preventScroll: true});
    });
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) {
        var rect = dialog.getBoundingClientRect();
        if (event.clientY < rect.top || event.clientY > rect.bottom) close();
      }
      var link = event.target.closest('a[href^="#"]');
      if (link) {
        returnFocus = doc.getElementById(decodeURIComponent(link.hash.slice(1))) || button;
        if (returnFocus !== button) returnFocus.setAttribute('tabindex', '-1');
        close();
      }
    });
    dialog.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') { event.preventDefault(); close(); }
      if (event.key !== 'Tab') return;
      var items = Array.from(dialog.querySelectorAll('button,a[href]'));
      var first = items[0], last = items[items.length - 1];
      if (event.shiftKey && doc.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && doc.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    return {open: open, close: close};
  }
  function init(doc, win) {
    var article = doc.querySelector('[data-reader]');
    if (!article) return;
    var body = article.querySelector('.ar-prose');
    var bar = doc.querySelector('.ar-progress');
    var headings = Array.from(body.querySelectorAll('h2[id],h3[id]'));
    var links = Array.from(article.querySelectorAll('.ar-toc a,.ar-toc-sheet nav a'));
    var button = article.querySelector('[data-toc-open]');
    var sheet = article.querySelector('.ar-toc-sheet');
    var mobile = win.matchMedia('(max-width: 800px)');
    var supported = sheet && typeof sheet.showModal === 'function';
    if (supported) {
      bindSheet(sheet, button, doc);
    }
    headings.forEach(function (heading) {
      var link = doc.createElement('a');
      link.className = 'ar-heading-link';
      link.href = '#' + heading.id;
      link.textContent = '#';
      link.setAttribute('aria-label', (doc.documentElement.lang === 'fa' ? 'پیوند به بخش: ' : 'Link to section: ') + heading.textContent);
      heading.appendChild(link);
    });
    var queued = false;
    function update() {
      queued = false;
      var rect = body.getBoundingClientRect();
      var percent = progress(rect.top, rect.height, win.innerHeight);
      bar.setAttribute('aria-valuenow', String(percent));
      bar.firstElementChild.style.transform = 'scaleX(' + percent / 100 + ')';
      var active = activeHeading(headings.map(function (h) { return {id: h.id, top: h.getBoundingClientRect().top}; }));
      links.forEach(function (link) {
        if (decodeURIComponent(link.hash.slice(1)) === active) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
      if (supported) {
        button.hidden = !showContents(rect.top, rect.bottom, win.innerHeight, mobile.matches);
        if (sheet.open && (!mobile.matches || button.hidden)) sheet.close();
      }
    }
    function queue() { if (!queued) { queued = true; win.requestAnimationFrame(update); } }
    win.addEventListener('scroll', queue, {passive: true});
    win.addEventListener('resize', queue);
    if (mobile.addEventListener) mobile.addEventListener('change', queue);
    update();
    var copy = article.querySelector('[data-copy-article]');
    var status = article.querySelector('.ar-copy-status');
    var fallback = article.querySelector('.ar-copy-fallback');
    fallback.hidden = true;
    copy.disabled = false;
    copy.addEventListener('click', async function () {
      copy.disabled = true;
      try {
        if (!win.navigator.clipboard) throw new Error('Clipboard unavailable');
        await win.navigator.clipboard.writeText(fallback.value);
        status.textContent = copy.dataset.success;
        fallback.hidden = true;
      } catch (_) {
        status.textContent = copy.dataset.failure;
        fallback.hidden = false;
        fallback.focus(); fallback.select();
      } finally { copy.disabled = false; }
    });
  }
  return {progress: progress, activeHeading: activeHeading, showContents: showContents, bindSheet: bindSheet, init: init};
});
