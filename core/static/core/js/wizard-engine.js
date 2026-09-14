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
      expired: "پیش‌نویس قبلی شما پس از هفت روز منقضی شده و حذف شد.",
      dismiss: "متوجه شدم",
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
      expired: "Your previous draft expired after seven days and was cleared.",
      dismiss: "Got it",
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

    // --- حالت پیش‌نویس سروری (V2.1-C1): فقط برای leads-contact، فقط وقتی
    // سرور صریحاً برای مشتری واردشدهٔ غیر staff فعالش کرده باشد (از طریق
    // data-server-draft="1" که هرگز برای مهمان/staff رندر نمی‌شود). این حالت
    // کاملاً از حالت local/guest بالا مجزاست — autosave محلی و autosave
    // سروری هرگز هم‌زمان روی یک فرم فعال نیستند.
    const serverDraftEnabled = isDemoContinuationWizard && form.dataset.serverDraft === "1";
    const serverDraftUrl = form.dataset.draftUrl || "";
    const serverDraftDeleteUrl = form.dataset.draftDeleteUrl || "";
    const serverCopy = (fa, en) => (isPersian ? fa : en);

    // نگاشت صریح میان نام فیلد DOM و کلید مجاز API — تنها این پنج فیلد
    // هرگز جمع‌آوری/اعمال می‌شوند؛ name/phone/email/business/website/message/
    // privacy_accept/CSRF/demo token هرگز به این نگاشت راه ندارند.
    const DOM_TO_API_FIELD = {
      request_type: "request_type", service: "service_id", budget_range: "budget_range",
      timeline: "timeline", preferred_contact: "preferred_contact",
    };

    const collectApiFields = () => {
      const out = {};
      draftFields.forEach(el => {
        const apiKey = DOM_TO_API_FIELD[el.name];
        if (!apiKey) return;
        const raw = el.value;
        if (!raw) return; // خالی/پاسخ‌داده‌نشده — هرگز ارسال نمی‌شود
        if (apiKey === "service_id") {
          const parsed = Number.parseInt(raw, 10);
          if (Number.isInteger(parsed) && parsed > 0) out[apiKey] = parsed;
          return;
        }
        out[apiKey] = raw;
      });
      return out;
    };

    const applyApiFieldsToDom = (apiFields) => {
      draftFields.forEach(el => {
        const apiKey = DOM_TO_API_FIELD[el.name];
        if (!apiKey || !apiFields || !(apiKey in apiFields)) return;
        const rawValue = apiFields[apiKey];
        const value = rawValue === null || rawValue === undefined ? "" : String(rawValue);
        // هرگز مقداری خارج از گزینه‌های موجود این select تزریق نمی‌شود.
        const optionExists = value === "" || [...el.options].some(option => option.value === value);
        el.value = optionExists ? value : "";
      });
    };

    // --- زمینهٔ دمو: مسیر کوچک و جدا از allowlist عمومی پیش‌نویس، فقط برای
    // فرم leads-contact. توکن هرگز از سمت سرور در DOM چاپ نمی‌شود؛ فقط از
    // خودِ URL خوانده می‌شود — همان مکانیزم موجود ?demo= که از قبل آن را حمل
    // می‌کند، نه یک data-attribute جدید. سرور فقط یک برچسب انسانیِ غیرحساس
    // (عنوان عمومی قالب دمو) را در data-demo-label برمی‌گرداند.
    const isDemoContinuationWizard = wizardName === "leads-contact";
    const demoContextKey = wizardKey + ":demo";
    const demoRedirectGuardKey = wizardKey + ":demo-redirect-guard";
    const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    const clearDemoContext = () => {
      try { localStorage.removeItem(demoContextKey); sessionStorage.removeItem(demoRedirectGuardKey); } catch (e) {}
    };
    const readDemoContext = () => {
      if (!isDemoContinuationWizard || readConsent() !== "granted") return null;
      try {
        const raw = JSON.parse(localStorage.getItem(demoContextKey) || "null");
        if (!raw || typeof raw.token !== "string" || !UUID_PATTERN.test(raw.token) || typeof raw.savedAt !== "number") { clearDemoContext(); return null; }
        if (Date.now() - raw.savedAt > DRAFT_MAX_AGE_MS) { clearDemoContext(); return null; }
        return raw;
      } catch (e) { clearDemoContext(); return null; }
    };
    const writeDemoContext = (token, label) => {
      if (!isDemoContinuationWizard || readConsent() !== "granted" || !UUID_PATTERN.test(token || "")) return;
      try {
        localStorage.setItem(demoContextKey, JSON.stringify({ token, label: String(label || "").slice(0, 120), savedAt: Date.now() }));
        // این توکن برای همین صفحه معتبر تشخیص داده شده — یعنی اگر یک
        // بازسازی خودکار همین حالا به این‌جا رسانده باشد، وظیفه‌اش تمام
        // شده. guard را همین‌جا مصرف می‌کنیم تا مراجعهٔ بعدی به URL بدون
        // ?demo= در همین تب دوباره بتواند یک‌بار بازسازی انجام دهد؛ در غیر
        // این صورت این پرچم یک‌بارمصرف برای همیشه ماندگار می‌شد.
        sessionStorage.removeItem(demoRedirectGuardKey);
      } catch (e) {}
    };
    if (isDemoContinuationWizard) {
      const params = new URLSearchParams(location.search);
      const urlDemoToken = params.get("demo") || "";
      const serverResolvedLabel = form.dataset.demoLabel || "";
      if (urlDemoToken && serverResolvedLabel) {
        // این درخواست دقیقاً همان چیزی است که سرور برایش دمو را معتبر
        // تشخیص داده — زمینهٔ محلی را با همین وضعیت هم‌سو نگه می‌داریم.
        writeDemoContext(urlDemoToken, serverResolvedLabel);
      } else if (urlDemoToken && !serverResolvedLabel) {
        // سرور این توکن را برای نشست جاری معتبر تشخیص نداده (نامعتبر، متعلق
        // به نشست دیگر، یا منقضی) — پیام خنثای موجود همان‌طور نمایش داده
        // می‌شود؛ فقط اشاره‌گر محلی پاک می‌شود تا حلقهٔ بازیابی/خطا ایجاد
        // نشود. سایر انتخاب‌های غیرحساس پیش‌نویس دست‌نخورده می‌مانند.
        clearDemoContext();
      } else if (!urlDemoToken) {
        const stored = readDemoContext();
        let alreadyRedirected = false;
        try { alreadyRedirected = sessionStorage.getItem(demoRedirectGuardKey) === "1"; } catch (e) {}
        if (stored && !alreadyRedirected) {
          try { sessionStorage.setItem(demoRedirectGuardKey, "1"); } catch (e) {}
          params.set("demo", stored.token);
          location.replace(location.pathname + "?" + params.toString() + location.hash);
          return;
        }
      }
    }

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
      const hasDraft = !!readDraft() || !!(isDemoContinuationWizard && readDemoContext());
      draftControls.innerHTML = "";
      if (consent === "granted") {
        const clearBtn = document.createElement("button");
        clearBtn.type = "button";
        clearBtn.className = "wizard-draft-clear";
        clearBtn.textContent = hasDraft ? copy.clearDraft : copy.draftEnabled;
        clearBtn.disabled = !hasDraft;
        clearBtn.addEventListener("click", () => { clearDraft(); if (isDemoContinuationWizard) clearDemoContext(); renderDraftControls(); });
        draftControls.appendChild(clearBtn);

        const disableBtn = document.createElement("button");
        disableBtn.type = "button";
        disableBtn.className = "wizard-draft-clear";
        disableBtn.textContent = copy.disableDraft;
        disableBtn.addEventListener("click", () => {
          clearDraft();
          if (isDemoContinuationWizard) clearDemoContext();
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
      writeConsent("granted"); consentBox.hidden = true; writeDraft();
      if (isDemoContinuationWizard && form.dataset.demoLabel) {
        writeDemoContext(new URLSearchParams(location.search).get("demo") || "", form.dataset.demoLabel);
      }
      renderDraftControls();
    });
    consentBox?.querySelector("[data-consent-decline]")?.addEventListener("click", () => {
      clearDraft(); if (isDemoContinuationWizard) clearDemoContext(); writeConsent("declined"); consentBox.hidden = true; renderDraftControls();
    });

    // یک بار توسط جنگو با خطای اعتبارسنجی رندر شده — پاسخ‌های واقعی کاربر در فرم است، نه یک بازدید تازه
    const isErrorRerender = !!form.dataset.errorStep;

    if (!serverDraftEnabled) {
      const consent = readConsent();
      const peekDraftAge = () => {
        try {
          const raw = JSON.parse(localStorage.getItem(wizardKey) || "null");
          return raw && typeof raw.savedAt === "number" ? Date.now() - raw.savedAt : null;
        } catch (e) { return null; }
      };
      // باید پیش از readDraft() سنجیده شود: خودِ readDraft() به‌محض تشخیص
      // انقضا، رکورد را از localStorage حذف می‌کند و دیگر چیزی برای سنجش نمی‌ماند.
      const draftAgeBeforeRead = isDemoContinuationWizard && consent === "granted" ? peekDraftAge() : null;
      const draft = consent === "granted" ? readDraft() : null;
      const isDraftExpired = isDemoContinuationWizard && consent === "granted" && !draft && draftAgeBeforeRead !== null && draftAgeBeforeRead > DRAFT_MAX_AGE_MS;

      if (!isErrorRerender && draft) {
        const banner = document.createElement("div");
        banner.className = "wizard-draft-banner";
        banner.setAttribute("role", "status");
        banner.innerHTML = `<span>${form.dataset.draftMessage || copy.restored}</span>
          <button type="button" data-draft-restore>${copy.restore}</button>
          <button type="button" data-draft-discard>${copy.restart}</button>`;
        form.prepend(banner);
        banner.querySelector("[data-draft-restore]").addEventListener("click", () => { applyDraft(draft); banner.remove(); });
        banner.querySelector("[data-draft-discard]").addEventListener("click", () => { clearDraft(); if (isDemoContinuationWizard) clearDemoContext(); banner.remove(); renderDraftControls(); });
      } else if (!isErrorRerender && isDraftExpired) {
        // پاک‌سازی بی‌صدا جای خود را به یک پیام قابل‌فهم می‌دهد — کاربر باید
        // بداند پیش‌نویسش گم نشده، بلکه طبق همان بازهٔ اعلام‌شده منقضی شده است.
        clearDraft();
        clearDemoContext();
        const expiredBanner = document.createElement("div");
        expiredBanner.className = "wizard-draft-banner";
        expiredBanner.setAttribute("role", "status");
        expiredBanner.innerHTML = `<span>${copy.expired}</span><button type="button" data-draft-expired-dismiss>${copy.dismiss}</button>`;
        form.prepend(expiredBanner);
        expiredBanner.querySelector("[data-draft-expired-dismiss]").addEventListener("click", () => { expiredBanner.remove(); });
      } else if (!isErrorRerender && consent === null) showConsent();
      renderDraftControls();
    }

    // در حالت سروری، initServerDraftMode() این را با تابع واقعیِ صف‌بندیِ
    // ذخیرهٔ سروری جایگزین می‌کند — پیش از هر تعامل کاربر، همگام و کامل.
    let requestServerSave = () => {};

    let saveTimer = null;
    const clearFieldError = (event) => {
      event.target?.removeAttribute?.("aria-invalid");
      event.target?.closest?.('fieldset[aria-invalid="true"]')?.removeAttribute("aria-invalid");
    };
    form.addEventListener("input", event => {
      clearFieldError(event);
      clearTimeout(saveTimer);
      if (serverDraftEnabled) saveTimer = setTimeout(() => requestServerSave(), 400);
      else saveTimer = setTimeout(() => { writeDraft(); renderDraftControls(); }, 400);
    });
    form.addEventListener("change", event => {
      clearFieldError(event);
      if (serverDraftEnabled) requestServerSave();
      else { writeDraft(); renderDraftControls(); }
    });

    if (next) next.addEventListener("click", () => { if (validate()) { show(current + 1); if (serverDraftEnabled) requestServerSave(); } });
    if (previous) previous.addEventListener("click", () => { show(current - 1); if (serverDraftEnabled) requestServerSave(); });

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
            if (isDemoContinuationWizard) clearDemoContext();
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

    // =====================================================================
    // V2.1-C1 — حالت پیش‌نویس سروری حساب‌محور (فقط leads-contact، فقط مشتری
    // واردشدهٔ غیر staff). کاملاً جدا از منطق local/guest بالا: هیچ‌کدام از
    // readConsent/writeDraft/renderDraftControls (نسخهٔ محلی) در این حالت
    // فراخوانی نمی‌شوند — فقط readDraft/clearDraft برای reconciliation اولیه
    // به‌کار می‌روند.
    // =====================================================================
    function initServerDraftMode() {
      function csrfToken() {
        return form.querySelector('input[name="csrfmiddlewaretoken"]')?.value
          || (document.cookie.match(/(?:^|; )csrftoken=([^;]*)/) || [])[1] || "";
      }

      async function apiRequest(url, method, body) {
        let response;
        try {
          response = await fetch(url, {
            method, credentials: "same-origin",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
            body: body === undefined ? undefined : JSON.stringify(body),
          });
        } catch (networkError) { return { networkError: true }; }
        let payload = null;
        try { payload = await response.json(); } catch (parseError) { payload = null; }
        return { status: response.status, payload };
      }

      // undefined فقط برای شکل غیرمنتظرهٔ پاسخ — هرگز فرم را پاک نمی‌کند؛
      // null یک payload کاملاً معتبر است (یعنی «پیش‌نویسی موجود نیست»).
      function safeDraft(payload) {
        if (!payload || typeof payload !== "object" || !("draft" in payload)) return undefined;
        return payload.draft;
      }

      const reconcileBanner = document.createElement("div");
      reconcileBanner.className = "wizard-draft-banner";
      reconcileBanner.hidden = true;
      reconcileBanner.setAttribute("role", "status");
      form.prepend(reconcileBanner);

      const draftStatusLine = document.createElement("p");
      draftStatusLine.className = "wizard-draft-status";
      draftStatusLine.setAttribute("role", "status");
      draftStatusLine.setAttribute("aria-live", "polite");
      draftStatusLine.hidden = true;
      if (draftControls) draftControls.insertAdjacentElement("beforebegin", draftStatusLine);
      else form.appendChild(draftStatusLine);

      const STATUS_TEXT = {
        saving: serverCopy("در حال ذخیره…", "Saving…"),
        saved: serverCopy("ذخیره شد", "Saved"),
        offline: serverCopy("ذخیره نشد؛ در حال تلاش دوباره.", "Not saved; retrying."),
        conflict: serverCopy("تعارض؛ تصمیم شما لازم است.", "Conflict — your decision is needed."),
      };
      const setDraftStatus = (kind) => {
        draftStatusLine.hidden = false;
        draftStatusLine.textContent = STATUS_TEXT[kind] || "";
        draftStatusLine.classList.toggle("is-error", kind === "offline" || kind === "conflict");
      };
      const clearDraftStatus = () => { draftStatusLine.hidden = true; draftStatusLine.textContent = ""; };
      const announceRestore = (text) => { stepStatus.textContent = text; };

      const state = { revision: null, ready: false, saving: false, dirty: false, pauseReason: null };

      function buildBannerButton(text, handler, primary) {
        const button = document.createElement("button");
        button.type = "button";
        if (primary) button.setAttribute("data-draft-primary-action", "");
        button.textContent = text;
        button.addEventListener("click", handler);
        return button;
      }

      function buildDeleteConfirmRow(onYes) {
        const row = document.createElement("div");
        row.className = "wizard-draft-confirm";
        const message = document.createElement("span");
        message.textContent = serverCopy(
          "این پیش‌نویس حساب برای همیشه حذف می‌شود. مطمئن هستید؟",
          "This account draft will be permanently deleted. Are you sure?",
        );
        const yes = document.createElement("button");
        yes.type = "button"; yes.className = "button danger compact";
        yes.textContent = serverCopy("بله، حذف کن", "Yes, delete");
        const no = document.createElement("button");
        no.type = "button"; no.className = "button-ghost";
        no.textContent = serverCopy("انصراف", "Cancel");
        no.addEventListener("click", () => row.remove());
        yes.addEventListener("click", () => { yes.disabled = true; no.disabled = true; onYes(row); });
        row.append(message, yes, no);
        return row;
      }

      async function performDelete(expectedRevision) {
        const result = await apiRequest(serverDraftDeleteUrl, "POST", { expected_revision: expectedRevision });
        if (result.networkError) return { outcome: "network" };
        if (result.status === 200) return { outcome: "deleted" };
        if (result.status === 409) {
          const canonical = safeDraft(result.payload);
          return canonical === null ? { outcome: "deleted" } : { outcome: "conflict", payload: result.payload };
        }
        return { outcome: "error" };
      }

      function renderPersistentDraftControls() {
        if (!draftControls) return;
        draftControls.innerHTML = "";
        if (!state.revision) return;
        const clearBtn = document.createElement("button");
        clearBtn.type = "button";
        clearBtn.className = "wizard-draft-clear";
        clearBtn.textContent = serverCopy("پاک‌کردن پیش‌نویس حساب", "Clear my account draft");
        clearBtn.addEventListener("click", () => {
          draftControls.appendChild(buildDeleteConfirmRow(async (row) => {
            const result = await performDelete(state.revision);
            if (result.outcome === "deleted") {
              clearDraft();
              if (isDemoContinuationWizard) clearDemoContext();
              state.revision = 0;
              draftFields.forEach(el => { el.value = ""; });
              syncConditionalFields();
              show(0, true, false);
              renderPersistentDraftControls();
              announceRestore(serverCopy("پیش‌نویس حساب پاک شد.", "Your account draft was cleared."));
            } else if (result.outcome === "conflict") {
              row.remove();
              handleConflict(result.payload);
            } else {
              row.remove();
              setDraftStatus("offline");
            }
          }));
        });
        draftControls.appendChild(clearBtn);
      }

      function enableAutosave(revision) {
        state.revision = revision; state.ready = true; state.pauseReason = null;
        clearDraftStatus(); renderPersistentDraftControls();
      }
      function startFreshAtZero() {
        state.revision = 0; state.ready = true; state.pauseReason = null;
        clearDraftStatus(); renderPersistentDraftControls();
      }

      function applyCanonicalDraft(canonical) {
        applyApiFieldsToDom(canonical.fields || {});
        syncConditionalFields();
        if (Number.isInteger(canonical.current_step)) show(canonical.current_step, false, false);
        steps[current].querySelector("h2")?.setAttribute("tabindex", "-1");
        steps[current].querySelector("h2")?.focus({ preventScroll: true });
        announceRestore(serverCopy("پیش‌نویس حساب شما بازیابی شد.", "Your account draft was restored."));
      }

      function hideReconcileBanner() { reconcileBanner.hidden = true; reconcileBanner.textContent = ""; }
      function renderReconcileBanner(nodes) {
        reconcileBanner.textContent = "";
        nodes.forEach(node => reconcileBanner.appendChild(node));
        reconcileBanner.hidden = false;
      }

      function showSessionEndedNotice() {
        const panel = document.createElement("div");
        panel.className = "wizard-draft-banner is-conflict";
        panel.setAttribute("role", "alert");
        const label = document.createElement("span");
        label.textContent = serverCopy(
          "نشست شما پایان یافته است. پاسخ‌های شما در همین صفحه حفظ شده‌اند.",
          "Your session has ended. Your answers are preserved on this page.",
        );
        const loginLink = document.createElement("a");
        loginLink.className = "button secondary";
        const next = encodeURIComponent(location.pathname + location.search);
        loginLink.href = `${form.dataset.loginUrl || "/"}?next=${next}`;
        loginLink.textContent = serverCopy("ورود دوباره", "Sign in again");
        panel.append(label, loginLink);
        form.prepend(panel);
        clearDraftStatus();
      }

      function handleConflict(payload) {
        state.pauseReason = "conflict";
        setDraftStatus("conflict");
        const canonical = safeDraft(payload);
        const panel = document.createElement("div");
        panel.className = "wizard-draft-banner is-conflict";
        panel.setAttribute("role", "alert");
        const label = document.createElement("span");
        if (canonical) {
          label.textContent = serverCopy(
            "این پیش‌نویس از دستگاه دیگری تغییر کرده است.", "This draft was changed from another device.",
          );
          const loadBtn = buildBannerButton(serverCopy("بارگذاری نسخه حساب", "Load account version"), () => {
            applyCanonicalDraft(canonical);
            enableAutosave(canonical.revision);
            panel.remove();
          }, true);
          const keepBtn = document.createElement("button");
          keepBtn.type = "button";
          keepBtn.textContent = serverCopy("ذخیره نسخه فعلی من", "Save my current version");
          keepBtn.addEventListener("click", async () => {
            keepBtn.disabled = true;
            const result = await apiRequest(serverDraftUrl, "POST", {
              fields: collectApiFields(), current_step: current, expected_revision: canonical.revision,
            });
            if (result.status === 200 || result.status === 201) {
              const fresh = safeDraft(result.payload);
              panel.remove();
              enableAutosave(fresh ? fresh.revision : canonical.revision);
              setDraftStatus("saved");
            } else if (result.status === 409) {
              panel.remove();
              handleConflict(result.payload);
            } else { keepBtn.disabled = false; }
          });
          panel.append(label, loadBtn, keepBtn);
        } else {
          label.textContent = serverCopy(
            "پیش‌نویس قبلی شما دیگر فعال نیست.", "Your previous draft is no longer active.",
          );
          const saveNewBtn = buildBannerButton(serverCopy("ذخیره این صفحه به‌عنوان پیش‌نویس جدید", "Save this page as a new draft"), async () => {
            saveNewBtn.disabled = true;
            const result = await apiRequest(serverDraftUrl, "POST", {
              fields: collectApiFields(), current_step: current, expected_revision: 0,
            });
            if (result.status === 200 || result.status === 201) {
              const fresh = safeDraft(result.payload);
              panel.remove();
              enableAutosave(fresh ? fresh.revision : 1);
              setDraftStatus("saved");
            } else if (result.status === 409) {
              panel.remove();
              handleConflict(result.payload);
            } else { saveNewBtn.disabled = false; }
          }, true);
          panel.append(label, saveNewBtn);
        }
        form.prepend(panel);
      }

      let networkRetryTimer = null;
      let networkRetryAttempts = 0;
      const NETWORK_RETRY_DELAYS_MS = [2000, 5000, 15000, 30000, 60000];
      function scheduleNetworkRetry() {
        clearTimeout(networkRetryTimer);
        if (networkRetryAttempts >= NETWORK_RETRY_DELAYS_MS.length) return; // بدون تلاش بی‌نهایت
        const delay = NETWORK_RETRY_DELAYS_MS[networkRetryAttempts];
        networkRetryAttempts += 1;
        networkRetryTimer = setTimeout(() => { queueServerSave(); }, delay);
      }
      window.addEventListener("online", () => {
        if (state.ready && !state.pauseReason && networkRetryAttempts > 0) {
          clearTimeout(networkRetryTimer);
          networkRetryAttempts = 0;
          queueServerSave();
        }
      });

      async function queueServerSave() {
        if (!state.ready || state.pauseReason) return;
        if (state.saving) { state.dirty = true; return; }
        state.saving = true;
        setDraftStatus("saving");
        const result = await apiRequest(serverDraftUrl, "POST", {
          fields: collectApiFields(), current_step: current, expected_revision: state.revision,
        });
        state.saving = false;
        if (result.networkError) { setDraftStatus("offline"); scheduleNetworkRetry(); return; }
        if (result.status === 401) { state.pauseReason = "auth"; showSessionEndedNotice(); return; }
        if (result.status === 403) { state.pauseReason = "forbidden"; clearDraftStatus(); return; }
        if (result.status === 409) { handleConflict(result.payload); return; }
        if (result.status === 200 || result.status === 201) {
          const canonical = safeDraft(result.payload);
          if (canonical) {
            networkRetryAttempts = 0;
            state.revision = canonical.revision;
            setDraftStatus("saved");
            renderPersistentDraftControls();
          }
          if (state.dirty) { state.dirty = false; queueServerSave(); }
          return;
        }
        // یک وضعیت غیرمنتظرهٔ دیگر (مثلاً 400 اعتبارسنجی) — داده‌های DOM دست‌نخورده می‌مانند
        setDraftStatus("offline");
      }
      requestServerSave = () => { queueServerSave(); };

      function apiFieldsFromLocal(snapshot) {
        const out = {};
        const data = (snapshot && snapshot.data) || {};
        Object.keys(data).forEach(domName => {
          const apiKey = DOM_TO_API_FIELD[domName];
          if (!apiKey) return;
          const raw = Array.isArray(data[domName]) ? data[domName][0] : data[domName];
          if (!raw) return;
          if (apiKey === "service_id") {
            const parsed = Number.parseInt(raw, 10);
            if (Number.isInteger(parsed) && parsed > 0) out[apiKey] = parsed;
            return;
          }
          out[apiKey] = raw;
        });
        return out;
      }

      function formatSavedAt(value) {
        try {
          return new Intl.DateTimeFormat(isPersian ? "fa-IR" : "en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
        } catch (e) { return ""; }
      }

      async function reconcile() {
        // خواندنِ فقط-در-حافظه: local draft هرگز به‌خودی‌خود روی DOM اعمال
        // نمی‌شود — فقط برای تصمیم‌گیری reconciliation استفاده می‌شود.
        const localSnapshot = readDraft();
        const result = await apiRequest(serverDraftUrl, "GET");
        if (result.networkError || result.status !== 200) { setDraftStatus("offline"); return; }
        const canonical = safeDraft(result.payload);
        if (canonical === undefined) { setDraftStatus("offline"); return; }

        if (isErrorRerender) {
          // پاسخ‌های فعلی فرم (از رندر خطای جنگو) اولویت دارند و هرگز
          // overwrite نمی‌شوند؛ فقط revision سرور خوانده می‌شود تا autosave
          // از این‌جا با شمارهٔ درست ادامه یابد.
          if (canonical) enableAutosave(canonical.revision); else startFreshAtZero();
          return;
        }

        if (!canonical && !localSnapshot) { startFreshAtZero(); return; }

        if (canonical && !localSnapshot) {
          const label = document.createElement("span");
          label.textContent = serverCopy("یک پیش‌نویس ذخیره‌شده در حساب شما پیدا شد.", "A saved draft was found in your account.");
          const continueBtn = buildBannerButton(serverCopy("ادامه پیش‌نویس حساب", "Continue account draft"), () => {
            applyCanonicalDraft(canonical);
            enableAutosave(canonical.revision);
            hideReconcileBanner();
          }, true);
          const restartBtn = buildBannerButton(serverCopy("شروع دوباره", "Start over"), () => {
            reconcileBanner.appendChild(buildDeleteConfirmRow(async (row) => {
              const deleteResult = await performDelete(canonical.revision);
              if (deleteResult.outcome === "deleted") { startFreshAtZero(); hideReconcileBanner(); }
              else if (deleteResult.outcome === "conflict") { hideReconcileBanner(); handleConflict(deleteResult.payload); }
              else { row.remove(); setDraftStatus("offline"); }
            }));
          });
          renderReconcileBanner([label, continueBtn, restartBtn]);
          return;
        }

        if (!canonical && localSnapshot) {
          const label = document.createElement("span");
          label.textContent = serverCopy("یک پیش‌نویس ذخیره‌شده روی این دستگاه پیدا شد.", "A draft saved on this device was found.");
          const importBtn = buildBannerButton(serverCopy("انتقال این پیش‌نویس به حساب", "Move this draft to my account"), async () => {
            importBtn.disabled = true;
            const result2 = await apiRequest(serverDraftUrl, "POST", {
              fields: apiFieldsFromLocal(localSnapshot),
              current_step: Number.isInteger(localSnapshot.step) ? localSnapshot.step : 0,
              expected_revision: 0,
            });
            if (result2.status === 200 || result2.status === 201) {
              const fresh = safeDraft(result2.payload);
              applyCanonicalDraft(fresh);
              clearDraft();
              enableAutosave(fresh.revision);
              hideReconcileBanner();
            } else if (result2.status === 409) {
              hideReconcileBanner();
              handleConflict(result2.payload);
            } else { importBtn.disabled = false; setDraftStatus("offline"); }
          }, true);
          const freshBtn = buildBannerButton(serverCopy("شروع تازه", "Start fresh"), () => {
            clearDraft();
            startFreshAtZero();
            hideReconcileBanner();
          });
          renderReconcileBanner([label, importBtn, freshBtn]);
          return;
        }

        // هر دو موجودند
        const label = document.createElement("span");
        label.textContent = serverCopy("هم نسخهٔ حساب و هم نسخهٔ این دستگاه موجود است.", "Both an account version and a device version exist.");
        const timesLine = document.createElement("small");
        const accountWhen = formatSavedAt(canonical.updated_at);
        const deviceWhen = typeof localSnapshot.savedAt === "number" ? formatSavedAt(new Date(localSnapshot.savedAt).toISOString()) : "";
        timesLine.textContent = serverCopy(`نسخهٔ حساب: ${accountWhen} — نسخهٔ دستگاه: ${deviceWhen}`, `Account version: ${accountWhen} — Device version: ${deviceWhen}`);
        const useAccountBtn = buildBannerButton(serverCopy("ادامه نسخه حساب", "Continue account version"), () => {
          applyCanonicalDraft(canonical);
          clearDraft();
          enableAutosave(canonical.revision);
          hideReconcileBanner();
        }, true);
        const useDeviceBtn = buildBannerButton(serverCopy("استفاده از نسخه این دستگاه", "Use this device's version"), async () => {
          useDeviceBtn.disabled = true;
          const result3 = await apiRequest(serverDraftUrl, "POST", {
            fields: apiFieldsFromLocal(localSnapshot),
            current_step: Number.isInteger(localSnapshot.step) ? localSnapshot.step : 0,
            expected_revision: canonical.revision,
          });
          if (result3.status === 200 || result3.status === 201) {
            const fresh = safeDraft(result3.payload);
            applyCanonicalDraft(fresh);
            clearDraft();
            enableAutosave(fresh.revision);
            hideReconcileBanner();
          } else if (result3.status === 409) {
            hideReconcileBanner();
            handleConflict(result3.payload);
          } else { useDeviceBtn.disabled = false; setDraftStatus("offline"); }
        });
        const restartBtn = buildBannerButton(serverCopy("شروع دوباره", "Start over"), () => {
          reconcileBanner.appendChild(buildDeleteConfirmRow(async (row) => {
            const deleteResult = await performDelete(canonical.revision);
            if (deleteResult.outcome === "deleted") { clearDraft(); startFreshAtZero(); hideReconcileBanner(); }
            else if (deleteResult.outcome === "conflict") { hideReconcileBanner(); handleConflict(deleteResult.payload); }
            else { row.remove(); setDraftStatus("offline"); }
          }));
        });
        renderReconcileBanner([label, timesLine, useAccountBtn, useDeviceBtn, restartBtn]);
      }

      reconcile();
    }

    if (serverDraftEnabled) initServerDraftMode();
  }
})();
