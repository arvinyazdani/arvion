(() => {
  const forms = document.querySelectorAll("[data-wizard]");
  forms.forEach(initWizard);

  function initWizard(form) {
    const steps = [...form.querySelectorAll("[data-step]")];
    if (!steps.length) return;
    const wizardKey = "rvion-draft:" + (form.dataset.wizard || "wizard");
    const indicators = [...document.querySelectorAll("[data-step-indicator]")];
    const previous = form.querySelector("[data-previous]");
    const next = form.querySelector("[data-next]");
    const submit = form.querySelector("[data-submit]");
    const requestedErrorStep = Number.parseInt(form.dataset.errorStep || "", 10);
    let current = Number.isInteger(requestedErrorStep)
      ? Math.max(0, requestedErrorStep - 1)
      : Math.max(0, steps.findIndex(step => step.querySelector(".errorlist")));

    const show = (index, moveFocus = true, pushHistory = true) => {
      current = Math.max(0, Math.min(index, steps.length - 1));
      steps.forEach((step, position) => step.hidden = position !== current);
      indicators.forEach((item, position) => {
        item.toggleAttribute("aria-current", position === current);
        item.classList.toggle("complete", position < current);
      });
      if (previous) previous.hidden = current === 0;
      if (next) next.hidden = current === steps.length - 1;
      if (submit) submit.hidden = current !== steps.length - 1;
      if (pushHistory) {
        try { history.pushState({ wizardStep: current }, "", location.href.split("#")[0] + "#step-" + (current + 1)); } catch (e) {}
      }
      if (moveFocus) {
        steps[current].querySelector("h2")?.setAttribute("tabindex", "-1");
        steps[current].querySelector("h2")?.focus({ preventScroll: true });
        steps[current].scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      }
    };

    window.addEventListener("popstate", (event) => {
      const target = event.state && Number.isInteger(event.state.wizardStep) ? event.state.wizardStep : 0;
      show(target, true, false);
    });

    const validate = () => {
      const controls = [...steps[current].querySelectorAll("input,select,textarea")];
      const invalid = controls.find(control => !control.checkValidity());
      if (invalid) { invalid.reportValidity(); invalid.focus(); return false; }
      return true;
    };

    // نمایش/اختفای شرطی فیلدها بر اساس چک‌باکس‌ها — data-show-if="fieldName:value"
    const conditionalGroups = [...form.querySelectorAll("[data-show-if]")];
    const syncConditionalFields = () => {
      conditionalGroups.forEach(group => {
        const [fieldName, value] = (group.dataset.showIf || "").split(":");
        if (!fieldName) return;
        const enabled = !!form.querySelector(`input[name="${fieldName}"][value="${value}"]:checked`);
        group.hidden = !enabled;
        group.querySelectorAll("input,select,textarea").forEach(input => input.disabled = !enabled);
      });
    };
    if (conditionalGroups.length) {
      const triggerNames = new Set(conditionalGroups.map(g => (g.dataset.showIf || "").split(":")[0]));
      triggerNames.forEach(name => {
        form.querySelectorAll(`input[name="${name}"]`).forEach(input => input.addEventListener("change", syncConditionalFields));
      });
      syncConditionalFields();
    }

    // پیش‌نویس محلی — تا سابمیت نهایی هیچ داده‌ای به سرور نمی‌رود اما کاربر ریسک از دست دادن پاسخ‌ها را ندارد.
    const draftFields = [...form.querySelectorAll("input,select,textarea")].filter(el => el.type !== "hidden" && el.name && el.name !== "csrfmiddlewaretoken");
    const readDraft = () => {
      try { return JSON.parse(localStorage.getItem(wizardKey) || "{}"); } catch (e) { return {}; }
    };
    const writeDraft = () => {
      const data = {};
      draftFields.forEach(el => {
        if (el.type === "checkbox" || el.type === "radio") { if (el.checked) data[el.name] = (data[el.name] || []).concat(el.value); }
        else { data[el.name] = el.value; }
      });
      try { localStorage.setItem(wizardKey, JSON.stringify(data)); } catch (e) {}
    };
    const clearDraft = () => { try { localStorage.removeItem(wizardKey); } catch (e) {} };
    const applyDraft = (data) => {
      draftFields.forEach(el => {
        if (!(el.name in data)) return;
        if (el.type === "checkbox" || el.type === "radio") { el.checked = Array.isArray(data[el.name]) && data[el.name].includes(el.value); }
        else if (!el.value) { el.value = data[el.name]; }
      });
      syncConditionalFields();
    };

    const hasServerValues = draftFields.some(el => el.type !== "checkbox" && el.type !== "radio" && el.value);
    const draft = readDraft();
    if (!hasServerValues && Object.keys(draft).length && !form.dataset.errorStep) {
      const banner = document.createElement("div");
      banner.className = "wizard-draft-banner";
      banner.setAttribute("role", "status");
      banner.innerHTML = `<span>${form.dataset.draftMessage || "پیش‌نویس قبلی شما بازیابی شد."}</span>
        <button type="button" data-draft-restore>بازیابی</button>
        <button type="button" data-draft-discard>شروع دوباره</button>`;
      form.prepend(banner);
      banner.querySelector("[data-draft-restore]").addEventListener("click", () => { applyDraft(draft); banner.remove(); });
      banner.querySelector("[data-draft-discard]").addEventListener("click", () => { clearDraft(); banner.remove(); });
    }
    let saveTimer = null;
    form.addEventListener("input", () => { clearTimeout(saveTimer); saveTimer = setTimeout(writeDraft, 400); });
    form.addEventListener("change", writeDraft);

    if (next) next.addEventListener("click", () => validate() && show(current + 1));
    if (previous) previous.addEventListener("click", () => show(current - 1));
    if (submit) {
      form.addEventListener("submit", () => {
        submit.disabled = true;
        submit.setAttribute("aria-disabled", "true");
        clearDraft();
      });
    }

    steps.forEach(step => step.querySelector("h2")?.setAttribute("tabindex", "-1"));
    show(current, false, false);
    if (form.dataset.errorStep) form.querySelector(".crm-error-summary")?.setAttribute("tabindex", "-1"), form.querySelector(".crm-error-summary")?.focus();
  }
})();
