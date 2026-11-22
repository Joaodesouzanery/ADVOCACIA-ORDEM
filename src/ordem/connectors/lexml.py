"""LexML / Senado: identificação de normas por URN e links oficiais.

O texto por artigo ainda NÃO é obtido aqui: o formato das respostas (Senado/LexML)
só será conhecido após a sondagem real no GitHub Actions (`ordem sondar`).
Até lá, este módulo só monta URN e URLs de consulta (sem inventar campos de resposta).
"""

from __future__ import annotations

import re
from urllib.parse import quote

_URN = re.compile(r"^urn:lex:br:federal:(lei|constituicao|decreto|decreto\.lei|lei\.complementar):[\d\-]+;\d+$")


def urn_valida(urn: str) -> bool:
    return bool(_URN.match(urn))


def url_busca_sru(urn: str, maximo: int = 1) -> str:
    """Consulta SRU do LexML por URN exata (endpoint candidato: validar na sondagem)."""
    if not urn_valida(urn):
        raise ValueError(f"URN fora do padrão esperado: {urn!r}")
    q = quote(f'urn exact "{urn}"')
    return f"https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&version=1.1&query={q}&maximumRecords={maximo}"


def url_resolver(urn: str) -> str:
    """Link de resolução oficial (apenas para conferência humana)."""
    if not urn_valida(urn):
        raise ValueError(f"URN fora do padrão esperado: {urn!r}")
    return f"https://www.lexml.gov.br/{urn}"
