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


def sondar_url(url: str, obter: Callable) -> dict:
    try:
        r = obter(url)
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
        "amostra": texto[:AMOSTRA_BYTES],
    }


def sondar(obter: Callable, destino: Path, ids: list[str] | None = None) -> dict:
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    destino.mkdir(parents=True, exist_ok=True)
    resumo: dict = {"executado_em": agora, "fontes": {}}
    for f in carregar_fontes():
        if ids and f["id"] not in ids:
            continue
        resultados = [{**sondar_url(s["url"], obter), "origem": s["origem"]} for s in f["sondar"]]
        (destino / f"{f['id']}.json").write_text(
            json.dumps({"fonte": f["id"], "nome": f["nome"], "executado_em": agora, "resultados": resultados},
                       ensure_ascii=False, indent=2), "utf-8")
        resumo["fontes"][f["id"]] = [
            {"url": r["url"], "ok": r["ok"], "status": r.get("status"), "erro": r.get("erro")} for r in resultados
        ]
    (destino / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), "utf-8")
    return resumo
