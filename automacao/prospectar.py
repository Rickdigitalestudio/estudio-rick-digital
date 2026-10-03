"""Varredura diária de comércios SEM site registrado (OpenStreetMap/Overpass).

Roda no GitHub Actions, com PC desligado e app fechado.
Saída: automacao/leads-latest.json (lido pelo app) + snapshot datado.
Só stdlib (urllib) — sem dependências.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "EstudioRickDigital-Prospeccao/1.0 (contato: portfolio studiorickdigital.github.io)"}

OSM = {
    "fitness": ["leisure=fitness_centre", "sport=fitness"],
    "academia_luta": ["leisure=sports_centre", "sport=martial_arts"],
    "beleza": ["shop=beauty", "shop=hairdresser", "shop=nail"],
    "barbearia": ["shop=hairdresser", "craft=barber"],
    "restaurante": ["amenity=restaurant", "amenity=fast_food"],
    "lanchonete": ["amenity=fast_food", "amenity=cafe"],
    "padaria": ["shop=bakery", "shop=pastry"],
    "mercado": ["shop=convenience", "shop=supermarket"],
    "roupas": ["shop=clothes", "shop=shoes"],
    "pet": ["shop=pet", "amenity=veterinary"],
    "farmacia": ["amenity=pharmacy"],
    "dentista": ["amenity=dentist", "healthcare=dentist"],
    "clinica": ["amenity=clinic", "amenity=doctors"],
    "advocacia": ["office=lawyer"],
    "contabil": ["office=accountant"],
    "imobiliaria": ["office=estate_agent"],
    "oficina": ["shop=car_repair", "amenity=car_wash"],
    "salao_festa": ["leisure=hall", "amenity=events_venue"],
    "papelaria": ["shop=stationery", "shop=books"],
    "informatica": ["shop=computer", "office=it"],
    "eletro": ["shop=electronics", "shop=mobile_phone"],
}


def get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get_retry(url, tries=3, espera=20, timeout=60):
    ultimo = None
    for t in range(tries):
        try:
            return get(url, timeout)
        except Exception as e:
            ultimo = e
            time.sleep(espera * (t + 1))
    raise ultimo


def tem_site(tags):
    v = (tags.get("website") or tags.get("contact:website")
         or tags.get("url") or tags.get("contact:url") or "").strip()
    return len(v) > 4


def fone(tags):
    for k in ("contact:phone", "phone", "contact:mobile", "mobile",
              "contact:whatsapp", "whatsapp"):
        v = (tags.get(k) or "").strip()
        if v:
            return v
    return ""


def tem_fone(tags):
    return len("".join(c for c in fone(tags) if c.isdigit())) >= 8


def endereco(tags):
    partes = [tags.get("addr:street"), tags.get("addr:suburb"), tags.get("addr:city")]
    return ", ".join([p for p in partes if p])


def clausulas(categoria, lat, lon, raio):
    tags = OSM.get(categoria, ["name~" + categoria])
    out = []
    for t in tags:
        k, v = t.split("=", 1)
        out.append('nwr["%s"~"%s",i](around:%s,%s,%s);' % (k, v, raio, lat, lon))
    return out


def varrer(alvo, raio, limite):
    geo_q = "%s, %s" % (alvo["cidade"], alvo["pais"])
    g = get("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
            + urllib.parse.quote(geo_q))
    if not g:
        return [], "cidade nao localizada: " + geo_q
    lat, lon = g[0]["lat"], g[0]["lon"]
    q = "".join(clausulas(alvo["categoria"], lat, lon, raio))
    data = "[out:json][timeout:25];(%s);out center 25;" % q
    url = ("https://overpass-api.de/api/interpreter?data="
           + urllib.parse.quote(data))
    j = get_retry(url)
    achados = [e for e in (j.get("elements") or []) if (e.get("tags") or {}).get("name")]
    com_site = sum(1 for e in achados if tem_site(e["tags"]))
    com_fone = sum(1 for e in achados if tem_fone(e["tags"]))
    filtrados = [e for e in achados if not tem_site(e["tags"])][:limite]
    leads = []
    for e in filtrados:
        t = e["tags"]
        leads.append({
            "nome": t.get("name"),
            "fone": fone(t).lstrip("+"),
            "fone_real": tem_fone(t),
            "endereco": endereco(t),
            "cidade": "%s/%s" % (alvo["cidade"], alvo["pais"]),
            "categoria": alvo["categoria"],
            "fonte": "GitHub-robo OSM/Overpass (sem site no cadastro)",
        })
    return leads, "%s: %d achados, %d com site descartados, %d com fone, %d candidatos" % (
        geo_q, len(achados), com_site, com_fone, len(leads))


def main():
    with open(os.path.join(BASE, "alvos.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    varredura = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    todos, resumo = [], []
    for alvo in cfg["alvos"]:
        try:
            leads, msg = varrer(alvo, cfg.get("raio_m", 5000),
                                cfg.get("max_por_alvo", 25))
            for l in leads:
                l["varredura"] = varredura
            todos.extend(leads)
            resumo.append(msg)
        except Exception as e:  # API instável: registra e segue
            resumo.append("%s/%s: ERRO %s" % (alvo["cidade"], alvo["pais"], e))
        time.sleep(2)
    # dedup por nome+cidade
    vistos, unicos = set(), []
    for l in todos:
        chave = (l["nome"] or "").lower() + "|" + l["cidade"].lower()
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(l)
    # une com a base anterior: o arquivo só cresce, nunca regride numa rodada fraca
    try:
        with open(os.path.join(BASE, "leads-latest.json"), encoding="utf-8") as f:
            antigos = json.load(f).get("leads", [])
        for l in antigos:
            chave = (l.get("nome") or "").lower() + "|" + (l.get("cidade") or "").lower()
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(l)
    except Exception:
        pass
    payload = {"varredura": varredura, "total": len(unicos), "leads": unicos[:150]}
    with open(os.path.join(BASE, "leads-latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    hist = os.path.join(BASE, "historico")
    os.makedirs(hist, exist_ok=True)
    dia = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(os.path.join(hist, "leads-%s.json" % dia), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("VARREDURA " + varredura)
    for m in resumo:
        print(" - " + m)
    print("TOTAL CANDIDATOS: %d" % len(unicos))


if __name__ == "__main__":
    main()
