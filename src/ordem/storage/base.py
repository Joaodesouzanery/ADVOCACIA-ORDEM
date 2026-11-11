"""Interface de armazenamento (troca SQLite -> Supabase sem mexer em conectores/MCP)."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

_NUM = re.compile(r"(\d[\d\.]*)")


def numero_artigo(caminho: str) -> int | None:
    """'Art. 1.583' -> 1583; 'Art. 33-A' -> 33; sem número -> None."""
    m = _NUM.search(caminho)
    if not m:
        return None
    digitos = m.group(1).replace(".", "")
    return int(digitos) if digitos else None


@dataclass(frozen=True)
class Registro:
    norma_id: str  # ex.: "cc"
    norma: str  # nome legível
    caminho: str  # "Art. 1.583"
    numero: int | None
    texto: str
    url_oficial: str
    fonte: str
    coletado_em: str  # ISO-8601

    def como_dict(self) -> dict:
        return {
            "norma_id": self.norma_id,
            "norma": self.norma,
            "caminho": self.caminho,
            "texto": self.texto,
            "url_oficial": self.url_oficial,
            "fonte": self.fonte,
            "coletado_em": self.coletado_em,
        }


class Repositorio(ABC):
    @abstractmethod
    def upsert(self, registros: Iterable[Registro]) -> int: ...

    @abstractmethod
    def buscar(self, consulta: str, limite: int = 10, norma_id: str | None = None) -> list[Registro]: ...

    @abstractmethod
    def obter_intervalo(self, norma_id: str, inicio: int, fim: int) -> list[Registro]: ...

    @abstractmethod
    def todos(self, norma_id: str | None = None) -> list[Registro]: ...

    @abstractmethod
    def contagem(self) -> dict[str, int]: ...
