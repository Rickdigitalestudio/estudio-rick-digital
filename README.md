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
- Filtros automáticos:
  - ✅ `website / contact:website / url` → descartado
  - ✅ Selo `🚫 SEM SITE` + link `checar se tem site`
- **Cidade/Bairro + País** (funciona no mundo todo)
- **🇧🇷 Modo brasileiros no exterior**: filtra por `cuisine=brazilian` + nome (brasil, churrasco, picanha, feijoada, açaí, coxinha…)
- Botões **Buscar / 🔄 Atualizar / + Funil / + Todos**
- Importação CSV (`nome,telefone,origem`) + links de captura p/ site, WhatsApp e TikTok

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
└── README.md
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
2. Busca categoria via Overpass (`amenity/shop/office/cuisine`)
3. Descarta tudo que tiver `website/contact:website/url`
4. Se modo BR ligado, mantém só `isBR()` (regex + cuisine)
5. Exibe 20 oportunidades com selo + prova + ação em 1 clique

> Limites gratuitos do OSM se aplicam. Se instável, use o botão `Abrir referência no Google Maps`.

## 🤝 Contribuindo

1. Fork → branch `feat/minha-ideia` → commit → PR. Mantenha arquivo único e sem dependências para continuar rodando offline.

## 📄 Licença

Proprietário — ESTÚDIO RICK DIGITAL / Rick Lima. Uso comercial autorizado apenas pelo titular.

---
Feito com 💙 por **Rick** — *sites que vendem de verdade.*
