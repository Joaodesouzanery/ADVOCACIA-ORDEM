"""Servidor MCP: expõe a base ao Claude (qualquer chat que conecte este servidor).

Rodar:  python -m ordem.mcp_server.server        (stdio)
Requer: pip install -e ".[mcp]"
"""

from __future__ import annotations

from datetime import date

from .. import knowledge, peticao
from ..prazos import Calendario, calcular_prazo, carregar_regras

INSTRUCOES = (
    "Base jurídica de apoio a escritórios de advocacia (Direito de Família no MVP). "
    "Toda referência vem com status de verificação; nunca afirme que um dispositivo diz "
    "algo sem o texto oficial. Prazos calculados são sugestões a conferir. "
    "Não substitui advogado(a) inscrito(a) na OAB."
)


def tool_artigos_para_pedido(tipo_pedido: str) -> dict:
    """Fundamentos legais candidatos para um pedido (ex.: 'guarda', 'alimentos', 'divorcio')."""
    return knowledge.artigos_para_pedido(tipo_pedido)


def tool_checklist_documentos(tipo_pedido: str) -> dict:
    """Documentos e perguntas a pedir ao cliente para o pedido informado."""
    return knowledge.checklist_documentos(tipo_pedido)


def tool_listar_regras_prazo() -> list[dict]:
    """Lista os atos processuais com prazo cadastrado."""
    return [
        {"id": r.id, "ato": r.ato, "dias": r.dias, "tipo": r.tipo, "base_legal": r.base_legal}
        for r in carregar_regras().values()
    ]


def tool_calcular_prazo(regra_id: str, data_inicio: str, em_dobro: bool = False) -> dict:
    """Calcula o vencimento. data_inicio no formato AAAA-MM-DD (data da intimação/citação)."""
    r = calcular_prazo(regra_id, date.fromisoformat(data_inicio), em_dobro=em_dobro, calendario=Calendario())
    return {
        "ato": r.regra.ato,
        "base_legal": r.regra.base_legal,
        "termo_inicial": r.regra.termo_inicial,
        "inicio": r.inicio.isoformat(),
        "primeiro_dia_contado": r.primeiro_dia_contado.isoformat(),
        "vencimento": r.vencimento.isoformat(),
        "dias": r.dias_efetivos,
        "tipo": r.regra.tipo,
        "em_dobro": r.em_dobro,
        "avisos": r.avisos,
    }


def tool_rascunho_peticao_inicial(tipo_pedido: str, caso: dict) -> dict:
    """Esqueleto de petição inicial usando SOMENTE fatos fornecidos; faltantes ficam [PENDENTE]."""
    return peticao.rascunho_peticao_inicial(tipo_pedido, caso)


TOOLS = [
    tool_artigos_para_pedido,
    tool_checklist_documentos,
    tool_listar_regras_prazo,
    tool_calcular_prazo,
    tool_rascunho_peticao_inicial,
]


def build_server():
    from mcp.server.mcpserver import MCPServer  # extra "mcp"

    server = MCPServer("ordem", instructions=INSTRUCOES)
    for fn in TOOLS:
        server.add_tool(fn, name=fn.__name__.removeprefix("tool_"))
    return server


def main() -> None:  # pragma: no cover
    build_server().run()


if __name__ == "__main__":  # pragma: no cover
    main()
