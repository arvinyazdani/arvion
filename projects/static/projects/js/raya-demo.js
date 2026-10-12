(() => {
  const root = document.querySelector("[data-raya-demo]");
  if (!root) return;

  const fa = document.documentElement.lang === "fa";
  const dialog = root.querySelector("[data-raya-dialog]");
  const status = root.querySelector("[data-raya-status]");
  const formatter = new Intl.NumberFormat(fa ? "fa-IR" : "en-US", { maximumFractionDigits: 0 });
  let unit = "toman";

  root.dataset.rayaEnhanced = "true";
  let activePanel = "raya-overview";
  const featureTargets = {
    transactions: ['a[href="#raya-transactions"]', ".raya-activity-card", ".raya-summary-row"],
    reports: ['a[href="#raya-reports"]'],
    accounts: ['a[href="#raya-accounts"]', ".raya-accounts-card", ".raya-balance-band"],
  };
  Object.entries({transactions: "raya-transactions", reports: "raya-reports", accounts: "raya-accounts"})
    .forEach(([feature, id]) => {
      const panel = root.querySelector(`#${CSS.escape(id)}`);
      if (panel) panel.dataset.rayaFeaturePanel = feature;
    });
  Object.entries(featureTargets).forEach(([feature, selectors]) => {
    selectors.forEach((selector) => root.querySelectorAll(selector).forEach((node) => {
      node.dataset.featureModule = feature;
    }));
  });
  const reportPeriod = root.querySelector(".raya-report-period");
  if (reportPeriod) {
    const exportButton = document.createElement("button");
    exportButton.type = "button";
    exportButton.className = "raya-soft-button raya-export-button";
    exportButton.dataset.featureModule = "exports";
    exportButton.textContent = fa ? "خروجی نمایشی" : "Sample export";
    exportButton.addEventListener("click", () => {
      if (status) status.textContent = fa
        ? "این پیش‌نمایش فایل واقعی تولید نمی‌کند؛ خروجی نهایی بر اساس نیاز پروژه تعریف می‌شود."
        : "This preview does not create a real file; export details are scoped for each project.";
    });
    reportPeriod.replaceWith(exportButton);
  }

  const setPanel = (target) => {
    const panel = root.querySelector(`#${CSS.escape(target)}`);
    if (!panel) return;
    activePanel = target;
    root.querySelectorAll("[data-raya-tab]").forEach((link) => {
      if (link.hash === `#${target}`) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  };

  window.addEventListener("hashchange", () => {
    const target = location.hash.slice(1);
    if (target && root.querySelector(`#${CSS.escape(target)}`)) setPanel(target);
    else if (!target) setPanel("raya-overview");
  });

  const refreshAmounts = () => {
    root.querySelectorAll("[data-raya-amount]").forEach((node) => {
      const toman = Number(node.dataset.toman || 0);
      const value = unit === "rial" ? toman * 10 : toman;
      const sign = node.dataset.sign || "";
      node.textContent = `${sign}${formatter.format(value)}`;
    });
    root.querySelectorAll("[data-raya-currency]").forEach((node) => {
      node.textContent = unit === "rial" ? (fa ? "ریال" : "rials") : (fa ? "تومان" : "tomans");
    });
    const button = root.querySelector("[data-raya-unit]");
    if (button) {
      button.textContent = unit === "rial" ? (fa ? "نمایش تومان" : "Show tomans") : (fa ? "نمایش ریال" : "Show rials");
      button.setAttribute("aria-label", unit === "rial"
        ? (fa ? "تغییر واحد نمایش به تومان" : "Switch display to tomans")
        : (fa ? "تغییر واحد نمایش به ریال" : "Switch display to rials"));
      button.setAttribute("aria-pressed", String(unit === "rial"));
    }
  };
  root.querySelector("[data-raya-unit]")?.addEventListener("click", () => {
    unit = unit === "toman" ? "rial" : "toman";
    refreshAmounts();
  });

  root.querySelectorAll("[data-raya-open]").forEach((button) => button.addEventListener("click", () => {
    if (!dialog?.showModal) {
      if (status) status.textContent = fa ? "ثبت نمایشی در این مرورگر پشتیبانی نمی‌شود؛ هیچ داده‌ای ثبت نشد." : "Sample entry is not supported in this browser; nothing was saved.";
      return;
    }
    dialog.showModal();
    dialog.querySelector('input[name="title"]')?.focus();
  }));
  root.querySelectorAll("[data-raya-close]").forEach((button) => button.addEventListener("click", () => dialog?.close()));
  dialog?.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  root.querySelector("[data-raya-entry-form]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const title = form.elements.title.value.trim();
    const amount = Math.max(0, Number(form.elements.amount.value));
    if (!title || !Number.isFinite(amount) || amount <= 0) return;
    const income = form.elements.kind.value === "income";
    const row = document.createElement("article");
    row.className = "raya-transaction-row";
    const icon = document.createElement("i");
    icon.className = `raya-kind ${income ? "income" : "expense"}`;
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = income ? "↗" : "↙";
    const details = document.createElement("div");
    const name = document.createElement("b");
    name.textContent = title;
    const note = document.createElement("small");
    note.textContent = fa ? "همین حالا · فقط پیش‌نمایش" : "Just now · Preview only";
    details.append(name, note);
    const value = document.createElement("strong");
    value.className = income ? "raya-positive" : "";
    value.dataset.rayaAmount = "";
    value.dataset.toman = String(amount);
    value.dataset.sign = income ? "+" : "−";
    row.append(icon, details, value);
    root.querySelector("[data-raya-added-rows]")?.prepend(row);
    refreshAmounts();
    dialog.close();
    form.reset();
    if (status) status.textContent = fa ? "تراکنش فقط در همین پیش‌نمایش اضافه شد؛ چیزی ذخیره نشد." : "Added to this preview only. Nothing was saved.";
  });
  root.querySelector("[data-raya-message]")?.addEventListener("click", () => {
    if (status) status.textContent = fa ? "افزودن حساب در این دمو نمایشی است؛ اطلاعاتی ذخیره نشد." : "Adding an account is illustrative here; nothing was saved.";
  });

  const initial = location.hash.slice(1);
  if (initial && root.querySelector(`#${CSS.escape(initial)}`)) setPanel(initial);
  else setPanel("raya-overview");
  refreshAmounts();
})();
