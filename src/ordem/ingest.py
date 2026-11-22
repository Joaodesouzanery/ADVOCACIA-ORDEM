"""Ingestão do corpus (letra da lei) a partir do Planalto.

Roda no GitHub Actions/local (o sandbox de desenvolvimento não alcança as fontes).
Falha em uma norma não interrompe as demais; o relatório registra tudo.
"""

from __future__ import annotations

import json
import unicodedata
from datetime import datetime, timezone
from functools import lru_cache
from importlib import resources
from typing import Callable

from .connectors.planalto import extrair_artigos
from .storage import Registro, Repositorio, numero_artigo


@lru_cache(maxsize=1)
def carregar_normas() -> list[dict]:
    txt = resources.files("ordem.data").joinpath("normas.json").read_text("utf-8")
    return json.loads(txt)["normas"]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def norma_por_nome(nome: str) -> dict | None:
    """Liga o nome usado no mapa curado (ex.: 'CPC (Lei 13.105/2015)') a uma norma do catálogo."""
    alvo = _norm(nome)
    for n in carregar_normas():
        if any(_norm(a) in alvo for a in n["aliases"]):
            return n
    return None


def ingerir(
    repo: Repositorio,
    baixar: Callable[[str], str],
    ids: list[str] | None = None,
) -> dict:
    """Baixa e grava cada norma. `baixar(url) -> html` é injetável (testes usam fixture)."""
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    relatorio: dict = {"executado_em": agora, "normas": {}}
    for n in carregar_normas():
        if ids and n["id"] not in ids:
            continue
        try:
            artigos = extrair_artigos(baixar(n["url"]))
            if not artigos:
                raise ValueError("nenhum artigo reconhecido no HTML (layout mudou?)")
            regs = [
                Registro(n["id"], n["nome"], caminho, numero_artigo(caminho), corpo, n["url"], "planalto", agora)
                for caminho, corpo in artigos
            ]
            relatorio["normas"][n["id"]] = {"status": "ok", "artigos": repo.upsert(regs), "url": n["url"]}
        except Exception as e:  # noqa: BLE001 - registrar e seguir
            relatorio["normas"][n["id"]] = {"status": "erro", "erro": f"{type(e).__name__}: {e}", "url": n["url"]}
    return relatorio
