// Ponte ESTÚDIO RICK DIGITAL <-> Evolution API (WhatsApp automático de verdade)
// Hospede grátis: Railway / Render / VPS. Depois cole URL + Key em Config > Controle Total.
//
// 1) Suba a Evolution: https://github.com/EvolutionAPI/evolution-api
//    Docker: docker run -p 8080:8080 -e AUTHENTICATION_API_KEY=SUA_KEY evolution-api
// 2) Crie instância: POST /instance/create {instanceName:"rick-digital"} -> escaneie QR 1x
// 3) Cole no app: URL + Key + instância rick-digital -> Testar conexão
// 4) Webhook (resposta automática): configure na Evolution:
//    POST para: https://SEU-SERVIDOR/webhook/evolution
//    Este arquivo é exemplo Node para receber e jogar no Firebase/CRM.
//
// Rotas desta ponte:
//   POST /webhook/evolution  -> recebe mensagem e responde boas-vindas
//   POST /check-number       -> {"numbers":["5511..."]} -> {numero:{exists,jid}}
//                               (o app usa para saber se o lead TEM WhatsApp)
//   GET  /health             -> status

const http = require('http');
const BOAS_VINDAS = process.env.BOAS_VINDAS || 'Olá! Aqui é do ESTÚDIO RICK DIGITAL. Portfólio: https://rickdigitalestudio.github.io/profissional-rickdutra/ — quer proposta?';

const EVO_URL = (process.env.EVO_URL || '').replace(/\/$/, '');
const EVO_KEY = process.env.EVO_KEY || '';
const EVO_INST = process.env.EVO_INST || 'rick-digital';

function cors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, apikey');
}

async function enviarTexto(evoUrl, apiKey, instancia, numero, texto) {
  const r = await fetch(`${evoUrl}/message/sendText/${instancia}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: apiKey },
    body: JSON.stringify({ number: numero.replace(/\D/g,''), text: texto })
  });
  if (!r.ok) throw new Error('Evo ' + r.status);
  return r.json();
}

// Confirma quais números têm WhatsApp. Tenta as duas rotas da Evolution
// (checkNumber nas versões novas, whatsappNumbers na v2).
async function checarWhatsApp(numeros) {
  const corpo = JSON.stringify({ numbers: numeros.map(n => String(n).replace(/\D/g, '')) });
  for (const rota of ['/chat/checkNumber/', '/chat/whatsappNumbers/']) {
    try {
      const r = await fetch(`${EVO_URL}${rota}${encodeURIComponent(EVO_INST)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', apikey: EVO_KEY },
        body: corpo
      });
      const j = await r.json();
      const itens = Array.isArray(j) ? j : (j?.result || []);
      if (!Array.isArray(itens) || !itens.length) continue;
      const saida = {};
      for (const it of itens) {
        const num = String(it?.number || '').replace(/\D/g, '');
        if (num) saida[num] = { exists: !!it.exists, jid: it.jid || '' };
      }
      if (Object.keys(saida).length) return saida;
    } catch (e) { /* tenta a próxima rota */ }
  }
  return {};
}

const server = http.createServer(async (req, res) => {
  cors(res);
  if (req.method === 'OPTIONS') { res.statusCode = 204; return res.end(); }

  // ---- verificação de WhatsApp (usada pelo CRM) ----
  if (req.url === '/check-number' && req.method === 'POST') {
    let b = ''; req.on('data', c => b += c); req.on('end', async () => {
      try {
        const j = JSON.parse(b || '{}');
        const numeros = (j.numbers || []).filter(n => String(n).replace(/\D/g, '').length >= 10).slice(0, 50);
        if (!numeros.length) { res.statusCode = 400; return res.end(JSON.stringify({ erro: 'mande {"numbers":["5511..."]}' })); }
        if (!EVO_URL || !EVO_KEY) { res.statusCode = 503; return res.end(JSON.stringify({ erro: 'Evolution não configurada no servidor (EVO_URL/EVO_KEY)' })); }
        const r = await checarWhatsApp(numeros);
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify(r));
      } catch (e) { res.statusCode = 500; res.end(JSON.stringify({ erro: String(e.message) })); }
    });
    return;
  }

  if (req.url === '/health') {
    res.setHeader('Content-Type', 'application/json');
    return res.end(JSON.stringify({ ok: true, evolution: !!(EVO_URL && EVO_KEY), instancia: EVO_INST }));
  }

  if (req.url === '/webhook/evolution' && req.method === 'POST') {
    let b = ''; req.on('data', c => b += c); req.on('end', async () => {
      try {
        const j = JSON.parse(b || '{}');
        const de = j?.data?.key?.remoteJid?.replace(/[^0-9]/g,'') || '';
        const msg = j?.data?.message?.conversation || j?.data?.message?.extendedTextMessage?.text || '';
        console.log('MSG de', de, ':', msg);
        // Auto-resposta simples: se cliente escreveu, responde boas-vindas + avança funil
        if (de && msg && !j?.data?.key?.fromMe) {
          await enviarTexto(EVO_URL, EVO_KEY, EVO_INST, de, BOAS_VINDAS);
          console.log('Auto-resposta enviada p/', de);
        }
        res.end('ok');
      } catch (e) { console.error(e); res.statusCode = 500; res.end('erro'); }
    });
    return;
  }
  res.end('rick-digital bridge on');
});

// Vigia 24h de leads do SITE (opcional, p/ rodar hospedado):
// POLL_SITE_LEADS=1 FIREBASE_URL=https://SEU-projeto-default-rtdb.firebaseio.com node evolution-bridge.js
// A cada 1 min lê /site-leads, manda boas-vindas a quem tem fone real e marca enviado:true.
// O CRM continua criando o lead no funil (sem duplicar o WhatsApp: ele respeita enviado:true).
const FB = (process.env.FIREBASE_URL || '').replace(/\/$/, '');
const vistosSite = new Set();
async function vigiarSite() {
  if (process.env.POLL_SITE_LEADS !== '1' || !FB) return;
  try {
    const j = await (await fetch(FB + '/site-leads.json')).json();
    if (!j) return;
    for (const k of Object.keys(j)) {
      if (vistosSite.has(k) || j[k].enviado) continue;
      vistosSite.add(k);
      const tel = String(j[k].zap || j[k].whatsapp || '').replace(/\D/g, '');
      if (tel.length >= 8) {
        try {
          await enviarTexto(process.env.EVO_URL, process.env.EVO_KEY, process.env.EVO_INST || 'rick-digital', tel, BOAS_VINDAS + ' (' + (j[k].nome || 'visitante') + ')');
          await fetch(FB + '/site-leads/' + k + '.json', { method: 'PATCH', body: JSON.stringify({ enviado: true }) });
          console.log('Site-lead atendido:', j[k].nome);
        } catch (e) { console.error('falha site-lead:', e.message); }
      }
    }
  } catch (e) { console.error('vigia site:', e.message); }
}
setInterval(vigiarSite, 60000);

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => console.log('Bridge no ar:' + PORT));
module.exports = { enviarTexto };
