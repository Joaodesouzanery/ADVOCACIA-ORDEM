"""Parsing do CKAN (portal de dados abertos do STJ e similares).

A API de ação do CKAN é padrão (`/api/3/action/package_list`, `package_show`).
Funções puras recebem o JSON já decodificado; rede fica em `listar_pacotes`/`recursos`.
Se o portal do STJ não expuser a API, a sondagem mostrará e trocamos para os links de recurso.
"""

from __future__ import annotations

import json
from typing import Callable

CKAN_ACTION = "/api/3/action/"


def pacotes_da_lista(dados: dict) -> list[str]:
    if not dados.get("success"):
        raise ValueError("resposta CKAN com success=false")
    return list(dados["result"])


def recursos_do_pacote(dados: dict) -> list[dict]:
    """Normaliza os recursos baixáveis de um `package_show`."""
    if not dados.get("success"):
        raise ValueError("resposta CKAN com success=false")
    pacote = dados["result"]
    return [
        {
            "pacote": pacote.get("name"),
            "titulo_pacote": pacote.get("title"),
            "recurso": r.get("name") or r.get("id"),
            "formato": (r.get("format") or "").lower(),
            "url": r.get("url"),
            "modificado": r.get("last_modified") or r.get("created"),
        }
        for r in pacote.get("resources", [])
        if r.get("url")
    ]


def listar_pacotes(base: str, obter: Callable) -> list[str]:  # pragma: no cover - requer rede
    r = obter(base.rstrip("/") + CKAN_ACTION + "package_list")
    r_ok = r.status == 200
    if not r_ok:
        raise ConnectionError(f"CKAN package_list HTTP {r.status}")
    return pacotes_da_lista(json.loads(r.texto()))


def recursos(base: str, pacote: str, obter: Callable) -> list[dict]:  # pragma: no cover - requer rede
    r = obter(f"{base.rstrip('/')}{CKAN_ACTION}package_show?id={pacote}")
    if r.status != 200:
        raise ConnectionError(f"CKAN package_show HTTP {r.status}")
    return recursos_do_pacote(json.loads(r.texto()))
