"""Esqueleto de petição inicial a partir de FATOS FORNECIDOS pelo cliente.

Regra de ouro: nada é inventado. Campo ausente vira [PENDENTE]. Fundamentos vêm
da base curada e continuam marcados como não verificados até a ingestão (M1).
"""

from __future__ import annotations

from .knowledge import STATUS_NAO_VERIFICADO, artigos_para_pedido, identificar_pedido

CAMPOS = [
    ("autor_nome", "Nome do autor"),
    ("autor_qualificacao", "Qualificação do autor (nacionalidade, estado civil, profissão, CPF, endereço)"),
    ("reu_nome", "Nome do réu"),
    ("reu_qualificacao", "Qualificação do réu"),
    ("comarca", "Comarca/foro"),
    ("fatos", "Narrativa dos fatos fornecida pelo cliente"),
    ("pedido_especifico", "Pedido específico (ex.: guarda compartilhada com residência base na mãe)"),
]


def rascunho_peticao_inicial(tipo_pedido: str, caso: dict) -> dict:
    base = artigos_para_pedido(tipo_pedido)
    if "erro" in base:
        return base
    chave = base["pedido"]

    def v(k: str) -> str:
        val = (caso.get(k) or "").strip()
        return val if val else "[PENDENTE]"

    pendentes = [rotulo for k, rotulo in CAMPOS if not (caso.get(k) or "").strip()]
    fundamentos = "\n".join(f"- {d['norma']}, {d['ref']} — {d['tema']}" for d in base["dispositivos"])
    texto = (
        f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA VARA COMPETENTE — {v('comarca')}\n\n"
        f"{v('autor_nome')}, {v('autor_qualificacao')}, vem propor\n\n"
        f"AÇÃO DE {chave.upper()}\n\n"
        f"em face de {v('reu_nome')}, {v('reu_qualificacao')}, pelos fatos e fundamentos a seguir.\n\n"
        f"I — DOS FATOS\n{v('fatos')}\n\n"
        f"II — DO DIREITO (fundamentos candidatos — conferir texto oficial)\n{fundamentos}\n\n"
        f"III — DOS PEDIDOS\n{v('pedido_especifico')}\n"
    )
    return {
        "pedido": chave,
        "rascunho": texto,
        "campos_pendentes": pendentes,
        "pontos_para_aval_do_cliente": [
            "Os fatos narrados correspondem exatamente à verdade?",
            "Os documentos listados no checklist foram todos fornecidos?",
            "O pedido específico reflete o que o cliente deseja?",
        ],
        "aviso": (
            "Rascunho de apoio. Somente fatos fornecidos pelo cliente; nenhuma informação foi "
            "acrescentada. " + STATUS_NAO_VERIFICADO + " Revisão obrigatória por advogado(a) inscrito(a) na OAB."
        ),
    }
