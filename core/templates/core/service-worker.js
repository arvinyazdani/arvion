const CACHE = "rvion-shell-v1";
const SHELL = ["/fa/", "/static/core/css/site.css", "/static/core/js/site-shell.js", "/static/core/favicon.svg"];
self.addEventListener("install", event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET" || !event.request.url.startsWith(self.location.origin)) return;
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/admin/") || url.pathname.includes("/account/") || url.pathname.includes("/checkout/")) return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok && (url.pathname.startsWith("/static/") || event.request.mode === "navigate")) caches.open(CACHE).then(cache => cache.put(event.request, response.clone()));
    return response;
  }).catch(() => caches.match(event.request).then(cached => cached || (event.request.mode === "navigate" ? caches.match("/fa/") : Response.error()))));
});
self.addEventListener("notificationclick", event => { event.notification.close(); event.waitUntil(clients.matchAll({type:"window",includeUncontrolled:true}).then(items => items[0] ? items[0].focus() : clients.openWindow("/fa/management/"))); });
