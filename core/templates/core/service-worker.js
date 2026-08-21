const CACHE = "rvion-shell-v4";
const OFFLINE_URL_FA = "/offline/fa/";
const OFFLINE_URL_EN = "/offline/en/";
const SHELL = [
  OFFLINE_URL_FA,
  OFFLINE_URL_EN,
  "/static/core/favicon.svg",
  "/static/core/icons/icon-192.png",
  "/static/core/icons/app-icon-maskable.svg",
  "/static/core/manifest.webmanifest",
];
const CACHEABLE_DESTINATIONS = new Set(["font", "image", "manifest", "script", "style"]);

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith("rvion-shell-") && key !== CACHE).map(key => caches.delete(key)));
    if (self.registration.navigationPreload) await self.registration.navigationPreload.enable();
    await self.clients.claim();
  })());
});

async function staticAsset(event) {
  const request = event.request;
  const cached = await caches.match(request);
  const refreshed = fetch(request).then(async response => {
    if (response.ok && response.type === "basic") {
      const cache = await caches.open(CACHE);
      await cache.put(request, response.clone());
    }
    return response;
  }).catch(error => {
    if (cached) return cached;
    throw error;
  });
  if (cached) {
    event.waitUntil(refreshed.then(() => undefined));
    return cached;
  }
  return refreshed;
}

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (event.request.mode === "navigate") {
    event.respondWith((async () => {
      try {
        return (await event.preloadResponse) || (await fetch(event.request));
      } catch (error) {
        const offlineUrl = url.pathname.startsWith("/en/") ? OFFLINE_URL_EN : OFFLINE_URL_FA;
        return (await caches.match(offlineUrl)) || Response.error();
      }
    })());
    return;
  }

  if (url.pathname.startsWith("/static/") && CACHEABLE_DESTINATIONS.has(event.request.destination)) {
    event.respondWith(staticAsset(event));
  }
});
self.addEventListener("push", event => { let data={};try{data=event.data?event.data.json():{}}catch(error){data={body:event.data?event.data.text():""}}event.waitUntil(self.registration.showNotification(data.title || "آرویون", {body:data.body || "رویداد تازه‌ای نیازمند بررسی است.",tag:data.tag || "rvion-management",icon:"/static/core/icons/icon-192.png",badge:"/static/core/icons/icon-192.png",data:{url:data.url || "/fa/management/notifications/"},requireInteraction:Boolean(data.urgent)})); });
self.addEventListener("notificationclick", event => { const fallback="/fa/management/notifications/";let target;try{target=new URL(event.notification.data?.url || fallback,self.location.origin)}catch(error){target=new URL(fallback,self.location.origin)}if(target.origin!==self.location.origin)target=new URL(fallback,self.location.origin);event.notification.close();event.waitUntil(clients.matchAll({type:"window",includeUncontrolled:true}).then(items => { const match=items.find(item=>item.url.includes("/management/")); return match ? match.focus().then(()=>match.navigate(target.href)) : clients.openWindow(target.href); })); });
