const CACHE='rick-digital-v41';
const FILES=['./','./index.html','./manifest.json','./icon.svg','./icon-512.png','./qrcode-celular.html','./vendor/leaflet/leaflet.js','./vendor/leaflet/leaflet.css','./vendor/leaflet/images/marker-icon.png','./vendor/leaflet/images/marker-icon-2x.png','./vendor/leaflet/images/marker-shadow.png','./fotos/livia.jpg','./fotos/nina.jpg','./fotos/vitoria.jpg'];
const ABS='https://rickdigitalestudio.github.io/estudio-rick-digital';

// Arquivos que precisam SEMPRE ser a versao mais nova do servidor.
// O CRM busca o JSON de leads todo dia: se ficar em cache, o usuario ve
// a lista de ontem para sempre. O mesmo vale pro versao.json (checagem
// de versao nova no celular).
const REDE=/\.(json)$|\/api\/|googleapis|githubusercontent|formsubmit|firebaseio/i;

self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys()
    .then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
    .then(()=>self.clients.claim()));
});

// O botao "Atualizar" do app pede isso: o SW novo assume na hora.
self.addEventListener('message',e=>{
  if(e.data&&e.data.type==='SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);

  // 0) PAGINA DO APP (abrir o app): rede primeiro, cache so se estiver sem net.
  //    E o que faz o celular pegar a versao nova so reabrindo o app.
  if(e.request.mode==='navigate'||(e.request.destination==='document'&&url.origin===self.location.origin)){
    e.respondWith(
      fetch(e.request).then(res=>{
        // guarda sempre na mesma chave, para nao encher o cache com ?_upd=...
        if(res&&res.status===200){const cp=res.clone();caches.open(CACHE).then(c=>c.put('./index.html',cp));}
        return res;
      }).catch(()=>caches.match('./index.html').then(r=>r||caches.match(e.request).then(r2=>r2||new Response('<h1>Offline</h1>',{headers:{'Content-Type':'text/html'}}))))
    );
    return;
  }

  // 1) rede primeiro para dados que mudam (JSON de leads, versao.json, APIs)
  if(REDE.test(url.pathname+url.href)){
    e.respondWith(
      fetch(e.request,{cache:'no-store'}).then(res=>{
        const cp=res.clone();
        caches.open(CACHE).then(c=>c.put(e.request,cp));
        return res;
      }).catch(()=>caches.match(e.request).then(r=>r||fetch(e.request,{cache:'no-store'}).catch(()=>new Response('[]',{headers:{'Content-Type':'application/json'}}))))
    );
    return;
  }

  // 2) cache primeiro para o resto (icones, fotos), atualizando em segundo plano
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
