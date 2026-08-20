(() => {
  let sent = 0;
  const MAX_PER_LOAD = 5;
  const send = (message, source, line) => {
    if (sent >= MAX_PER_LOAD) return;
    sent += 1;
    try {
      const body = JSON.stringify({ message: String(message || "").slice(0, 280), source: String(source || ""), line, path: location.pathname });
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/log/js-error/", new Blob([body], { type: "application/json" }));
      } else {
        fetch("/log/js-error/", { method: "POST", body, headers: { "Content-Type": "application/json" }, keepalive: true });
      }
    } catch (e) {}
  };
  window.addEventListener("error", (event) => {
    send(event.message, event.filename, event.lineno);
  });
  window.addEventListener("unhandledrejection", (event) => {
    send("Unhandled promise rejection: " + (event.reason && event.reason.message ? event.reason.message : event.reason), location.pathname, "");
  });
})();
