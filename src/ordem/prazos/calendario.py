"""Calendário forense: dias úteis, feriados nacionais e recesso (CPC art. 220)."""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


def pascoa(ano: int) -> date:
    """Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


@lru_cache(maxsize=None)
def feriados_nacionais(ano: int) -> frozenset[date]:
    """Feriados nacionais fixos + Sexta-feira Santa.

    Carnaval e Corpus Christi NÃO entram por padrão (variam por tribunal);
    use `extras` em `Calendario` para configurá-los por comarca.
    Consciência Negra (20/11) é feriado nacional desde a Lei 14.759/2023.
    """
    fixos = [(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (12, 25)]
    dias = {date(ano, m, d) for m, d in fixos}
    if ano >= 2024:
        dias.add(date(ano, 11, 20))
    dias.add(pascoa(ano) - timedelta(days=2))  # Sexta-feira Santa
    return frozenset(dias)


def em_recesso(d: date) -> bool:
    """Suspensão dos prazos de 20/12 a 20/01, inclusive (CPC art. 220)."""
    return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20)


class Calendario:
    def __init__(self, extras: set[date] | None = None, aplicar_recesso: bool = True):
        self.extras = set(extras or ())
        self.aplicar_recesso = aplicar_recesso

    def eh_dia_util(self, d: date) -> bool:
        if d.weekday() >= 5:
            return False
        if d in feriados_nacionais(d.year) or d in self.extras:
            return False
        if self.aplicar_recesso and em_recesso(d):
            return False
        return True

    def proximo_dia_util(self, d: date) -> date:
        """Primeiro dia útil >= d."""
        while not self.eh_dia_util(d):
            d += timedelta(days=1)
        return d
