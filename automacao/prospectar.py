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
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from canais import (REDES, T_CELULAR, T_FIXO, T_ANTIGO, T_INVALIDO,
                    escolhe_canal, ordem_redes, parse_br, presenca,
                    tag_whatsapp)

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

# Segunda passada: quem tem presenca em REDE SOCIAL (e nao tem site).
# Medindo a regiao ABC: 634 negocios com rede social em 4 cidades, 202
# deles com telefone e sem site. Boa parte NAO aparece na busca por
# categoria (bar/restaurante/etc) porque o OSM nao tem a tag de oficio
# deles. Quem tem Instagram/Facebook cadastrado e um comercio pequeno
# de verdade - e o canal de entrada quando nao tem WhatsApp.
QUERY_SOCIAL = """[out:json][timeout:60];(
nwr["contact:instagram"](around:%s,%s,%s);
nwr["contact:facebook"](around:%s,%s,%s);
nwr["contact:tiktok"](around:%s,%s,%s);
nwr["contact:whatsapp"](around:%s,%s,%s);
nwr["contact:youtube"](around:%s,%s,%s);
nwr["contact:twitter"](around:%s,%s,%s);
);out center 500;""" % (
    "%R%", "%LAT%", "%LON%",
    "%R%", "%LAT%", "%LON%",
    "%R%", "%LAT%", "%LON%",
    "%R%", "%LAT%", "%LON%",
    "%R%", "%LAT%", "%LON%",
    "%R%", "%LAT%", "%LON%",
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


TAGS_FONE = ("contact:mobile", "mobile", "contact:whatsapp", "whatsapp",
             "contact:phone", "phone", "contact:telephone", "telephone")


def fone_bruto(tags):
    """Texto do telefone cadastrado (preferindo mobile/whatsapp)."""
    for k in TAGS_FONE:
        v = (tags.get(k) or "").strip()
        if v:
            return v
    return ""


def classifica_fone(tags):
    """Todos os telefones do cadastro, classificados de verdade.

    O motor antigo aceitava qualquer numero com 8+ digitos e marcava
    'fone_real': True. Medindo a base real: 120 de 152 leads eram LINHA
    FIXA. O link wa.me existia, a tela dizia "fone real" e a mensagem nao
    chegava em ninguem.

    Retorna:
      bruto -> texto original do telefone escolhido
      info  -> classificacao (canais.parse_br)
      fixo  -> (bruto, info) de uma linha fixa, se houver (serve p/ ligar)
      todos -> lista de (bruto, info) de tudo que foi encontrado
    """
    brutos, vistos = [], set()
    origem = {}
    for k in TAGS_FONE:
        v = (tags.get(k) or "").strip()
        if not v:
            continue
        d = re.sub(r"\D", "", v)
        if len(d) < 8 or d in vistos:
            continue
        vistos.add(d)
        brutos.append(v)
        origem.setdefault(v, k)

    todos = [(b, parse_br(b)) for b in brutos]

    def peso(i):
        return {T_CELULAR: 3, T_ANTIGO: 2, T_FIXO: 1}.get(i["tipo"], 0)

    wa, fixo = None, None
    for b, i in todos:
        p = peso(i)
        if p >= 2 and (wa is None or p > peso(wa[1])):
            wa = (b, i)
        if i["tipo"] == T_FIXO and fixo is None:
            fixo = (b, i)

    escolhido = wa or (todos[0] if todos else ("", parse_br("")))
    bruto, info = escolhido
    # o proprio negocio cadastrou um link de WhatsApp? entao o numero e
    # declarado como WhatsApp, mesmo que o formato pareca linha fixa.
    tag_wa = tag_whatsapp(tags)
    return {"bruto": bruto, "info": info, "fixo": fixo, "todos": todos,
            "tag_whatsapp": tag_wa,
            "origem_tag": origem.get(bruto, "")}


def normaliza_fone(bruto):
    """E.164 do telefone (BR) ou '' se nao servir para WhatsApp."""
    info = parse_br(bruto)
    if info["tipo"] == T_INVALIDO:
        return ""
    if info["tipo"] == T_ANTIGO:
        return info.get("e164_celular") or info["e164"]
    return info["e164"]


def tem_site(tags):
    return bool(presenca(tags)["site"])



PUBLICO = (
    "unidade basica", "ubs", "unidade saude", "unidade de saude",
    "unidade basica de saude", "unidade de saude da familia", "saude da familia",
    "centro de saude", "posto de saude", "posto de saude", "centro de especialidade",
    "caps", "ps ", "pronto socorro", "hospital municipal", "samu", "upa ",
    "secretaria de", "prefeitura", "escola municipal", "creche municipal",
    "biblioteca publica", "centro comunitario", "associacao de",
)


def sem_acento(txt):
    """Normaliza para comparar: 'Unidade Basica' == 'Unidade Básica'."""
    return "".join(c for c in unicodedata.normalize("NFD", txt or "")
                   if unicodedata.category(c) != "Mn").lower().strip()


def eh_publico(nome):
    """Governo e sem fins lucrativos nao sao cliente de site particular."""
    n = sem_acento(nome)
    if not n:
        return True
    for p in PUBLICO:
        p = sem_acento(p)
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
                               "yoga_centre", "sports_hall", "stadium"):
        return "fitness"
    if tags.get("sport"):
        return "fitness"

    # fallback pelo nome: o OSM as vezes nao tem tag util
    n = sem_acento(tags.get("name", ""))
    if any(x in n for x in ("ginasio", "academia", "fitness", "crossfit",
                            "musculacao", "studio pilates", "pilates", "box")):
        return "fitness"
    if "drogaria" in n or "farmacia" in n or "farma" in n:
        return "farmacia"
    if any(x in n for x in ("barbearia", "barbeiro", "cabeleireir", "salon",
                            "espaco de beleza", "manicure", "pedicure")):
        return "beleza" if "barbearia" not in n else "barbearia"
    if "veterinaria" in n or "clinica vet" in n:
        return "pet"
    if any(x in n for x in ("dentista", "odontolog", "clinica odonto")):
        return "dentista"
    if any(x in n for x in ("padaria", "panificadora", "confeitaria")):
        return "padaria"
    if any(x in n for x in ("restaurante", "lanchonete", "pizzaria", "churrascaria",
                            "burger", "food", "cafe", "cafeitaria", "lanchonete",
                            "torresmo", "churrasqueira")):
        return "restaurante"
    if any(x in n for x in ("pet shop", "petshop", "banho e tosa")):
        return "pet"
    if any(x in n for x in ("oficina", "mecanica", "centro automotivo", "lavagem")):
        return "oficina"
    return "loja"


def endereco(tags):
    partes = [tags.get("addr:street"), tags.get("addr:housenumber"),
              tags.get("addr:suburb"), tags.get("addr:city")]
    return ", ".join([p for p in partes if p])


def monta_query(raio, lat, lon):
    return (QUERY.replace("%R%", str(raio))
                   .replace("%LAT%", lat).replace("%LON%", lon))


def monta_query_social(raio, lat, lon):
    return (QUERY_SOCIAL.replace("%R%", str(raio))
                            .replace("%LAT%", lat).replace("%LON%", lon))


def overpass(q):
    return get_retry(OVERPASS + "?data=" + urllib.parse.quote(q)).get("elements") or []


def monta_mensagem(nome, pitch, pagina, canal, redes):
    """Mensagem conforme o canal real do lead.

    Mandar "chama no WhatsApp" para quem so tem linha fixa (ou nao tem
    WhatsApp) e o jeito mais rapido de queimar a abordagem. Aqui o texto
    muda sozinho: WhatsApp, direct na rede social, ou roteiro de ligacao.
    """
    site = SITE + "/" + pagina
    if canal in ("whatsapp", "whatsapp_provavel"):
        return ("Ola! Vi que a {nome} ainda nao tem site. {pitch} "
                "Posso montar em 10 dias, a partir de R$ 997. "
                "Meu trabalho: {site}").format(nome=nome, pitch=pitch, site=site)
    if canal == "social" and redes:
        chave = ordem_redes(redes)[0]
        rotulo = REDES.get(chave, (chave, ""))[0]
        url = redes[chave]["url"]
        return ("Ola! Vi que a {nome} ainda nao tem site. {pitch} "
                "Posso montar em 10 dias, a partir de R$ 997. "
                "Achei voces no {rotulo} e preferi mandar por aqui: {url}. "
                "Meu trabalho: {site}").format(nome=nome, pitch=pitch,
                                                rotulo=rotulo, url=url, site=site)
    if canal == "ligacao":
        return ("Script de ligacao - {nome}: 'Ola, aqui e do Estudio Rick "
                "Digital. Vi que voces ainda nao tem site, e a {nome} aparece "
                "no Google quando alguem procura esse servico na regiao. "
                "Eu monto site em 10 dias a partir de R$ 997. Quer que eu "
                "mande o exemplo por e-mail ou WhatsApp?'").format(nome=nome)
    return ("Ola! Vi que a {nome} ainda nao tem site. {pitch} "
            "Meu trabalho: {site}").format(nome=nome, pitch=pitch, site=site)


def _lead_de(e, alvo):
    """Monta um lead a partir de um elemento do OSM. None se nao serve."""
    t = e.get("tags") or {}
    nome = t.get("name")
    if not nome or eh_publico(nome):
        return None
    p = presenca(t)
    if p["status"] == "tem_site":
        return None
    redes = p["redes"]
    cf = classifica_fone(t)
    info = cf["info"]
    tem_fone = info["tipo"] != T_INVALIDO
    if not tem_fone:
        info = parse_br("")
    canal = escolhe_canal(info, redes, None, tag_wa=bool(cf["tag_whatsapp"]))
    if canal["canal"] == "sem_contato":
        return None  # nem telefone nem rede: nao da para abordar

    # o proprio negocio cadastrou um link de WhatsApp (contact:whatsapp).
    # esse numero e declaracao dele de que TEM WhatsApp - mesmo que o
    # formato pareca linha fixa. Entra como lead de WhatsApp para ser
    # checado na Evolution, em vez de descartado como "so ligar".
    fone_wa_tag = ""
    if cf["tag_whatsapp"]:
        d = re.sub(r"\D", "", cf["tag_whatsapp"])
        if len(d) >= 10:
            fone_wa_tag = d
    if fone_wa_tag and canal["canal"] in ("ligacao", "social"):
        canal = dict(canal, canal="whatsapp_provavel",
                     rotulo="WhatsApp no cadastro · validar",
                     confianca="media")
    cat = categoria_de(t)
    pitch, pagina = PITCH.get(cat, PITCH["loja"])
    fone = fone_wa_tag or (normaliza_fone(cf["bruto"]) if tem_fone else "")
    msg = monta_mensagem(nome, pitch, pagina, canal["canal"], redes)
    fone_fixo = cf["fixo"][1]["e164"] if cf["fixo"] else ""

    return {
        "nome": nome,
        "fone": fone,
        "fone_bruto": cf["bruto"],
        "fone_fixo": fone_fixo,
        # fone_real = tem numero que realmente chega no WhatsApp
        "fone_real": canal["canal"] in ("whatsapp", "whatsapp_provavel"),
        "fone_ok": tem_fone,
        "tipo_fone": info["tipo"],
        "motivo_fone": info.get("motivo", "") or ("sem telefone cadastrado"
                                                  if not tem_fone else ""),
        "canal": canal["canal"],
        "canal_rotulo": canal["rotulo"],
        "confianca": canal["confianca"],
        "alternativas": canal["alternativas"],
        "status_site": p["status"],
        "tag_whatsapp": cf["tag_whatsapp"],
        "redes": {k: v["url"] for k, v in redes.items()},
        "endereco": endereco(t),
        "cidade": "%s/%s" % (alvo["cidade"], alvo["pais"]),
        "bairro": t.get("addr:suburb", ""),
        "categoria": cat,
        "semSite": True,
        "origem": "Maps local · %s · sem site no cadastro" % alvo["cidade"],
        "landing": pagina,
        "pitch": pitch,
        "msg": msg,
        "wa_link": ("https://wa.me/%s?text=%s" % (fone, urllib.parse.quote(msg))
                    if canal["canal"] in ("whatsapp", "whatsapp_provavel") else ""),
        "tel_link": ("tel:+%s" % fone_fixo) if fone_fixo else "",
        "lat": e.get("lat") or (e.get("center") or {}).get("lat"),
        "lon": e.get("lon") or (e.get("center") or {}).get("lon"),
    }


# prioridade de abordagem: quem tem WhatsApp primeiro, depois rede social,
# depois so telefone fixo (que exige ligacao).
PESO_CANAL = {"whatsapp": 0, "whatsapp_provavel": 1,
              "social": 2, "ligacao": 3, "sem_contato": 9}


def varrer(alvo, raio, limite):
    geo_q = "%s, %s" % (alvo["cidade"], alvo["pais"])
    g = get("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
            + urllib.parse.quote(geo_q))
    if not g:
        return [], "cidade nao localizada: " + geo_q
    lat, lon = g[0]["lat"], g[0]["lon"]

    # --- passada 1: por categoria (achada pelo oficio) ----------------
    try:
        achados = overpass(monta_query(raio, lat, lon))
    except Exception:
        achados = []
    achados = [e for e in achados if (e.get("tags") or {}).get("name")]

    # --- passada 2: por presenca em rede social ------------------------
    try:
        achados_soc = overpass(monta_query_social(raio, lat, lon))
    except Exception:
        achados_soc = []
    achados_soc = [e for e in achados_soc if (e.get("tags") or {}).get("name")]

    com_site = [e for e in achados if tem_site(e["tags"])]
    com_fone = [e for e in achados if normaliza_fone(fone_bruto(e["tags"]))]

    leads = []
    vistos_fone, vistos_nome = set(), set()

    def aceita(l):
        if not l:
            return False
        if l["fone"]:
            if l["fone"] in vistos_fone:
                return False
            vistos_fone.add(l["fone"])
        chave = l["nome"].lower().strip() + "|" + l["cidade"].lower()
        if chave in vistos_nome:
            return False
        vistos_nome.add(chave)
        return True

    for e in achados:
        if not normaliza_fone(fone_bruto(e["tags"])) or tem_site(e["tags"]):
            continue
        l = _lead_de(e, alvo)
        if aceita(l):
            leads.append(l)

    # quem tem rede social e nao tem site entra mesmo sem telefone:
    # o canal e o direct, e o lead e valido do mesmo jeito
    for e in achados_soc:
        if tem_site(e["tags"]):
            continue
        l = _lead_de(e, alvo)
        if aceita(l):
            leads.append(l)

    n_cel = n_fixo = n_social = 0
    for l in leads:
        c = l["canal"]
        if c in ("whatsapp", "whatsapp_provavel"):
            n_cel += 1
        elif c == "ligacao":
            n_fixo += 1
        else:
            n_social += 1

    # ordena pela prioridade de abordagem e corta no limite
    leads.sort(key=lambda l: (PESO_CANAL.get(l["canal"], 8), l["nome"].lower()))
    leads = leads[:limite]
    return leads, ("%s (raio %sm): %d achados, %d com site, %d com fone | "
                   "%d ALVOS | %d celular, %d so fixo, %d so rede social" % (
                       geo_q, raio, len(achados), len(com_site), len(com_fone),
                       len(leads), n_cel, n_fixo, n_social))


def migra_lead(l):
    """Reclassifica lead salvo no formato antigo.

    A base atual foi gerada com 'fone_real': True em tudo. Na primeira
    varredura com o motor novo, os leads antigos ainda carregam essa
    marca falsa. Aqui eles sao reclassificados pelo numero real.
    """
    if l.get("canal"):
        return l  # ja esta no formato novo
    info = parse_br(l.get("fone_bruto") or l.get("fone"))
    l["tipo_fone"] = info["tipo"]
    l["motivo_fone"] = info.get("motivo", "")
    l["fone_real"] = info["tipo"] in (T_CELULAR, T_ANTIGO)
    l["fone_ok"] = info["tipo"] != T_INVALIDO
    l["redes"] = l.get("redes") or {}
    l["status_site"] = l.get("status_site") or "sem_presenca"
    canal = escolhe_canal(info, l["redes"], None)
    l["canal"] = canal["canal"]
    l["canal_rotulo"] = canal["rotulo"]
    l["confianca"] = canal["confianca"]
    l["alternativas"] = canal["alternativas"]
    if l["canal"] not in ("whatsapp", "whatsapp_provavel"):
        l["wa_link"] = ""
    return l


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
    vistos, vistos_nome, unicos = set(), set(), []
    for l in todos:
        chave = l.get("fone") or (l["nome"] or "").lower()
        nomecid = (l["nome"] or "").lower().strip() + "|" + (l.get("cidade") or "").lower()
        if chave in vistos or nomecid in vistos_nome:
            continue
        vistos.add(chave)
        vistos_nome.add(nomecid)
        unicos.append(l)

    # une com a base anterior (o arquivo nunca regride)
    try:
        with open(os.path.join(BASE, "leads-latest.json"), encoding="utf-8") as f:
            antigos = json.load(f).get("leads", [])
        for l in antigos:
            if not l.get("fone"):
                continue  # descarta lead antigo sem telefone
            l = migra_lead(l)
            if l.get("canal") == "sem_contato":
                continue  # sem telefone e sem rede: nao da para abordar
            chave = l.get("fone")
            nomecid = (l["nome"] or "").lower().strip() + "|" + (l.get("cidade") or "").lower()
            if chave in vistos or nomecid in vistos_nome:
                continue
            vistos.add(chave)
            vistos_nome.add(nomecid)
            unicos.append(l)
    except Exception:
        pass

    cidades_alvo = [a["cidade"].split(",")[0].strip().lower() for a in cfg["alvos"]]
    unicos = [l for l in unicos
              if any(c in (l.get("cidade", "") or "").lower() for c in cidades_alvo)]

    # ordena por prioridade de abordagem e corta
    unicos.sort(key=lambda l: (PESO_CANAL.get(l.get("canal"), 8), l.get("nome", "").lower()))
    payload = {"varredura": varredura, "total": len(unicos), "leads": unicos[:600]}
    with open(os.path.join(BASE, "leads-latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    hist = os.path.join(BASE, "historico")
    os.makedirs(hist, exist_ok=True)
    dia = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(os.path.join(hist, "leads-%s.json" % dia), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    # resumo por canal: e isso que diz quem da para abordar e como
    canais = {}
    for l in unicos:
        c = l.get("canal") or "sem_contato"
        canais[c] = canais.get(c, 0) + 1
    print("VARREDURA " + varredura)
    for m in resumo:
        print(" - " + m)
    print("TOTAL ALVOS: %d" % len(unicos))
    print("POR CANAL:")
    for k, v in sorted(canais.items(), key=lambda x: -x[1]):
        print("   %-18s %d" % (k, v))
    wa = sum(1 for l in unicos if l.get("fone_real"))
    print("ALVOS COM WHATSAPP POSSIVEL: %d de %d" % (wa, len(unicos)))


if __name__ == "__main__":
    main()
