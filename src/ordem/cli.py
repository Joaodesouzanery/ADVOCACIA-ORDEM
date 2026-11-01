"""CLI mínima: `ordem prazo contestacao 2026-03-02`, `ordem pedido guarda`."""

from __future__ import annotations

import argparse
import json
from datetime import date

from . import knowledge
from .prazos import calcular_prazo


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ordem")
    sub = p.add_subparsers(dest="cmd", required=True)
    pz = sub.add_parser("prazo", help="calcula vencimento")
    pz.add_argument("regra")
    pz.add_argument("inicio", help="AAAA-MM-DD")
    pz.add_argument("--dobro", action="store_true")
    pd = sub.add_parser("pedido", help="fundamentos candidatos para um pedido")
    pd.add_argument("tipo")
    a = p.parse_args(argv)

    if a.cmd == "prazo":
        r = calcular_prazo(a.regra, date.fromisoformat(a.inicio), em_dobro=a.dobro)
        print(f"{r.regra.ato}: vence em {r.vencimento.isoformat()} ({r.dias_efetivos} dias {r.regra.tipo})")
        for av in r.avisos:
            print(f"! {av}")
    else:
        print(json.dumps(knowledge.artigos_para_pedido(a.tipo), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
