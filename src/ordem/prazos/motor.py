"""Motor de prazos processuais.

Regra geral (CPC arts. 219, 224 e 231): na contagem em dias úteis exclui-se o dia
do começo e inclui-se o do vencimento; só contam dias úteis; se o vencimento cair
em dia não útil, prorroga-se para o primeiro dia útil seguinte.

O resultado é SEMPRE uma sugestão a ser conferida pelo advogado (feriados locais,
suspensões por ato do tribunal, indisponibilidade do sistema etc.).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from importlib import resources

from .calendario import Calendario

AVISO = (
    "Prazo calculado automaticamente: SUGESTÃO sujeita a conferência pelo advogado "
    "(feriados locais, suspensões, termo inicial real da intimação/citação)."
)


@dataclass(frozen=True)
class RegraPrazo:
    id: str
    ato: str
    dias: int
    tipo: str  # "uteis" | "corridos"
    base_legal: str
    termo_inicial: str
    observacoes: str = ""
    verificar: bool = True


@dataclass
class ResultadoPrazo:
    regra: RegraPrazo
    inicio: date
    primeiro_dia_contado: date
    vencimento: date
    dias_efetivos: int
    em_dobro: bool
    avisos: list[str] = field(default_factory=list)


def carregar_regras() -> dict[str, RegraPrazo]:
    raw = json.loads(resources.files("ordem.data").joinpath("regras_prazo.json").read_text("utf-8"))
    return {r["id"]: RegraPrazo(**r) for r in raw["regras"]}


def calcular_prazo(
    regra_id: str,
    inicio: date,
    *,
    em_dobro: bool = False,
    calendario: Calendario | None = None,
    regras: dict[str, RegraPrazo] | None = None,
) -> ResultadoPrazo:
    """Calcula o vencimento a partir da data da intimação/citação/ciência (`inicio`).

    `em_dobro`: Fazenda Pública, Ministério Público e Defensoria (CPC 180, 183, 186)
    ou litisconsortes com procuradores diferentes (CPC 229).
    """
    regras = regras or carregar_regras()
    if regra_id not in regras:
        raise KeyError(f"Regra de prazo desconhecida: {regra_id!r}. Disponíveis: {sorted(regras)}")
    cal = calendario or Calendario()
    regra = regras[regra_id]
    dias = regra.dias * (2 if em_dobro else 1)

    if regra.tipo == "uteis":
        cursor = inicio
        contados = 0
        primeiro = None
        while contados < dias:
            cursor += timedelta(days=1)
            if cal.eh_dia_util(cursor):
                contados += 1
                if primeiro is None:
                    primeiro = cursor
        venc = cursor
    elif regra.tipo == "corridos":
        primeiro = cal.proximo_dia_util(inicio + timedelta(days=1))
        venc = cal.proximo_dia_util(primeiro + timedelta(days=dias - 1))
    else:
        raise ValueError(f"Tipo de prazo inválido: {regra.tipo!r}")

    avisos = [AVISO]
    if regra.verificar:
        avisos.append("Regra ainda não validada por advogado (verificar=true em regras_prazo.json).")
    return ResultadoPrazo(regra, inicio, primeiro, venc, dias, em_dobro, avisos)
