"""Consulta ao mapa curado pedido -> fundamentos.

M1: quando o corpus local (SQLite/CSV em `data/`) tiver a norma ingerida, anexa o
TEXTO oficial coletado do Planalto, com URL e data. Sem corpus: `[PENDENTE]`.
`verificado` continua falso até revisão de advogado(a).
"""

from __future__ import annotations

import json
import re
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


PENDENTE = "[PENDENTE] texto oficial ainda não ingerido (rodar a ingestão no GitHub Actions)"
MAX_TEXTOS_POR_REF = 25

_repo_cache: list = []


def _repo():
    """Corpus local (lazy). Retorna None se ainda não houve ingestão."""
    if not _repo_cache:
        from .storage import abrir_repositorio

        _repo_cache.append(abrir_repositorio())
    return _repo_cache[0]


def definir_repositorio(repo) -> None:
    """Injeta um repositório (testes / futuro Supabase)."""
    _repo_cache[:] = [repo]


def intervalos_da_ref(ref: str) -> list[tuple[int, int]] | None:
    """'arts. 1.583 a 1.590' -> [(1583,1590)]; 'arts. 19, 33 e 148' -> 3 itens;
    'art. 226, §6º' -> [(226,226)]; 'integral' -> None (norma inteira)."""
    if "integral" in ref.lower():
        return None
    limpo = re.sub(r"§\s*\d+\s*[º°o]?", " ", ref)
    toks = re.findall(r"\d[\d\.]*\d|\d|\ba\b", limpo)
    saida: list[tuple[int, int]] = []
    i = 0
    while i < len(toks):
        if toks[i] == "a":
            i += 1
            continue
        ini = int(toks[i].replace(".", ""))
        if i + 2 < len(toks) and toks[i + 1] == "a" and toks[i + 2] != "a":
            saida.append((ini, int(toks[i + 2].replace(".", ""))))
            i += 3
        else:
            saida.append((ini, ini))
            i += 1
    return saida


def textos_oficiais(norma_nome: str, ref: str) -> dict:
    from .ingest import norma_por_nome

    repo = _repo()
    norma = norma_por_nome(norma_nome)
    if repo is None or norma is None:
        return {"texto_oficial": PENDENTE}
    intervalos = intervalos_da_ref(ref)
    if intervalos is None:
        regs = repo.todos(norma["id"])
    else:
        regs = [r for a, b in intervalos for r in repo.obter_intervalo(norma["id"], a, b)]
    if not regs:
        return {"texto_oficial": PENDENTE}
    return {
        "fonte_ingerida": True,
        "url_oficial": norma["url"],
        "total_artigos": len(regs),
        "textos_oficiais": [
            {"caminho": r.caminho, "texto": r.texto, "coletado_em": r.coletado_em}
            for r in regs[:MAX_TEXTOS_POR_REF]
        ],
        **({"aviso": f"Mostrando {MAX_TEXTOS_POR_REF} de {len(regs)}; use buscar_dispositivo."}
           if len(regs) > MAX_TEXTOS_POR_REF else {}),
    }


def buscar_dispositivo(consulta: str, limite: int = 10, norma: str | None = None) -> dict:
    from .ingest import norma_por_nome

    repo = _repo()
    if repo is None:
        return {"erro": PENDENTE, "resultados": []}
    norma_id = None
    if norma:
        n = norma_por_nome(norma)
        norma_id = n["id"] if n else norma
    regs = repo.buscar(consulta, limite=limite, norma_id=norma_id)
    return {
        "consulta": consulta,
        "status": "Texto coletado do Planalto; NÃO revisado por advogado(a). Conferir antes de citar.",
        "resultados": [
            {"norma": r.norma, "caminho": r.caminho, "texto": r.texto, "url_oficial": r.url_oficial,
             "coletado_em": r.coletado_em}
            for r in regs
        ],
    }


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
        "dispositivos": [
            {**disp, **textos_oficiais(disp["norma"], disp["ref"]), "verificado": False}
            for disp in d["dispositivos"]
        ],
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
