(() => {
  const forms = document.querySelectorAll("[data-notification-action]");
  if (!forms.length) return;

  const badges = document.querySelectorAll("[data-notification-badge]");
  const counters = document.querySelectorAll("[data-unread-count]");
  const fa = document.documentElement.lang === "fa";

  const confirmAction = (message, needsReason = false) => new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "n-confirm";
    dialog.innerHTML = `<form method="dialog"><p></p>${needsReason ? `<label>${fa ? "دلیل رد" : "Rejection reason"}<textarea required minlength="3"></textarea></label>` : ""}<div><button value="cancel">${fa ? "انصراف" : "Cancel"}</button><button class="n-confirm-submit" value="confirm">${fa ? "تأیید اقدام" : "Confirm action"}</button></div></form>`;
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
      const confirmation = form.dataset.confirmText;
      if (confirmation) {
        const result = await confirmAction(confirmation, form.hasAttribute("data-requires-note"));
        if (!result.accepted || (form.hasAttribute("data-requires-note") && result.reason.length < 3)) return;
        const note = form.querySelector('[name="review_note"]');
        if (note) note.value = result.reason;
      }
      const card = form.closest("[data-notification]");
      const buttons = [...form.querySelectorAll("button")];
      buttons.forEach((button) => (button.disabled = true));
      try {
        const response = await fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          credentials: "same-origin",
          headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json" },
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.ok) {
          feedback(card, data.message || (fa ? "انجام نشد؛ دوباره تلاش کنید." : "The action failed. Please try again."), true);
          buttons.forEach((button) => (button.disabled = false));
          return;
        }
        feedback(card, data.message, false);
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
        // A resolved or snoozed item leaves this queue; fade it out in place
        // so the manager keeps their scroll position.
        if (data.action === "resolved" || data.action === "snooze" || String(data.action).startsWith("payment_")) {
          card?.classList.add("is-leaving");
          setTimeout(() => card?.remove(), 900);
        } else {
          buttons.forEach((button) => (button.disabled = false));
        }
      } catch (error) {
        feedback(card, fa ? "ارتباط با سرور برقرار نشد؛ دوباره تلاش کنید." : "Could not reach the server. Please try again.", true);
        buttons.forEach((button) => (button.disabled = false));
      }
    });
  });
})();
