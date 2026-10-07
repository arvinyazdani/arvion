(() => {
  const record = document.querySelector('[data-customer-record]');
  if (!record) return;
  const panels = [...record.querySelectorAll('[data-record-panel]')];
  const links = [...record.querySelectorAll('.cr-tabs a')];
  const show = (focus = false) => {
    const target = document.getElementById(location.hash.slice(1));
    const panel = target?.closest('[data-record-panel]') || panels[0];
    panels.forEach(item => { item.hidden = item !== panel; });
    links.forEach(link => {
      if (link.hash === '#' + panel.id) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    if (target instanceof HTMLDetailsElement) target.open = true;
    if (target && focus) {
      (target instanceof HTMLDetailsElement ? target.querySelector('summary') : target).focus({preventScroll: true});
    }
  };
  show();
  window.addEventListener('hashchange', () => show(true));
  record.querySelectorAll('.cr-action-menu a').forEach(link => link.addEventListener('click', () => {
    record.querySelector('.cr-new-action').open = false;
    const target = document.getElementById(link.hash.slice(1));
    if (target instanceof HTMLDetailsElement) target.open = true;
    show();
  }));
  record.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const menu = record.querySelector('.cr-new-action');
      if (menu.open) { menu.open = false; menu.querySelector('summary').focus(); }
    }
  });
})();
