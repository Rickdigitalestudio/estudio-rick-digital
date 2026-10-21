"""Motor de prospeccao: comercios LOCAIS sem site, mas com telefone.

Por que este motor existe: quem NAO tem site e tem telefone e o lead mais
quente que existe para quem vende site. O business nao te procura porque nao
sabe que voce existe — voce aparece e resolve o problema.

O que mudou em relacao a versao anterior:
  - alvos locais (ABC paulista), nao capitals distantes
  - EXIGE telefone valido (>= 8 digitos) — sem contato o lead nao serve
  - raio maior em cidades menores (cobre o ABC inteiro)
  - uma unica query Overpass por cidade (10x mais rapido)
  - telefone normalizado em E.164, com link de WhatsApp pronto
  - pitch especifico por categoria + landing page certa

Roda no GitHub Actions (sem depender do PC). So stdlib.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "EstudioRickDigital-Prospeccao/2.0 (contato: portfolio rickdigitalestudio.github.io/profissional-rickdutra)"}
SITE = "https://rickdigitalestudio.github.io/profissional-rickdutra"
OVERPASS = "https://overpass-api.de/api/interpreter"

# --- categorias: tag do OSM -> categoria comercial -----------------------
SHOP = ("hairdresser|beauty|nail|computer|pet|bakery|pastry|florist|tailor|"
        "car_repair|car_wash|convenience|supermarket|clothes|shoes|electronics|"
        "mobile_phone|butcher|greengrocer|furniture|doityourself")
AMENITY = ("restaurant|fast_food|cafe|dentist|veterinary|clinic|doctors|pharmacy|"
           "bar|pub|biergarten|ice_cream|food_court")
CRAFT = "barber|photographer|caterer|confectionery"
OFFICE = "it|accountant|lawyer|estate_agent|insurance|travel_agent|company"
LEISURE = "fitness_centre|sports_centre|swimming_pool|yoga_centre|sports_hall"

QUERY = """[out:json][timeout:60];(
nwr["shop"~"^(%s)$",i](around:%s,%s,%s);
nwr["amenity"~"^(%s)$",i](around:%s,%s,%s);
nwr["craft"~"^(%s)$",i](around:%s,%s,%s);
nwr["office"~"^(%s)$",i](around:%s,%s,%s);
nwr["leisure"~"^(%s)$",i](around:%s,%s,%s);
nwr["shop"~"^(%s)$",i](around:%s,%s,%s);
);out center 500;""" % (
    SHOP, "%R%", "%LAT%", "%LON%",
    AMENITY, "%R%", "%LAT%", "%LON%",
    CRAFT, "%R%", "%LAT%", "%LON%",
    OFFICE, "%R%", "%LAT%", "%LON%",
    LEISURE, "%R%", "%LAT%", "%LON%",
    SHOP, "%R%", "%LAT%", "%LON%",
)

# --- comercial: categoria -> (pitch, landing page) -----------------------
PITCH = {
    "restaurante": ("Sua loja aparece no Google quando alguém procura por delivery na sua rua. Hoje você está no mapa, mas sem site — dá para achar, mas não dá para pedir pelo celular.",
                    "criacao-de-sites-profissionais.html"),
    "barbearia": ("Barbearia com site não perde cliente: quem pesquisa 'barbearia perto de mim' vê a agenda e marca antes de chegar.",
                  "site-para-pequenas-empresas.html"),
    "beleza": ("Clientes de beleza decidem olhando o trabalho. Um site com antes e depois é o portfólio que fecha manicure e escova.",
               "criacao-de-sites-profissionais.html"),
    "fitness": ("Academia que tem site mostra a grade de aulas e vende mensalidade online, 24h por dia.",
                "site-para-pequenas-empresas.html"),
    "pet": ("Pet shop, clínica veterinária e banho: quem procura 'pet shop perto de mim' decide em 3 segundos no celular.",
            "site-para-pequenas-empresas.html"),
    "dentista": ("Para clínica odontológica, o site não é capa — é agenda. Paciente encontra, vê horários e marca.",
                 "site-para-pequenas-empresas.html"),
    "clinica": ("Clínica com site ganha paciente de busca local e preenche agenda vazia sem gastar em anúncio.",
                "site-para-pequenas-empresas.html"),
    "informatica": ("Loja de informática e assistência: o cliente pesquisa o problema ('troca de tela', 'formatação') e precisa cair num site rápido com WhatsApp.",
                   "criacao-de-sites-profissionais.html"),
    "loja": ("Loja virtual vende de madrugada, para todo o Brasil, sem depender de aplicativo de delivery.",
             "loja-virtual-completa.html"),
    "oficina": ("Oficina e centro automotivo: o cliente pesquisa o serviço na sua rua e chama quem tem site.",
                 "site-para-pequenas-empresas.html"),
    "contabil": ("Escritório contábil com site capta cliente pelo Google na hora que ele precisa declarar.",
                 "site-para-pequenas-empresas.html"),
    "imobiliaria": ("Imobiliária com site tem vitrine 24h — enquanto o concorrente está fechado, o seu imóvel continua sendo visto.",
                    "criacao-de-sites-profissionais.html"),
    "advocacia": ("Advogado com site aparece na busca quando alguém já está procurando advogado na sua região.",
                  "site-para-pequenas-empresas.html"),
    "padaria": ("Padaria e café: cardápio digital e link no WhatsApp aumentam o pedido por delivery sem sair do balcão.",
                "fanpage-que-vende.html"),
    "farmacia": ("Drogaria com site vende delivery e assinatura de medicação direto pelo WhatsApp — sem depender de aplicativo que fica com 20% do pedido.",
                 "fanpage-que-vende.html"),
}


def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get_retry(url, tries=2, espera=12, timeout=75):
    ultimo = None
    for t in range(tries):
        try:
            return get(url, timeout)
        except Exception as e:
            ultimo = e
            time.sleep(espera * (t + 1))
    raise ultimo


def fone_bruto(tags):
    for k in ("contact:phone", "phone", "contact:mobile", "mobile",
              "contact:whatsapp", "whatsapp"):
        v = (tags.get(k) or "").strip()
        if v:
            return v
    return ""


def normaliza_fone(bruto):
    """'Pizzaria Rittorno | +55 11 4822 4352' -> '551148224352' (E.164 BR)."""
    if not bruto:
        return ""
    digitos = re.sub(r"\D", "", bruto)
    if len(digitos) < 8:
        return ""
    if digitos.startswith("55"):
        digitos = digitos[2:]
    if len(digitos) in (10, 11):
        return "55" + digitos
    return ""


def tem_site(tags):
    v = (tags.get("website") or tags.get("contact:website")
         or tags.get("url") or tags.get("contact:url") or "").strip()
    return len(v) > 4


PUBLICO = (
    "unidade basica", "ubs", "unidade saude", "unidade de saude",
    "centro de saude", "posto de saude", "posto de saude", "centro de especialidade",
    "caps", "ps ", "pronto socorro", "hospital municipal", "samu", "upa ",
    "secretaria de", "prefeitura", "escola municipal", "creche municipal",
    "biblioteca publica", "centro comunitario", "associacao de",
)


def eh_publico(nome):
    """Governo e sem fins lucrativos nao sao cliente de site particular."""
    n = (nome or "").lower().strip()
    if not n:
        return True
    for p in PUBLICO:
        if n.startswith(p) or p in n:
            return True
    return False


def categoria_de(tags):
    """Deriva a categoria comercial a partir das tags do OSM."""
    t = tags.get("shop", "")
    if t in ("hairdresser", "beauty", "nail", "barber"):
        return "beleza" if t != "hairdresser" else "barbearia"
    if t in ("computer", "mobile_phone", "electronics"):
        return "informatica"
    if t in ("pet",):
        return "pet"
    if t in ("bakery", "pastry", "confectionery"):
        return "padaria"
    if t in ("supermarket", "convenience", "butcher", "greengrocer",
             "clothes", "shoes", "furniture"):
        return "loja"
    if t in ("car_repair", "car_wash"):
        return "oficina"
    if t in ("florist", "tailor"):
        return "loja"
    a = tags.get("amenity", "")
    if a in ("restaurant", "fast_food", "cafe", "food_court", "bar", "pub",
             "biergarten", "ice_cream"):
        return "restaurante"
    if a == "dentist":
        return "dentista"
    if a == "veterinary":
        return "pet"
    if a == "pharmacy" or tags.get("shop") == "chemist":
        return "farmacia"
    if a in ("clinic", "doctors"):
        return "clinica"
    if tags.get("craft") == "barber":
        return "barbearia"
    if tags.get("craft") == "photographer":
        return "informatica"
    o = tags.get("office", "")
    if o == "accountant":
        return "contabil"
    if o == "estate_agent":
        return "imobiliaria"
    if o == "lawyer":
        return "advocacia"
    if o == "it":
        return "informatica"
    if tags.get("leisure") in ("fitness_centre", "sports_centre", "swimming_pool",
                               "yoga_centre"):
        return "fitness"
    return "loja"


def endereco(tags):
    partes = [tags.get("addr:street"), tags.get("addr:housenumber"),
              tags.get("addr:suburb"), tags.get("addr:city")]
    return ", ".join([p for p in partes if p])


def monta_query(raio, lat, lon):
    return (QUERY.replace("%R%", str(raio))
                   .replace("%LAT%", lat).replace("%LON%", lon))


def varrer(alvo, raio, limite):
    geo_q = "%s, %s" % (alvo["cidade"], alvo["pais"])
    g = get("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
            + urllib.parse.quote(geo_q))
    if not g:
        return [], "cidade nao localizada: " + geo_q
    lat, lon = g[0]["lat"], g[0]["lon"]
    q = monta_query(raio, lat, lon)
    j = get_retry(OVERPASS + "?data=" + urllib.parse.quote(q))
    achados = [e for e in (j.get("elements") or []) if (e.get("tags") or {}).get("name")]

    com_site = [e for e in achados if tem_site(e["tags"])]
    com_fone = [e for e in achados if normaliza_fone(fone_bruto(e["tags"]))]
    # o alvo ideal: tem telefone, NAO tem site
    alvo_leads = [e for e in achados
                  if normaliza_fone(fone_bruto(e["tags"])) and not tem_site(e["tags"])]

    leads = []
    for e in alvo_leads:
        t = e["tags"]
        fone = normaliza_fone(fone_bruto(t))
        if eh_publico(t.get("name")):
            continue
        cat = categoria_de(t)
        pitch, pagina = PITCH.get(cat, PITCH["loja"])
        nome = t.get("name")
        msg = ("Ola! Vi que a {nome} ainda nao tem site. "
               "{pitch} Posso montar em 10 dias, a partir de R$ 997. "
               "Meu trabalho: {site}").format(
            nome=nome, pitch=pitch, site=SITE + "/" + pagina)
        leads.append({
            "nome": nome,
            "fone": fone,
            "fone_real": True,
            "fone_bruto": fone_bruto(t),
            "endereco": endereco(t),
            "cidade": "%s/%s" % (alvo["cidade"], alvo["pais"]),
            "bairro": t.get("addr:suburb", ""),
            "categoria": cat,
            "semSite": True,
            "origem": "Maps local · %s · sem site no cadastro" % alvo["cidade"],
            "landing": pagina,
            "pitch": pitch,
            "wa_link": "https://wa.me/%s?text=%s" % (
                fone, urllib.parse.quote(msg)),
            "lat": e.get("lat") or (e.get("center") or {}).get("lat"),
            "lon": e.get("lon") or (e.get("center") or {}).get("lon"),
        })
    leads = leads[:limite]
    return leads, "%s (raio %sm): %d achados, %d com site, %d com fone, %d ALVOS" % (
        geo_q, raio, len(achados), len(com_site), len(com_fone), len(leads))


def main():
    with open(os.path.join(BASE, "alvos.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    varredura = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    todos, resumo = [], []

    # --- rodizio: cada rodada varre so um Excerpto das cidades ---
    # A varredura completa demora muito e o Overpass derruba. Varrendo 2
    # cidades por dia, em 4 dias cobre todas, e a base so cresce.
    alvos = cfg["alvos"]
    por_rodada = cfg.get("cidades_por_rodada", 2)
    estado_arq = os.path.join(BASE, "rodizio.json")
    try:
        with open(estado_arq, encoding="utf-8") as f:
            i = json.load(f).get("i", 0)
    except Exception:
        i = 0
    if not cfg.get("todos_always"):
        alvos = alvos[i % len(alvos):] + alvos[:i % len(alvos)]
        alvos = alvos[:por_rodada]
    with open(estado_arq, "w", encoding="utf-8") as f:
        json.dump({"i": (i + 1) % len(cfg["alvos"]), "quando": varredura}, f)

    for alvo in alvos:
        raio = alvo.get("raio_m", cfg.get("raio_m", 8000))
        limite = alvo.get("max", cfg.get("max_por_alvo", 40))
        try:
            leads, msg = varrer(alvo, raio, limite)
            for l in leads:
                l["varredura"] = varredura
            todos.extend(leads)
            resumo.append(msg)
        except Exception as e:
            resumo.append("%s/%s: ERRO %s" % (alvo["cidade"], alvo["pais"], str(e)[:90]))
        time.sleep(3)

    # dedup por telefone (o mesmo negocio com 2 tags cai 2x)
    vistos, unicos = set(), []
    for l in todos:
        chave = l.get("fone") or (l["nome"] or "").lower()
        if chave in vistos:
            continue
        vistos.add(chave)
        unicos.append(l)

    # une com a base anterior (o arquivo nunca regride)
    try:
        with open(os.path.join(BASE, "leads-latest.json"), encoding="utf-8") as f:
            antigos = json.load(f).get("leads", [])
        for l in antigos:
            if not l.get("fone"):
                continue  # descarta lead antigo sem telefone
            chave = l.get("fone")
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(l)
    except Exception:
        pass

    cidades_alvo = [a["cidade"].split(",")[0].strip().lower() for a in cfg["alvos"]]
    unicos = [l for l in unicos
              if any(c in (l.get("cidade", "") or "").lower() for c in cidades_alvo)]

    payload = {"varredura": varredura, "total": len(unicos), "leads": unicos[:200]}
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
    print("TOTAL ALVOS COM TELEFONE: %d" % len(unicos))


if __name__ == "__main__":
    main()
