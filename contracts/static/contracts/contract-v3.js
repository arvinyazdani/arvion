(() => {
  document.documentElement.classList.add("contract-js");
  requestAnimationFrame(() => document.body?.classList.add("contract-ready"));

  const toggle = document.querySelector("[data-password-toggle]");
  if (toggle) {
    const input = document.getElementById(toggle.dataset.passwordToggle);
    toggle.addEventListener("click", () => {
      if (!input) return;
      const visible = input.type === "text";
      input.type = visible ? "password" : "text";
      toggle.textContent = visible ? toggle.dataset.showLabel : toggle.dataset.hideLabel;
      toggle.setAttribute("aria-label", visible ? toggle.dataset.showLabel : toggle.dataset.hideLabel);
      toggle.setAttribute("aria-pressed", String(!visible));
    });
  }

  document.querySelectorAll("[data-legal-article]").forEach(article => {
    const label = article.querySelector(".legal-article-toggle");
    article.addEventListener("toggle", () => {
      if (label) label.textContent = article.open ? "بستن" : "نمایش";
    });
  });
  document.querySelectorAll("[data-legal-close]").forEach(button => {
    button.addEventListener("click", () => {
      const article = button.closest("[data-legal-article]");
      if (!article) return;
      article.open = false;
      article.querySelector("summary")?.focus({preventScroll: true});
      article.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center"});
    });
  });

  document.querySelectorAll("form[data-contract-submit]").forEach(form => {
    form.addEventListener("submit", () => {
      if (!form.checkValidity()) return;
      const button = form.querySelector("button[type=submit]");
      if (!button) return;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      button.dataset.originalLabel = button.textContent;
      button.textContent = button.dataset.busyLabel || "در حال ثبت…";
    });
  });
})();
