"""Senado offline: fixture SINTÉTICA no formato real conferido na sondagem (não é a norma real)."""

from ordem import knowledge
from ordem.connectors.senado import numero_do_artigo, parse_detalhe, url_por_urn

DETALHE = {"DetalheDocumento": {"documentos": {"documento": [{
    "id": "1", "identificacao": {"normaNome": "Lei nº 1 de 01/01/2000", "apelido": "LEI-1, Código Ficticio",
                                 "dataassinatura": "01/01/2000", "urlDocumento": "https://normas.leg.br/?urn=x"},
    "publicacoes": {"publicacao": {"fonte": "DOU de 02/01/2000 ", "data": "02/01/2000", "urlPubOficial": "https://p"}},
    "ementa": "Ementa ficticia.",
    "disps": {"disp": [
        {"nomeDispositivo": "Art. 1.583 [Lei nº 1 de 01/01/2000]",
         "refs": {"ref": [{"dispositivo": "Lei nº 9 de 01/01/2010", "comentario": "Alteração"},
                          {"dispositivo": "Lei nº 8 de 01/01/2009", "comentario": "Revogação"}]}},
        {"nomeDispositivo": "Art. 5 [Lei nº 1 de 01/01/2000]", "refs": {"ref": {"dispositivo": "Lei nº 7", "comentario": "Alteração"}}},
        {"nomeDispositivo": "Ementa", "refs": {"ref": {"dispositivo": "x"}}}]}}]}}}


def test_numero_do_artigo():
    assert numero_do_artigo("Art. 1.583 [Lei nº 10.406]") == 1583
    assert numero_do_artigo("Art. 3 [x]") == 3 and numero_do_artigo("Ementa") is None


def test_parse_detalhe_aceita_objeto_ou_lista():
    r = parse_detalhe(DETALHE)
    assert r["norma_nome"] == "Lei nº 1 de 01/01/2000" and r["publicacoes"][0]["fonte"] == "DOU de 02/01/2000"
    assert [a["por"] for a in r["alteracoes_por_artigo"]["1583"]] == ["Lei nº 9 de 01/01/2010", "Lei nº 8 de 01/01/2009"]
    assert list(r["alteracoes_por_artigo"]) == ["1583", "5"]  # 'Ementa' ignorada; 1 ref (objeto) vira lista
    assert url_por_urn("urn:lex:br:federal:lei:2002-01-10;10406").endswith("urn=urn:lex:br:federal:lei:2002-01-10;10406")


def test_artigos_para_pedido_traz_alteracoes_oficiais(tmp_path, monkeypatch):
    import json
    from ordem.storage import diretorio_dados

    dados = {"normas": {"cc": {"status": "ok", **parse_detalhe(DETALHE)}}}
    (diretorio_dados()).mkdir(parents=True, exist_ok=True)
    (diretorio_dados() / "senado_normas.json").write_text(json.dumps(dados), "utf-8")
    cc = next(d for d in knowledge.artigos_para_pedido("guarda")["dispositivos"] if d["ref"] == "arts. 1.583 a 1.590")
    assert list(cc["alteracoes_senado"]) == ["1583"] and cc["norma_oficial"]["url"].startswith("https://normas.leg.br")
    assert cc["verificado"] is False
    eca = next(d for d in knowledge.artigos_para_pedido("guarda")["dispositivos"] if "8.069" in d["norma"])
    assert "alteracoes_senado" not in eca
