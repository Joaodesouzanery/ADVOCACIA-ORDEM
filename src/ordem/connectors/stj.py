"""STJ (dados abertos, CKAN): espelhos de acórdãos e precedentes qualificados, só Família.

Formatos conferidos na sondagem de 22/11/2026 (GitHub Actions):
- Espelhos: ZIP inicial (histórico) + JSON mensal; cada arquivo é uma lista de objetos com
  id, numeroProcesso, numeroRegistro, siglaClasse, descricaoClasse, nomeOrgaoJulgador,
  ministroRelator, dataPublicacao, ementa, tipoDeDecisao, dataDecisao (AAAAMMDD)...
  Meses sem lançamento trazem um objeto com "Obs" e id vazio (ignorado).
- Precedentes: `Temas.csv` e `Processos.csv` (há versões duplicadas; vale a mais recente),
  ligados por `sequencialPrecedente`. Separador do CSV é detectado pelo cabeçalho.
O histórico completo NÃO é guardado: só ementas que casam com os temas de Família.
"""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
import zipfile
from datetime import datetime, timezone
from typing import Callable, Iterable, Iterator

from ..storage.jurisprudencia import Julgado, RepositorioJurisprudencia
from .ckan import recursos

BASE = "https://dadosabertos.web.stj.jus.br"
PACOTES_ESPELHOS_FAMILIA = [
    "espelhos-de-acordaos-terceira-turma",
    "espelhos-de-acordaos-quarta-turma",
    "espelhos-de-acordaos-segunda-secao",
]
PACOTE_PRECEDENTES = "precedentes-qualificados"

# tema -> termos (comparados sem acento e em minúsculas). Escolha editorial, revisável.
TEMAS_FAMILIA: dict[str, list[str]] = {
    "guarda": ["guarda compartilhada", "guarda unilateral", "guarda de menor", "guarda do filho",
               "guarda dos filhos", "regime de guarda", "alienacao parental"],
    "convivencia": ["convivencia familiar", "direito de visita", "regime de visitas", "visitacao"],
    "alimentos": ["alimentos", "pensao alimenticia", "obrigacao alimentar", "execucao de alimentos",
                  "binomio necessidade"],
    "divorcio": ["divorcio", "dissolucao do casamento", "partilha de bens", "uniao estavel"],
    "poder_familiar": ["poder familiar", "destituicao do poder", "adocao", "filiacao", "paternidade"],
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def temas_do_texto(texto: str) -> list[str]:
    alvo = _norm(texto)
    return [t for t, termos in TEMAS_FAMILIA.items() if any(x in alvo for x in termos)]


def _data_iso(valor: str) -> str:
    valor = (valor or "").strip()
    if re.fullmatch(r"\d{8}", valor):
        return f"{valor[:4]}-{valor[4:6]}-{valor[6:]}"
    return valor


def ler_json_espelho(conteudo: bytes) -> list[dict]:
    dados = json.loads(conteudo.decode("utf-8-sig"))
    return dados if isinstance(dados, list) else []


def ler_zip_espelhos(conteudo: bytes) -> Iterator[list[dict]]:
    """O ZIP inicial contém vários .json; devolve a lista de cada um."""
    with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
        for nome in z.namelist():
            if nome.lower().endswith(".json"):
                yield ler_json_espelho(z.read(nome))


def julgados_do_espelho(registros: Iterable[dict], url_fonte: str, coletado_em: str) -> Iterator[Julgado]:
    for r in registros:
        if not r.get("id") or r.get("Obs"):  # mês sem lançamento
            continue
        ementa = (r.get("ementa") or "").strip()
        temas = temas_do_texto(ementa)
        if not ementa or not temas:
            continue
        yield Julgado(
            tipo="acordao", tribunal="STJ", fonte_id=str(r["id"]),
            orgao=r.get("nomeOrgaoJulgador") or "", classe=r.get("siglaClasse") or "",
            processo=f"{r.get('siglaClasse') or ''} {r.get('numeroProcesso') or ''}".strip(),
            registro=r.get("numeroRegistro") or "", relator=r.get("ministroRelator") or "",
            data=_data_iso(r.get("dataDecisao") or ""), ementa=ementa, temas=";".join(temas),
            url_oficial=url_fonte, coletado_em=coletado_em)


def escolher_recursos_espelho(lista: list[dict]) -> list[dict]:
    """Mantém ZIP e JSON (descarta o dicionário CSV); em nomes repetidos fica o mais recente."""
    por_nome: dict[str, dict] = {}
    for r in lista:
        if r["formato"] not in ("zip", "json"):
            continue
        atual = por_nome.get(r["recurso"])
        if atual is None or (r.get("modificado") or "") > (atual.get("modificado") or ""):
            por_nome[r["recurso"]] = r
    return sorted(por_nome.values(), key=lambda r: r["recurso"])


def _ler_csv(texto: str) -> list[dict]:
    texto = texto.lstrip("﻿")
    cabecalho = texto.split("\n", 1)[0]
    delim = ";" if cabecalho.count(";") > cabecalho.count(",") else ","
    return list(csv.DictReader(io.StringIO(texto), delimiter=delim))


def escolher_mais_recente(lista: list[dict], nome: str) -> dict | None:
    cand = [r for r in lista if (r["recurso"] or "").lower() == nome.lower() and r["formato"] == "csv"]
    return max(cand, key=lambda r: r.get("modificado") or "") if cand else None


def precedentes_de_familia(temas_csv: str, processos_csv: str, url_fonte: str,
                           coletado_em: str) -> Iterator[Julgado]:
    """Junta Temas e Processos por sequencialPrecedente e filtra por tema de Família."""
    procs: dict[str, list[dict]] = {}
    for p in _ler_csv(processos_csv):
        procs.setdefault(p.get("sequencialPrecedente", ""), []).append(p)
    for t in _ler_csv(temas_csv):
        seq = t.get("sequencialPrecedente", "")
        texto = " ".join(filter(None, [t.get("questaoSubmetidaAJulgamento"), t.get("teseFirmada")]))
        temas = temas_do_texto(texto)
        if not seq or not temas:
            continue
        ps = procs.get(seq, [])
        lead = next((p for p in ps if (p.get("leadingCase") or "").strip().upper() == "S"), ps[0] if ps else {})
        tese = (t.get("teseFirmada") or "").strip()
        ementa = f"Questão: {(t.get('questaoSubmetidaAJulgamento') or '').strip()}" + (f"\nTese: {tese}" if tese else "")
        yield Julgado(
            tipo="precedente", tribunal="STJ", fonte_id=seq, orgao=t.get("tipoPrecedente") or "",
            classe=f"{t.get('tipoPrecedente') or ''} {t.get('numeroPrecedente') or ''}".strip(),
            processo=(lead.get("Processo") or "").strip(), registro=(lead.get("numeroRegistro") or "").strip(),
            relator=(lead.get("ministroRelator") or "").strip(), data=t.get("dataJulgamento") or "",
            ementa=ementa, temas=";".join(temas), url_oficial=url_fonte, coletado_em=coletado_em)


def agora() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ingerir_stj(repo: RepositorioJurisprudencia, obter: Callable, pacotes: list[str] | None = None,
                incluir_precedentes: bool = True) -> dict:  # pragma: no cover - requer rede
    """Baixa os recursos reais do CKAN, filtra Família e grava. Erro num arquivo não para os demais."""
    quando = agora()
    rel: dict = {"executado_em": quando, "recursos": {}}

    def baixar(url: str) -> bytes:
        r = obter(url, tentativas=3, timeout=300)
        if r.status != 200:
            raise ConnectionError(f"HTTP {r.status}")
        return r.conteudo

    for pacote in pacotes or PACOTES_ESPELHOS_FAMILIA:
        try:
            lista = escolher_recursos_espelho(recursos(BASE, pacote, obter))
        except Exception as e:  # noqa: BLE001
            rel["recursos"][pacote] = {"status": "erro", "erro": f"{type(e).__name__}: {e}"}
            continue
        for rec in lista:
            chave = f"{pacote}/{rec['recurso']}"
            try:
                bruto = baixar(rec["url"])
                partes = ler_zip_espelhos(bruto) if rec["formato"] == "zip" else [ler_json_espelho(bruto)]
                n = sum(repo.upsert(julgados_do_espelho(p, rec["url"], quando)) for p in partes)
                rel["recursos"][chave] = {"status": "ok", "gravados": n}
            except Exception as e:  # noqa: BLE001
                rel["recursos"][chave] = {"status": "erro", "erro": f"{type(e).__name__}: {e}"}
    if incluir_precedentes:
        try:
            lista = recursos(BASE, PACOTE_PRECEDENTES, obter)
            t, p = escolher_mais_recente(lista, "Temas.csv"), escolher_mais_recente(lista, "Processos.csv")
            if not (t and p):
                raise ValueError("Temas.csv/Processos.csv não encontrados")
            n = repo.upsert(precedentes_de_familia(baixar(t["url"]).decode("utf-8-sig", "replace"),
                                                   baixar(p["url"]).decode("utf-8-sig", "replace"), t["url"], quando))
            rel["recursos"][PACOTE_PRECEDENTES] = {"status": "ok", "gravados": n}
        except Exception as e:  # noqa: BLE001
            rel["recursos"][PACOTE_PRECEDENTES] = {"status": "erro", "erro": f"{type(e).__name__}: {e}"}
    return rel
