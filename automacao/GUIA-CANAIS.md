# 🎯 Canais de contato — como ter lead REAL que dá pra falar

> Resposta curta: o problema nunca foi "faltar lead". Era **o sistema dizer que
> tinha WhatsApp quando não tinha**. Este guia explica o que foi corrigido e
> como ligar cada camada.

---

## 🔴 O que estava errado (medido na base real)

O motor de prospecção marcava **todo** número com 8+ dígitos como
`"fone_real": true`. A tela mostrava "fone real" e o botão abria um
`wa.me/...`. Mas a base tinha 152 leads:

| Tipo do número | Quantidade | WhatsApp funciona? |
|---|---|---|
| **Linha fixa** (10 dígitos, começa 2-5) | **120 (79%)** | ❌ **não tem WhatsApp** |
| Celular com 9 (11 dígitos) | 31 | ✅ provavelmente sim |
| Número inválido / DDD errado | 1 | ❌ |

Ou seja: **4 de cada 5 leads tinham um link de WhatsApp morto.** A mensagem
ia para o vazio. Pior: o CRM mandava "chama no WhatsApp" para um comércio que
só tinha telefone de balcão — e isso queima a abordagem na primeira vez.

O número também era salvo com bug: o código de país `55` era repetido
(`5551145534340`), o que quebrava o link.

---

## ✅ O que mudou

### 1. Classificação real do telefone (`automacao/canais.py`)

Todo número agora é classificado antes de virar lead:

| Tipo | Como identificar | Canal |
|---|---|---|
| `celular` | 11 dígitos, 3º = 9 | 📲 WhatsApp |
| `celular_antigo` | 10 dígitos, 3º = 6-9 | 📲 recupera o nº com o 9 |
| `fixo` | 10 dígitos, 3º = 2-5 | ☎️ **ligar** (não tem WhatsApp) |
| `invalido` | DDD inexistente / < 8 dígitos | descartado |

O `celular_antigo` é o achado fino: muitos negócios trocaram o telefone fixo
pelo celular e o número antigo (8 dígitos) ainda está no cadastro. Com o 9 na
frente (`5511968881234`) ele vira um celular válido — o sistema já faz isso e
marca `fone_recuperado: true`.

### 2. Descoberta por rede social (2ª passada do Overpass)

O motor agora varre o OSM **duas vezes**:

1. **por categoria** (bar, clínica, barbearia, oficina…) → acha quem tem telefone
2. **por presença em rede social** (`contact:instagram`, `contact:facebook`,
   `contact:tiktok`…) → acha quem tem **Instagram/Facebook mas o OSM não
   classificou o ofício**

Medido na região ABC: **634 negócios com rede social em 4 cidades**, 202 deles
com telefone **e** sem site. Boa parte nunca aparecia na busca por categoria.

### 3. Canal definido por lead

Cada lead nasce com um canal e a mensagem já vem no tom certo:

| Canal | Significado | Botão no CRM | Mensagem |
|---|---|---|---|
| `whatsapp` | nº **confirmado** na Evolution | 📲 WhatsApp | "chama no WhatsApp" |
| `whatsapp_provavel` | celular, ainda não checado | 📲 WhatsApp | "chama no WhatsApp" |
| `social` | **sem WhatsApp**, mas tem rede | 📸 Instagram / 📘 Facebook | "achei vocês no Instagram" |
| `ligacao` | só telefone fixo | ☎️ **Ligar** | roteiro de ligação |
| `sem_contato` | nada disso | — | descartado da base |

> **O link `wa.me` só aparece quando o número é capaz de receber mensagem.**
> Lead de linha fixa ganha botão **Ligar** e um roteiro pronto, não um link morto.

---

## 🔎 Como saber DE VERDADE se o número tem WhatsApp

Testei antes: `wa.me/5511...` e `api.whatsapp.com/send` devolvem **a mesma
página** para número válido, fixo ou inexistente. Não dá para checar assim.

A checagem real é a **Evolution API** (Baileys), que responde `exists: true/false`:

```
POST {EVO_URL}/chat/checkNumber/{instancia}
apikey: {EVO_KEY}
body:   {"numbers":["5511999999999", ...]}

-> [{"exists":true,"jid":"5511999999999@s.whatsapp.net","number":"5511999999999"}]
```

A versão v2 usa `/chat/whatsappNumbers/{instancia}` — o código tenta as duas.

### Como subir (grátis)

```bash
docker run -p 8080:8080 -e AUTHENTICATION_API_KEY=SUA_KEY evolution-api
```

1. `POST /instance/create` → `{"instanceName":"rick-digital"}`
2. Escaneie o QR **uma vez** no celular
3. Anote a URL e a Key

### Ativando no app (sem digitar nada)

O `automacao/evolution-bridge.js` já expõe a rota que o CRM usa:

```
POST https://SUA-PONTE/check-number
body: {"numbers":["5511...","5511..."]}
-> {"5511...":{"exists":true,"jid":"..."}}
```

No app: **Config → Controle Total WhatsApp** → preencha

- **URL da Evolution API** (ex: `https://sua-evo.up.railway.app`)
- **API Key**
- **Instância** (`rick-digital`)
- **URL da Ponte** (opcional — a mesma URL se você hospeda o `evolution-bridge.js`)

Depois clique em **🔎 Verificar WhatsApp**. O app confere a lista inteira,
reclassifica cada lead e avisa:

```
Verificados 77 numeros:
✅ 61 TEM WhatsApp
❌ 16 não tem WhatsApp
```

A partir daí o painel mostra **📲 zap confirmado** nos que têm, e os que não
têm caem sozinhos em "Só fixo" ou "Rede social".

### Pela linha de comando

```bash
cd automacao
python verificar_canais.py --evo        # só checa WhatsApp
python verificar_canais.py --evo --places --site
python verificar_canais.py --simular    # diagnóstico, não grava
```

Credenciais por variável de ambiente **ou** em `automacao/evo-config.json`
(veja `evo-config.example.json`):

```json
{
  "url": "https://sua-evo.up.railway.app",
  "key": "SUA_API_KEY",
  "inst": "rick-digital",
  "places": "SUA_GOOGLE_PLACES_KEY"
}
```

---

## 🌐 Google Places (opcional) — telefone real + rede social

Places traz o telefone **real** do cadastro do Google e o site oficial — que
para comércio pequeno costuma ser o **Instagram**, não um site.

```bash
export GOOGLE_PLACES_KEY=SUA_KEY
python verificar_canais.py --places
```

> Sem Places: tudo funciona, mas o telefone vem só do OSM (que às vezes é o
> fixo do balcão). Com Places, a taxa de acerto do WhatsApp sobe bastante.

---

## 🗺️ Other camadas (todas opcionais, todas grátis)

| Camada | O que faz | Precisa de |
|---|---|---|
| **Site do negócio** | lê o site e extrai Instagram/Facebook/WhatsApp do rodapé | nada |
| **OSM `contact:*`** | Instagram/Facebook/TikTok/YouTube/X já cadastrados | nada |
| **`contact:whatsapp`** | o proprio comercio publica um link de WhatsApp -> o lead entra na fila de checagem, mesmo com formato de fixo | nada |
| **Evolution** | confirma se o número tem WhatsApp | URL + Key |

---

## 📋 Como usar no dia a dia

1. **Painel Automação** (aba *Gerador de Leads*) → o robô já deixou a lista
2. **Filtro "Todos os canais"** → escolha `Celular · validar`, `Rede social` ou
   `Só fixo · ligar`
3. **🔎 Verificar WhatsApp** → confere tudo de uma vez (precisa da Evolution)
4. Abordagem:
   - 📲 **WhatsApp** → mensagem já personalizada, clique e envie
   - 📸 **Rede social** → abre o Instagram/Facebook + msg copiada
   - ☎️ **Só fixo** → botão **Ligar** + roteiro pronto
5. **+ Funil** → joga no CRM mantendo canal, redes e mensagem

---

## 🧪 Auditoria rápida da base

```bash
python automacao/canais.py
```

```
AUDITORIA DE 268 LEADS
  fixo             137
  celular          85
  invalido         1
  TOTAL whatsapp   85  <- unicos que PODEM ter WhatsApp
```

Se a linha "TOTAL whatsapp" for bem menor que o total, quase tudo é fixo e
a estratégia tem que ser **ligação + Instagram**, não disparo de WhatsApp.
