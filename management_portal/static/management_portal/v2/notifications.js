(() => {
  const forms = document.querySelectorAll("[data-notification-action]");
  if (!forms.length) return;

  const badges = document.querySelectorAll("[data-notification-badge]");
  const counters = document.querySelectorAll("[data-unread-count]");
  const fa = document.documentElement.lang === "fa";
  const refreshCounts = async () => {
    try {
      const response = await fetch(location.pathname + location.search, { credentials: "same-origin", cache: "no-store" });
      if (!response.ok || response.redirected) return;
      const doc = new DOMParser().parseFromString(await response.text(), "text/html");
      doc.querySelectorAll("[data-notification-view-count]").forEach((source) => {
        const target = document.querySelector(`[data-notification-view-count="${source.dataset.notificationViewCount}"]`);
        if (target) target.textContent = source.textContent;
      });
    } catch (error) { /* The successful action remains confirmed; refresh is optional. */ }
  };
  document.addEventListener("rvion-inbox-state-changed", refreshCounts);

  const confirmAction = (message, needsReason = false) => new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "n-confirm";
    dialog.setAttribute("aria-labelledby", "inbox-confirm-title");
    dialog.innerHTML = `<form method="dialog" data-no-loader><p id="inbox-confirm-title"></p>${needsReason ? `<label>${fa ? "دلیل رد" : "Rejection reason"}<textarea required minlength="3"></textarea></label>` : ""}<div><button value="cancel" formnovalidate>${fa ? "انصراف" : "Cancel"}</button><button class="n-confirm-submit" value="confirm">${fa ? "تأیید اقدام" : "Confirm action"}</button></div></form>`;
    dialog.querySelector("p").textContent = message;
    document.body.appendChild(dialog);
    dialog.addEventListener("close", () => {
      const accepted = dialog.returnValue === "confirm";
      dialog.remove();
      resolve({ accepted, reason: dialog.querySelector("textarea")?.value.trim() || "" });
    }, { once: true });
    dialog.showModal();
  });

  const feedback = (card, message, isError) => {
    const target = card?.querySelector("[data-notification-feedback]");
    if (!target) return;
    target.textContent = message;
    target.hidden = !message;
    target.classList.toggle("is-error", !!isError);
  };

  forms.forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const card = form.closest("[data-notification]");
      if (!card || card.dataset.busy === "true") return;
      card.dataset.busy = "true";
      const confirmation = form.dataset.confirmText;
      if (confirmation) {
        const context = card.querySelector(".n-source-details")?.innerText || "";
        const result = await confirmAction(`${context}\n${confirmation}`, form.hasAttribute("data-requires-note"));
        if (!result.accepted || (form.hasAttribute("data-requires-note") && result.reason.length < 3)) {
          delete card.dataset.busy;
          return;
        }
        const note = form.querySelector('[name="review_note"]');
        if (note) note.value = result.reason;
      }
      const body = new FormData(form);
      const buttons = [...card.querySelectorAll("button, select")];
      buttons.forEach((button) => (button.disabled = true));
      card.setAttribute("aria-busy", "true");
      feedback(card, fa ? "در حال ثبت اقدام…" : "Saving action…", false);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      try {
        const response = await fetch(form.action, {
          method: "POST",
          body,
          signal: controller.signal,
          credentials: "same-origin",
          headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json" },
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.ok) {
          feedback(card, data.message || (fa ? "اقدام تأیید نشد؛ جزئیات را باز کنید و وضعیت را بررسی کنید." : "Action not confirmed; open the details to check its status."), true);
          buttons.forEach((button) => (button.disabled = false));
          return;
        }
        feedback(card, data.message, false);
        refreshCounts();
        const status = card?.querySelector("[data-notification-status]");
        const owner = card?.querySelector("[data-notification-owner]");
        if (status && data.display_status) status.textContent = data.display_status;
        if (owner && data.owner) owner.textContent = `${fa ? "مسئول" : "Owner"}: ${data.owner}`;
        if (typeof data.unread_count === "number") {
          badges.forEach((badge) => {
            badge.textContent = String(data.unread_count);
            badge.hidden = data.unread_count === 0;
          });
          counters.forEach((node) => (node.textContent = String(data.unread_count)));
        }
        if ("BroadcastChannel" in window) {
          const channel = new BroadcastChannel("rvion-notifications");
          channel.postMessage({ type: "action", id: data.id, action: data.action, count: data.unread_count, display_status: data.display_status });
          channel.close();
        }
        // Keep confirmation at the same position; do not strand focus or jump the queue.
        if (["resolved", "snooze", "dismiss"].includes(data.action) || String(data.action).startsWith("payment_")) {
          card.classList.add("is-settled");
          card.querySelectorAll(".n-actions form, .n-more-actions").forEach((node) => { node.hidden = true; });
          card.focus({ preventScroll: true });
        } else {
          buttons.forEach((button) => (button.disabled = false));
        }
      } catch (error) {
        feedback(card, fa ? "پاسخ سرور دریافت نشد؛ ممکن است اقدام ثبت شده باشد. ابتدا جزئیات را بررسی کنید." : "No server confirmation; the action may have completed. Check the details first.", true);
        buttons.forEach((button) => (button.disabled = false));
      } finally {
        clearTimeout(timeout);
        delete card.dataset.busy;
        card.removeAttribute("aria-busy");
        if (!card.classList.contains("is-settled") && event.submitter?.isConnected && !event.submitter.disabled) {
          event.submitter.focus({ preventScroll: true });
        }
      }
    });
  });
})();
