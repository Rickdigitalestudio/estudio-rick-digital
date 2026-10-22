#!/usr/bin/env python3
"""Migrar a base de leads para o formato novo da ficha (sem varrer de novo).

O motor (prospectar.py) ja grava cada lead no formato que o app usa:
telefone em E.164, segmento, empresa, origem, obs com endereco/fonte/data.
Este script aplica o mesmo formato na base que ja existe - util depois de
mudar o formato, sem esperar a varredura do dia seguinte.

Uso:
    python automacao/migrar_ficha.py            # migra e mostra o resumo
    python automacao/migrar_ficha.py --dry      # so mostra, nao grava
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prospectar import formato_app  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(BASE, "leads-latest.json")


def main() -> int:
    dry = "--dry" in sys.argv
    with open(ARQ, encoding="utf-8") as f:
        dados = json.load(f)
    leads = dados.get("leads", [])
    for l in leads:
        formato_app(l)
    dados["total"] = len(leads)
    dados["formato"] = "ficha-app-v1"
    if not dry:
        tmp = ARQ + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
        os.replace(tmp, ARQ)

    com_tel = sum(1 for l in leads if l.get("tel"))
    com_seg = sum(1 for l in leads if l.get("segmento"))
    com_obs = sum(1 for l in leads if l.get("obs"))
    print("MIGRADOS: %d leads" % len(leads))
    print("  com telefone (E.164): %d" % com_tel)
    print("  com segmento:         %d" % com_seg)
    print("  com obs preenchida:   %d" % com_obs)
    if not dry:
        print("  gravado em:", os.path.basename(ARQ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
