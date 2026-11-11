"""CLI: `ordem prazo contestacao 2026-03-02`, `ordem pedido guarda`,
`ordem ingerir`, `ordem buscar "guarda compartilhada"`, `ordem exportar --xlsx`."""

from __future__ import annotations

import argparse
import os
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
    ig = sub.add_parser("ingerir", help="baixa a letra da lei do Planalto (requer rede + extra ingest)")
    ig.add_argument("normas", nargs="*", help="ids (cc, cpc, cf, eca...); vazio = todas")
    ig.add_argument("--xlsx", action="store_true", help="também gera data/corpus.xlsx")
    bu = sub.add_parser("buscar", help="busca na letra da lei ingerida")
    bu.add_argument("consulta")
    bu.add_argument("--norma")
    bu.add_argument("-n", type=int, default=10)
    ex = sub.add_parser("exportar", help="gera data/corpus.csv (e .xlsx)")
    ex.add_argument("--xlsx", action="store_true")
    so = sub.add_parser("sondar", help="1 requisição leve por fonte; grava data/sondagem/*.json (requer rede)")
    so.add_argument("fontes", nargs="*")
    a = p.parse_args(argv)

    if a.cmd == "sondar":
        from .connectors.http import obter
        from .sondagem import sondar
        from .storage import diretorio_dados

        resumo = sondar(obter, diretorio_dados() / "sondagem", ids=a.fontes or None)
        for fid, rs in resumo["fontes"].items():
            for r in rs:
                print(f"{fid}: {'OK ' if r['ok'] else 'FALHA'} {r['status'] or r['erro']}  {r['url']}")
        return 0

    if a.cmd in ("ingerir", "exportar"):
        return _ingerir_exportar(a)
    if a.cmd == "buscar":
        res = knowledge.buscar_dispositivo(a.consulta, limite=a.n, norma=a.norma)
        if res.get("erro"):
            print(res["erro"])
            return 1
        for r in res["resultados"]:
            print(f"== {r['norma']} — {r['caminho']}  ({r['url_oficial']})")
            print(r["texto"][:600] + ("..." if len(r["texto"]) > 600 else ""))
        return 0

    if a.cmd == "prazo":
        r = calcular_prazo(a.regra, date.fromisoformat(a.inicio), em_dobro=a.dobro)
        print(f"{r.regra.ato}: vence em {r.vencimento.isoformat()} ({r.dias_efetivos} dias {r.regra.tipo})")
        for av in r.avisos:
            print(f"! {av}")
    else:
        print(json.dumps(knowledge.artigos_para_pedido(a.tipo), ensure_ascii=False, indent=2))
    return 0


def _ingerir_exportar(a) -> int:
    from .storage import RepositorioSQLite, abrir_repositorio, caminho_csv, diretorio_dados
    from .storage.exportar import exportar_csv, exportar_xlsx

    dados = diretorio_dados()
    dados.mkdir(parents=True, exist_ok=True)
    repo = abrir_repositorio() or RepositorioSQLite(dados / "corpus.sqlite")
    codigo = 0
    if a.cmd == "ingerir":
        from .connectors import baixar_html
        from .ingest import ingerir

        rel = ingerir(repo, baixar_html, ids=a.normas or None)
        (dados / "ingestao_relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2), "utf-8")
        for nid, r in rel["normas"].items():
            print(f"{nid}: {r['status']} {r.get('artigos', r.get('erro', ''))}")
        codigo = 0 if any(r["status"] == "ok" for r in rel["normas"].values()) else 2
    from .storage.supabase import RepositorioSupabase

    remoto = RepositorioSupabase.do_ambiente()
    if remoto is not None and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        print(f"Supabase: {remoto.upsert(repo.todos())} dispositivos sincronizados")
    print(f"CSV: {exportar_csv(repo, caminho_csv())} dispositivos -> {caminho_csv()}")
    if a.xlsx:
        print(f"XLSX: {exportar_xlsx(repo, dados / 'corpus.xlsx')} dispositivos -> {dados / 'corpus.xlsx'}")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
