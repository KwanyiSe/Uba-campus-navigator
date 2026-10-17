const CACHE_NAME = "unimap-v5-compass-fix";
const APP_SHELL = [
  "/map/",
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
  if (url.origin !== self.location.origin) return;

  // Never cache authenticated pages, API responses, or dynamic user data.
  const isStaticAsset = url.pathname.startsWith("/static/");
  const isMapPage = request.mode === "navigate" && url.pathname === "/map/";
  if (!isStaticAsset && !isMapPage) return;

  event.respondWith((async () => {
    try {
      const response = await fetch(request, { cache: "no-cache" });
      if (response && response.ok) {
        const cache = await caches.open(CACHE_NAME);
        await cache.put(request, response.clone());
      }
      return response;
    } catch (error) {
      const cached = await caches.match(request);
      if (cached) return cached;
      throw error;
    }
  })());
});
