(() => {
  const payloadNode = document.getElementById("sms-template-payload");
  const message = document.querySelector("[data-sms-message]");
  if (payloadNode && message) {
    const payload = JSON.parse(payloadNode.textContent);
    document.getElementById("id_template")?.addEventListener("change", (event) => {
      const selected = payload.find(item => String(item.id) === event.target.value);
      if (selected) message.value = selected.body;
    });
  }
  const error = document.querySelector(".fu-error[role=alert]");
  if (error) error.focus();
  else document.getElementById("preview-heading")?.focus();
})();
