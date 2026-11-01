from datetime import date

from ordem.prazos import Calendario, calcular_prazo
from ordem.prazos.calendario import em_recesso, feriados_nacionais, pascoa


def test_pascoa_conhecida():
    assert pascoa(2024) == date(2024, 3, 31)
    assert pascoa(2025) == date(2025, 4, 20)
    assert pascoa(2026) == date(2026, 4, 5)


def test_sexta_santa_e_feriado():
    assert date(2026, 4, 3) in feriados_nacionais(2026)


def test_consciencia_negra_so_desde_2024():
    assert date(2024, 11, 20) in feriados_nacionais(2024)
    assert date(2023, 11, 20) not in feriados_nacionais(2023)


def test_recesso_limites():
    assert em_recesso(date(2026, 12, 20)) and em_recesso(date(2027, 1, 20))
    assert not em_recesso(date(2026, 12, 19)) and not em_recesso(date(2027, 1, 21))


def test_contestacao_15_uteis_simples():
    # Início seg 02/03/2026; conta a partir de ter 03/03; sem feriados em março -> 15º útil = seg 23/03.
    r = calcular_prazo("contestacao", date(2026, 3, 2))
    assert r.primeiro_dia_contado == date(2026, 3, 3)
    assert r.vencimento == date(2026, 3, 23)


def test_embargos_5_uteis_atravessa_fim_de_semana():
    # Intimação sex 06/03/2026 -> conta seg 09..sex 13 = 5 úteis
    r = calcular_prazo("embargos_declaracao", date(2026, 3, 6))
    assert r.vencimento == date(2026, 3, 13)


def test_prazo_atravessa_recesso():
    # Intimação sex 18/12/2026; recesso 20/12-20/01; 1º dia contado = qui 21/01/2027; 15º útil = qua 10/02/2027.
    r = calcular_prazo("apelacao", date(2026, 12, 18))
    assert r.primeiro_dia_contado == date(2027, 1, 21)
    assert r.vencimento == date(2027, 2, 10)


def test_em_dobro_dobra_dias():
    r = calcular_prazo("contestacao", date(2026, 3, 2), em_dobro=True)
    assert r.dias_efetivos == 30


def test_regra_desconhecida():
    import pytest

    with pytest.raises(KeyError):
        calcular_prazo("inexistente", date(2026, 3, 2))


def test_feriado_extra_local_desloca():
    base = calcular_prazo("embargos_declaracao", date(2026, 3, 6)).vencimento
    cal = Calendario(extras={date(2026, 3, 10)})
    assert base == date(2026, 3, 13)
    assert calcular_prazo("embargos_declaracao", date(2026, 3, 6), calendario=cal).vencimento == date(2026, 3, 16)
