const CACHE='rick-digital-v34';
const FILES=['./','./index.html','./manifest.json','./icon.svg','./icon-512.png','./qrcode-celular.html','./fotos/livia.jpg','./fotos/nina.jpg','./fotos/vitoria.jpg'];

// Arquivos que precisam SEMPRE ser a versao mais nova do servidor.
// O CRM busca o JSON de leads todo dia: se ficar em cache, o usuario ve
// a lista de ontem para sempre.
const REDE=/\.(json)$|\/api\/|googleapis|githubusercontent|formsubmit|firebaseio/i;

self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys()
    .then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
    .then(()=>self.clients.claim()));
});

self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);

  // 1) rede primeiro para dados que mudam (JSON de leads, APIs)
  if(REDE.test(url.pathname+url.href)){
    e.respondWith(
      fetch(e.request,{cache:'no-store'}).then(res=>{
        const cp=res.clone();
        caches.open(CACHE).then(c=>c.put(e.request,cp));
        return res;
      }).catch(()=>caches.match(e.request).then(r=>r||new Response('[]',{headers:{'Content-Type':'application/json'}})))
    );
    return;
  }

  // 2) cache primeiro para o app em si (abre offline), atualizando em segundo plano
  e.respondWith(
    caches.match(e.request).then(r=>{
      const rede=fetch(e.request).then(res=>{
        if(res&&res.status===200){const cp=res.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));}
        return res;
      }).catch(()=>r);
      return r||rede;
    })
  );
});
