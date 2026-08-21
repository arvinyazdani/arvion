(() => {
  const moreShell = document.querySelector("[data-more-shell]");
  const morePanel = document.querySelector(".m-more-panel");
  const moreTriggers = [...document.querySelectorAll(".m-more-toggle")];
  const moreClose = document.querySelector(".m-more-close");
  const moreScrim = document.querySelector(".m-more-scrim");
  let lastMoreTrigger = null;

  const focusableSelector = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    '[tabindex]:not([tabindex="-1"])',
  ].join(",");

  const setMoreExpanded = (expanded) => {
    moreTriggers.forEach((trigger) => trigger.setAttribute("aria-expanded", String(expanded)));
  };

  const closeMore = ({ returnFocus = true } = {}) => {
    if (!moreShell || !morePanel || moreShell.hidden) return;
    morePanel.setAttribute("aria-hidden", "true");
    morePanel.setAttribute("inert", "");
    moreShell.hidden = true;
    document.body.classList.remove("m-overlay-open");
    setMoreExpanded(false);
    if (returnFocus && lastMoreTrigger instanceof HTMLElement) lastMoreTrigger.focus();
    lastMoreTrigger = null;
  };

  const openMore = (trigger) => {
    if (!moreShell || !morePanel) return;
    lastMoreTrigger = trigger instanceof HTMLElement ? trigger : document.activeElement;
    moreShell.hidden = false;
    morePanel.removeAttribute("inert");
    morePanel.setAttribute("aria-hidden", "false");
    document.body.classList.add("m-overlay-open");
    setMoreExpanded(true);
    window.requestAnimationFrame(() => (moreClose || morePanel.querySelector(focusableSelector))?.focus());
  };

  moreTriggers.forEach((trigger) => trigger.addEventListener("click", () => {
    if (moreShell?.hidden) openMore(trigger);
    else closeMore();
  }));
  moreClose?.addEventListener("click", () => closeMore());
  moreScrim?.addEventListener("click", () => closeMore());

  document.addEventListener("keydown", (event) => {
    if (!moreShell || !morePanel || moreShell.hidden) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeMore();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = [...morePanel.querySelectorAll(focusableSelector)].filter((element) => (
      element instanceof HTMLElement && !element.hidden && element.getClientRects().length > 0
    ));
    if (!focusable.length) {
      event.preventDefault();
      morePanel.focus();
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

  /* Sensitive management actions use one predictable, accessible confirmation
     pattern. The original submitter is retained so payment reject `formaction`
     continues to target the correct endpoint after confirmation. */
  const confirmationDialog = document.createElement("dialog");
  confirmationDialog.className = "m-confirm-dialog";
  confirmationDialog.setAttribute("role", "alertdialog");
  confirmationDialog.setAttribute("aria-modal", "true");
  confirmationDialog.setAttribute("aria-labelledby", "m-confirm-title");
  confirmationDialog.setAttribute("aria-describedby", "m-confirm-message");
  confirmationDialog.innerHTML = `
    <form class="m-confirm-dialog__body" method="dialog">
      <p class="m-confirm-dialog__eyebrow"></p>
      <h2 id="m-confirm-title"></h2>
      <p class="m-confirm-dialog__message" id="m-confirm-message"></p>
      <div class="m-confirm-dialog__actions">
        <button type="submit" value="cancel"></button>
        <button type="submit" value="confirm"></button>
      </div>
    </form>`;
  document.body.appendChild(confirmationDialog);

  const confirmEyebrow = confirmationDialog.querySelector(".m-confirm-dialog__eyebrow");
  const confirmTitle = confirmationDialog.querySelector("#m-confirm-title");
  const confirmMessage = confirmationDialog.querySelector("#m-confirm-message");
  const confirmCancel = confirmationDialog.querySelector('[value="cancel"]');
  const confirmApprove = confirmationDialog.querySelector('[value="confirm"]');
  const isPersianDocument = document.documentElement.lang === "fa";
  let pendingSubmission = null;
  let bypassConfirmationFor = null;

  const confirmationValue = (submitter, form, name, fallback) => (
    submitter?.dataset?.[name] || form.dataset[name] || fallback
  );

  const markSubmitting = (form, submitter) => {
    form.dataset.submitting = "true";
    form.setAttribute("aria-busy", "true");
    if (submitter instanceof HTMLElement) {
      submitter.setAttribute("aria-disabled", "true");
      const submittingLabel = form.dataset.submittingLabel;
      if (submittingLabel) {
        submitter.dataset.readyLabel = submitter.textContent;
        submitter.textContent = submittingLabel;
      }
    }
  };

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.closest(".m-confirm-dialog")) return;
    if (form.dataset.submitting === "true") {
      event.preventDefault();
      return;
    }

    const submitter = event.submitter instanceof HTMLElement ? event.submitter : null;
    if (bypassConfirmationFor === form) {
      bypassConfirmationFor = null;
      markSubmitting(form, submitter);
      return;
    }

    const message = confirmationValue(submitter, form, "confirm", "");
    if (!message) {
      markSubmitting(form, submitter);
      return;
    }

    event.preventDefault();
    pendingSubmission = { form, submitter, returnFocus: submitter || document.activeElement };
    confirmEyebrow.textContent = isPersianDocument ? "بازبینی پیش از ثبت" : "Review before submitting";
    confirmTitle.textContent = confirmationValue(
      submitter,
      form,
      "confirmTitle",
      isPersianDocument ? "این اقدام تأیید شود؟" : "Confirm this action?",
    );
    confirmMessage.textContent = message;
    confirmCancel.textContent = confirmationValue(
      submitter,
      form,
      "confirmCancel",
      isPersianDocument ? "انصراف" : "Cancel",
    );
    confirmApprove.textContent = confirmationValue(
      submitter,
      form,
      "confirmApprove",
      isPersianDocument ? "تأیید اقدام" : "Confirm action",
    );
    confirmationDialog.dataset.tone = confirmationValue(submitter, form, "confirmTone", "default");
    confirmationDialog.showModal();
    window.requestAnimationFrame(() => confirmCancel.focus());
  });

  confirmationDialog.addEventListener("close", () => {
    const submission = pendingSubmission;
    pendingSubmission = null;
    if (!submission) return;
    if (confirmationDialog.returnValue !== "confirm") {
      if (submission.returnFocus instanceof HTMLElement) submission.returnFocus.focus();
      return;
    }
    bypassConfirmationFor = submission.form;
    submission.form.requestSubmit(submission.submitter || undefined);
    queueMicrotask(() => {
      if (bypassConfirmationFor === submission.form) bypassConfirmationFor = null;
    });
  });

  confirmationDialog.addEventListener("click", (event) => {
    if (event.target === confirmationDialog) confirmationDialog.close("cancel");
  });

  window.addEventListener("pageshow", () => {
    document.querySelectorAll('form[data-submitting="true"]').forEach((form) => {
      delete form.dataset.submitting;
      form.removeAttribute("aria-busy");
      form.querySelectorAll('[aria-disabled="true"]').forEach((control) => {
        control.removeAttribute("aria-disabled");
        if (control.dataset.readyLabel) {
          control.textContent = control.dataset.readyLabel;
          delete control.dataset.readyLabel;
        }
      });
    });
  });

  const buttons = [...document.querySelectorAll(".m-alert-enable")];
  if (!buttons.length) return;
  const fa = document.documentElement.lang === "fa";
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
    const registration = await navigator.serviceWorker.register("/service-worker.js?v=4", { updateViaCache: "none" });
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
