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
self.addEventListener("push", event => { const data = event.data ? event.data.json() : {}; event.waitUntil(self.registration.showNotification(data.title || "آرویون", {body:data.body || "رویداد تازه‌ای نیازمند بررسی است.",tag:data.tag || "rvion-management",icon:"/static/core/favicon.svg",badge:"/static/core/favicon.svg",data:{url:data.url || "/fa/management/notifications/"},requireInteraction:Boolean(data.urgent)})); });
self.addEventListener("notificationclick", event => { const url=event.notification.data?.url || "/fa/management/notifications/"; event.notification.close(); event.waitUntil(clients.matchAll({type:"window",includeUncontrolled:true}).then(items => { const match=items.find(item=>item.url.includes("/management/")); return match ? match.focus().then(()=>match.navigate(url)) : clients.openWindow(url); })); });
