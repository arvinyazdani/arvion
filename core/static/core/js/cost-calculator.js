(() => {
  const root = document.querySelector('[data-cost-calculator]');
  const dataNode = document.getElementById('cost-calculator-data');
  if (!root || !dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const form = root.querySelector('[data-cost-form]');
  const lang = root.dataset.language;
  // Share only the calculator's allow-listed choices; don't propagate
  // unrelated query parameters into a newly copied URL.
  const params = new URLSearchParams();
  const get = (name, fallback, min, max) => {
    const input = form.elements.namedItem(name);
    const raw = name === 'mobile' || name === 'legal' ? Number(input.checked) : input.value;
    const n = Number(raw);
    return Number.isFinite(n) ? Math.max(min, Math.min(max, n)) : fallback;
  };
  const money = value => new Intl.NumberFormat(lang === 'fa' ? 'fa-IR' : 'en-US', {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0
  }).format(Math.round(value / 1000) * 1000);
  const duration = (weeks, high) => {
    const value = Math.round(weeks);
    return lang === 'fa' ? `${value.toLocaleString('fa-IR')} تا ${Math.round(high).toLocaleString('fa-IR')} هفته` : `${value}–${Math.round(high)} weeks`;
  };
  const recalc = () => {
    const productKey = data.products[form.elements.product.value] ? form.elements.product.value : 'crm';
    const teamKey = data.teams[form.elements.team.value] ? form.elements.team.value : 'company';
    const product = data.products[productKey];
    const roles = get('roles', 3, 1, 20);
    const integrations = get('integrations', 0, 0, 20);
    const erp = get('erp', 0, 0, 5);
    const mobile = get('mobile', 0, 0, 1);
    const legal = get('legal', 0, 0, 1);
    const maintenance = get('maintenance', 15, 10, 20) / 100;
    const roleFactor = 1 + Math.max(0, roles - 2) * data.roleFactor;
    const teamFactor = data.teams[teamKey];
    const values = product.range.map((base, i) => {
      let total = (base + integrations * data.integration[i] + erp * data.erp[i] + mobile * data.mobile[i]) * roleFactor * teamFactor;
      if (legal) total *= data.legal[i];
      return total;
    });
    const weeksAdded = Math.max(0, roles - 2) * 1.5 + integrations + erp * 3 + mobile * 6 + legal * 2;
    const lowWeeks = product.weeks[0] + weeksAdded;
    const highWeeks = product.weeks[2] + weeksAdded;
    root.querySelector('[data-result="low"]').textContent = money(values[0]);
    root.querySelector('[data-result="mid"]').textContent = money(values[1]);
    root.querySelector('[data-result="high"]').textContent = `${money(values[2])}${values[2] >= 360000 ? '+' : ''}`;
    root.querySelector('[data-result="time"]').textContent = duration(lowWeeks, highWeeks);
    root.querySelector('[data-result="maintenance"]').textContent = `${money(values[0] * maintenance)} – ${money(values[2] * maintenance)}`;
    const safe = new URLSearchParams({
      service: 'custom-web-application', estimate: '1', product: productKey,
      roles: String(roles), integrations: String(integrations), erp: String(erp),
      mobile: String(mobile), legal: String(legal), team: teamKey,
      maintenance: String(Math.round(maintenance * 100)),
    });
    root.querySelector('[data-enquiry]').href = `/${lang}/contact/?${safe.toString()}`;
    params.set('product', productKey); params.set('roles', String(roles));
    params.set('integrations', String(integrations)); params.set('erp', String(erp));
    params.set('mobile', String(mobile)); params.set('legal', String(legal));
    params.set('team', teamKey); params.set('maintenance', String(Math.round(maintenance * 100)));
    const share = `${location.origin}${location.pathname}?${params.toString()}`;
    root.dataset.shareUrl = share;
    if (history.replaceState) history.replaceState(null, '', `?${params.toString()}`);
  };
  form.addEventListener('input', recalc);
  form.addEventListener('change', recalc);
  form.querySelector('[data-copy-link]').addEventListener('click', async event => {
    try {
      await navigator.clipboard.writeText(root.dataset.shareUrl);
      event.currentTarget.textContent = lang === 'fa' ? 'پیوند کپی شد' : 'Link copied';
    } catch (_) {
      const helper = document.createElement('textarea'); helper.value = root.dataset.shareUrl;
      helper.setAttribute('readonly', ''); helper.style.position = 'fixed'; helper.style.opacity = '0';
      document.body.appendChild(helper); helper.select(); document.execCommand('copy'); helper.remove();
      event.currentTarget.textContent = lang === 'fa' ? 'پیوند کپی شد' : 'Link copied';
    }
  });
  recalc();
})();
