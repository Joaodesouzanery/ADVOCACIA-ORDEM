"""M1 offline: fixture HTML SINTÉTICA (não é texto de lei real) -> SQLite -> busca/MCP/export."""

import csv

from ordem import knowledge
from ordem.cli import main
from ordem.ingest import carregar_normas, ingerir, norma_por_nome
from ordem.knowledge import PENDENTE, intervalos_da_ref
from ordem.storage import RepositorioSQLite, abrir_repositorio, caminho_csv
from ordem.storage.exportar import exportar_csv, exportar_xlsx

HTML_CC = """<html><body>
<p>Art. 1.583. A guarda sera unilateral ou compartilhada (texto ficticio).</p>
<p><strike>Art. 1.584. Redacao antiga revogada ficticia.</strike></p>
<p>Art. 1.584. A guarda podera ser requerida por qualquer dos pais (ficticio).</p>
<p>Art. 1.694. Parentes podem pedir alimentos uns aos outros (ficticio).</p>
</body></html>"""
HTML_CPC = "<p>Art. 693. Normas para acoes de familia (ficticio).</p><p>Art. 335. Contestacao (ficticio).</p>"


def baixar_fixture(url: str) -> str:
    if "l10406" in url:
        return HTML_CC
    if "l13105" in url:
        return HTML_CPC
    raise ConnectionError("sem rede nos testes")


def _repo_ingerido():
    repo = RepositorioSQLite()
    rel = ingerir(repo, baixar_fixture)
    return repo, rel


def test_ingestao_tolera_falhas_e_descarta_riscado():
    repo, rel = _repo_ingerido()
    assert rel["normas"]["cc"] == {"status": "ok", "artigos": 3, "url": rel["normas"]["cc"]["url"]}
    assert rel["normas"]["eca"]["status"] == "erro"
    textos = {r.caminho: r.texto for r in repo.todos("cc")}
    assert "revogada" not in textos["Art. 1.584"]


def test_busca_sem_acento_e_intervalo():
    repo, _ = _repo_ingerido()
    achados = repo.buscar("GUARDA podera")
    assert [r.caminho for r in achados] == ["Art. 1.584"]
    assert [r.caminho for r in repo.obter_intervalo("cc", 1583, 1590)] == ["Art. 1.583", "Art. 1.584"]


def test_intervalos_da_ref():
    assert intervalos_da_ref("arts. 1.583 a 1.590") == [(1583, 1590)]
    assert intervalos_da_ref("arts. 19, 33 e 148") == [(19, 19), (33, 33), (148, 148)]
    assert intervalos_da_ref("art. 226, §6º") == [(226, 226)]
    assert intervalos_da_ref("arts. 528 e 911 a 913") == [(528, 528), (911, 913)]
    assert intervalos_da_ref("art. 53, II") == [(53, 53)]
    assert intervalos_da_ref("integral") is None


def test_mapa_curado_liga_ao_catalogo():
    assert norma_por_nome("Código Civil (Lei 10.406/2002)")["id"] == "cc"
    assert norma_por_nome("CPC (Lei 13.105/2015)")["id"] == "cpc"
    assert norma_por_nome("Constituição Federal")["id"] == "cf"
    assert len({n["id"] for n in carregar_normas()}) == len(carregar_normas())


def test_artigos_para_pedido_com_e_sem_corpus():
    sem = knowledge.artigos_para_pedido("guarda")
    assert all(d["texto_oficial"] == PENDENTE for d in sem["dispositivos"])

    repo, _ = _repo_ingerido()
    knowledge.definir_repositorio(repo)
    com = knowledge.artigos_para_pedido("guarda")
    cc = next(d for d in com["dispositivos"] if d["ref"] == "arts. 1.583 a 1.590")
    assert cc["fonte_ingerida"] and cc["verificado"] is False
    assert [t["caminho"] for t in cc["textos_oficiais"]] == ["Art. 1.583", "Art. 1.584"]
    eca = next(d for d in com["dispositivos"] if "8.069" in d["norma"])
    assert eca["texto_oficial"] == PENDENTE  # nunca inventa


def test_mcp_buscar_dispositivo():
    from ordem.mcp_server.server import TOOLS, tool_buscar_dispositivo

    assert tool_buscar_dispositivo in TOOLS
    assert tool_buscar_dispositivo("guarda")["resultados"] == []
    repo, _ = _repo_ingerido()
    knowledge.definir_repositorio(repo)
    res = tool_buscar_dispositivo("contestacao", norma="cpc")
    assert [r["caminho"] for r in res["resultados"]] == ["Art. 335"]


def test_export_csv_xlsx_e_reconstrucao(tmp_path):
    repo, _ = _repo_ingerido()
    assert exportar_csv(repo, caminho_csv()) == 5
    with open(caminho_csv(), encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 5
    assert exportar_xlsx(repo, tmp_path / "c.xlsx") == 5
    # SQLite reconstruído a partir do CSV versionado
    reaberto = abrir_repositorio()
    assert reaberto.contagem() == {"cc": 3, "cpc": 2}


def test_cli_buscar(capsys):
    assert main(["buscar", "guarda"]) == 1  # sem corpus
    repo, _ = _repo_ingerido()
    exportar_csv(repo, caminho_csv())
    knowledge._repo_cache.clear()
    assert main(["buscar", "alimentos"]) == 0
    assert "Art. 1.694" in capsys.readouterr().out
