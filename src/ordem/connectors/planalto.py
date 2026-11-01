"""Parser de textos compilados do Planalto (HTML) em artigos.

`dividir_artigos` é função pura (testável offline). O download real roda no
ambiente de ingestão (GitHub Actions/local), pois o sandbox de desenvolvimento
não alcança planalto.gov.br.
"""

from __future__ import annotations

import html
import re
from typing import Iterator

from .base import Conector, Dispositivo

_TAG = re.compile(r"<[^>]+>")
# "Art. 1.583." / "Art. 5º" / "Art. 33-A." no início de linha
_ART = re.compile(r"^\s*(Art\.\s*\d[\d\.]*\s*(?:º|°|o)?(?:-[A-Z])?)\s*[\.\-–]?\s", re.MULTILINE)


def html_para_texto(conteudo: str) -> str:
    conteudo = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>", "\n", conteudo)
    conteudo = _TAG.sub("", conteudo)
    conteudo = html.unescape(conteudo).replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", conteudo)


def dividir_artigos(texto: str) -> list[tuple[str, str]]:
    """Retorna [(caminho, texto_do_artigo)] preservando parágrafos/incisos no corpo."""
    marcas = list(_ART.finditer(texto))
    saida = []
    for i, m in enumerate(marcas):
        fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        caminho = re.sub(r"\s+", " ", m.group(1)).strip().rstrip(".")
        corpo = texto[m.start():fim].strip()
        saida.append((caminho, corpo))
    return saida


class PlanaltoConector(Conector):
    nome = "planalto"

    def __init__(self, norma: str, url: str):
        self.norma, self.url = norma, url

    def fetch(self) -> Iterator[Dispositivo]:  # pragma: no cover - requer rede
        import httpx  # extra "ingest"

        resp = httpx.get(self.url, timeout=60, follow_redirects=True)
        resp.raise_for_status()
        # Textos do Planalto costumam vir em windows-1252/latin-1
        texto = html_para_texto(resp.content.decode("latin-1", errors="replace"))
        for caminho, corpo in dividir_artigos(texto):
            yield Dispositivo(self.norma, caminho, corpo, self.url, self.nome)
