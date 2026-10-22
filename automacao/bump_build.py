#!/usr/bin/env python3
"""Sobe a versao do app (PC e celular) em 1 comando.

Por que existe: o celular so percebe a versao nova olhando o arquivo
versao.json. Se o BUILD do index.html e o build do versao.json ficarem
diferentes, o celular nunca avisa que ha update (ou avisa sempre).

Uso:
    python automacao/bump_build.py           # so mostra a versao atual
    python automacao/bump_build.py           # sobe para a versao de hoje
    python automacao/bump_build.py 2026.10.22-2   # sobe para a versao exata

Depois é só commitar e dar push: o GitHub Pages publica e o celular
atualiza sozinho (ou pelo botao 🔄 Atualizar).
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
INDEX = RAIZ / "index.html"
VERSAO = RAIZ / "versao.json"
SW = RAIZ / "sw.js"


def build_atual() -> str:
    m = re.search(r"const BUILD='([^']+)'", INDEX.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def proximo_build(atual: str) -> str:
    hoje = dt.date.today()
    try:
        data_antiga, n = atual.split("-")
        y, m, d = (int(x) for x in data_antiga.split("."))
        antigo = dt.date(y, m, d)
        n = int(n)
    except Exception:
        antigo, n = None, 0
    if antigo == hoje:
        return f"{hoje:%Y.%m.%d}-{n + 1}"
    return f"{hoje:%Y.%m.%d}-1"


def aplicar(novo: str) -> None:
    # 1) index.html
    t = INDEX.read_text(encoding="utf-8")
    t = re.sub(r"const BUILD='[^']*'", f"const BUILD='{novo}'", t, count=1)
    INDEX.write_text(t, encoding="utf-8")

    # 2) versao.json (o que o celular consulta)
    dados = {"build": novo, "data": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "nota": "Atualizacao do app: o celular confere este arquivo, avisa quando ha versao nova e o botao Atualizar limpa o cache."}
    VERSAO.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 3) sw.js - sobe o nome do cache para o service worker antigo ser descartado
    s = SW.read_text(encoding="utf-8")

    def bump(m: re.Match) -> str:
        return f"const CACHE='rick-digital-v{int(m.group(1)) + 1}'"

    s2 = re.sub(r"const CACHE='rick-digital-v(\d+)'", bump, s, count=1)
    SW.write_text(s2, encoding="utf-8")
    cache = re.search(r"rick-digital-v\d+", s2)
    print(f"OK - build {novo} | cache do service worker: {cache.group(0) if cache else '?'}")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    atual = build_atual()
    if "--so-mostrar" in sys.argv and not args:
        print(f"build atual: {atual}")
        return 0
    novo = args[0] if args else proximo_build(atual)
    if novo == atual:
        print(f"ja esta na versao {atual}")
        return 0
    aplicar(novo)
    print(f"antes: {atual}  ->  agora: {novo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
