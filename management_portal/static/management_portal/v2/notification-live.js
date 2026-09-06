(() => {
  const endpoint = window.RVION_NOTIFICATION_FEED;
  if (!endpoint) return;
  const fa = document.documentElement.lang === "fa";
  const CURSOR_KEY = "rvion-notification-cursor-v2";
  const shown = new Set();
  const channel = "BroadcastChannel" in window ? new BroadcastChannel("rvion-notifications") : null;
  let cursor = Number(sessionStorage.getItem(CURSOR_KEY) || 0);
  let busy = false;
  let failures = 0;
  let lastSoundAt = 0;

  const setCount = (count) => {
    document.querySelectorAll("[data-notification-badge]").forEach((badge) => {
      badge.textContent = String(count);
      badge.hidden = count === 0;
    });
    document.querySelectorAll("[data-unread-count]").forEach((node) => { node.textContent = String(count); });
    document.querySelectorAll("[data-notification-link]").forEach((link) => {
      const base = fa ? link.dataset.labelFa : link.dataset.labelEn;
      link.setAttribute("aria-label", `${base}; ${count} ${fa ? "مورد جدید" : "new item(s)"}`);
    });
    if ("setAppBadge" in navigator) {
      const task = count ? navigator.setAppBadge(count) : navigator.clearAppBadge();
      task?.catch?.(() => {});
    }
  };

  const stack = () => {
    let node = document.querySelector("[data-notification-toasts]");
    if (!node) {
      node = document.createElement("div");
      node.className = "n-toast-stack";
      node.dataset.notificationToasts = "";
      node.setAttribute("aria-live", "polite");
      node.setAttribute("aria-label", fa ? "اعلان‌های تازه" : "New notifications");
      document.body.appendChild(node);
    }
    return node;
  };

  const toast = (item) => {
    if (!item?.id || shown.has(String(item.id))) return false;
    shown.add(String(item.id));
    const card = document.createElement("article");
    card.className = "n-toast";
    card.dataset.priority = item.priority || "normal";
    const tone = document.createElement("i");
    tone.setAttribute("aria-hidden", "true");
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    const body = document.createElement("small");
    title.textContent = item.title || (fa ? "رویداد تازه" : "New update");
    body.textContent = item.description || item.category || "";
    copy.append(title, body);
    const link = document.createElement("a");
    link.href = item.url;
    link.textContent = fa ? "باز کردن" : "Open";
    card.append(tone, copy, link);
    stack().prepend(card);
    window.setTimeout(() => card.remove(), item.priority === "critical" ? 12000 : 7000);
    return true;
  };

  const announceBatch = (items) => {
    const fresh = items.filter(toast);
    if (!fresh.length) return;
    const now = Date.now();
    if (now - lastSoundAt > 1200) {
      const priority = fresh.some((item) => item.priority === "critical") ? "critical" : fresh.some((item) => item.priority === "high") ? "high" : "normal";
      window.RvionSounds?.playNotification(priority).catch(() => {});
      lastSoundAt = now;
    }
    const banner = document.querySelector("[data-notification-live-banner]");
    const copy = document.querySelector("[data-notification-live-copy]");
    if (banner && copy) {
      copy.textContent = fa ? `${fresh.length} مورد تازه رسید.` : `${fresh.length} new item(s) arrived.`;
      banner.hidden = false;
    }
  };

  const rememberCursor = (next) => {
    cursor = Math.max(cursor, Number(next || 0));
    try { sessionStorage.setItem(CURSOR_KEY, String(cursor)); } catch (error) {}
  };

  const sync = async ({ forceBootstrap = false } = {}) => {
    if (busy || document.visibilityState === "hidden" || !navigator.onLine) return;
    busy = true;
    try {
      const url = new URL(endpoint, window.location.origin);
      if (!cursor || forceBootstrap) url.searchParams.set("bootstrap", "1");
      else url.searchParams.set("since", String(cursor));
      const response = await fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" }, cache: "no-store" });
      if (!response.ok) throw new Error(`feed_${response.status}`);
      const data = await response.json();
      setCount(Number(data.unread_count || 0));
      Object.entries(data.counts || {}).forEach(([view, count]) => {
        const node = document.querySelector(`[data-notification-view-count="${view}"]`);
        if (node) node.textContent = String(count);
      });
      announceBatch(Array.isArray(data.notifications) ? data.notifications : []);
      rememberCursor(data.latest_id);
      failures = 0;
      channel?.postMessage({ type: "count", count: Number(data.unread_count || 0), cursor });
      if (data.has_more) window.setTimeout(() => sync(), 0);
    } catch (error) {
      failures = Math.min(failures + 1, 5);
    } finally {
      busy = false;
    }
  };

  channel?.addEventListener("message", (event) => {
    if (event.data?.type === "count") {
      setCount(Number(event.data.count || 0));
      rememberCursor(event.data.cursor);
    }
    if (event.data?.type === "action") {
      if (typeof event.data.count === "number") setCount(event.data.count);
      if (["resolved", "snooze", "dismiss", "payment_approve", "payment_reject"].includes(event.data.action)) {
        document.querySelector(`[data-notification="${event.data.id}"]`)?.remove();
      }
      sync();
    }
  });
  navigator.serviceWorker?.addEventListener("message", (event) => {
    if (event.data?.type !== "rvion-notification") return;
    const item = event.data.payload || {};
    toast({
      id: item.notification_id || item.tag,
      title: item.title,
      description: item.body,
      url: item.url,
      priority: item.priority,
    });
    window.RvionSounds?.playNotification(item.priority).catch(() => {});
    sync();
  });
  document.querySelector("[data-notification-live-refresh]")?.addEventListener("click", () => window.location.reload());
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") sync(); });
  window.addEventListener("focus", () => sync());
  window.addEventListener("online", () => sync());
  window.addEventListener("pageshow", () => sync());

  sync({ forceBootstrap: !cursor });
  window.setInterval(() => sync(), 15000 * Math.max(1, 2 ** failures));
})();
