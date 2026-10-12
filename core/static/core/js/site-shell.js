// Timed UX guard only. No identity, analytics, or security authority.
function rvionEntryAdmission({path, type, referrer, origin, reduced, now, state}) {
  if (!['/fa/', '/en/'].includes(path) || type === 'back_forward' || reduced) return {show: false};
  if (type !== 'reload' && referrer) {
    try { if (new URL(referrer).origin === origin) return {show: false}; } catch (error) { return {show: false}; }
  }
  const blockedUntil = Number.isFinite(state?.blockedUntil) ? state.blockedUntil : 0;
  if (blockedUntil > now && blockedUntil <= now + 300000) return {show: false};
  const starts = Array.isArray(state?.starts) ? state.starts.filter(t => Number.isFinite(t) && t <= now && t >= now - 90000).slice(-3) : [];
  if (starts.length >= 3) return {show: false, state: {starts: [], blockedUntil: now + 300000}};
  return {show: true, state: {starts: [...starts, now], blockedUntil: 0}};
}
if (typeof module !== 'undefined') module.exports = {rvionEntryAdmission};
if (typeof document !== 'undefined') (() => {
  const menuButton = document.querySelector(".menu-button");
  const nav = document.querySelector(".site-nav");
  const scrim = document.querySelector(".nav-scrim");
  const preferences = document.querySelector(".nav-preferences");
  const closePreferences = () => { if (preferences) preferences.open = false; };
  document.addEventListener("click", event => {
    if (preferences && !preferences.contains(event.target)) closePreferences();
  });
  document.addEventListener("focusin", event => {
    if (preferences?.open && !preferences.contains(event.target)) closePreferences();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && preferences?.open) {
      closePreferences();
      preferences.querySelector("summary")?.focus();
      event.stopImmediatePropagation();
    }
  });

  if (menuButton && nav && scrim) {
    const menuBackground = [...document.querySelectorAll("main,.mobile-tabbar,.site-footer")];
    const setMenuBackgroundInert = inert => menuBackground.forEach(item => item.toggleAttribute("inert", inert));
    let menuFocusFrame = 0;
    const focusMenu = () => {
      if (nav.classList.contains("is-open") && document.activeElement === menuButton) nav.querySelector("a")?.focus();
    };
    nav.addEventListener("transitionend", focusMenu);
    const closeMenu = (restoreFocus = false) => {
      window.cancelAnimationFrame(menuFocusFrame);
      closePreferences();
      nav.classList.remove("is-open");
      menuButton.classList.remove("is-open");
      scrim.classList.remove("is-open");
      menuButton.setAttribute("aria-expanded", "false");
      menuButton.setAttribute("aria-label", menuButton.dataset.openLabel);
      document.body.classList.remove("menu-open");
      setMenuBackgroundInert(false);
      if (restoreFocus) menuButton.focus();
    };
    const openMenu = () => {
      nav.classList.add("is-open");
      menuButton.classList.add("is-open");
      scrim.classList.add("is-open");
      menuButton.setAttribute("aria-expanded", "true");
      menuButton.setAttribute("aria-label", menuButton.dataset.closeLabel);
      document.body.classList.add("menu-open");
      setMenuBackgroundInert(true);
      // Wait for the visibility rule to apply before focusing the opened menu.
      menuFocusFrame = window.requestAnimationFrame(focusMenu);
    };

    menuButton.addEventListener("click", () => menuButton.getAttribute("aria-expanded") === "true" ? closeMenu() : openMenu());
    scrim.addEventListener("click", () => closeMenu(true));
    nav.querySelectorAll("a").forEach(link => link.addEventListener("click", () => closeMenu()));
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        closeMenu(true);
      }
      if (event.key === "Tab" && nav.classList.contains("is-open")) {
        const focusable = [menuButton, ...nav.querySelectorAll("a,summary,button:not([disabled])")]
          .filter(item => item.getClientRects().length && getComputedStyle(item).visibility !== "hidden");
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault(); last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault(); first.focus();
        }
      }
    });
    // CSS owns the breakpoint; do not close a tablet menu using a stale width.
    window.addEventListener("resize", () => { if (getComputedStyle(menuButton).display === "none") closeMenu(); });
  }

  if ("serviceWorker" in navigator && location.protocol === "https:") {
    window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js?v=5", {updateViaCache: "none"}).catch(() => {}));
  }

  const welcome = document.querySelector("[data-navigation-loader]");
  const routeShell = [...document.querySelectorAll("[data-route-shell]")];
  const navigationBackground = routeShell.length
    ? routeShell
    : [...document.querySelectorAll(".site-header,main,.mobile-tabbar,.site-footer")];
  const main = document.querySelector("main");
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)");
  const NAVIGATION_REVEAL_DELAY_MS = 160;
  const NAVIGATION_FAILSAFE_MS = 8000;
  const prefersReducedMotion = () => Boolean(reducedMotion?.matches);
  let navigationRevealTimer = null;
  let navigationFailsafe = null;
  let navigationScheduled = false;
  const entryPayload = document.getElementById('rvion-entry-payload');
  if (entryPayload) {
    const bootEntry = () => {
      if (navigationScheduled) return;
      const guardKey = 'rvion-entry-starts-v1';
      let state = null;
      try { state = JSON.parse(localStorage.getItem(guardKey)); } catch (error) {}
      const result = rvionEntryAdmission({path: location.pathname,
        type: performance.getEntriesByType('navigation')[0]?.type || 'navigate',
        referrer: document.referrer, origin: location.origin,
        reduced: prefersReducedMotion(), now: Date.now(), state});
      const localSeek = ['localhost','127.0.0.1','[::1]'].includes(location.hostname)
        && new URLSearchParams(location.search).has('entry_seek') && !prefersReducedMotion();
      if (!result.show && !localSeek) {
        if (result.state) {try {localStorage.setItem(guardKey, JSON.stringify(result.state));} catch (error) {}}
        return;
      }
      let payload;
      try { payload = JSON.parse(entryPayload.textContent); } catch (error) { return; }
      if (!payload.css?.startsWith('/static/core/css/entry.css?') || !payload.js?.startsWith('/static/core/js/entry.js?')) return;
      const sheet = document.createElement('link');
      sheet.rel = 'stylesheet';sheet.href = payload.css;
      const script = document.createElement('script');script.src = payload.js;
      let canceled = false;
      const timer = window.setTimeout(() => {canceled = true;sheet.remove();script.remove();}, 8000);
      const fail = () => {canceled = true;window.clearTimeout(timer);sheet.remove();script.remove();};
      sheet.onerror = fail;script.onerror = fail;
      sheet.onload = () => {if (!canceled) document.head.append(script);};
      script.onload = () => {
        const open = scene => {
          window.clearTimeout(timer);
          if (canceled || navigationScheduled || prefersReducedMotion()) return;
          if (window.RvionEntry?.start(scene) && result.state && !localSeek) {
            try { localStorage.setItem(guardKey, JSON.stringify(result.state)); } catch (error) {}
          }
        };
        if (payload.scene_gzip) {
          if (!window.RvionEntry?.decode) {fail();return;}
          window.RvionEntry.decode(payload).then(open).catch(fail);
        } else open(payload);
      };
      document.head.append(sheet);
    };
    if (document.readyState === 'complete') bootEntry();
    else window.addEventListener('load', bootEntry, {once: true});
  }
  const setMainBusy = busy => main?.setAttribute("aria-busy", busy ? "true" : "false");
  const setNavigationLocked = locked => navigationBackground.forEach(item => item.toggleAttribute("inert", locked));
  const setWelcomeVisible = visible => welcome?.setAttribute("aria-hidden", visible ? "false" : "true");
  const hideNavigationLoader = () => {
    if (navigationRevealTimer) window.clearTimeout(navigationRevealTimer);
    if (navigationFailsafe) window.clearTimeout(navigationFailsafe);
    navigationRevealTimer = null;
    navigationFailsafe = null;
    navigationScheduled = false;
    document.documentElement.classList.remove("navigation-pending");
    welcome?.classList.remove("is-leaving");
    setWelcomeVisible(false);
    setNavigationLocked(false);
    setMainBusy(false);
  };
  const revealNavigationLoader = () => {
    navigationRevealTimer = null;
    if (!welcome || !navigationScheduled || prefersReducedMotion()) return;
    welcome.classList.remove("is-leaving");
    setWelcomeVisible(true);
    document.documentElement.classList.add("navigation-pending");
    setNavigationLocked(true);
  };
  const scheduleNavigationLoader = () => {
    if (!welcome || navigationScheduled) return;
    navigationScheduled = true;
    setMainBusy(true);
    if (!prefersReducedMotion()) {
      navigationRevealTimer = window.setTimeout(revealNavigationLoader, NAVIGATION_REVEAL_DELAY_MS);
    }
    navigationFailsafe = window.setTimeout(hideNavigationLoader, NAVIGATION_FAILSAFE_MS);
  };
  setWelcomeVisible(false);
  setMainBusy(false);

  document.addEventListener("click", event => {
    const link = event.target.closest("a[href]");
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (link.target === "_blank" || link.hasAttribute("download") || link.dataset.noLoader !== undefined) return;
    let destination;
    try { destination = new URL(link.href, location.href); } catch (error) { return; }
    if (destination.origin !== location.origin || !/^https?:$/.test(destination.protocol)) return;
    if (destination.pathname === location.pathname && destination.search === location.search && destination.hash) return;
    scheduleNavigationLoader();
  });
  document.addEventListener("submit", event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || event.defaultPrevented || form.dataset.noLoader !== undefined) return;
    if (form.target === "_blank") return;
    if (typeof form.checkValidity === "function" && !form.checkValidity()) return;
    scheduleNavigationLoader();
  });
  window.addEventListener("pageshow", () => {
    hideNavigationLoader();
  });
  if (reducedMotion?.addEventListener) {
    reducedMotion.addEventListener("change", event => {
      if (!event.matches) return;
      hideNavigationLoader();
    });
  }

  const revealItems = [...document.querySelectorAll("[data-ui-reveal]")];
  if (revealItems.length) {
    if (prefersReducedMotion() || !("IntersectionObserver" in window)) {
      revealItems.forEach(item => item.classList.add("is-visible"));
    } else {
      document.documentElement.classList.add("has-ui-reveal");
      const revealObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        });
      }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
      revealItems.forEach((item, index) => {
        item.style.setProperty("--ui-reveal-delay", `${Math.min(index % 4, 3) * 45}ms`);
        revealObserver.observe(item);
      });
    }
  }

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
