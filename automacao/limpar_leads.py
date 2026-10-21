#!/usr/bin/env python3
"""Limpa a base de leads: tira instituicao publica e o que esta fora da regiao.

Uso: python automacao/limpar_leads.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prospectar import eh_publico  # noqa: E402

BASE = Path(__file__).resolve().parent
LEADS = BASE / "leads-latest.json"
ALVOS = BASE / "alvos.json"


def main() -> int:
    cfg = json.loads(ALVOS.read_text(encoding="utf-8"))
    cidades = [a["cidade"].split(",")[0].strip().lower() for a in cfg["alvos"]]

    dados = json.loads(LEADS.read_text(encoding="utf-8"))
    leads = dados.get("leads", [])

    antes = len(leads)
    fora = [l for l in leads if not any(c in (l.get("cidade") or "").lower() for c in cidades)]
    publics = [l for l in leads if eh_publico(l.get("nome"))]
    sem_fone = [l for l in leads if not l.get("fone")]

    limpados = [l for l in leads
                if any(c in (l.get("cidade") or "").lower() for c in cidades)
                and not eh_publico(l.get("nome"))
                and l.get("fone")]

    # dedup por telefone
    vistos, unicos = set(), []
    for l in limpados:
        if l["fone"] in vistos:
            continue
        vistos.add(l["fone"])
        unicos.append(l)

    dados["leads"] = unicos
    dados["total"] = len(unicos)
    LEADS.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"leads antes      : {antes}")
    print(f"fora da regiao   : {len(fora)}")
    print(f"instituicao publica: {len(publics)}")
    print(f"sem telefone     : {len(sem_fone)}")
    print(f"duplicados (fone): {len(limpados) - len(unicos)}")
    print(f"leads finais     : {len(unicos)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
