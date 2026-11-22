/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Service Worker (PWA)
   Cache first para assets estáticos, network first para API.
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

const CACHE_NAME   = 'maer-v8-cache';
const CACHE_STATIC = 'maer-v8-static';

// Assets que se cachean al instalar el SW (shell de la app)
const PRECACHE_URLS = [
  '/',
  '/static/css/maer.css',
  '/static/js/maer.core.js',
  '/static/js/maer.chat.js',
  '/static/js/maer.archivos.js',
  '/static/js/maer.poder.js',
  '/static/js/maer.diagnostico.js',
  '/static/js/maer.sinavid.js',
  '/static/js/maer.busqueda.js',
  '/static/js/maer.voz.js',
  '/static/js/maer.guardian.js',
  '/static/manifest.json',
];

// Rutas de API — siempre van a la red (no se cachean)
const API_ROUTES = [
  '/api/',
];

// ── INSTALL: precachear shell ──
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_STATIC)
      .then(cache => {
        // Cachear cada URL individualmente (no falla si una falla)
        return Promise.allSettled(
          PRECACHE_URLS.map(url =>
            cache.add(url).catch(e => console.warn(`MAER SW: no se pudo cachear ${url}`, e))
          )
        );
      })
      .then(() => self.skipWaiting())
  );
});

// ── ACTIVATE: limpiar caches viejos ──
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME && k !== CACHE_STATIC)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── FETCH: estrategia híbrida ──
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Solo manejar peticiones a nuestro mismo origen
  if (url.origin !== location.origin) return;

  // API: Network First (siempre datos frescos)
  if (API_ROUTES.some(r => url.pathname.startsWith(r))) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  // Documentos y código (HTML/JS/CSS): Network First para no servir versiones viejas
  const esCodigo = event.request.mode === 'navigate'
    || url.pathname === '/'
    || /\.(html|js|css|json)$/i.test(url.pathname);
  if (esCodigo) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  // Assets estáticos: Cache First con fallback a red
  event.respondWith(cacheFirst(event.request));
});

/* Estrategia: Cache First */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_STATIC);
      cache.put(request, response.clone());
    }
    return response;
  } catch(e) {
    // Offline fallback: devuelve página principal si existe
    const fallback = await caches.match('/');
    return fallback || new Response('MAER offline — recarga cuando tengas conexión.', {
      status: 503,
      headers: {'Content-Type': 'text/plain; charset=utf-8'}
    });
  }
}

/* Estrategia: Network First */
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok && request.method === 'GET') {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch(e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ ok: false, code: 'OFFLINE',
                       message: 'Sin conexión — servidor MAER no disponible.' }),
      { status: 503, headers: {'Content-Type': 'application/json'} }
    );
  }
}

// ── MENSAJE: limpiar cache manualmente ──
self.addEventListener('message', event => {
  if (event.data?.action === 'clearCache') {
    caches.keys().then(keys => Promise.all(keys.map(k => caches.delete(k))));
    event.ports[0]?.postMessage({ ok: true });
  }
  if (event.data?.action === 'skipWaiting') {
    self.skipWaiting();
  }
});
