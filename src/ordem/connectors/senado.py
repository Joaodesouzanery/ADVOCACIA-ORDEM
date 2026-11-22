"""Senado – API de Dados Abertos Legislativos: identificação oficial e histórico de alterações.

Conferido na sondagem de 22/11/2026: `GET /dadosabertos/legislacao/urn?urn=<URN>` (Accept: application/json)
devolve `DetalheDocumento` com identificação (normaNome, apelido, urlDocumento em normas.leg.br),
publicações e, em `disps.disp[]`, a lista de dispositivos que sofreram alteração (nomeDispositivo +
refs[{dispositivo, comentario, codNormaPosterior}]). **A API NÃO traz o texto dos artigos**: o texto
continua pendente (Planalto bloqueia o Actions; LexML tem anti-robô). Aqui só entra o que é confirmado.
"""

from __future__ import annotations

import json
import re
from typing import Callable

BASE = "https://legis.senado.leg.br/dadosabertos"
_ART = re.compile(r"^Art\.?\s*(\d[\d\.]*)", re.IGNORECASE)


def url_por_urn(urn: str) -> str:
    return f"{BASE}/legislacao/urn?urn={urn}"


def _lista(v) -> list:
    """A API (XML→JSON) devolve objeto quando há 1 item e lista quando há vários."""
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def numero_do_artigo(nome_dispositivo: str) -> int | None:
    m = _ART.match((nome_dispositivo or "").strip())
    return int(m.group(1).replace(".", "")) if m else None


def parse_detalhe(dados: dict) -> dict:
    docs = _lista(dados["DetalheDocumento"]["documentos"]["documento"])
    if not docs:
        raise ValueError("resposta sem documento")
    d = docs[0]
    ident = d.get("identificacao") or {}
    alteracoes: dict[str, list[dict]] = {}
    for disp in _lista((d.get("disps") or {}).get("disp")):
        n = numero_do_artigo(disp.get("nomeDispositivo", ""))
        if n is None:
            continue
        for ref in _lista((disp.get("refs") or {}).get("ref")):
            alteracoes.setdefault(str(n), []).append({
                "dispositivo": disp.get("nomeDispositivo", "").strip(),
                "por": (ref.get("dispositivo") or "").strip(),
                "comentario": (ref.get("comentario") or "").strip(),
            })
    return {
        "id_senado": d.get("id"),
        "norma_nome": ident.get("normaNome"),
        "apelido": ident.get("apelido"),
        "ementa": d.get("ementa"),
        "data_assinatura": ident.get("dataassinatura"),
        "url_documento": ident.get("urlDocumento"),
        "publicacoes": [
            {"fonte": (p.get("fonte") or "").strip(), "data": p.get("data"), "url": p.get("urlPubOficial")}
            for p in _lista((d.get("publicacoes") or {}).get("publicacao"))
        ],
        "alteracoes_por_artigo": alteracoes,
    }


def ingerir_senado(normas: list[dict], obter: Callable, agora: str) -> dict:  # pragma: no cover - requer rede
    saida: dict = {"coletado_em": agora, "fonte": f"{BASE}/legislacao/urn", "normas": {}}
    for n in normas:
        try:
            r = obter(url_por_urn(n["urn"]), cabecalhos={"Accept": "application/json"})
            if r.status != 200:
                raise ConnectionError(f"HTTP {r.status}")
            saida["normas"][n["id"]] = {"status": "ok", "urn": n["urn"], **parse_detalhe(json.loads(r.texto()))}
        except Exception as e:  # noqa: BLE001
            saida["normas"][n["id"]] = {"status": "erro", "urn": n["urn"], "erro": f"{type(e).__name__}: {e}"}
    return saida
