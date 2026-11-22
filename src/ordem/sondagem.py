"""Sondagem das fontes: 1 requisição leve por URL, grava status/formato/amostra.

É assim que validamos endpoints sem acesso local: roda no GitHub Actions
(`sondagem.yml`) e o relatório volta commitado em `data/sondagem/`. Nada aqui
declara uma fonte 'verificada': quem decide é a pessoa lendo o relatório.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Callable

AMOSTRA_BYTES = 2048


@lru_cache(maxsize=1)
def carregar_fontes() -> list[dict]:
    txt = resources.files("ordem.data").joinpath("fontes.json").read_text("utf-8")
    return json.loads(txt)["fontes"]


def sondar_url(url: str, obter: Callable, cabecalhos: dict | None = None) -> dict:  # noqa: C901
    try:
        r = obter(url, cabecalhos=cabecalhos) if cabecalhos else obter(url)
    except Exception as e:  # noqa: BLE001 - registrar e seguir
        return {"url": url, "ok": False, "erro": f"{type(e).__name__}: {e}"}
    texto = r.texto()
    desafio = "html" in r.content_type.lower() and "verificação de segurança" in texto[:4000].lower()
    return {
        "url": url,
        "url_final": r.url,
        "status": r.status,
        "ok": 200 <= r.status < 300 and not desafio,
        "desafio_antirrobo": desafio,  # página de verificação: NÃO contornar
        "content_type": r.content_type,
        "bytes": len(r.conteudo),
        "magic_hex": r.conteudo[:4].hex(),  # ex.: 504b0304 = ZIP
        "amostra": texto[:AMOSTRA_BYTES],
    }


def sondar_openapi(url: str, obter: Callable) -> dict:
    """Baixa a especificação OpenAPI e guarda só (caminho, métodos, resumo): a spec inteira é grande."""
    try:
        r = obter(url)
        spec = json.loads(r.texto())
        caminhos = [
            {"caminho": c, "metodos": sorted(m for m in ops if m in ("get", "post", "put", "delete")),
             "parametros": [{"nome": x.get("name"), "em": x.get("in"), "obrigatorio": x.get("required", False)}
                            for o in ops.values() if isinstance(o, dict)
                            for x in o.get("parameters", []) if isinstance(x, dict)],
             "produz": sorted({t for o in ops.values() if isinstance(o, dict)
                               for resp in (o.get("responses", {}).get("200") or {},)
                               for t in (resp.get("content") or {})}),
             "resumo": next((o.get("summary") or o.get("operationId") or "" for o in ops.values()
                             if isinstance(o, dict)), "")[:120]}
            for c, ops in spec.get("paths", {}).items()
        ]
    except Exception as e:  # noqa: BLE001
        return {"url": url, "ok": False, "erro": f"{type(e).__name__}: {e}"}
    return {"url": url, "ok": True, "status": r.status, "titulo": (spec.get("info") or {}).get("title"),
            "versao": (spec.get("info") or {}).get("version"),
            "servidores": [x.get("url") for x in spec.get("servers", [])],
            "num_caminhos": len(caminhos), "caminhos": caminhos}


def estrutura_json(v, profundidade: int = 7):
    """Resumo da forma de um JSON: chaves, tamanhos de listas, prévia curta de textos."""
    if profundidade == 0:
        return "..."
    if isinstance(v, dict):
        return {k: estrutura_json(x, profundidade - 1) for k, x in v.items()}
    if isinstance(v, list):
        return {"__lista__": len(v), "__item0__": estrutura_json(v[0], profundidade - 1) if v else None}
    if isinstance(v, str):
        return f"str[{len(v)}]:{v[:50]!r}"
    return v


def sondar_json_estrutura(url: str, obter: Callable, cabecalhos: dict | None = None) -> dict:
    try:
        r = obter(url, cabecalhos=cabecalhos) if cabecalhos else obter(url)
        dados = json.loads(r.texto())
    except Exception as e:  # noqa: BLE001
        return {"url": url, "ok": False, "erro": f"{type(e).__name__}: {e}"}
    return {"url": url, "ok": 200 <= r.status < 300, "status": r.status, "bytes": len(r.conteudo),
            "estrutura": estrutura_json(dados)}


_ORDEM_FORMATO = {"csv": 0, "json": 1, "zip": 2}


def sondar_pacote_ckan(base: str, pacote: str, obter: Callable, max_recursos: int = 4,
                       bytes_: int = 4096) -> dict:
    """package_show -> lista compacta de recursos + cabeçalho (Range) de alguns arquivos.

    Descobre URLs reais em vez de adivinhá-las; nunca baixa o arquivo inteiro.
    """
    url = f"{base.rstrip('/')}/api/3/action/package_show?id={pacote}"
    try:
        r = obter(url)
        dados = json.loads(r.texto())
        recursos = dados["result"]["resources"]
    except Exception as e:  # noqa: BLE001
        return {"url": url, "ok": False, "erro": f"{type(e).__name__}: {e}"}
    compactos = [
        {"nome": x.get("name"), "formato": (x.get("format") or "").lower(), "url": x.get("url"),
         "tamanho": x.get("size"), "modificado": x.get("last_modified") or x.get("created")}
        for x in recursos
        if x.get("url")
    ]
    escolhidos = sorted(compactos,
                        key=lambda c: (_ORDEM_FORMATO.get(c["formato"], 9), c["tamanho"] or 0))[:max_recursos]
    cabecalhos = [
        {**{k: c[k] for k in ("nome", "formato", "url", "tamanho")},
         **sondar_url(c["url"], obter, {"Range": f"bytes=0-{bytes_ - 1}"})}
        for c in escolhidos
    ]
    return {"url": url, "ok": True, "status": r.status, "num_recursos": len(compactos),
            "recursos": compactos, "cabecalhos": cabecalhos}


def sondar(obter: Callable, destino: Path, ids: list[str] | None = None) -> dict:
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    destino.mkdir(parents=True, exist_ok=True)
    resumo: dict = {"executado_em": agora, "fontes": {}}
    for f in carregar_fontes():
        if ids and f["id"] not in ids:
            continue
        resultados = []
        for s in f["sondar"]:
            if s.get("json_estrutura"):
                res = sondar_json_estrutura(s["url"], obter, s.get("cabecalhos"))
            elif s.get("openapi"):
                res = sondar_openapi(s["url"], obter)
            elif s.get("ckan_pacote"):
                res = sondar_pacote_ckan(s["url"], s["ckan_pacote"], obter, s.get("max_recursos", 4))
            else:
                res = sondar_url(s["url"], obter, s.get("cabecalhos"))
            resultados.append({**res, "origem": s["origem"]})
        (destino / f"{f['id']}.json").write_text(
            json.dumps({"fonte": f["id"], "nome": f["nome"], "executado_em": agora, "resultados": resultados},
                       ensure_ascii=False, indent=2), "utf-8")
        resumo["fontes"][f["id"]] = [
            {"url": r["url"], "ok": r["ok"], "status": r.get("status"), "erro": r.get("erro")} for r in resultados
        ]
    (destino / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), "utf-8")
    return resumo
