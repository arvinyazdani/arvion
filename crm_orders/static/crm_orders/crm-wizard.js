(() => {
  const form = document.querySelector("[data-crm-wizard]");
  if (!form) return;
  const steps = [...form.querySelectorAll("[data-step]")];
  const indicators = [...document.querySelectorAll("[data-step-indicator]")];
  const previous = form.querySelector("[data-previous]");
  const next = form.querySelector("[data-next]");
  const submit = form.querySelector("[data-submit]");
  const correspondenceOptions = form.querySelector("[data-correspondence-options]");
  const requestedErrorStep = Number.parseInt(form.dataset.errorStep || "", 10);
  let current = Number.isInteger(requestedErrorStep)
    ? Math.max(0, requestedErrorStep - 1)
    : Math.max(0, steps.findIndex(step => step.querySelector(".errorlist")));

  const show = (index, moveFocus = true) => {
    current = Math.max(0, Math.min(index, steps.length - 1));
    steps.forEach((step, position) => step.hidden = position !== current);
    indicators.forEach((item, position) => {
      item.toggleAttribute("aria-current", position === current);
      item.classList.toggle("complete", position < current);
    });
    previous.hidden = current === 0;
    next.hidden = current === steps.length - 1;
    submit.hidden = current !== steps.length - 1;
    if (moveFocus) {
      steps[current].querySelector("h2")?.focus({preventScroll: true});
      steps[current].scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start"});
    }
  };
  const validate = () => {
    const controls = [...steps[current].querySelectorAll("input,select,textarea")];
    const invalid = controls.find(control => !control.checkValidity());
    if (invalid) { invalid.reportValidity(); invalid.focus(); return false; }
    return true;
  };
  steps.forEach(step => step.querySelector("h2")?.setAttribute("tabindex", "-1"));
  const syncConditionalFields = () => {
    if (!correspondenceOptions) return;
    const enabled = !!form.querySelector('input[name="required_capabilities"][value="correspondence"]:checked');
    correspondenceOptions.hidden = !enabled;
    correspondenceOptions.querySelectorAll("input").forEach(input => input.disabled = !enabled);
  };
  form.querySelectorAll('input[name="required_capabilities"]').forEach(input => input.addEventListener("change", syncConditionalFields));
  syncConditionalFields();
  next.addEventListener("click", () => validate() && show(current + 1));
  previous.addEventListener("click", () => show(current - 1));
  show(current, false);
  if (form.dataset.errorStep) form.querySelector(".crm-error-summary")?.focus();
})();
