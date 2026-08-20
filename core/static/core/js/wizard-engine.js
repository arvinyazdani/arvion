(() => {
  const LEGACY_DRAFT_CONSENT_KEY = "rvion-draft-consent";
  const DRAFT_SCHEMA_VERSION = 2;
  const DRAFT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // ۷ روز
  const SAFE_DRAFT_INPUT_TYPES = new Set(["checkbox", "radio", "number", "range"]);

  const forms = document.querySelectorAll("[data-wizard]");
  forms.forEach(initWizard);

  function initWizard(form) {
    const isPersian = document.documentElement.lang === "fa";
    const copy = isPersian ? {
      step: (current, total) => `مرحله ${current} از ${total}`,
      requiredGroup: "حداقل یک گزینه انتخاب کنید.",
      completeRequired: "لطفاً فیلد مشخص‌شده را کامل کنید تا به مرحله بعد بروید.",
      clearDraft: "پاک‌کردن پیش‌نویس این دستگاه",
      draftEnabled: "ذخیره پیش‌نویس محلی فعال است",
      disableDraft: "غیرفعال‌کردن ذخیره محلی",
      enableDraft: "فعال‌کردن ذخیره محلی",
      restored: "گزینه‌های غیرحساس پیش‌نویس قبلی شما آماده بازیابی است.",
      restore: "بازیابی",
      restart: "شروع دوباره",
      sending: "در حال ارسال...",
      serverError: "خطایی در سرور رخ داد. پاسخ‌های شما حفظ شده؛ چند لحظه دیگر دوباره تلاش کنید.",
      networkError: "ارتباط با سرور برقرار نشد. اتصال اینترنت را بررسی کنید و دوباره تلاش کنید؛ پاسخ‌های شما حفظ شده است.",
    } : {
      step: (current, total) => `Step ${current} of ${total}`,
      requiredGroup: "Select at least one option.",
      completeRequired: "Complete the highlighted field before continuing.",
      clearDraft: "Clear this device's draft",
      draftEnabled: "Local draft saving is active",
      disableDraft: "Disable local draft saving",
      enableDraft: "Enable local draft saving",
      restored: "Your previous non-sensitive selections are ready to restore.",
      restore: "Restore",
      restart: "Start again",
      sending: "Submitting...",
      serverError: "The server could not process the request. Your answers are preserved; please try again shortly.",
      networkError: "The server could not be reached. Check your connection and try again; your answers are preserved.",
    };
    const steps = [...form.querySelectorAll("[data-step]")];
    if (!steps.length) return;
    const wizardName = form.dataset.wizard || "wizard";
    const wizardKey = "rvion-draft:" + wizardName;
    const consentKey = wizardKey + ":consent";
    const indicators = [...document.querySelectorAll("[data-step-indicator]")];
    const previous = form.querySelector("[data-previous]");
    const next = form.querySelector("[data-next]");
    const submit = form.querySelector("[data-submit]");
    const requestedErrorStep = Number.parseInt(form.dataset.errorStep || "", 10);
    let current = Number.isInteger(requestedErrorStep)
      ? Math.max(0, requestedErrorStep - 1)
      : Math.max(0, steps.findIndex(step => step.querySelector(".errorlist")));

    const stepStatus = document.createElement("p");
    stepStatus.className = "sr-only";
    stepStatus.setAttribute("role", "status");
    stepStatus.setAttribute("aria-live", "polite");
    stepStatus.setAttribute("aria-atomic", "true");
    form.prepend(stepStatus);

    let submitStatus = form.querySelector(".wizard-submit-status");
    if (!submitStatus && submit) {
      submitStatus = document.createElement("p");
      submitStatus.className = "wizard-submit-status";
      submitStatus.setAttribute("role", "alert");
      submitStatus.hidden = true;
      submit.insertAdjacentElement("afterend", submitStatus);
    }
    const showStatus = (text, isError) => {
      if (!submitStatus) return;
      submitStatus.textContent = text;
      submitStatus.hidden = !text;
      submitStatus.classList.toggle("is-error", !!isError);
    };

    const show = (index, moveFocus = true, pushHistory = true) => {
      current = Math.max(0, Math.min(index, steps.length - 1));
      steps.forEach((step, position) => step.hidden = position !== current);
      indicators.forEach((item, position) => {
        if (position === current) item.setAttribute("aria-current", "step");
        else item.removeAttribute("aria-current");
        item.classList.toggle("complete", position < current);
      });
      stepStatus.textContent = copy.step(current + 1, steps.length);
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
      const activeStep = steps[current];
      activeStep.querySelectorAll('[aria-invalid="true"]').forEach(element => element.removeAttribute("aria-invalid"));
      const missingGroup = [...steps[current].querySelectorAll('fieldset[aria-required="true"]')]
        .find(group => !group.querySelector('input[type="checkbox"]:checked,input[type="radio"]:checked'));
      if (missingGroup) {
        missingGroup.setAttribute("aria-invalid", "true");
        showStatus(copy.requiredGroup, true);
        const firstChoice = missingGroup.querySelector('input[type="checkbox"],input[type="radio"]');
        if (firstChoice) {
          firstChoice.setCustomValidity(copy.requiredGroup);
          firstChoice.reportValidity();
          firstChoice.setCustomValidity("");
          firstChoice.focus();
        }
        return false;
      }
      const controls = [...steps[current].querySelectorAll("input,select,textarea")];
      const invalid = controls.find(control => !control.checkValidity());
      if (invalid) {
        invalid.setAttribute("aria-invalid", "true");
        showStatus(copy.completeRequired, true);
        invalid.reportValidity();
        invalid.focus();
        return false;
      }
      showStatus("", false);
      return true;
    };

    // نمایش/اختفای شرطی فیلدها — data-show-if="fieldName:value"
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

    // --- پيش‌نويس محلی: رضایت و داده برای هر فرم جدا است و فقط گزینه‌های مجاز صریح ذخیره می‌شوند. ---
    const allowedDraftNames = new Set((form.dataset.draftFields || "").split(/\s+/).filter(Boolean));
    const draftFields = [...form.querySelectorAll("input,select")].filter(el => {
      if (!allowedDraftNames.has(el.name)) return false;
      return el.tagName === "SELECT" || SAFE_DRAFT_INPUT_TYPES.has(el.type);
    });

    // رضایت عمومی نسخه قدیمی دیگر معتبر نیست؛ حذف آن از فعال‌شدن ناخواسته فرم دیگری جلوگیری می‌کند.
    try { localStorage.removeItem(LEGACY_DRAFT_CONSENT_KEY); } catch (e) {}

    const readConsent = () => {
      try {
        const value = localStorage.getItem(consentKey);
        return value === "granted" || value === "declined" ? value : null;
      } catch (e) { return null; }
    };
    const writeConsent = (value) => {
      try {
        if (value === null) localStorage.removeItem(consentKey);
        else localStorage.setItem(consentKey, value);
      } catch (e) {}
    };
    const clearDraft = () => { try { localStorage.removeItem(wizardKey); } catch (e) {} };
    const readDraft = () => {
      try {
        const raw = JSON.parse(localStorage.getItem(wizardKey) || "null");
        const age = raw && typeof raw.savedAt === "number" ? Date.now() - raw.savedAt : -1;
        const validShape = raw && raw.version === DRAFT_SCHEMA_VERSION && Number.isInteger(raw.step)
          && raw.data && typeof raw.data === "object" && !Array.isArray(raw.data);
        const allowedShape = validShape && Object.keys(raw.data).every(name => allowedDraftNames.has(name));
        if (!validShape || !allowedShape || age < 0 || age > DRAFT_MAX_AGE_MS) {
          clearDraft();
          return null;
        }
        const validValues = Object.values(raw.data).every(value => {
          if (Array.isArray(value)) return value.length <= 30 && value.every(item => typeof item === "string" && item.length <= 120);
          return typeof value === "string" && value.length <= 120;
        });
        if (!validValues) {
          clearDraft();
          return null;
        }
        return raw;
      } catch (e) {
        clearDraft();
        return null;
      }
    };
    const writeDraft = () => {
      if (readConsent() !== "granted") return;
      const data = {};
      draftFields.forEach(el => {
        if (el.type === "checkbox" || el.type === "radio") { if (el.checked) data[el.name] = (data[el.name] || []).concat(el.value); }
        else if (el.multiple) { data[el.name] = [...el.selectedOptions].map(option => option.value); }
        else { data[el.name] = String(el.value || "").slice(0, 120); }
      });
      try { localStorage.setItem(wizardKey, JSON.stringify({ version: DRAFT_SCHEMA_VERSION, savedAt: Date.now(), step: current, data })); } catch (e) {}
    };
    const applyDraft = (draft) => {
      draftFields.forEach(el => {
        if (!(el.name in draft.data)) return;
        if (el.type === "checkbox" || el.type === "radio") { el.checked = Array.isArray(draft.data[el.name]) && draft.data[el.name].includes(el.value); }
        else if (el.multiple) { [...el.options].forEach(option => option.selected = draft.data[el.name].includes(option.value)); }
        else { el.value = draft.data[el.name]; }
      });
      syncConditionalFields();
      if (Number.isInteger(draft.step)) show(draft.step, false, false);
    };

    const consentBox = form.querySelector("[data-draft-consent]");
    const draftControls = form.querySelector("[data-draft-controls]");
    const showConsent = () => { if (consentBox) consentBox.hidden = false; };
    const renderDraftControls = () => {
      if (!draftControls) return;
      const consent = readConsent();
      const hasDraft = !!readDraft();
      draftControls.innerHTML = "";
      if (consent === "granted") {
        const clearBtn = document.createElement("button");
        clearBtn.type = "button";
        clearBtn.className = "wizard-draft-clear";
        clearBtn.textContent = hasDraft ? copy.clearDraft : copy.draftEnabled;
        clearBtn.disabled = !hasDraft;
        clearBtn.addEventListener("click", () => { clearDraft(); renderDraftControls(); });
        draftControls.appendChild(clearBtn);

        const disableBtn = document.createElement("button");
        disableBtn.type = "button";
        disableBtn.className = "wizard-draft-clear";
        disableBtn.textContent = copy.disableDraft;
        disableBtn.addEventListener("click", () => {
          clearDraft();
          writeConsent("declined");
          renderDraftControls();
        });
        draftControls.appendChild(disableBtn);
      } else if (consent === "declined") {
        const enableBtn = document.createElement("button");
        enableBtn.type = "button";
        enableBtn.className = "wizard-draft-clear";
        enableBtn.textContent = copy.enableDraft;
        enableBtn.addEventListener("click", () => {
          writeConsent(null);
          showConsent();
          renderDraftControls();
        });
        draftControls.appendChild(enableBtn);
      }
    };

    consentBox?.querySelector("[data-consent-accept]")?.addEventListener("click", () => {
      writeConsent("granted"); consentBox.hidden = true; writeDraft(); renderDraftControls();
    });
    consentBox?.querySelector("[data-consent-decline]")?.addEventListener("click", () => {
      clearDraft(); writeConsent("declined"); consentBox.hidden = true; renderDraftControls();
    });

    // یک بار توسط جنگو با خطای اعتبارسنجی رندر شده — پاسخ‌های واقعی کاربر در فرم است، نه یک بازدید تازه
    const isErrorRerender = !!form.dataset.errorStep;
    const consent = readConsent();
    const draft = consent === "granted" ? readDraft() : null;

    if (!isErrorRerender && draft) {
      const banner = document.createElement("div");
      banner.className = "wizard-draft-banner";
      banner.setAttribute("role", "status");
      banner.innerHTML = `<span>${form.dataset.draftMessage || copy.restored}</span>
        <button type="button" data-draft-restore>${copy.restore}</button>
        <button type="button" data-draft-discard>${copy.restart}</button>`;
      form.prepend(banner);
      banner.querySelector("[data-draft-restore]").addEventListener("click", () => { applyDraft(draft); banner.remove(); });
      banner.querySelector("[data-draft-discard]").addEventListener("click", () => { clearDraft(); banner.remove(); renderDraftControls(); });
    } else if (!isErrorRerender && consent === null) showConsent();
    renderDraftControls();

    let saveTimer = null;
    const clearFieldError = (event) => {
      event.target?.removeAttribute?.("aria-invalid");
      event.target?.closest?.('fieldset[aria-invalid="true"]')?.removeAttribute("aria-invalid");
    };
    form.addEventListener("input", event => {
      clearFieldError(event);
      clearTimeout(saveTimer);
      saveTimer = setTimeout(() => { writeDraft(); renderDraftControls(); }, 400);
    });
    form.addEventListener("change", event => {
      clearFieldError(event);
      writeDraft();
      renderDraftControls();
    });

    if (next) next.addEventListener("click", () => validate() && show(current + 1));
    if (previous) previous.addEventListener("click", () => show(current - 1));

    // Enter هیچ‌وقت فرم ناقص را submit نمی‌کند — فقط معادل «ادامه» عمل می‌کند
    form.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" || e.target.tagName === "TEXTAREA" || e.target.type === "submit") return;
      e.preventDefault();
      if (current < steps.length - 1 && validate()) show(current + 1);
    });

    // سابمیت مقاوم در برابر خطای شبکه/سرور — تا رسیدن به صفحه کد پیگیری، هیچ پاسخی گم نمی‌شود
    if (submit) {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!validate()) return;
        submit.disabled = true;
        submit.setAttribute("aria-disabled", "true");
        showStatus(copy.sending, false);
        try {
          const response = await fetch(form.action || location.href, {
            method: "POST", body: new FormData(form), credentials: "same-origin",
          });
          if (response.redirected) {
            clearTimeout(saveTimer);
            clearDraft();
            location.href = response.url;
            return;
          }
          if (response.status >= 500) {
            showStatus(copy.serverError, true);
            submit.disabled = false; submit.removeAttribute("aria-disabled");
            return;
          }
          const html = await response.text();
          document.open(); document.write(html); document.close();
        } catch (err) {
          showStatus(copy.networkError, true);
          submit.disabled = false; submit.removeAttribute("aria-disabled");
        }
      });
    }

    steps.forEach(step => step.querySelector("h2")?.setAttribute("tabindex", "-1"));
    show(current, false, false);
    if (form.dataset.errorStep) { form.querySelector(".crm-error-summary")?.setAttribute("tabindex", "-1"); form.querySelector(".crm-error-summary")?.focus(); }
  }
})();
