"""Canais de contato: classifica telefone BR, detecta redes e escolhe o canal.

Por que este modulo existe
--------------------------
O OSM (OpenStreetMap) guarda o telefone que o comercio registrou. Esse
telefone pode ser:

  - celular com 9 (11 digitos)          -> WhatsApp funciona
  - celular antigo (8 digitos, 6-9)      -> vira celular com o nono digito
  - LINHA FIXA (8 digitos, comeca 2-5)   -> WhatsApp NAO funciona
  - numero invalido / de outra pais     -> sem contato

A versao anterior do motor marcava TODO numero como "fone_real": True sem
checar nada. Medindo a base real: de 152 leads, 120 eram LINHA FIXA. O link
wa.me existia, a tela dizia "fone real" e a mensagem nao chegava em ninguem.

Este modulo resolve 4 coisas:

  1. parse_br()      -> classifica o numero (celular/fixo/antigo/invalido)
  2. redes_de()      -> extrai Instagram/Facebook/TikTok/... das tags OSM
  3. presenca()      -> detecta se o negocio tem site OU pagina social
  4. escolhe_canal() -> decide por onde abordar (whatsapp/social/ligacao)

So stdlib. Roda no GitHub Actions.
"""
from __future__ import annotations

import re
import unicodedata

# --- DDDs oficiais do Brasil (67 codigos) --------------------------------
DDDS = {
    "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "21", "22", "24", "27", "28",
    "31", "32", "33", "34", "35", "37", "38",
    "41", "42", "43", "44", "45", "46", "47", "48", "49",
    "51", "53", "54", "55",
    "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "71", "73", "74", "75", "77", "79",
    "81", "82", "83", "84", "85", "86", "87", "88", "89",
    "91", "92", "93", "94", "95", "96", "97", "98", "99",
}

# tipo do numero
T_CELULAR = "celular"        # 11 digitos, nono digito = 9  (WhatsApp)
T_ANTIGO = "celular_antigo"  # 10 digitos, 3o digito 6-9  (recupera com o 9)
T_FIXO = "fixo"              # 10 digitos, 3o digito 2-5  (NAO tem WhatsApp)
T_INTL = "internacional"     # fora do padrao BR
T_INVALIDO = "invalido"

# --- redes sociais: tag do OSM -> (rotulo, dominio) ----------------------
REDES = {
    "instagram": ("Instagram", "instagram.com"),
    "facebook": ("Facebook", "facebook.com"),
    "tiktok": ("TikTok", "tiktok.com"),
    "twitter": ("X/Twitter", "twitter.com"),
    "youtube": ("YouTube", "youtube.com"),
    "linkedin": ("LinkedIn", "linkedin.com"),
    "telegram": ("Telegram", "t.me"),
    "whatsapp": ("WhatsApp", "wa.me"),
}

# ordem de preferencia: rede que aceita DM e responde rapido primeiro
ORDEM_REDES = ("whatsapp", "instagram", "facebook", "tiktok",
               "twitter", "youtube", "linkedin", "telegram")


def digitos(bruto) -> str:
    """So numeros, sem '+', espacos, parenteses ou barras."""
    return re.sub(r"\D", "", str(bruto or ""))


def _ddd_valido(local: str) -> bool:
    return len(local) >= 2 and local[:2] in DDDS


def _classifica_local(local: str) -> dict:
    """Classifica os digitos locais (sem DDD, sem codigo do pais)."""
    n = len(local)
    if n == 11 and local[2] == "9":
        return {"tipo": T_CELULAR, "e164": "55" + local, "local": local}
    if n == 10:
        terceiro = local[2]
        if terceiro in "2345":
            return {"tipo": T_FIXO, "e164": "55" + local, "local": local}
        if terceiro in "6789":
            # celular antigo (8 digitos). Com o nono digito vira celular valido.
            novo = local[:2] + "9" + local[2:]
            return {"tipo": T_ANTIGO, "e164": "55" + local,
                    "e164_celular": "55" + novo, "local": local}
    return {"tipo": T_INVALIDO, "e164": "", "local": local}


def parse_br(bruto) -> dict:
    """'Pizzaria | +55 11 4577-4527' -> {tipo:'fixo', e164:'551145774527', ...}

    Corrige o bug do motor antigo, que repetia o '55' do codigo do pais e
    produzia numeros com 13 digitos (ex.: '5551145534340') que quebravam no
    wa.me. Aqui tentamos todas as leituras possiveis e fica a valida.
    """
    raw = str(bruto or "").strip()
    d = digitos(raw)
    if len(d) < 8:
        return {"tipo": T_INVALIDO, "e164": "", "local": "", "bruto": raw,
                "motivo": "menos de 8 digitos"}

    candidatos = []
    # leituras: 0 = sem codigo do pais, 1 = tira um '55', 2 = tira dois '55'
    for k in (0, 1, 2):
        local = d
        ok = True
        for _ in range(k):
            if local.startswith("55"):
                local = local[2:]
            else:
                ok = False
                break
        if ok and len(local) >= 8:
            candidatos.append(local)

    melhor = None
    for local in candidatos:
        if not _ddd_valido(local):
            continue
        info = _classifica_local(local)
        # prioridade: celular > celular_antigo > fixo
        peso = {T_CELULAR: 3, T_ANTIGO: 2, T_FIXO: 1}.get(info["tipo"], 0)
        if peso == 0:
            continue
        if melhor is None or peso > melhor[0]:
            melhor = (peso, info)

    if melhor:
        info = dict(melhor[1])
        info["bruto"] = raw
        info["motivo"] = {
            T_CELULAR: "celular com 9 (11 digitos)",
            T_ANTIGO: "celular antigo (8 digitos) - recupera com o 9",
            T_FIXO: "linha fixa - WhatsApp nao funciona",
        }[info["tipo"]]
        info["pode_whatsapp"] = info["tipo"] in (T_CELULAR, T_ANTIGO)
        return info

    # fora do padrao BR: se tem '+' e nao comeca com 55, e internacional
    if raw.startswith("+") and not d.startswith("55") and 8 <= len(d) <= 15:
        return {"tipo": T_INTL, "e164": d, "local": d, "bruto": raw,
                "motivo": "numero internacional", "pode_whatsapp": True}

    return {"tipo": T_INVALIDO, "e164": "", "local": "", "bruto": raw,
            "motivo": "DDD invalido ou numero incompleto",
            "pode_whatsapp": False}


def _normaliza_url_rede(rede: str, valor: str) -> str:
    """'603pizzerie' -> 'https://instagram.com/603pizzerie'."""
    v = str(valor or "").strip()
    if not v:
        return ""
    if v.startswith("http://") or v.startswith("https://"):
        return v
    v = v.lstrip("@").strip()
    if not v:
        return ""
    dominio = REDES.get(rede, (rede, rede + ".com"))[1]
    if rede == "whatsapp":
        dig = digitos(v)
        if len(dig) >= 8:
            return "https://wa.me/" + dig
        return ""
    return "https://" + dominio + "/" + v


def redes_de(tags: dict) -> dict:
    """Extrai as redes sociais e o e-mail das tags do OSM.

    O OSM guarda o perfil em 'contact:instagram', 'contact:facebook',
    'contact:tiktok'... (e as vezes so o @usuario). Este motor pegava o
    elemento completo do Overpass e descartava essas tags.
    """
    tags = tags or {}
    achadas = {}
    for chave, (rotulo, _dom) in REDES.items():
        for tag in ("contact:" + chave, chave):
            v = (tags.get(tag) or "").strip()
            if not v:
                continue
            url = _normaliza_url_rede(chave, v)
            if url:
                achadas[chave] = {"rotulo": rotulo, "url": url, "usuario": v}
                break
    email = (tags.get("contact:email") or tags.get("email") or "").strip()
    if email and "@" in email:
        achadas["email"] = {"rotulo": "E-mail", "url": "mailto:" + email,
                            "usuario": email}
    return achadas


def ordem_redes(redes: dict) -> list:
    """Redes ordenadas pela preferencia de resposta."""
    return [r for r in ORDEM_REDES if r in (redes or {})]


def tag_whatsapp(tags: dict) -> str:
    """Valor cru da tag contact:whatsapp / whatsapp do OSM.

    Quando o proprio comercio cadastra um link de WhatsApp, esse numero
    e uma declaracao dele de que TEM WhatsApp - mesmo que o numero
    pareca linha fixa. Vale checar na Evolution antes de descartar.
    """
    tags = tags or {}
    for k in ("contact:whatsapp", "whatsapp"):
        v = (tags.get(k) or "").strip()
        if v:
            return v
    return ""


def site_de(tags: dict) -> str:
    """URL de site cadastrada (vazia se nao houver)."""
    tags = tags or {}
    for tag in ("website", "contact:website", "url", "contact:url"):
        v = (tags.get(tag) or "").strip()
        if len(v) > 4:
            return v
    return ""


def presenca(tags: dict) -> dict:
    """Situa o negocio: tem site? tem pagina social? nao tem nada?"""
    site = site_de(tags)
    redes = redes_de(tags)
    if site:
        status = "tem_site"
    elif redes:
        status = "so_redes"
    else:
        status = "sem_presenca"
    return {"site": site, "redes": redes, "status": status}


def escolhe_canal(fone_info: dict, redes: dict, wa_verificado=None,
                  tag_wa: bool = False) -> dict:
    """Decide o canal de abordagem do lead.

    wa_verificado: True  -> o numero foi checado no WhatsApp e EXISTE
                   False -> o numero foi checado e NAO existe no WhatsApp
                   None  -> ainda nao checado
    tag_wa:       True  -> o proprio negocio cadastrou contact:whatsapp,
                            ou seja, DECLAROU que tem WhatsApp. Vale
                            promover o lead mesmo que o numero pareca
                            linha fixa (a checagem final e da Evolution).
    """
    tipo = (fone_info or {}).get("tipo")
    pode_wa = (fone_info or {}).get("pode_whatsapp", False)
    redes = redes or {}
    tem_social = bool(ordem_redes(redes))

    if tipo == T_CELULAR and wa_verificado is True:
        canal, conf = "whatsapp", "alta"
    elif tipo in (T_CELULAR, T_ANTIGO) and wa_verificado is None:
        canal, conf = "whatsapp_provavel", "media"
    elif tipo in (T_CELULAR, T_ANTIGO) and wa_verificado is False:
        # celula existe mas NAO tem WhatsApp -> so rede social ou ligacao
        canal = "social" if tem_social else "ligacao"
        conf = "baixa"
    elif tipo == T_FIXO:
        canal = "social" if tem_social else "ligacao"
        conf = "media" if tem_social else "baixa"
    elif tipo == T_INTL:
        canal = "whatsapp_provavel" if wa_verificado is not False else "social"
        conf = "media"
    else:
        canal = "social" if tem_social else "sem_contato"
        conf = "baixa"

    # o comercio cadastrou o proprio link de WhatsApp -> promote o lead
    if tag_wa and wa_verificado is not False and canal in ("ligacao", "social"):
        canal, conf = "whatsapp_provavel", "media"

    return {
        "canal": canal,
        "confianca": conf,
        "wa_verificado": wa_verificado,
        "tem_social": tem_social,
        # canais alternativos, em ordem de quem mais responde
        "alternativas": ordem_redes(redes),
        "rotulo": {
            "whatsapp": "WhatsApp confirmado",
            "whatsapp_provavel": "Celular (validar WhatsApp)",
            "social": "Sem WhatsApp - abordar por rede social",
            "ligacao": "Somente telefone fixo",
            "sem_contato": "Sem canal de contato",
        }.get(canal, canal),
    }


def sem_acento(txt) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(txt or ""))
                   if unicodedata.category(c) != "Mn").lower().strip()


if __name__ == "__main__":
    # auditoria rapida da base atual
    import json
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    arq = os.path.join(base, "leads-latest.json")
    with open(arq, encoding="utf-8") as f:
        dados = json.load(f)
    leads = dados.get("leads", [])
    cont = {}
    for l in leads:
        info = parse_br(l.get("fone_bruto") or l.get("fone"))
        cont[info["tipo"]] = cont.get(info["tipo"], 0) + 1
    print("AUDITORIA DE %d LEADS" % len(leads))
    for k, v in sorted(cont.items(), key=lambda x: -x[1]):
        print("  %-16s %d" % (k, v))
    wa = sum(1 for l in leads
             if parse_br(l.get("fone_bruto") or l.get("fone")).get("pode_whatsapp"))
    print("  %-16s %d  <- unicos que PODEM ter WhatsApp" % ("TOTAL whatsapp", wa))
