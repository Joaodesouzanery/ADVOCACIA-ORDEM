"""Conectores de dados abertos: tudo offline, com fixtures SINTÉTICAS."""

import json

import pytest

from ordem.connectors.ckan import pacotes_da_lista, recursos_do_pacote
from ordem.connectors.http import Resposta
from ordem.connectors.lexml import url_busca_sru, url_resolver, urn_valida
from ordem.ingest import carregar_normas
from ordem.sondagem import carregar_fontes, sondar


def test_catalogo_de_fontes_cobre_as_13_do_usuario():
    ids = {f["id"] for f in carregar_fontes()}
    assert {"senado", "lexml", "camara", "stj", "datajud", "cnj", "tjrs", "tjdft"} <= ids
    urls = {s["url"] for f in carregar_fontes() for s in f["sondar"] if s["origem"] == "usuario"}
    assert "https://scon.stj.jus.br/SCON/sumstj/" in urls
    assert all(f["sondar"] for f in carregar_fontes())


def test_sondagem_registra_sucesso_e_falha(tmp_path):
    def obter(url):
        if "stj" in url:
            raise ConnectionError("proxy recusou")
        return Resposta(url, 200, "application/json", b'{"ok": true}' + b"x" * 5000)

    resumo = sondar(obter, tmp_path, ids=["stj", "camara"])
    assert resumo["fontes"]["camara"][0]["ok"] is True
    assert all(r["ok"] is False and "ConnectionError" in r["erro"] for r in resumo["fontes"]["stj"])
    amostra = json.loads((tmp_path / "camara.json").read_text())["resultados"][0]["amostra"]
    assert len(amostra) == 2048  # amostra truncada
    assert (tmp_path / "resumo.json").exists()


def test_ckan_parsing():
    assert pacotes_da_lista({"success": True, "result": ["a", "b"]}) == ["a", "b"]
    with pytest.raises(ValueError):
        pacotes_da_lista({"success": False})
    pacote = {"success": True, "result": {"name": "sumulas", "title": "Súmulas", "resources": [
        {"name": "csv", "format": "CSV", "url": "https://x/s.csv", "created": "2026-01-01"},
        {"name": "sem url", "format": "JSON"}]}}
    rec = recursos_do_pacote(pacote)
    assert [r["formato"] for r in rec] == ["csv"] and rec[0]["pacote"] == "sumulas"


def test_urns_do_catalogo_seguem_o_padrao():
    for n in carregar_normas():
        assert urn_valida(n["urn"]), n["id"]
    assert url_resolver("urn:lex:br:federal:lei:2002-01-10;10406").endswith("10406")
    assert "searchRetrieve" in url_busca_sru("urn:lex:br:federal:lei:2002-01-10;10406")
    with pytest.raises(ValueError):
        url_busca_sru("qualquer coisa")
