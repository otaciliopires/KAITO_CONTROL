const SHELL=new URL('.',self.location.href).pathname;
const ROOT=SHELL.slice(0,-'ceq/campo/'.length);
const PREFIX='kaito-campo-'+encodeURIComponent(SHELL)+'-shell-';
const CACHE=PREFIX+'v7';
const ASSETS=[SHELL,ROOT+'static/campo/campo.css',ROOT+'static/campo/campo.js',ROOT+'static/campo/icon.svg',SHELL+'manifest.webmanifest'];
self.addEventListener('install',event=>event.waitUntil((async()=>{const cache=await caches.open(CACHE);await cache.addAll(ASSETS.map(url=>new Request(url,{credentials:'omit',cache:'reload'})));await self.skipWaiting();})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const key of await caches.keys()){if(key.startsWith(PREFIX)&&key!==CACHE)await caches.delete(key);}await self.clients.claim();})()));
self.addEventListener('fetch',event=>{const url=new URL(event.request.url);if(event.request.method!=='GET'||url.origin!==self.location.origin||!ASSETS.includes(url.pathname))return;event.respondWith((async()=>{const cache=await caches.open(CACHE);return (await cache.match(url.pathname))||fetch(event.request);})());});
