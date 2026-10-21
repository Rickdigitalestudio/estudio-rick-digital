#!/usr/bin/env python3
"""Upgrade do CRM: a lista de leads vira uma maquina de prospeccao.

Troca a aba "Automacao" (que so mostrava o nome) por um painel com:
  - filtro por cidade e categoria
  - busca
  - botao "Abrir WhatsApp" com a mensagem personalizada pronta
  - botao "Copiar mensagem"
  - link da landing page certa para o servico
  - contador de quantos ja foram_CONTATADOS (estado salvo no CRM)

Uso: python automacao/upgrade_crm_prospeccao.py
"""
from __future__ import annotations

import pathlib
import sys

BASE = pathlib.Path(r"C:\Users\Henrique Luiz\Documents\Default Project\estudio-rick-digital")
ARQ = BASE / "index.html"

NOVO = r"""
// ═══════════════ PROSPECCAO ATIVA (painel de abordagem) ═══════════════
let autoLeads=[], autoFiltroCidade='', autoFiltroCat='', autoBusca='', autoContatados={};

function renderAuto(){
  const box=document.getElementById('auto-result'); if(!box)return;
  const cid=autoFiltroCidade, cat=autoFiltroCat, q=autoBusca.toLowerCase();
  const lista=autoLeads.filter(a=>{
    if(cid && !(a.cidade||'').includes(cid)) return false;
    if(cat && a.categoria!==cat) return false;
    if(q && !((a.nome||'')+' '+(a.categoria||'')+' '+(a.endereco||'')).toLowerCase().includes(q)) return false;
    return true;
  });
  if(!lista.length){box.innerHTML='<p class="legend">Nenhum lead com esse filtro.</p>';return;}
  const cidades=[...new Set(autoLeads.map(a=>(a.cidade||'').split(',')[0].trim()))].sort();
  const cats=[...new Set(autoLeads.map(a=>a.categoria).filter(Boolean))].sort();
  box.innerHTML=
    '<div style="display:flex;gap:.4rem;flex-wrap:wrap;margin-bottom:.6rem">'+
      '<input id="auto-busca" placeholder="Buscar lead..." value="'+autoBusca.replace(/"/g,'&quot;')+'" style="flex:1;min-width:160px;padding:.4rem;border:1px solid #ddd;border-radius:8px" oninput="autoBusca=this.value;renderAuto()">'+
      '<select onchange="autoFiltroCidade=this.value;renderAuto()" style="padding:.4rem;border:1px solid #ddd;border-radius:8px">'+
        '<option value="">Todas as cidades</option>'+
        cidades.map(c=>'<option '+(cid===c?'selected':'')+'>'+c+'</option>').join('')+
      '</select>'+
      '<select onchange="autoFiltroCat=this.value;renderAuto()" style="padding:.4rem;border:1px solid #ddd;border-radius:8px">'+
        '<option value="">Todas as categorias</option>'+
        cats.map(c=>'<option '+(cat===c?'selected':'')+'>'+c+'</option>').join('')+
      '</select>'+
    '</div>'+
    '<div class="legend" style="margin-bottom:.4rem"><b>'+lista.length+'</b> leads prontos para abordagem ('+autoLeads.length+' no total)</div>'+
    lista.map(a=>{
      const k=(a.fone||a.nome);
      const feito=autoContatados[k];
      const link=a.wa_link||('https://wa.me/'+(a.fone||''));
      const lp=a.landing?'https://rickdigitalestudio.github.io/profissional-rickdutra/'+a.landing:'';
      return '<div style="padding:.5rem 0;border-bottom:1px solid #eee">'+
        '<b>'+a.nome+'</b> '+
        (a.fone?'<span class="tag" style="background:#D1FAE5">📞 '+a.fone+'</span>':'<span class="tag" style="background:#FEE2E2;color:#991B1B">sem fone</span>')+
        ' <span class="tag">'+((a.categoria||'').toUpperCase())+'</span>'+
        (feito?'<span class="tag" style="background:#DBEAFE;color:#1E40AF">✔ contatado</span>':'')+
        '<br><small>'+(a.endereco||'')+' · '+((a.cidade||'').split(',')[0])+' · '+
        '<a target=_blank rel=noopener href="https://www.google.com/search?q='+encodeURIComponent(a.nome+' '+((a.cidade||'').split(',')[0]))+'">checar no Google 🔍</a>'+
        (lp?' · <a target=_blank rel=noopener href="'+lp+'">ver exemplo de site ↗</a>':'')+'</small>'+
        '<div style="display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.35rem">'+
          '<a class="btn btn-wa" target=_blank rel=noopener href="'+link+'" onclick="marcarContatado(\''+k+'\')">📲 WhatsApp</a>'+
          '<button class="btn btn-v" onclick="copiarTexto(\''+(a.pitch||'').replace(/'/g,"\\'")+'\')">📋 Copiar pitch</button>'+
          '<button class="btn btn-v" onclick="addLeadAuto(\''+k+'\')">+ Funil</button>'+
        '</div>'+
      '</div>';
    }).join('')+
    '<div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.8rem">'+
      '<button class="btn-g" style="background:#059669" onclick="addAllAuto()">+ Jogar os '+lista.length+' no funil</button>'+
      '<button class="btn btn-v" onclick="copiarTodosPitches()">📋 Copiar todos os pitches</button>'+
    '</div>';
}
function marcarContatado(k){autoContatados[k]=new Date().toLocaleString('pt-BR');try{localStorage.setItem('autoContatados',JSON.stringify(autoContatados));}catch(e){}renderAuto();}
function copiarTodosPitches(){const l=autoLeads.filter(a=>a.pitch);copiarTexto(l.map(a=>'=== '+a.nome+' ('+a.categoria+') ===\n'+(a.wa_link||'')).join('\n\n'));}
function addLeadAuto(k){const a=autoLeads.find(x=>(x.fone||x.nome)===k);if(!a)return;DB.leads.unshift({id:Date.now(),nome:a.nome,tel:a.fone||'',origem:'Prospecção 🤖 '+((a.cidade||'').split(',')[0]),servico:a.categoria==='loja'?'Loja Virtual':'Site Institucional',valor:a.categoria==='loja'?2497:997,etapa:'novo',obs:(a.pitch||'')+' | '+(a.endereco||'')+' | varredura '+(a.varredura||''),data:new Date().toLocaleString('pt-BR')});save();acaoReal('Lead da prospecção','+ '+a.nome+' ('+a.categoria+')');}
"""

ALVO_ANTIGO = "async function carregarAutomacao(){try{const j=await(await fetch('automacao/leads-latest.json',{cache:'no-store'})).json();autoLeads=j.leads||[];"


def main() -> int:
    t = ARQ.read_text(encoding="utf-8")
    if "PROSPECCAO ATIVA" in t:
        print("ja upgraded")
        return 0

    # 1) remove a declaracao antiga de autoLeads
    t = t.replace("let autoLeads=[]; async function verificarAutomacao()",
                  "let autoLeads=[]; async function verificarAutomacao()")

    # 2) substitui o corpo do carregarAutomacao para usar o painel
    ini = t.find(ALVO_ANTIGO)
    if ini < 0:
        print("ERRO: nao achei carregarAutomacao")
        return 1
    fim = t.find("function addAllAuto()", ini)
    if fim < 0:
        print("ERRO: nao achei addAllAuto")
        return 1

    novo_carregar = (
        "async function carregarAutomacao(){try{const j=await(await fetch('automacao/leads-latest.json',{cache:'no-store'})).json();"
        "autoLeads=(j.leads||[]).filter(a=>a.fone);"
        "try{autoContatados=JSON.parse(localStorage.getItem('autoContatados')||'{}');}catch(e){autoContatados={};}"
        "if(!autoLeads.length){alert('Automação sem leads com telefone desta vez.');return;}"
        "renderAuto();"
        "notif('🤖 '+autoLeads.length+' leads prontos para abordagem','Varredura '+(j.varredura||''));"
        "}catch(e){alert('Não achei o arquivo da automação. Abra pelo link público (GitHub Pages) ou rode a busca manual.');}}"
    )
    t = t[:ini] + novo_carregar + t[fim:]

    # 3) addAllAuto passa a pegar so os que tem fone e usa a categoria
    t = t.replace(
        "function addAllAuto(){if(!autoLeads.length)return;let cf=0;autoLeads.forEach((a,i)=>{const ok=String(a.fone||'').replace(/\\D/g,'').length>=8||a.fone_real;",
        "function addAllAuto(){if(!autoLeads.length)return;let cf=0;autoLeads.filter(a=>a.fone).forEach((a,i)=>{const ok=true;")

    # 4) insere o painel novo antes de addAllAuto
    t = t.replace("function addAllAuto(){", NOVO + "\nfunction addAllAuto(){", 1)

    ARQ.write_text(t, encoding="utf-8")
    print("CRM atualizado com o painel de prospeccao ativa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
