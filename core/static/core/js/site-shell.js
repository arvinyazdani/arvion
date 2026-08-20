(() => {
  const menuButton = document.querySelector(".menu-button");
  const nav = document.querySelector(".site-nav");
  const scrim = document.querySelector(".nav-scrim");

  if (menuButton && nav && scrim) {
    const closeMenu = () => {
      nav.classList.remove("is-open");
      menuButton.classList.remove("is-open");
      scrim.classList.remove("is-open");
      menuButton.setAttribute("aria-expanded", "false");
      menuButton.setAttribute("aria-label", menuButton.dataset.openLabel);
      document.body.classList.remove("menu-open");
    };
    const openMenu = () => {
      nav.classList.add("is-open");
      menuButton.classList.add("is-open");
      scrim.classList.add("is-open");
      menuButton.setAttribute("aria-expanded", "true");
      menuButton.setAttribute("aria-label", menuButton.dataset.closeLabel);
      document.body.classList.add("menu-open");
      nav.querySelector("a")?.focus();
    };

    menuButton.addEventListener("click", () => menuButton.getAttribute("aria-expanded") === "true" ? closeMenu() : openMenu());
    scrim.addEventListener("click", closeMenu);
    nav.querySelectorAll("a").forEach(link => link.addEventListener("click", closeMenu));
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        closeMenu();
        menuButton.focus();
      }
      if (event.key === "Tab" && nav.classList.contains("is-open")) {
        const focusable = [menuButton, ...nav.querySelectorAll("a,button:not([disabled])")];
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault(); last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault(); first.focus();
        }
      }
    });
    window.addEventListener("resize", () => { if (window.innerWidth > 820) closeMenu(); });
  }

  if ("serviceWorker" in navigator && location.protocol === "https:") {
    window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js?v=2", {updateViaCache: "none"}).catch(() => {}));
  }

  const welcome = document.querySelector("[data-app-welcome]");
  const navigationBackground = [...document.querySelectorAll(".site-header,main,.mobile-tabbar,.site-footer")];
  const setNavigationBusy = busy => {
    navigationBackground.forEach(item => {
      item.toggleAttribute("inert", busy);
      if (item.tagName === "MAIN") item.setAttribute("aria-busy", busy ? "true" : "false");
    });
  };
  let navigationFailsafe = null;
  const hideNavigationLoader = () => {
    if (navigationFailsafe) window.clearTimeout(navigationFailsafe);
    navigationFailsafe = null;
    document.documentElement.classList.remove("navigation-pending");
    if (welcome) welcome.setAttribute("aria-hidden", "true");
    setNavigationBusy(false);
  };
  const showNavigationLoader = () => {
    if (!welcome) return;
    welcome.classList.remove("is-leaving");
    welcome.setAttribute("aria-hidden", "false");
    document.documentElement.classList.add("navigation-pending");
    setNavigationBusy(true);
    navigationFailsafe = window.setTimeout(hideNavigationLoader, 15000);
  };
  if (document.documentElement.classList.contains("welcome-pending") && welcome) {
    const startedAt = performance.now();
    let welcomeDismissed = false;
    const dismissWelcome = () => {
      if (welcomeDismissed) return;
      welcomeDismissed = true;
      const wait = Math.max(0, 1050 - (performance.now() - startedAt));
      window.setTimeout(() => {
        welcome.classList.add("is-leaving");
        document.documentElement.classList.remove("welcome-pending");
        try { sessionStorage.setItem("rvion-welcome-v1", "seen"); } catch (error) {}
        window.setTimeout(() => welcome.classList.remove("is-leaving"), 650);
      }, wait);
    };
    if (document.readyState === "complete") dismissWelcome();
    else window.addEventListener("load", dismissWelcome, { once: true });
    window.setTimeout(dismissWelcome, 3500);
  } else {
    document.documentElement.classList.remove("welcome-pending");
  }

  document.addEventListener("click", event => {
    const link = event.target.closest("a[href]");
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (link.target === "_blank" || link.hasAttribute("download") || link.dataset.noLoader !== undefined) return;
    let destination;
    try { destination = new URL(link.href, location.href); } catch (error) { return; }
    if (destination.origin !== location.origin || !/^https?:$/.test(destination.protocol)) return;
    if (destination.pathname === location.pathname && destination.search === location.search && destination.hash) return;
    showNavigationLoader();
  });
  document.addEventListener("submit", event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || event.defaultPrevented || form.dataset.noLoader !== undefined) return;
    if (typeof form.checkValidity === "function" && !form.checkValidity()) return;
    showNavigationLoader();
  });
  window.addEventListener("pageshow", hideNavigationLoader);
  window.addEventListener("pagehide", () => {});

  const guideButtons = [...document.querySelectorAll("[data-install-guide]")];
  const dialog = document.querySelector("[data-install-dialog]");
  if (!dialog) return;
  guideButtons.forEach(button => {
    button.setAttribute("aria-haspopup", "dialog");
    button.setAttribute("aria-controls", dialog.id);
  });

  const standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  let installedRemembered = false;
  try { installedRemembered = localStorage.getItem("rvion-installed") === "yes"; } catch (error) {}
  const ua = navigator.userAgent.toLowerCase();
  const iPadDesktopMode = navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1;
  const isIOS = /iphone|ipad|ipod/.test(ua) || iPadDesktopMode;
  const isAndroid = /android/.test(ua);
  const isSafari = /safari/.test(ua) && !/crios|fxios|edgios|chrome|android/.test(ua);
  const platform = isIOS ? "ios" : isAndroid ? "android" : "desktop";
  const labels = {
    ios: document.documentElement.lang === "fa" ? "راهنمای iPhone و iPad" : "iPhone & iPad guide",
    android: document.documentElement.lang === "fa" ? "راهنمای Android" : "Android guide",
    desktop: document.documentElement.lang === "fa" ? "راهنمای دسکتاپ" : "Desktop guide",
  };
  let installPrompt = null;
  let trigger = null;

  const hideGuideEntry = () => guideButtons.forEach(button => button.hidden = true);
  if (standalone || installedRemembered) {
    hideGuideEntry();
    dialog.remove();
    return;
  }

  dialog.querySelector(`[data-install-panel="${platform}"]`).hidden = false;
  dialog.querySelector("[data-device-label]").textContent = labels[platform];
  if (isIOS && !isSafari) dialog.querySelector("[data-ios-browser-note]").hidden = false;
  if (platform === "desktop" && isSafari) {
    dialog.querySelector("[data-desktop-step]").innerHTML = document.documentElement.lang === "fa"
      ? "در Safari از منوی <strong>File</strong> گزینه <strong>Add to Dock</strong> را انتخاب کنید."
      : "In Safari, choose <strong>File → Add to Dock</strong>.";
  }

  const confirmButton = dialog.querySelector("[data-install-confirm]");
  const updateInstallAction = () => { confirmButton.hidden = !installPrompt; };
  window.addEventListener("beforeinstallprompt", event => {
    event.preventDefault();
    installPrompt = event;
    updateInstallAction();
  });
  window.addEventListener("appinstalled", () => {
    try { localStorage.setItem("rvion-installed", "yes"); } catch (error) {}
    installPrompt = null;
    closeDialog();
    hideGuideEntry();
  });

  const focusable = () => [...dialog.querySelectorAll(".install-sheet button:not([hidden]):not([disabled]):not([tabindex='-1'])")].filter(item => !item.closest("[hidden]"));
  const dialogBackground = [...document.querySelectorAll(".site-header,main,.mobile-tabbar,.site-footer")];
  const setDialogBackgroundInert = inert => dialogBackground.forEach(item => item.toggleAttribute("inert", inert));
  const openDialog = event => {
    trigger = event.currentTarget;
    dialog.hidden = false;
    document.body.classList.add("install-open");
    setDialogBackgroundInert(true);
    dialog.querySelector(".install-close").focus();
  };
  function closeDialog() {
    if (dialog.hidden) return;
    dialog.hidden = true;
    document.body.classList.remove("install-open");
    setDialogBackgroundInert(false);
    trigger?.focus();
  }
  guideButtons.forEach(button => button.addEventListener("click", openDialog));
  dialog.querySelectorAll("[data-install-close]").forEach(button => button.addEventListener("click", closeDialog));
  dialog.addEventListener("keydown", event => {
    if (event.key === "Escape") closeDialog();
    if (event.key === "Tab") {
      const items = focusable();
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  confirmButton.addEventListener("click", async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    const choice = await installPrompt.userChoice;
    installPrompt = null;
    updateInstallAction();
    if (choice.outcome === "accepted") closeDialog();
  });
})();
