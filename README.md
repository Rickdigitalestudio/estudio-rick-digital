# 🎨 ESTÚDIO RICK DIGITAL — CRM + Gerador de Leads + Fábrica de Banners

> Sistema completo para vender **Fanpages, Sites e Lojas Virtuais** com prospecção automática, funil de vendas, orçamento e equipe IA em plantão ao vivo.

[![PWA](https://img.shields.io/badge/PWA-Instalável-2563EB?logo=pwa)](./index.html)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Oficial-25D366?logo=whatsapp)](https://wa.me/qr/MOOILZTYKO2EI1)
[![TikTok](https://img.shields.io/badge/TikTok-@ricklima991-000?logo=tiktok)](https://www.tiktok.com/@ricklima991)
[![Portfólio](https://img.shields.io/badge/Portfólio-Ao_vivo-7C3AED)](https://rickdigitalestudio.github.io/profissional-rickdutra/)
[![Licença](https://img.shields.io/badge/Licença-Proprietária-orange)]()

## ✨ Demonstração

Abra `index.html` no navegador — **sem servidor, sem build, sem API key**. Funciona no PC e instala como app no celular (PWA).

| Desktop | Mobile (PWA) |
|---------|--------------|
| CRM + Kanban + Relatórios | Instalar via ⋮ → Adicionar à tela inicial |

## 🚀 Funcionalidades

### 📊 1. Dashboard + CRM
- Resumo: novos leads, clientes, quentes, conversão e valor total
- Alertas: leads quentes, sem resposta há 3+ dias, retornos de hoje
- Notificações internas + persistência em `localStorage`

### 📈 2. Funil de Vendas (arrastar e soltar)
`🆕 Novo → 🔍 Qualificação → 🔥 Quente → 🤝 Negociação → ✅ Cliente (+ ⚫ Arquivado)`
- Cards com origem, valor, WhatsApp direto com mensagem pré-preenchida
- Ficha completa: nome, telefone, e-mail, origem, interesse, valor, obs, histórico

### 🎣 3. Gerador de Leads — só SEM site
- **Google Maps + OSM/Overpass por categoria** (sem API key)
- **🔍 Busca dentro da ficha do lead**: digita o nome do comércio → o app traz
  **nome, telefone, endereço, segmento e se já tem site** (o alvo é quem **não**
  tem site). Usa o Google Places se houver chave em Config; sem chave, usa o
  OpenStreetMap (também sem chave) e avisa para conferir no Maps
- Filtros automáticos:
  - ✅ `website / contact:website / url` → descartado
  - ✅ Selo `🚫 SEM SITE` + link `checar se tem site`
- **2ª passada por rede social** (`contact:instagram/facebook/tiktok`) — acha
  comércio que o OSM não classificou por ofício
- **Canal definido por lead**: 📲 WhatsApp · 📸 Rede social · ☎️ Ligar
- **Telefone classificado de verdade**: celular (11 díg, 3º=9) · celular antigo
  (recupera o 9) · **linha fixa (não tem WhatsApp)** · inválido
- **🔎 Verificar WhatsApp** — confirma na Evolution se o número existe;
  linha fixa vira "Ligar", celular sem zap vira "Rede social"
- **Cidade/Bairro + País** (funciona no mundo todo)
  - 🌍 **País: só selecionar** — `<select>` com **177 países** (apenas nomes,
    sem digitação); a bandeira do país escolhido aparece ao lado do campo
  - 📍 **Cidade / Bairro: um select só, com as cidades de TODOS os países**
    (agrupadas por país, ~8 mil cidades) — a primeira opção (padrão) é
    **“🏙️ Todas as cidades”**; escolhendo uma cidade, a busca usa o país
    **dela** automaticamente
  - Ordem do formulário: **País → Cidade / Bairro → Categoria**
- 🗺️ **Mapa interativo + prévia do local** (Leaflet + OSM, sem chave e
  **sem CDN — os arquivos do Leaflet ficam no próprio projeto** em
  `vendor/leaflet/`, então o mapa não quebra se o CDN estiver bloqueado)
  - **Clique em qualquer ponto**: mostra a **prévia** (endereço) e os comércios
    da categoria **por perto** em 1,5 km — clique no deles para escolher
  - Cada resultado/marcador tem botão **📍 Prévia**
  - A prévia já vem com **nome da empresa** (auto) + **“O que ela precisa”** e
    monta a **mensagem automática** — troque a necessidade e a mensagem muda
  - Botões: **💬 Mandar mensagem automática** (wa.me ou Evolution API) ·
    📋 Copiar · **+ Adicionar ao funil** (ficha já preenchida)
  - Sem telefone no cadastro: copia a mensagem e avisa para completar o número
  - 🔎 **Busca de local (integração OSM · Nominatim)** — digite endereço,
    bairro ou cidade, **ou cole um link do Google Maps/OpenStreetMap**: o mapa
    voa até lá e abre a prévia com a mensagem pronta (até 5 resultados em
    botões para escolher)
  - 📍 **Gerar link do ponto**: botões **Link OSM** e **Link Google** na prévia
- **🇧🇷 Modo brasileiros no exterior**: filtra por `cuisine=brazilian` + nome (brasil, churrasco, picanha, feijoada, açaí, coxinha…)
- Botões **Buscar / 🔄 Atualizar / + Funil / + Todos**
- Importação CSV (`nome,telefone,origem`) + links de captura p/ site, WhatsApp e TikTok

> 📖 **Guia completo dos canais:** [`automacao/GUIA-CANAIS.md`](automacao/GUIA-CANAIS.md)
> — a medição do problema (79% dos leads eram linha fixa), como ativar a
> checagem real de WhatsApp, Google Places e leitura de site.

### 🎨 4. Fábrica de Banners
- Canvas 1080×1080, 3 modelos (Azul Pro / Roxo TikTok / Verde WhatsApp)
- Logo RD + CTA + link portfólio, download PNG, legenda pronta p/ postar

### 💡 5. Ideias de Posts
- Gerador focado em vender fanpage/site/loja usando o portfólio como prova
- Copiar + enviar WhatsApp + abrir TikTok em 1 clique

### 💰 6. Orçamento do Portfólio (a partir de)
| Serviço | Preço |
|---------|-------|
| Fanpage Profissional | a partir de **R$ 497** |
| Site Institucional | a partir de **R$ 997** |
| Landing Page | a partir de **R$ 697** |
| Loja Virtual | a partir de **R$ 2.497** |
| Manutenção Mensal | a partir de **R$ 297** |

**Extras (a partir de):** Domínio+Hospedagem +480 · Logo +200 · WhatsApp auto +300 · TikTok/vídeos +400 · Maps+SEO +350
- Gera proposta em texto + envio direto p/ WhatsApp

### 📁 Projetos (aba Projetos)
- Escolha o **lead do funil** e o projeto nasce preenchido (serviço + valor)
- **📁 Criar projeto atualiza tudo**: move o lead para ✅ Cliente, cria a tarefa
  de entrega, recalcula **funil, financeiro, dashboard e relatórios** e avisa o
  cliente no WhatsApp (se o envio automático estiver ligado)
- Regra de pagamento: 50% na entrada, 100% na conclusão (o progresso move o dinheiro)

### 🤖 10. Varredura noturna com a ficha já preenchida
A varredura automática (GitHub Actions, 1x/dia) entrega cada lead **no formato
da ficha do app**:

| Campo | Origem |
|---|---|
| `tel` | telefone em **E.164** (55 + DDD + número) — o wa.me nasce certo |
| `segmento` | ofício em português ("Restaurante / Lanchonete", "Padaria / Confeitaria"…) |
| `empresa` | nome do comércio |
| `origem` | "Google Maps" |
| `statusSite` | `sem_presenca` / `so_redes` / `tem_site` (achado no Google Places) |
| `obs` | endereço + bairro + cidade + "SEM SITE no cadastro — é o alvo" + fonte |
| `servico` / `valor` / `etapa` / `prob` / `tags` | já no padrão do app |

Ao clicar em **"+ Jogar os N no funil"**, o lead entra **completo**: nome,
WhatsApp, segmento, obs, etiquetas e o selo **✅ sem site** no card. Sem
digitar nada.

Reformatar a base a qualquer momento: `python automacao/migrar_ficha.py`.

### ⏰ 7. Tarefas · 📋 8. Relatórios
- Lembretes 24h automáticos, conclusão, origem principal, conversão, export CSV + impressão PDF

### 🤖 9. Equipe IA — 15 funcionários + 🔴 Plantão AO VIVO
**9 mulheres · 6 homens**, cada um com função (banners, copy, TikTok, WhatsApp, Maps, closer, dev, vídeo, relatórios…).
- `▶️ Ligar plantão`: a cada **4s** um funcionário age **de verdade** no funil (capta, qualifica, gera banner, cria tarefa) e a conversão recalcula
- A cada **25s** registra prova em `⚙️ Ações reais executadas`
- **Ordem do CEO**: `relatório` · `encher a fila` · `banner` · `cobrar leads`

## 🗂️ Estrutura

```
estudio-rick-digital/
├── index.html      # App completo (CRM + Leads + Banners + Equipe)
├── manifest.json   # PWA instalável
├── sw.js           # Service Worker (offline)
├── icon.svg        # Logo RD
├── README.md
└── automacao/
    ├── canais.py            # classifica telefone BR + detecta redes
    ├── prospectar.py        # varredura OSM (categoria + rede social)
    ├── verificar_canais.py  # checa WhatsApp na Evolution + Places + site
    ├── evolution-bridge.js  # ponte (envio + /check-number)
    ├── alvos.json           # cidades-alvo
    ├── leads-latest.json    # base (gerada pelo robô)
    └── GUIA-CANAIS.md       # 📖 como ativar cada camada
```

## ▶️ Como rodar

### Opção 1 — só abrir (mais rápido)
1. Baixe/clone este repositório
2. Abra `estudio-rick-digital/index.html` no Chrome/Edge
3. Use. Os dados ficam salvos no navegador.

### Opção 2 — GitHub Pages (link público)
1. Suba para o GitHub (ver abaixo)
2. Settings → Pages → Deploy from branch → `main` → `/root` ou `/estudio-rick-digital`
3. Acesse `https://SEU-USUARIO.github.io/SEU-REPO/`

### Opção 3 — celular como app
Android/iOS → abra o link → ⋮ → **Instalar app / Adicionar à tela inicial**.

### 🔄 Atualizar o app (PC e celular)

| Onde | Como |
|------|------|
| 📱 Celular (PWA) | Botão **🔄 Atualizar** no topo — limpa o cache e recarrega. Sem reinstalar. |
| 💻 PC (programa) | 2x em **`Atualizar-CRM.bat`** (git pull + limpa cache + reabre). |
| ⚙️ Config | Aba **Config → 🔄 Atualização do app**: versão local, versão do servidor, "Verificar agora" e "Atualizar agora". |

O app confere o servidor sozinho (ao abrir, ao voltar do segundo plano, quando
a internet volta e a cada 10 min). Se houver versão nova, o botão do topo fica
**laranja pulsando** e aparece o aviso "🚀 Versão nova disponível".

Detalhes: [`LINK-CELULAR.txt`](LINK-CELULAR.txt).

**Ao publicar uma mudança:** rode `python automacao/bump_build.py` (sobe o
`BUILD` do `index.html`, o `versao.json` e o cache do service worker) e depois
`git push` — o GitHub Pages publica e o celular recebe.


## ⬆️ Subir para o GitHub

```bash
cd estudio-rick-digital
git init
git add .
git commit -m "feat: ESTÚDIO RICK DIGITAL — CRM + Leads SEM site + Banners + Equipe IA"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/SEU-REPO.git
git push -u origin main
```

Ou com GitHub CLI:

```bash
gh repo create SEU-REPO --public --source=. --push
```

## 🔗 Integrações oficiais

- 💬 WhatsApp: https://wa.me/qr/MOOILZTYKO2EI1
- 🎵 TikTok: https://www.tiktok.com/@ricklima991
- 🌐 Portfólio: https://rickdigitalestudio.github.io/profissional-rickdutra/

Mensagens diretas usam `wa.me/55+DDD+numero` com texto pré-preenchido por lead/serviço.

## 🗺️ Como funciona a prospecção SEM site?

1. Geocodifica `Cidade + País` via Nominatim (OSM)
2. **Passada 1** — busca por categoria via Overpass (`amenity/shop/office/cuisine`)
3. **Passada 2** — busca por presença em rede social (`contact:instagram/facebook/tiktok`)
4. Descarta tudo que tiver `website/contact:website/url`
5. **Classifica o telefone**: celular (WhatsApp) · celular antigo (recupera o 9)
   · **linha fixa (só ligação)** · inválido (DDD inexistente)
6. **Define o canal** de cada lead e monta a mensagem no tom certo
   (WhatsApp / direct na rede / roteiro de ligação)
7. Se modo BR ligado, mantém só `isBR()` (regex + cuisine)
8. Exibe as oportunidades com selo de canal + prova + ação em 1 clique
9. **Mapa da região**: clique em qualquer ponto → prévia do local (Nominatim
   reverse) + comércios da categoria por perto (Overpass) → escolha da empresa
   e do que ela precisa → **mensagem automática pronta** p/ WhatsApp

> 📖 Detalhes e ativação da checagem real de WhatsApp: [`automacao/GUIA-CANAIS.md`](automacao/GUIA-CANAIS.md)

> Limites gratuitos do OSM se aplicam. Se instável, use o botão `Abrir referência no Google Maps`.

> 🗺️ O mapa interativo usa **Leaflet** (dentro do projeto, em `vendor/leaflet/`).
> Os tiles têm **3 provedores com troca automática**: OpenStreetMap → CARTO →
> Esri — se um negar o carregamento (**"Access Blocked"/403**), o mapa sozinho
> passa p/ o próximo. Se todos falharem, cai no embed do Google Maps.

## 🤝 Contribuindo

1. Fork → branch `feat/minha-ideia` → commit → PR. Mantenha arquivo único e sem dependências para continuar rodando offline.

## 📄 Licença

Proprietário — ESTÚDIO RICK DIGITAL / Rick Lima. Uso comercial autorizado apenas pelo titular.

---
Feito com 💙 por **Rick** — *sites que vendem de verdade.*
