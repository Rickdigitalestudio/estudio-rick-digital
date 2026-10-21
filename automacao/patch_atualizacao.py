#!/usr/bin/env python3
"""Aplica o patch de atualizacao no CRM (PC via file:// e celular via PWA).

1) buscarJSON(): tenta o caminho local e cai para a URL publica do GitHub.
   Sem isso, no app do PC (file://) o fetch do JSON e bloqueado pelo CORS
   e a aba de prospeccao nao carrega lead nenhum.
2) Botao "Atualizar" que limpa cache + desregistra o service worker e recarrega.
   No celular (PWA) e o que traz a versao nova na hora.
3) Selo de versao, para saber se o app esta atualizado.
"""
from __future__ import annotations

import pathlib
import sys

ARQ = pathlib.Path(r"C:\Users\Henrique Luiz\Documents\Default Project\estudio-rick-digital\index.html")
BUILD = "2026.10.21-1"
ABS = "https://rickdigitalestudio.github.io/estudio-rick-digital"


def main() -> int:
    t = ARQ.read_text(encoding="utf-8")
    if "atualizarApp" in t:
        print("ja aplicado")
        return 0

    # ---------- 1) helpers ----------
    helper = f"""
// ════ ATUALIZACAO / BUILD ════
const BUILD='{BUILD}';
const ABS_BASE='{ABS}';
// No app do PC a pagina abre como file:// e o Chrome bloqueia fetch local
// (CORS). Entao tentamos o caminho relativo primeiro e caimos na URL publica.
async function buscarJSON(caminho){{
  const urls=[caminho, ABS_BASE+'/'+caminho.replace(/^\\//,'')];
  let ultimoErro=null;
  for(const u of urls){{
    try{{
      const r=await fetch(u,{{cache:'no-store'}});
      if(!r.ok) throw new Error('HTTP '+r.status);
      return await r.json();
    }}catch(e){{ ultimoErro=e; }}
  }}
  throw ultimoErro||new Error('sem resposta');
}}
async function atualizarApp(){{
  const b=document.getElementById('btn-atualizar');
  if(b){{b.textContent='⏳ Atualizando...';b.disabled=true;}}
  try{{
    if(navigator.serviceWorker){{
      const regs=await navigator.serviceWorker.getRegistrations();
      for(const r of regs) await r.unregister();
    }}
  }}catch(e){{}}
  try{{ if(window.caches){{ const ks=await caches.keys(); for(const k of ks) await caches.delete(k); }} }}catch(e){{}}
  try{{ localStorage.setItem('build',BUILD); }}catch(e){{}}
  const u=new URL(location.href);
  u.searchParams.set('_upd',Date.now());
  location.replace(u.toString());
}}
async function checarAtualizacao(){{
  try{{
    const el=document.getElementById('build-tag');
    const salvo=localStorage.getItem('build')||'';
    if(el) el.textContent=salvo===BUILD?BUILD:salvo+' → '+BUILD;
  }}catch(e){{}}
}}
"""

    # insere o helper antes da primeira funcao do app
    marca = "let DB={leads:[],tarefas:[]"
    i = t.find(marca)
    if i < 0:
        print("ERRO: nao achei o ponto de insercao")
        return 1
    t = t[:i] + helper + "\n" + t[i:]

    # ---------- 2) fetch com fallback ----------
    t = t.replace(
        "await fetch('automacao/leads-latest.json',{cache:'no-store'})",
        "await buscarJSON('automacao/leads-latest.json')")
    t = t.replace(
        "await(await fetch('automacao/leads-latest.json',{cache:'no-store'})).json()",
        "await buscarJSON('automacao/leads-latest.json')")

    # ---------- 3) botao + selo de versao no header ----------
    antigo = '<div class="sino" onclick="toggleNot()">'
    novo = ('<button class="hbtn at" id="btn-atualizar" onclick="atualizarApp()" '
            'title="Atualizar o app (PC e celular)">🔄 Atualizar</button>\n'
            '<span class="build-tag" id="build-tag"></span>\n'
            + antigo)
    if antigo not in t:
        print("ERRO: nao achei o sino do header")
        return 1
    t = t.replace(antigo, novo, 1)

    # ---------- 4) css do botao ----------
    css_antigo = ".sino{"
    css_novo = (".hbtn.at{background:linear-gradient(135deg,#0F766E,#059669);color:#fff}"
                ".hbtn.at:hover{filter:brightness(1.12)}"
                ".build-tag{font-size:.6rem;opacity:.55;letter-spacing:.04em;align-self:center;padding:0 .2rem}"
                ".sino{")
    if css_antigo not in t:
        print("ERRO: nao achei o css do sino")
        return 1
    t = t.replace(css_antigo, css_novo, 1)

    # ---------- 5) checa a versao ao abrir ----------
    t = t.replace("function salvarCfg(){", "checarAtualizacao();\nfunction salvarCfg(){", 1)

    ARQ.write_text(t, encoding="utf-8")
    print(f"patch aplicado (build {BUILD})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
