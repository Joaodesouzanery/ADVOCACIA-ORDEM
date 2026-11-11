"""Cliente HTTP único dos conectores: User-Agent honesto, retry com backoff, Retry-After.

Não disfarça o cliente (sem User-Agent de navegador). Se a fonte recusar, registramos
o erro na sondagem e buscamos outra via oficial; não contornamos bloqueios.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

USER_AGENT = "ordem-dados-abertos/0.1 (+https://github.com/Joaodesouzanery/ADVOCACIA-ORDEM)"


@dataclass(frozen=True)
class Resposta:
    url: str
    status: int
    content_type: str
    conteudo: bytes

    def texto(self, encoding: str | None = None) -> str:
        return self.conteudo.decode(encoding or "utf-8", errors="replace")


def obter(url: str, *, tentativas: int = 3, timeout: float = 60, cabecalhos: dict | None = None,
          cliente=None, dormir=time.sleep) -> Resposta:  # pragma: no cover - requer rede
    import httpx  # extra "ingest"

    h = {"User-Agent": USER_AGENT, "Accept": "application/json, application/xml, text/html;q=0.8, */*;q=0.5"}
    h.update(cabecalhos or {})
    ultimo: Exception | None = None
    with (cliente or httpx.Client(timeout=timeout, follow_redirects=True, headers=h)) as c:
        for i in range(tentativas):
            try:
                r = c.get(url)
                if r.status_code in (429, 503) and i < tentativas - 1:
                    dormir(min(float(r.headers.get("Retry-After", 2 ** (i + 1))), 30))
                    continue
                return Resposta(str(r.url), r.status_code, r.headers.get("content-type", ""), r.content)
            except httpx.HTTPError as e:
                ultimo = e
                dormir(2 ** (i + 1))
    raise ultimo  # type: ignore[misc]
