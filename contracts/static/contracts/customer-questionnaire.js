(() => {
  const root = document.querySelector("[data-questionnaire]");
  const form = root?.querySelector("[data-questionnaire-form]");
  if (!root || !form) return;

  const status = root.querySelector("[data-save-status]");
  const conflict = root.querySelector("[data-conflict]");
  const reloadButton = root.querySelector("[data-conflict-reload]");
  const revisionInput = root.querySelector("[data-revision-input]");
  const submitButton = root.querySelector("[data-questionnaire-submit]");
  const csrf = form.querySelector("input[name=csrfmiddlewaretoken]")?.value || "";
  const pending = new Map();
  let revision = Number(root.dataset.revision || 0);
  let timer = null;
  let inFlight = false;
  let blocked = false;

  const setStatus = (message, state = "") => {
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("saving", state === "saving");
    status.classList.toggle("error", state === "error");
  };

  const valueFor = (field) => {
    const name = CSS.escape(field.name);
    if (field.type === "radio") {
      return form.querySelector(`input[name="${name}"]:checked`)?.value || "";
    }
    if (field.type === "checkbox") {
      return Array.from(form.querySelectorAll(`input[name="${name}"]:checked`), item => item.value);
    }
    return field.value;
  };

  const showConflict = (message) => {
    blocked = true;
    pending.clear();
    if (conflict) {
      conflict.hidden = false;
      const detail = conflict.querySelector("span");
      if (detail && message) detail.textContent = message;
      conflict.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center"});
    }
    setStatus("ذخیره متوقف شد تا نسخه تازه را بارگذاری کنید.", "error");
  };

  const saveOne = async (field, value) => {
    const response = await fetch(root.dataset.autosaveUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest"},
      body: JSON.stringify({section: root.dataset.sectionKey, field, value, revision}),
    });
    let data = {};
    try { data = await response.json(); } catch (_error) { /* handled below */ }
    if (response.status === 401 && data.redirect) {
      window.location.assign(data.redirect);
      const error = new Error("auth");
      error.retryable = false;
      throw error;
    }
    if (response.status === 409) {
      showConflict(data.message);
      const error = new Error("conflict");
      error.retryable = false;
      throw error;
    }
    if (response.status === 423) {
      showConflict(data.message || "این فرم نهایی شده است.");
      const error = new Error("locked");
      error.retryable = false;
      throw error;
    }
    if (!response.ok || !data.ok) {
      const error = new Error(data.message || "save_failed");
      error.retryable = false;
      throw error;
    }
    revision = Number(data.revision);
    root.dataset.revision = String(revision);
    revisionInput.value = String(revision);
  };

  const flush = async () => {
    if (inFlight || blocked || pending.size === 0) return !blocked;
    inFlight = true;
    let activeSave = null;
    setStatus("در حال ذخیره امن پاسخ‌ها…", "saving");
    try {
      while (pending.size && !blocked) {
        const [field, value] = pending.entries().next().value;
        pending.delete(field);
        activeSave = {field, value};
        await saveOne(field, value);
        activeSave = null;
      }
      if (!blocked) setStatus("همه پاسخ‌های این بخش روی سرور ذخیره شد.");
      return !blocked;
    } catch (error) {
      if (!blocked && activeSave && error.retryable !== false && !pending.has(activeSave.field)) {
        pending.set(activeSave.field, activeSave.value);
      }
      if (!blocked && error.message !== "auth") {
        setStatus(error.retryable === false ? error.message : "ذخیره خودکار انجام نشد؛ اتصال را بررسی کنید. پاسخ در همین صفحه باقی مانده است.", "error");
      }
      return false;
    } finally {
      inFlight = false;
    }
  };

  const schedule = (field) => {
    if (blocked || !field.name) return;
    pending.set(field.name, valueFor(field));
    setStatus("تغییر ثبت شد؛ تا لحظاتی دیگر ذخیره می‌شود…", "saving");
    window.clearTimeout(timer);
    timer = window.setTimeout(flush, 850);
  };

  form.querySelectorAll("[data-autosave-field]").forEach(field => {
    const eventName = ["radio", "checkbox"].includes(field.type) || field.tagName === "SELECT" ? "change" : "input";
    field.addEventListener(eventName, () => schedule(field));
  });

  form.addEventListener("submit", async event => {
    if (blocked || (!pending.size && !inFlight)) return;
    event.preventDefault();
    window.clearTimeout(timer);
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.setAttribute("aria-busy", "true");
    }
    while (inFlight) await new Promise(resolve => window.setTimeout(resolve, 60));
    const saved = await flush();
    if (saved && !pending.size) {
      HTMLFormElement.prototype.submit.call(form);
      return;
    }
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.removeAttribute("aria-busy");
    }
  });

  reloadButton?.addEventListener("click", () => window.location.reload());
  window.addEventListener("online", () => {
    if (pending.size && !blocked) flush();
  });
  window.addEventListener("beforeunload", event => {
    if (!pending.size && !inFlight) return;
    event.preventDefault();
    event.returnValue = "";
  });
})();
