(() => {
  const root = document.querySelector("[data-pull-refresh]");
  if (!root) return;

  const standalone = window.matchMedia?.("(display-mode: standalone)").matches
    || window.navigator.standalone === true;
  const touchDevice = navigator.maxTouchPoints > 0 || "ontouchstart" in window;
  const mobileTouch = window.matchMedia?.("(max-width: 1024px) and (pointer: coarse)").matches;
  if (!standalone || !touchDevice || !mobileTouch) return;

  const label = root.querySelector("[data-pull-refresh-label]");
  const status = root.querySelector("[data-pull-refresh-status]");
  const fa = document.documentElement.lang !== "en";
  const threshold = 76;
  const maxDistance = 116;
  const ignoredTarget = "input,textarea,select,button,a,[contenteditable='true'],[role='dialog'],dialog,summary";
  let startX = 0;
  let startY = 0;
  let tracking = false;
  let direction = "";
  let readyAnnounced = false;
  let reloading = false;

  const atDocumentTop = () => window.scrollY <= 1 && document.documentElement.scrollTop <= 1;
  const hasVisibleDialog = () => [...document.querySelectorAll("dialog,[role='dialog']")].some((dialog) => {
    if (dialog.tagName === "DIALOG") return dialog.hasAttribute("open");
    return !dialog.closest("[hidden]") && dialog.getAttribute("aria-hidden") !== "true";
  });
  const hasOpenOverlay = () => (
    document.body.classList.contains("m-overlay-open")
    || document.body.classList.contains("menu-open")
    || document.documentElement.classList.contains("navigation-pending")
    || hasVisibleDialog()
  );
  const hasScrolledContainer = (target) => {
    let node = target instanceof Element ? target.parentElement : null;
    while (node && node !== document.body) {
      const style = window.getComputedStyle(node);
      if (/(auto|scroll)/.test(style.overflowY) && node.scrollHeight > node.clientHeight && node.scrollTop > 1) return true;
      node = node.parentElement;
    }
    return false;
  };
  const canStart = (event) => {
    const target = event.target;
    return event.touches.length === 1
      && atDocumentTop()
      && !hasOpenOverlay()
      && !(target instanceof Element && target.closest(ignoredTarget))
      && !hasScrolledContainer(target);
  };
  const setDistance = (distance) => {
    const progress = Math.min(1, distance / threshold);
    root.style.setProperty("--pull-distance", `${distance}px`);
    root.style.setProperty("--pull-progress", String(progress));
    root.classList.toggle("is-visible", distance > 7);
    root.classList.toggle("is-ready", distance >= threshold);
    root.setAttribute("aria-hidden", String(distance <= 7));
    if (distance >= threshold && !readyAnnounced) {
      readyAnnounced = true;
      label.textContent = fa ? "رها کنید تا به‌روز شود" : "Release to refresh";
      status.textContent = label.textContent;
    } else if (distance < threshold && readyAnnounced) {
      readyAnnounced = false;
      label.textContent = fa ? "برای به‌روزرسانی به پایین بکشید" : "Pull down to refresh";
      status.textContent = "";
    }
  };
  const reset = () => {
    tracking = false;
    direction = "";
    readyAnnounced = false;
    root.classList.remove("is-visible", "is-ready");
    root.style.setProperty("--pull-distance", "0px");
    root.style.setProperty("--pull-progress", "0");
    root.setAttribute("aria-hidden", "true");
    label.textContent = fa ? "برای به‌روزرسانی به پایین بکشید" : "Pull down to refresh";
    status.textContent = "";
  };

  root.hidden = false;
  document.addEventListener("touchstart", (event) => {
    if (reloading || !canStart(event)) return;
    const touch = event.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;
    tracking = true;
    direction = "";
  }, { passive: true });

  document.addEventListener("touchmove", (event) => {
    if (!tracking || reloading || event.touches.length !== 1) return;
    const touch = event.touches[0];
    const deltaX = touch.clientX - startX;
    const deltaY = touch.clientY - startY;
    if (!direction && Math.max(Math.abs(deltaX), Math.abs(deltaY)) > 8) {
      direction = Math.abs(deltaX) > Math.abs(deltaY) ? "horizontal" : "vertical";
    }
    if (direction === "horizontal" || deltaY <= 0 || !atDocumentTop() || hasOpenOverlay()) {
      reset();
      return;
    }
    if (direction !== "vertical") return;
    event.preventDefault();
    setDistance(Math.min(maxDistance, deltaY * .56));
  }, { passive: false });

  document.addEventListener("touchend", () => {
    if (!tracking || reloading) return;
    const shouldReload = root.classList.contains("is-ready");
    if (!shouldReload) {
      reset();
      return;
    }
    reloading = true;
    root.classList.add("is-refreshing", "is-visible");
    root.classList.remove("is-ready");
    label.textContent = fa ? "در حال به‌روزرسانی…" : "Refreshing…";
    status.textContent = label.textContent;
    window.setTimeout(() => window.location.reload(), 120);
  }, { passive: true });

  document.addEventListener("touchcancel", reset, { passive: true });
  window.addEventListener("pageshow", () => {
    if (!reloading) reset();
  });
})();
