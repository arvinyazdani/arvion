(() => {
  const form = document.querySelector("[data-specialist-form]");
  const submitButton = form?.querySelector("[data-submit]");
  const previousLink = form?.querySelector("[data-previous-link]");
  let dirty = false;
  let submitting = false;

  form?.addEventListener("input", () => { dirty = true; });
  previousLink?.addEventListener("click", event => {
    if (!dirty || window.confirm("تغییرات این بخش هنوز ذخیره نشده‌اند. بدون ذخیره به بخش قبل برگردیم؟")) return;
    event.preventDefault();
  });
  window.addEventListener("beforeunload", event => {
    if (!dirty || submitting) return;
    event.preventDefault();
    event.returnValue = "";
  });
  form?.addEventListener("submit", event => {
    if (submitting) {
      event.preventDefault();
      return;
    }
    if (!form.checkValidity()) return;
    submitting = true;
    dirty = false;
    if (submitButton) {
      submitButton.dataset.readyLabel = submitButton.querySelector("span")?.textContent || "";
      const label = submitButton.querySelector("span");
      if (label) label.textContent = submitButton.dataset.busyLabel;
      submitButton.disabled = true;
      submitButton.setAttribute("aria-busy", "true");
    }
  });
  window.addEventListener("pageshow", () => {
    submitting = false;
    if (!submitButton) return;
    submitButton.disabled = false;
    submitButton.removeAttribute("aria-busy");
    const label = submitButton.querySelector("span");
    if (label && submitButton.dataset.readyLabel) label.textContent = submitButton.dataset.readyLabel;
  });

  const layer = document.querySelector("[data-help-layer]");
  const dialog = layer?.querySelector(".help-popover");
  const closeButton = dialog?.querySelector(".help-close");
  const content = dialog?.querySelector("#question-help-content");
  const background = [...document.querySelectorAll(".specialist-shell > *:not(.help-layer)")];
  let opener = null;

  const setBackgroundInert = inert => background.forEach(item => item.toggleAttribute("inert", inert));
  const closeHelp = () => {
    if (!layer || layer.hidden) return;
    layer.hidden = true;
    document.body.classList.remove("help-open");
    setBackgroundInert(false);
    opener?.setAttribute("aria-expanded", "false");
    opener?.focus();
    opener = null;
  };
  const openHelp = button => {
    if (!layer || !content) return;
    opener?.setAttribute("aria-expanded", "false");
    opener = button;
    content.textContent = button.dataset.help || "";
    layer.hidden = false;
    document.body.classList.add("help-open");
    setBackgroundInert(true);
    button.setAttribute("aria-expanded", "true");
    closeButton?.focus();
  };
  document.querySelectorAll("[data-help]").forEach(button => button.addEventListener("click", () => openHelp(button)));
  layer?.querySelectorAll("[data-close-help]").forEach(button => button.addEventListener("click", closeHelp));
  layer?.addEventListener("keydown", event => {
    if (event.key === "Escape") closeHelp();
    if (event.key !== "Tab" || !closeButton) return;
    event.preventDefault();
    closeButton.focus();
  });

  const errorSummary = document.querySelector("[data-error-summary]");
  if (errorSummary) {
    errorSummary.focus();
    errorSummary.scrollIntoView({ block: "center", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }

  const copyButton = document.querySelector("[data-copy-url]");
  const copyStatus = document.querySelector("[data-copy-status]");
  copyButton?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(location.href);
      if (copyStatus) copyStatus.textContent = "لینک پیگیری کپی شد.";
    } catch (error) {
      if (copyStatus) copyStatus.textContent = "کپی خودکار انجام نشد؛ لینک نوار آدرس را کپی کنید.";
    }
  });
})();
