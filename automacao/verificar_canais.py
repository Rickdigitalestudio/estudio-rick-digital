"""Verificador de canais: confirma WhatsApp, acha o site e mapeia as redes.

O motor de prospeccao (prospectar.py) traz o telefone e as redes que estao
cadastrados no OSM. Mas cadastro nao e contato:

  - o telefone cadastrado muitas vezes e LINHA FIXA (nao tem WhatsApp)
  - o OSM raramente traz a rede social junto do telefone
  - nao da para saber se o celular tem WhatsApp sem CHECAR

Este modulo faz a checagem em 3 camadas. Cada uma e opcional e roda So se
tiver credencial:

  1. SITE      (gratis)  le o site do negocio e extrai Instagram/Facebook/
                         WhatsApp dos links do rodape
  2. PLACES    (opcional) Google Places: telefone real + site oficial
               precisa GOOGLE_PLACES_KEY
  3. EVOLUTION (opcional) checa se o numero tem WhatsApp de verdade
               precisa EVO_URL + EVO_KEY (+ EVO_INST)

Sem nenhuma credencial o script ainda roda e devolve o diagnostico: quantos
leads tem celular, quantos so tem fixo e quantos tem rede social. Com a
Evolution ele responde a pergunta que importa: "esse numero tem zap?".

Uso:
    python automacao/verificar_canais.py                # toda a base
    python automacao/verificar_canais.py --limite 30    # so os 30 primeiros
    python automacao/verificar_canais.py --so-wpp       # so checa WhatsApp
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canais import (REDES, T_CELULAR, T_ANTIGO, T_FIXO, T_INVALIDO,
                    escolhe_canal, ordem_redes, parse_br, site_de)

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "EstudioRickDigital-Verificador/2.0 "
                    "(contato: rickdigitalestudio.github.io/profissional-rickdutra)",
      "Accept-Language": "pt-BR,pt;q=0.9"}
CACHE_ARQ = os.path.join(BASE, "canais-cache.json")
LEADS_ARQ = os.path.join(BASE, "leads-latest.json")

# host -> chave de rede (para descobrir a rede pelo link do site)
HOST_REDES = {
    "instagram.com": "instagram", "instagr.am": "instagram",
    "facebook.com": "facebook", "fb.com": "facebook", "fb.me": "facebook",
    "tiktok.com": "tiktok",
    "twitter.com": "twitter", "x.com": "twitter",
    "youtube.com": "youtube", "youtu.be": "youtube",
    "linkedin.com": "linkedin",
    "wa.me": "whatsapp", "api.whatsapp.com": "whatsapp",
    "web.whatsapp.com": "whatsapp",
    "t.me": "telegram", "telegram.me": "telegram",
    "linktr.ee": "linktree", "beacons.ai": "linktree", "bio.link": "linktree",
    "business.site": "site", "sites.google.com": "site",
    "maps.app.goo.gl": "maps", "g.page": "maps",
}


# ---------------------------------------------------------------- utilidades
def agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def get(url, timeout=25, headers=None):
    req = urllib.request.Request(url, headers=headers or UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def carrega_cache() -> dict:
    try:
        with open(CACHE_ARQ, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salva_cache(cache: dict):
    with open(CACHE_ARQ, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


def host_de(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


# ------------------------------------------------- camada 1: site do negocio
RE_LINK = re.compile(r'href=["\']([^"\']+)["\']', re.I)
RE_ABS = re.compile(r'https?://[^\s"\'<>\\)]+', re.I)


def redes_do_site(url: str) -> dict:
    """Le o site do negocio e extrai as redes + WhatsApp dos links.

    Foo esta no rodape de quase todo site de comercio local. E a forma
    mais barata de descobrir o Instagram/Facebook/WhatsApp de quem tem
    site - e de montar o pitch de upgrade em vez de "voce nao tem site".
    """
    if not url:
        return {"redes": {}, "whatsapp": []}
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html = get(url, timeout=20)
    except Exception:
        return {"redes": {}, "whatsapp": []}

    links = set(RE_LINK.findall(html)) | set(RE_ABS.findall(html))
    redes, waps = {}, []
    for link in links:
        link = link.strip().strip('"\'')
        if link.startswith("//"):
            link = "https:" + link
        if not link.startswith("http"):
            continue
        h = host_de(link)
        if not h:
            continue
        if h in HOST_REDES:
            chave = HOST_REDES[h]
            if chave in ("site", "maps"):
                continue
            if chave == "whatsapp":
                d = re.sub(r"\D", "", link)
                if len(d) >= 10:
                    waps.append(d[-13:] if len(d) > 13 else d)
                continue
            if chave not in redes:
                redes[chave] = link.split("?")[0].rstrip("/")
    return {"redes": redes, "whatsapp": list(dict.fromkeys(waps))}


# ------------------------------------------------- camada 2: Google Places
def places_buscar(nome: str, endereco: str, chave: str) -> dict:
    """Text Search do Google Places (API nova, v1).

    Traz o telefone REAL do cadastro do Google e o site oficial - que
    costuma ser a rede social (instagram.com/loja) e nao um site.
    """
    if not chave:
        return {}
    consulta = (nome + " " + (endereco or "")).strip()
    url = ("https://places.googleapis.com/v1/places:searchText?key=" +
           urllib.parse.quote(chave))
    corpo = {"textQuery": consulta, "languageCode": "pt-BR",
             "maxResultCount": 3}
    try:
        req = urllib.request.Request(
            url, data=json.dumps(corpo).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", "X-Goog-FieldMask":
                     "places.id,places.displayName,places.formattedAddress,"
                     "places.nationalPhoneNumber,places.internationalPhoneNumber,"
                     "places.websiteUri,places.googleMapsUri,places.primaryType"})
        with urllib.request.urlopen(req, timeout=25) as r:
            j = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"erro": str(e)[:120]}

    lugares = j.get("places") or []
    if not lugares:
        return {}
    p = lugares[0]
    site = p.get("websiteUri") or ""
    return {
        "id": p.get("id", "").rsplit("/", 1)[-1],
        "nome": (p.get("displayName") or {}).get("text", ""),
        "endereco": p.get("formattedAddress", ""),
        "site": site,
        "maps": p.get("googleMapsUri", ""),
        "fone": p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber") or "",
        "rede_do_site": HOST_REDES.get(host_de(site), "") if site else "",
        "tipo": p.get("primaryType", ""),
    }


# ------------------------------------------- camada 3: Evolution (WhatsApp)
def evo_check(numeros: list, url: str, key: str, inst: str) -> dict:
    """Checa se os numeros tem WhatsApp. -> {numero: {'exists':bool,'jid':str}}

    Suporta as duas rotas da Evolution (a /chat/checkNumber das versoes
    novas e a /chat/whatsappNumbers da v2).
    """
    if not (url and key and numeros):
        return {}
    cab = {"Content-Type": "application/json", "apikey": key}
    corpo = json.dumps({"numbers": [str(n) for n in numeros]}).encode("utf-8")
    ultimo_erro = ""
    for rota in ("/chat/checkNumber/", "/chat/whatsappNumbers/"):
        try:
            req = urllib.request.Request(url.rstrip("/") + rota +
                                        urllib.parse.quote(inst),
                                        data=corpo, method="POST", headers=cab)
            with urllib.request.urlopen(req, timeout=45) as r:
                j = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            ultimo_erro = str(e)[:140]
            continue

        itens = j.get("result") if isinstance(j, dict) else j
        if isinstance(j, dict) and j.get("status") == "error":
            ultimo_erro = str(j.get("response") or j)[:140]
            continue
        if not isinstance(itens, list):
            ultimo_erro = ("resposta inesperada: " + str(j)[:140])
            continue
        saida = {}
        for it in itens:
            if not isinstance(it, dict):
                continue
            num = re.sub(r"\D", "", str(it.get("number") or ""))
            if not num:
                continue
            saida[num] = {"exists": bool(it.get("exists")),
                          "jid": it.get("jid") or ""}
        if saida:
            return saida
        ultimo_erro = "resposta sem itens: " + str(j)[:140]
    if ultimo_erro:
        print("  ! Evolution: " + ultimo_erro)
    return {}


# -----------------------------------------------------------------.pipeline
def enriquece(lead: dict, cfg: dict, cache: dict, so_wpp: bool) -> dict:
    """Enriquece um lead: site -> places -> whatsapp. Devolve o lead pronto."""
    nome = lead.get("nome") or ""
    fone_atual = lead.get("fone") or ""
    redes = dict(lead.get("redes") or {})
    wa_verif = lead.get("wa_verificado")
    origem_ver = lead.get("verificacao") or ""

    # ---- 1. Google Places (opcional) ---------------------------------
    if cfg.get("places") and not so_wpp:
        chave = "places:%s|%s" % (nome.lower(), (lead.get("endereco") or "").lower())
        if chave not in cache:
            try:
                cache[chave] = places_buscar(nome, lead.get("endereco") or "",
                                             cfg.get("places"))
            except Exception as e:
                cache[chave] = {"erro": str(e)[:120]}
            time.sleep(0.4)
        p = cache.get(chave) or {}
        if p and not p.get("erro"):
            lead["places"] = {k: v for k, v in p.items() if k != "erro"}
            if p.get("site") and not site:
                site = p["site"]
                lead["site"] = site
                if p.get("rede_do_site") and p["rede_do_site"] != "site":
                    redes.setdefault(p["rede_do_site"], p["site"])
            if p.get("fone"):
                info = parse_br(p["fone"])
                if info["tipo"] in (T_CELULAR, T_ANTIGO) and not fone_atual:
                    fone_atual = info["e164"]
                    lead["fone"] = fone_atual
                    lead["fone_origem"] = "Google Places"
                elif info["tipo"] == T_FIXO and not lead.get("fone_fixo"):
                    lead["fone_fixo"] = info["e164"]

    # ---- 2. site do negocio (gratis) ---------------------------------
    site = lead.get("site") or ""
    if not site and cfg.get("usar_site") and lead.get("status_site") == "tem_site":
        site = ""  # status_site ja garante; o site vem do cadastro
    if site and cfg.get("usar_site"):
        chave = "site:" + site
        if chave not in cache:
            cache[chave] = redes_do_site(site)
        achado = cache[chave]
        for k, v in (achado.get("redes") or {}).items():
            redes.setdefault(k, v)
        if achado.get("whatsapp") and not fone_atual:
            fone_atual = achado["whatsapp"][0]
            lead["fone"] = fone_atual

    # ---- 3. checagem de WhatsApp (Evolution) -------------------------
    info = parse_br(lead.get("fone") or lead.get("fone_bruto"))
    alvo = ""
    if info["tipo"] in (T_CELULAR, T_ANTIGO):
        alvo = info.get("e164_celular") or info["e164"]
    elif lead.get("tag_whatsapp"):
        # o proprio negocio cadastrou o link de WhatsApp: o numero entra
        # na fila de checagem mesmo que o formato pareca linha fixa.
        d = re.sub(r"\D", "", str(lead.get("fone") or lead.get("tag_whatsapp")))
        if len(d) >= 10:
            alvo = d
            info = dict(info, tipo=T_CELULAR, pode_whatsapp=True)
    if alvo and cfg.get("evo"):
        ck = "wa:" + alvo
        if ck not in cache:
            r = evo_check([alvo], cfg["evo_url"], cfg["evo_key"], cfg["evo_inst"])
            cache[ck] = r.get(re.sub(r"\D", "", alvo), {"exists": False})
            time.sleep(0.3)
        res = cache.get(ck) or {}
        wa_verif = bool(res.get("exists"))
        if wa_verif:
            lead["wa_jid"] = res.get("jid") or ""
            origem_ver = "Evolution checkNumber"
            if info["tipo"] == T_ANTIGO:
                # o celular antigo virou celular: o 9 e o numero atual
                lead["fone"] = alvo
                lead["fone_recuperado"] = True
                origem_ver += " (celular antigo recuperado com o 9)"
    elif alvo:
        wa_verif = None  # nao deu para checar (sem credencial)

    # ---- fecha o canal ------------------------------------------------
    canal = escolhe_canal(info, redes, wa_verif,
                          tag_wa=bool(lead.get("tag_whatsapp")))
    lead["redes"] = redes
    lead["wa_verificado"] = wa_verif
    lead["canal"] = canal["canal"]
    lead["canal_rotulo"] = canal["rotulo"]
    lead["confianca"] = canal["confianca"]
    lead["alternativas"] = canal["alternativas"]
    lead["fone_real"] = canal["canal"] in ("whatsapp", "whatsapp_provavel")
    lead["tipo_fone"] = info["tipo"]
    lead["motivo_fone"] = info.get("motivo", "")
    if origem_ver:
        lead["verificacao"] = origem_ver
    lead["verificado_em"] = agora()
    lead["msg"] = monta_msg(lead, canal["canal"], redes)
    if canal["canal"] in ("whatsapp", "whatsapp_provavel"):
        lead["wa_link"] = ("https://wa.me/%s?text=%s" %
                           (lead.get("fone", ""), urllib.parse.quote(lead["msg"])))
    else:
        lead["wa_link"] = ""
    return lead


def monta_msg(lead: dict, canal: str, redes: dict) -> str:
    """Mensagem coerente com o canal REAL do lead."""
    nome = lead.get("nome") or ""
    pitch = lead.get("pitch") or ""
    site = "https://rickdigitalestudio.github.io/profissional-rickdutra/"
    landing = lead.get("landing") or ""
    portfolio = site + landing
    if canal in ("whatsapp", "whatsapp_provavel"):
        return ("Ola! Vi que a {nome} ainda nao tem site. {pitch} "
                "Posso montar em 10 dias, a partir de R$ 997. "
                "Meu trabalho: {pf}").format(nome=nome, pitch=pitch, pf=portfolio)
    if canal == "social" and redes:
        chave = ordem_redes(redes)[0]
        rotulo = REDES.get(chave, (chave, ""))[0]
        return ("Ola! Vi que a {nome} ainda nao tem site. {pitch} "
                "Posso montar em 10 dias, a partir de R$ 997. "
                "Achei voces no {rotulo} e preferi mandar por aqui: {url}. "
                "Meu trabalho: {pf}").format(nome=nome, pitch=pitch, rotulo=rotulo,
                                             url=redes[chave], pf=portfolio)
    if canal == "ligacao":
        return ("Script de ligacao - {nome}: 'Ola, aqui e do Estudio Rick "
                "Digital. Vi que voces ainda nao tem site, e a {nome} aparece "
                "no Google quando alguem procura esse servico na regiao. "
                "Eu monto site em 10 dias a partir de R$ 997. Quer que eu "
                "mande o exemplo por e-mail ou WhatsApp?'").format(nome=nome)
    return ("Ola! Vi que a {nome} ainda nao tem site. {pitch} "
            "Meu trabalho: {pf}").format(nome=nome, pitch=pitch, pf=portfolio)


# ---------------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0, help="verifica so N leads")
    ap.add_argument("--so-wpp", action="store_true", help="so checa WhatsApp")
    ap.add_argument("--site", action="store_true", help="le o site do negocio")
    ap.add_argument("--places", action="store_true", help="usa Google Places")
    ap.add_argument("--evo", action="store_true", help="usa Evolution API")
    ap.add_argument("--simular", action="store_true",
                    help="mostra o que seria feito, sem gravar")
    args = ap.parse_args()

    # credenciais: variavel de ambiente > automacao/evo-config.json
    evo_url = os.environ.get("EVO_URL", "")
    evo_key = os.environ.get("EVO_KEY", "")
    evo_inst = os.environ.get("EVO_INST", "rick-digital")
    places_key = os.environ.get("GOOGLE_PLACES_KEY", "")
    try:
        with open(os.path.join(BASE, "evo-config.json"), encoding="utf-8") as f:
            ec = json.load(f)
        evo_url = evo_url or ec.get("url", "")
        evo_key = evo_key or ec.get("key", "")
        evo_inst = ec.get("inst", evo_inst)
        places_key = places_key or ec.get("places", "")
    except Exception:
        pass

    cfg = {
        "evo": bool(args.evo and evo_url and evo_key),
        "evo_url": evo_url, "evo_key": evo_key, "evo_inst": evo_inst,
        "places": bool(args.places and places_key),
        "places_key": places_key,
        "usar_site": bool(args.site),
    }

    try:
        with open(LEADS_ARQ, encoding="utf-8") as f:
            base = json.load(f)
    except Exception as e:
        print("ERRO: nao achei %s (%s)" % (LEADS_ARQ, e))
        return 1

    leads = base.get("leads", [])
    if args.limite:
        leads = leads[:args.limite]

    print("ESTUDIO RICK DIGITAL - verificacao de canais")
    print("Base: %d leads" % len(leads))
    print("Camadas ativas: Evolution=%s | Places=%s | Site=%s" % (
        "SIM" if cfg["evo"] else "nao",
        "SIM" if cfg["places"] else "nao",
        "SIM" if cfg["usar_site"] else "nao"))
    if not (cfg["evo"] or cfg["places"] or cfg["usar_site"]):
        print("  (sem chave, so o diagnostico local roda)")
    print()

    cache = carrega_cache()
    for i, lead in enumerate(leads):
        try:
            enriquece(lead, cfg, cache, args.so_wpp)
        except Exception as e:
            print("  ! %s: %s" % (lead.get("nome", "?"), str(e)[:100]))
        if (i + 1) % 25 == 0:
            print("  ... %d/%d" % (i + 1, len(leads)))

    canais = {}
    for l in leads:
        c = l.get("canal") or "?"
        canais[c] = canais.get(c, 0) + 1
    print()
    print("RESULTADO POR CANAL:")
    for k, v in sorted(canais.items(), key=lambda x: -x[1]):
        print("   %-20s %d" % (k, v))
    wa = [l for l in leads if l.get("wa_verificado") is True]
    print()
    print("WHATSAPP CONFIRMADO: %d" % len(wa))
    for l in wa[:20]:
        print("   OK %s -> %s" % (l.get("nome"), l.get("fone")))
    if cfg["evo"] and not wa:
        print("   (nenhum confirmado - confira se a instancia da Evolution esta "
              "com o QR escaneado e conectada)")

    if args.simular:
        print("\n(--simular: nada foi gravado)")
        return 0

    base["leads"] = leads
    base["verificado_em"] = agora()
    with open(LEADS_ARQ, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
    salva_cache(cache)
    print("\nBase atualizada: %s" % LEADS_ARQ)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
