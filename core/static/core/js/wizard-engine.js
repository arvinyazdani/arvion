(() => {
  const DRAFT_CONSENT_KEY = "rvion-draft-consent"; // "granted" | "declined" | absent
  const DRAFT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // ۷ روز
  const SENSITIVE_NAME = /phone|email/i; // شماره و ایمیل هیچ‌وقت در پیش‌نویس محلی ذخیره نمی‌شوند

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

    // --- پیش‌نویس محلی: پیش‌فرض خاموش، رضایت صریح لازم، شماره/ایمیل/متن آزاد هرگز ذخیره نمی‌شود ---
    const allFields = [...form.querySelectorAll("input,select,textarea")].filter(el => el.type !== "hidden" && el.name && el.name !== "csrfmiddlewaretoken");
    const draftFields = allFields.filter(el => el.tagName !== "TEXTAREA" && !SENSITIVE_NAME.test(el.name));

    const readConsent = () => { try { return localStorage.getItem(DRAFT_CONSENT_KEY); } catch (e) { return null; } };
    const writeConsent = (value) => { try { localStorage.setItem(DRAFT_CONSENT_KEY, value); } catch (e) {} };
    const readDraft = () => {
      try {
        const raw = JSON.parse(localStorage.getItem(wizardKey) || "null");
        if (!raw || !raw.savedAt || Date.now() - raw.savedAt > DRAFT_MAX_AGE_MS) return null;
        return raw;
      } catch (e) { return null; }
    };
    const clearDraft = () => { try { localStorage.removeItem(wizardKey); } catch (e) {} };
    const writeDraft = () => {
      if (readConsent() !== "granted") return;
      const data = {};
      draftFields.forEach(el => {
        if (el.type === "checkbox" || el.type === "radio") { if (el.checked) data[el.name] = (data[el.name] || []).concat(el.value); }
        else { data[el.name] = el.value; }
      });
      try { localStorage.setItem(wizardKey, JSON.stringify({ savedAt: Date.now(), step: current, data })); } catch (e) {}
    };
    const applyDraft = (draft) => {
      draftFields.forEach(el => {
        if (!(el.name in draft.data)) return;
        if (el.type === "checkbox" || el.type === "radio") { el.checked = Array.isArray(draft.data[el.name]) && draft.data[el.name].includes(el.value); }
        else if (!el.value) { el.value = draft.data[el.name]; }
      });
      syncConditionalFields();
      if (Number.isInteger(draft.step)) show(draft.step, false, false);
    };

    const consentBox = form.querySelector("[data-draft-consent]");
    const draftControls = form.querySelector("[data-draft-controls]");
    const renderDraftControls = () => {
      if (!draftControls) return;
      const consent = readConsent();
      const hasDraft = !!readDraft();
      draftControls.innerHTML = "";
      if (consent === "granted") {
        const clearBtn = document.createElement("button");
        clearBtn.type = "button";
        clearBtn.className = "wizard-draft-clear";
        clearBtn.textContent = hasDraft ? "پاک‌کردن پیش‌نویس این دستگاه" : "ذخیره پیش‌نویس محلی فعال است";
        clearBtn.disabled = !hasDraft;
        clearBtn.addEventListener("click", () => { clearDraft(); renderDraftControls(); });
        draftControls.appendChild(clearBtn);
      }
    };

    // یک بار توسط جنگو با خطای اعتبارسنجی رندر شده — پاسخ‌های واقعی کاربر در فرم است، نه یک بازدید تازه
    const isErrorRerender = !!form.dataset.errorStep;
    const consent = readConsent();
    const draft = consent === "granted" ? readDraft() : null;

    if (!isErrorRerender && draft) {
      const banner = document.createElement("div");
      banner.className = "wizard-draft-banner";
      banner.setAttribute("role", "status");
      banner.innerHTML = `<span>${form.dataset.draftMessage || "پیش‌نویس قبلی شما (بدون شماره/ایمیل) بازیابی شد."}</span>
        <button type="button" data-draft-restore>بازیابی</button>
        <button type="button" data-draft-discard>شروع دوباره</button>`;
      form.prepend(banner);
      banner.querySelector("[data-draft-restore]").addEventListener("click", () => { applyDraft(draft); banner.remove(); });
      banner.querySelector("[data-draft-discard]").addEventListener("click", () => { clearDraft(); banner.remove(); renderDraftControls(); });
    } else if (!isErrorRerender && consent === null && consentBox) {
      consentBox.hidden = false;
      consentBox.querySelector("[data-consent-accept]")?.addEventListener("click", () => {
        writeConsent("granted"); consentBox.hidden = true; writeDraft(); renderDraftControls();
      });
      consentBox.querySelector("[data-consent-decline]")?.addEventListener("click", () => {
        writeConsent("declined"); consentBox.hidden = true;
      });
    }
    renderDraftControls();

    let saveTimer = null;
    form.addEventListener("input", () => { clearTimeout(saveTimer); saveTimer = setTimeout(() => { writeDraft(); renderDraftControls(); }, 400); });
    form.addEventListener("change", () => { writeDraft(); renderDraftControls(); });

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
        showStatus("در حال ارسال...", false);
        try {
          const response = await fetch(form.action || location.href, {
            method: "POST", body: new FormData(form), credentials: "same-origin",
          });
          if (response.redirected) { location.href = response.url; return; }
          if (response.status >= 500) {
            showStatus("خطایی در سرور رخ داد. پاسخ‌های شما حفظ شده؛ چند لحظه دیگر دوباره تلاش کنید.", true);
            submit.disabled = false; submit.removeAttribute("aria-disabled");
            return;
          }
          const html = await response.text();
          document.open(); document.write(html); document.close();
        } catch (err) {
          showStatus("ارتباط با سرور برقرار نشد. اتصال اینترنت را بررسی کنید و دوباره تلاش کنید؛ پاسخ‌های شما حفظ شده است.", true);
          submit.disabled = false; submit.removeAttribute("aria-disabled");
        }
      });
    }

    steps.forEach(step => step.querySelector("h2")?.setAttribute("tabindex", "-1"));
    show(current, false, false);
    if (form.dataset.errorStep) { form.querySelector(".crm-error-summary")?.setAttribute("tabindex", "-1"); form.querySelector(".crm-error-summary")?.focus(); }
  }
})();
