(() => {
  let sent = 0;
  const MAX_PER_LOAD = 5;
  const ALLOWED_KINDS = new Set(["Error", "EvalError", "InternalError", "RangeError", "ReferenceError", "SyntaxError", "TypeError", "URIError"]);
  const errorKind = (error, fallback) => {
    const candidate = error && ALLOWED_KINDS.has(error.name) ? error.name : String(fallback || "").split(":", 1)[0];
    return ALLOWED_KINDS.has(candidate) ? candidate : "Error";
  };
  const sourceName = (source) => {
    try {
      const url = new URL(String(source || ""), location.origin);
      if (url.origin !== location.origin) return "";
      return url.pathname.split("/").pop().slice(0, 100);
    } catch (e) { return ""; }
  };
  const send = (kind, source, line) => {
    if (sent >= MAX_PER_LOAD) return;
    sent += 1;
    try {
      const body = JSON.stringify({ kind, source: sourceName(source), line: Number(line) || 0, path: location.pathname });
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/log/js-error/", new Blob([body], { type: "application/json" }));
      } else {
        fetch("/log/js-error/", { method: "POST", body, headers: { "Content-Type": "application/json" }, keepalive: true });
      }
    } catch (e) {}
  };
  window.addEventListener("error", (event) => {
    send(errorKind(event.error, event.message), event.filename, event.lineno);
  });
  window.addEventListener("unhandledrejection", (event) => {
    send("UnhandledRejection", "", 0);
  });
})();
