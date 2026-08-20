(() => {
  window.RVION_STAFF_PUSH = true;
  const onboarding = document.createElement("script");
  onboarding.src = "/static/core/js/staff-push.js?v=1";
  onboarding.defer = true;
  document.head.appendChild(onboarding);

  const menu = document.querySelector(".m-menu");
  const bottomMenu = document.querySelector(".m-bottom-menu");
  const sidebar = document.querySelector(".m-sidebar");
  const sidebarClose = document.querySelector(".m-sidebar-close");
  const scrim = document.querySelector(".m-scrim");
  const moreGroup = document.querySelector(".m-nav-more");
  const moreSummary = moreGroup?.querySelector("summary");
  const mobileViewport = window.matchMedia("(max-width: 760px)");
  const fa = document.documentElement.lang === "fa";
  const openLabel = fa ? "بازکردن منو" : "Open menu";
  const moreLabel = fa ? "ابزارهای بیشتر" : "More tools";
  const closeLabel = fa ? "بستن منو" : "Close menu";
  let lastDrawerTrigger = null;

  const drawerTriggers = [menu, bottomMenu].filter(Boolean);
  const focusableSelector = [
    "a[href]",
    "button:not([disabled])",
    "summary",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    '[tabindex]:not([tabindex="-1"])',
  ].join(",");

  const setDrawerTriggerState = (open) => {
    drawerTriggers.forEach((trigger) => trigger.setAttribute("aria-expanded", String(open)));
    if (menu) menu.setAttribute("aria-label", open ? closeLabel : openLabel);
    if (bottomMenu) bottomMenu.setAttribute("aria-label", open ? closeLabel : moreLabel);
  };

  const mobileDrawerIsOpen = () => Boolean(
    mobileViewport.matches && sidebar?.classList.contains("open")
  );

  const closeDrawer = ({ returnFocus = true } = {}) => {
    if (!sidebar || !scrim) return;
    sidebar.classList.remove("open");
    scrim.classList.remove("open");
    document.body.classList.remove("m-menu-open");
    setDrawerTriggerState(false);

    if (mobileViewport.matches) {
      sidebar.setAttribute("aria-hidden", "true");
      sidebar.setAttribute("inert", "");
      sidebar.removeAttribute("role");
      sidebar.removeAttribute("aria-modal");
    }

    if (returnFocus && lastDrawerTrigger instanceof HTMLElement) {
      lastDrawerTrigger.focus();
    }
    lastDrawerTrigger = null;
  };

  const openDrawer = (trigger) => {
    if (!sidebar || !scrim || !mobileViewport.matches) return;
    lastDrawerTrigger = trigger instanceof HTMLElement ? trigger : document.activeElement;
    sidebar.classList.add("open");
    scrim.classList.add("open");
    document.body.classList.add("m-menu-open");
    sidebar.removeAttribute("aria-hidden");
    sidebar.removeAttribute("inert");
    sidebar.setAttribute("role", "dialog");
    sidebar.setAttribute("aria-modal", "true");
    setDrawerTriggerState(true);
    window.requestAnimationFrame(() => {
      const firstTarget = sidebarClose || sidebar.querySelector(focusableSelector);
      firstTarget?.focus();
    });
  };

  const toggleDrawer = (trigger) => {
    if (mobileDrawerIsOpen()) closeDrawer();
    else openDrawer(trigger);
  };

  const syncNavigationForViewport = () => {
    if (!sidebar || !scrim) return;
    if (mobileViewport.matches) {
      closeDrawer({ returnFocus: false });
      if (moreGroup) moreGroup.open = false;
    } else {
      sidebar.classList.remove("open");
      sidebar.removeAttribute("aria-hidden");
      sidebar.removeAttribute("inert");
      sidebar.removeAttribute("role");
      sidebar.removeAttribute("aria-modal");
      scrim.classList.remove("open");
      document.body.classList.remove("m-menu-open");
      setDrawerTriggerState(false);
      if (moreGroup) moreGroup.open = true;
    }
    if (moreSummary) {
      moreSummary.setAttribute("aria-expanded", String(Boolean(moreGroup?.open)));
      moreSummary.tabIndex = mobileViewport.matches ? 0 : -1;
    }
  };

  drawerTriggers.forEach((trigger) => {
    trigger.addEventListener("click", () => toggleDrawer(trigger));
  });
  sidebarClose?.addEventListener("click", () => closeDrawer());
  scrim?.addEventListener("click", () => closeDrawer());
  moreGroup?.addEventListener("toggle", () => {
    moreSummary?.setAttribute("aria-expanded", String(moreGroup.open));
  });

  document.addEventListener("keydown", (event) => {
    if (!mobileDrawerIsOpen() || !sidebar) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeDrawer();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = [...sidebar.querySelectorAll(focusableSelector)].filter((element) => {
      return element instanceof HTMLElement && !element.hidden && element.getClientRects().length > 0;
    });
    if (!focusable.length) {
      event.preventDefault();
      sidebar.focus();
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  if (typeof mobileViewport.addEventListener === "function") {
    mobileViewport.addEventListener("change", syncNavigationForViewport);
  } else {
    mobileViewport.addListener(syncNavigationForViewport);
  }
  syncNavigationForViewport();

  const languageLink = document.querySelector(".m-top-actions a.m-lang");
  if (languageLink) {
    const target = fa ? "en" : "fa";
    languageLink.href = location.pathname.replace(/^\/(fa|en)(?=\/)/, `/${target}`) + location.search;
  }

  const buttons = [...document.querySelectorAll(".m-alert-enable")];
  if (!buttons.length) return;
  const help = document.querySelector("[data-notification-help]");
  const notificationStatus = document.querySelector("[data-notification-status]");
  const b64 = (value) => {
    const padding = "=".repeat((4 - value.length % 4) % 4);
    const raw = atob((value + padding).replace(/-/g, "+").replace(/_/g, "/"));
    return Uint8Array.from([...raw].map((character) => character.charCodeAt(0)));
  };
  const csrf = () => document.cookie.split("; ").find((value) => value.startsWith("csrftoken="))?.split("=")[1] || "";
  const announce = (text) => {
    if (notificationStatus) notificationStatus.textContent = text;
  };
  const label = (text, state = "") => {
    buttons.forEach((button) => {
      button.textContent = text;
      button.dataset.state = state;
      button.setAttribute("aria-busy", String(state === "loading"));
    });
    announce(text);
  };
  const setHelp = (text) => {
    if (help) help.textContent = text;
    announce(text);
  };
  const explainBlocked = () => {
    const iphone = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    const text = iphone
      ? (fa
        ? "اعلان در آیفون مسدود است. Settings ← Notifications ← Rvion را باز و Allow Notifications را روشن کنید. برنامه باید از Home Screen اجرا شود."
        : "Notifications are blocked. Open Settings → Notifications → Rvion and enable Allow Notifications. Launch Rvion from the Home Screen.")
      : (fa
        ? "مجوز قبلاً مسدود شده است. کنار آدرس سایت روی آیکن تنظیمات بزنید، Notifications را روی Allow قرار دهید و صفحه را دوباره بارگذاری کنید."
        : "Permission was previously blocked. Open site settings beside the address bar, set Notifications to Allow, then reload.");
    setHelp(text);
    label(fa ? "راهنمای رفع مسدودی اعلان" : "How to unblock alerts", "blocked");
  };
  const enable = async (localTest = false) => {
    if (!("Notification" in window) || !("serviceWorker" in navigator) || !("PushManager" in window)) {
      setHelp(fa
        ? "این مرورگر از اعلان وب پشتیبانی نمی‌کند. در آیفون، ابتدا سایت را به Home Screen اضافه کنید."
        : "This browser does not support web push. On iPhone, add the site to the Home Screen first.");
      label(fa ? "اعلان در این مرورگر آماده نیست" : "Alerts unavailable", "unsupported");
      return;
    }
    if (!window.RVION_VAPID_PUBLIC_KEY) {
      label(fa ? "تنظیمات سرور اعلان کامل نیست" : "Server push is not configured", "error");
      return;
    }
    if (Notification.permission === "denied") {
      explainBlocked();
      return;
    }
    label(fa ? "در حال فعال‌سازی…" : "Enabling…", "loading");
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      explainBlocked();
      return;
    }
    const registration = await navigator.serviceWorker.register("/service-worker.js?v=2", { updateViaCache: "none" });
    await registration.update();
    await navigator.serviceWorker.ready;
    let subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: b64(window.RVION_VAPID_PUBLIC_KEY),
      });
    }
    const response = await fetch(window.RVION_PUSH_SUBSCRIBE, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify(subscription.toJSON()),
    });
    if (!response.ok) throw new Error("subscription_failed");
    if (localTest) {
      await registration.showNotification(fa ? "تست اعلان آرویون" : "Rvion notification test", {
        body: fa
          ? "اگر این پیام را می‌بینید، نمایش اعلان روی دستگاه سالم است."
          : "If you can see this message, on-device notifications work.",
        tag: "rvion-local-test",
        icon: "/static/core/icons/icon-192.png",
        badge: "/static/core/icons/icon-192.png",
        data: { url: location.pathname },
      });
    }
    setHelp(localTest
      ? (fa ? "تست محلی ارسال شد؛ اکنون باید اعلان تست روی همین دستگاه دیده شود." : "Local test sent; a test notification should now appear on this device.")
      : (fa ? "این دستگاه با موفقیت برای همه رویدادهای مدیریتی ثبت شد." : "This device is registered for all management events."));
    label(fa ? "اعلان فعال است — ارسال تست" : "Alerts enabled — send test", "ready");
  };
  buttons.forEach((button) => button.addEventListener("click", () => enable(true).catch(() => {
    setHelp(fa
      ? "اتصال یا نمایش تست کامل نشد. تنظیمات اعلان دستگاه را بررسی کنید."
      : "Setup or local display failed. Check device notification settings.");
    label(fa ? "تلاش دوباره" : "Try again", "error");
  })));
  if ("Notification" in window) {
    if (Notification.permission === "granted") {
      enable(false).catch(() => label(fa ? "تلاش دوباره" : "Try again", "error"));
    } else if (Notification.permission === "denied") {
      explainBlocked();
    }
  }
})();
