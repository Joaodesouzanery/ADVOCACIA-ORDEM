"""Interface comum dos conectores de dados abertos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class Dispositivo:
    """Um artigo/parágrafo ingerido de uma norma, com rastreabilidade."""

    norma: str  # ex.: "Lei 10.406/2002"
    caminho: str  # ex.: "art. 1.583"
    texto: str
    url_oficial: str
    fonte: str  # ex.: "planalto"


class Conector(ABC):
    nome: str

    @abstractmethod
    def fetch(self) -> Iterator[Dispositivo]:
        """Itera registros normalizados. Rede só aqui; parsing fica em funções puras."""
