(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const connectFieldErrors = () => {
    document.querySelectorAll(".field.field-error").forEach((field) => {
      const control = field.querySelector("input, select, textarea");
      const error = field.querySelector(".form-error");
      if (!control || !error) return;
      if (!error.id) error.id = `${control.id || control.name}-error`;
      control.setAttribute("aria-invalid", "true");
      control.setAttribute("aria-describedby", error.id);
    });
  };

  const enhanceSubmits = () => {
    document.querySelectorAll("form[data-busy-label]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        if (event.defaultPrevented) return;
        if (form.dataset.submitState === "submitting") {
          event.preventDefault();
          event.stopImmediatePropagation();
          return;
        }
        const button = event.submitter || form.querySelector('button[type="submit"]');
        if (!button) return;

        form.dataset.submitState = "submitting";
        form.setAttribute("aria-busy", "true");
        const label = button.querySelector("span") || button;
        button.dataset.originalLabel = label.textContent.trim();
        button.dataset.originalDisabled = String(button.disabled);
        button.dataset.submitGuard = "true";
        label.textContent = form.dataset.busyLabel;
        button.setAttribute("aria-busy", "true");
        button.setAttribute("aria-disabled", "true");
        button.disabled = true;

        // Disabled submitters are excluded from native form serialization. Keep
        // a named submitter's value without reopening a second submission path.
        if (button.name) {
          const proxy = document.createElement("input");
          proxy.type = "hidden";
          proxy.name = button.name;
          proxy.value = button.value;
          proxy.dataset.submitterProxy = "true";
          form.append(proxy);
        }
      });
    });
    window.addEventListener("pageshow", () => {
      document.querySelectorAll('form[data-submit-state="submitting"]').forEach((form) => {
        form.removeAttribute("data-submit-state");
        form.removeAttribute("aria-busy");
        form.querySelectorAll('[data-submitter-proxy="true"]').forEach((proxy) => proxy.remove());
      });
      document.querySelectorAll('button[data-submit-guard="true"][data-original-label]').forEach((button) => {
        const label = button.querySelector("span") || button;
        label.textContent = button.dataset.originalLabel;
        button.disabled = button.dataset.originalDisabled === "true";
        button.removeAttribute("aria-busy");
        button.removeAttribute("aria-disabled");
        button.removeAttribute("data-submit-guard");
        button.removeAttribute("data-original-label");
        button.removeAttribute("data-original-disabled");
      });
    });
  };

  const watchPayment = () => {
    const box = document.querySelector("[data-payment-watch]");
    if (!box) return;
    const title = box.querySelector("[data-payment-title]");
    const note = box.querySelector("[data-payment-note]");
    let stopped = false;
    let failures = 0;
    let timer;

    const later = (delay) => {
      window.clearTimeout(timer);
      if (!stopped) timer = window.setTimeout(check, delay);
    };
    const check = async () => {
      if (document.hidden) {
        later(5000);
        return;
      }
      try {
        const response = await fetch(box.dataset.statusUrl, {
          headers: { Accept: "application/json" },
          cache: "no-store",
          credentials: "same-origin",
        });
        if (!response.ok) throw new Error("payment_status_failed");
        const data = await response.json();
        failures = 0;
        if (data.ready) {
          stopped = true;
          box.classList.add("is-approved");
          title.textContent = box.dataset.approvedTitle;
          note.textContent = box.dataset.approvedNote;
          window.setTimeout(() => window.location.assign(data.redirect_url), reduceMotion ? 0 : 650);
          return;
        }
        if (data.state === "rejected") {
          stopped = true;
          box.classList.add("is-rejected");
          title.textContent = box.dataset.rejectedTitle;
          note.textContent = box.dataset.rejectedNote;
          window.setTimeout(() => window.location.reload(), reduceMotion ? 0 : 900);
          return;
        }
        later(5000);
      } catch (error) {
        failures += 1;
        note.textContent = box.dataset.offlineNote;
        later(Math.min(30000, 5000 * failures));
      }
    };
    check();
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && !stopped) check();
    });
  };

  const revealContent = () => {
    const items = [...document.querySelectorAll(
      ".assessment-card, .purchase-card, .checkout-card-v3, .support-ticket, .learning-card, .result-panel"
    )];
    if (!items.length || reduceMotion || !("IntersectionObserver" in window)) return;
    document.documentElement.classList.add("has-assessment-motion");
    items.forEach((item, index) => {
      item.classList.add("assessment-reveal");
      item.style.transitionDelay = `${Math.min(index, 4) * 45}ms`;
    });
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -24px" });
    items.forEach((item) => observer.observe(item));
  };

  connectFieldErrors();
  enhanceSubmits();
  watchPayment();
  revealContent();
})();
