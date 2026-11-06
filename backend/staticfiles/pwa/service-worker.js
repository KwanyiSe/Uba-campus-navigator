const CACHE_NAME = "unimap-static-v5";
const APP_SHELL = [
  "/static/css/shared.css",
  "/static/css/campus-map.css",
  "/static/js/campus-map.js",
  "/static/pwa/manifest.json",
  "/static/pwa/icon-192.png",
  "/static/pwa/icon-512.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key.startsWith("unimap-") && key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  // Never cache API responses, pages, authentication, profiles, notifications,
  // classes, or attendance. Those must always reflect current server state.
  if (url.origin !== self.location.origin || !url.pathname.startsWith("/static/")) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    if (cached) {
      // Refresh in the background so the next visit gets current static assets.
      event.waitUntil(fetch(request).then(response => {
        if (response.ok) return cache.put(request, response.clone());
      }).catch(() => {}));
      return cached;
    }
    try {
      const response = await fetch(request);
      if (response.ok && response.type === "basic") await cache.put(request, response.clone());
      return response;
    } catch (error) {
      return new Response("This resource is unavailable offline.", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
    }
  })());
});
