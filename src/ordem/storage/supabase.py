"""Repositório Supabase via PostgREST (httpx, sem SDK).

Ativado quando SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY (escrita) ou
SUPABASE_ANON_KEY (só leitura) estão no ambiente. Tabela: corpus_dispositivo
(migration supabase/migrations/0002_corpus_dispositivo.sql).
"""

from __future__ import annotations

import os
from typing import Iterable

from .base import Registro, Repositorio

TABELA = "corpus_dispositivo"
_CAMPOS = "norma_id,norma,caminho,numero,texto,url_oficial,fonte,coletado_em"


def _reg(d: dict) -> Registro:
    return Registro(d["norma_id"], d["norma"], d["caminho"], d.get("numero"), d["texto"],
                    d["url_oficial"], d["fonte"], d["coletado_em"])


class RepositorioSupabase(Repositorio):
    def __init__(self, url: str, chave: str, cliente=None, lote: int = 500):
        self.base = url.rstrip("/") + "/rest/v1"
        self.lote = lote
        if cliente is None:
            import httpx  # extra "ingest"

            cliente = httpx.Client(
                timeout=120, headers={"apikey": chave, "Authorization": f"Bearer {chave}"}
            )
        self.http = cliente

    @classmethod
    def do_ambiente(cls) -> "RepositorioSupabase | None":
        url = os.environ.get("SUPABASE_URL")
        chave = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        return cls(url, chave) if url and chave else None

    def _get(self, params: dict) -> list[dict]:
        r = self.http.get(f"{self.base}/{TABELA}", params={"select": _CAMPOS, **params})
        r.raise_for_status()
        return r.json()

    def upsert(self, registros: Iterable[Registro]) -> int:
        linhas = [{**g.como_dict(), "numero": g.numero} for g in registros]
        for i in range(0, len(linhas), self.lote):
            r = self.http.post(
                f"{self.base}/{TABELA}",
                params={"on_conflict": "norma_id,caminho"},
                headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                json=linhas[i:i + self.lote],
            )
            r.raise_for_status()
        return len(linhas)

    def buscar(self, consulta: str, limite: int = 10, norma_id: str | None = None) -> list[Registro]:
        r = self.http.post(f"{self.base}/rpc/buscar_dispositivos",
                           json={"consulta": consulta, "limite": limite, "filtro_norma": norma_id})
        r.raise_for_status()
        return [_reg(d) for d in r.json()]

    def obter_intervalo(self, norma_id: str, inicio: int, fim: int) -> list[Registro]:
        return [_reg(d) for d in self._get({"norma_id": f"eq.{norma_id}",
                                            "and": f"(numero.gte.{inicio},numero.lte.{fim})",
                                            "order": "numero,caminho"})]

    def todos(self, norma_id: str | None = None) -> list[Registro]:
        params = {"order": "norma_id,numero,caminho"}
        if norma_id:
            params["norma_id"] = f"eq.{norma_id}"
        return [_reg(d) for d in self._get(params)]

    def contagem(self) -> dict[str, int]:
        saida: dict[str, int] = {}
        for r in self.todos():
            saida[r.norma_id] = saida.get(r.norma_id, 0) + 1
        return saida
