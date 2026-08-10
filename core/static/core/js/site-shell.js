(() => {
  const button = document.querySelector(".menu-button");
  const nav = document.querySelector(".site-nav");
  const scrim = document.querySelector(".nav-scrim");
  if (!button || !nav || !scrim) return;

  const close = () => {
    nav.classList.remove("is-open");
    button.classList.remove("is-open");
    scrim.classList.remove("is-open");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-label", button.dataset.openLabel);
    document.body.classList.remove("menu-open");
  };
  const open = () => {
    nav.classList.add("is-open");
    button.classList.add("is-open");
    scrim.classList.add("is-open");
    button.setAttribute("aria-expanded", "true");
    button.setAttribute("aria-label", button.dataset.closeLabel);
    document.body.classList.add("menu-open");
    nav.querySelector("a")?.focus();
  };

  button.addEventListener("click", () => button.getAttribute("aria-expanded") === "true" ? close() : open());
  scrim.addEventListener("click", close);
  nav.querySelectorAll("a").forEach(link => link.addEventListener("click", close));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && nav.classList.contains("is-open")) {
      close();
      button.focus();
    }
    if (event.key === "Tab" && nav.classList.contains("is-open")) {
      const focusable = [button, ...nav.querySelectorAll("a")];
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 820) close();
  });
  if ("serviceWorker" in navigator && location.protocol === "https:") {
    window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js").catch(() => {}));
  }
  const installButton = document.querySelector("[data-install-app]");
  let installPrompt;
  window.addEventListener("beforeinstallprompt", event => {
    event.preventDefault(); installPrompt = event;
    if (installButton) installButton.hidden = false;
  });
  installButton?.addEventListener("click", async () => {
    if (!installPrompt) return;
    installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null; installButton.hidden = true;
  });
})();
