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

const http = require('http');
const BOAS_VINDAS = process.env.BOAS_VINDAS || 'Olá! Aqui é do ESTÚDIO RICK DIGITAL. Portfólio: https://studiorickdigital.github.io/ — quer proposta?';

async function enviarTexto(evoUrl, apiKey, instancia, numero, texto) {
  const r = await fetch(`${evoUrl}/message/sendText/${instancia}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: apiKey },
    body: JSON.stringify({ number: numero.replace(/\D/g,''), text: texto })
  });
  if (!r.ok) throw new Error('Evo ' + r.status);
  return r.json();
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/webhook/evolution' && req.method === 'POST') {
    let b = ''; req.on('data', c => b += c); req.on('end', async () => {
      try {
        const j = JSON.parse(b || '{}');
        const de = j?.data?.key?.remoteJid?.replace(/[^0-9]/g,'') || '';
        const msg = j?.data?.message?.conversation || j?.data?.message?.extendedTextMessage?.text || '';
        console.log('MSG de', de, ':', msg);
        // Auto-resposta simples: se cliente escreveu, responde boas-vindas + avança funil
        if (de && msg && !j?.data?.key?.fromMe) {
          await enviarTexto(process.env.EVO_URL, process.env.EVO_KEY, process.env.EVO_INST || 'rick-digital', de, BOAS_VINDAS);
          console.log('Auto-resposta enviada p/', de);
        }
        res.end('ok');
      } catch (e) { console.error(e); res.statusCode = 500; res.end('erro'); }
    });
    return;
  }
  res.end('rick-digital bridge on');
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => console.log('Bridge no ar:' + PORT));
module.exports = { enviarTexto };
