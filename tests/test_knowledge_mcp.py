from ordem import knowledge, peticao
from ordem.mcp_server import server


def test_identifica_guarda_em_texto_livre():
    assert knowledge.identificar_pedido("Quero a guarda do meu filho") == "guarda"
    assert knowledge.identificar_pedido("preciso revisar a pensão alimentícia") == "alimentos"


def test_artigos_guarda_marcados_nao_verificados():
    r = knowledge.artigos_para_pedido("guarda")
    assert any("1.583" in d["ref"] for d in r["dispositivos"])
    assert "NÃO verificada" in r["status"]


def test_pedido_desconhecido():
    assert "erro" in knowledge.artigos_para_pedido("xyz inexistente")


def test_rascunho_nao_inventa_fatos():
    r = peticao.rascunho_peticao_inicial("guarda", {"autor_nome": "Fulano"})
    assert "[PENDENTE]" in r["rascunho"]
    assert "Narrativa dos fatos fornecida pelo cliente" in r["campos_pendentes"]
    assert "Fulano" in r["rascunho"]


def test_tools_mcp_funcionam_sem_o_pacote_mcp():
    out = server.tool_calcular_prazo("contestacao", "2026-03-02")
    assert out["vencimento"] == "2026-03-23" and out["avisos"]
    assert server.tool_listar_regras_prazo()
