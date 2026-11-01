"""Consulta ao mapa curado pedido -> fundamentos (M0).

No M1 isto passa a consultar o Supabase (busca híbrida) e devolve o TEXTO oficial
ingerido. Enquanto isso, devolve apenas referências marcadas como NÃO VERIFICADAS.
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from importlib import resources

STATUS_NAO_VERIFICADO = (
    "Referência curada, NÃO verificada contra o texto oficial. "
    "Conferir na fonte (Planalto/Senado/STJ) e com advogado antes de citar."
)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


@lru_cache(maxsize=1)
def _pedidos() -> dict:
    txt = resources.files("ordem.data").joinpath("pedidos_familia.json").read_text("utf-8")
    return json.loads(txt)["pedidos"]


def listar_pedidos() -> list[str]:
    return sorted(_pedidos())


def identificar_pedido(texto: str) -> str | None:
    """Mapeia texto livre ('quero a guarda do meu filho') para um tipo de pedido."""
    alvo = _norm(texto)
    melhor, pontos = None, 0
    for chave, dados in _pedidos().items():
        p = sum(1 for kw in dados["palavras_chave"] if _norm(kw) in alvo)
        if _norm(chave) in alvo:
            p += 2
        if p > pontos:
            melhor, pontos = chave, p
    return melhor


def artigos_para_pedido(tipo_pedido: str) -> dict:
    chave = tipo_pedido if tipo_pedido in _pedidos() else identificar_pedido(tipo_pedido)
    if chave is None:
        return {"erro": f"Pedido não reconhecido: {tipo_pedido!r}", "disponiveis": listar_pedidos()}
    d = _pedidos()[chave]
    return {
        "pedido": chave,
        "descricao": d["descricao"],
        "dispositivos": d["dispositivos"],
        "sumulas": d["sumulas"],
        "prazos_relacionados": d["prazos_relacionados"],
        "status": STATUS_NAO_VERIFICADO,
    }


def checklist_documentos(tipo_pedido: str) -> dict:
    chave = tipo_pedido if tipo_pedido in _pedidos() else identificar_pedido(tipo_pedido)
    if chave is None:
        return {"erro": f"Pedido não reconhecido: {tipo_pedido!r}", "disponiveis": listar_pedidos()}
    d = _pedidos()[chave]
    return {
        "pedido": chave,
        "documentos": d["documentos"],
        "perguntas_ao_cliente": d["perguntas_ao_cliente"],
    }
