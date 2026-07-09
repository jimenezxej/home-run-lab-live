const CACHE='hr-lab-3-v1';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const url=new URL(e.request.url); if(url.pathname.endsWith('.json')){e.respondWith(fetch(e.request).catch(()=>caches.match(e.request))); return;} e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));});
