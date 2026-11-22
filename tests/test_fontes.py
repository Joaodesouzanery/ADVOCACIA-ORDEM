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


def test_sondagem_detecta_pagina_de_desafio(tmp_path):
    html = b"<title>Verifica\xc3\xa7\xc3\xa3o de seguran\xc3\xa7a \xe2\x80\x94 Senado Federal</title>"
    resumo = sondar(lambda u: Resposta(u, 200, "text/html", html), tmp_path, ids=["lexml"])
    assert resumo["fontes"]["lexml"][0]["ok"] is False
    assert json.loads((tmp_path / "lexml.json").read_text())["resultados"][0]["desafio_antirrobo"] is True


def test_sondagem_de_pacote_ckan_descobre_recursos_e_pede_so_o_cabecalho(tmp_path):
    from ordem.sondagem import sondar_pacote_ckan

    pedidos = []
    pacote = {"success": True, "result": {"resources": [
        {"name": "zip", "format": "ZIP", "url": "https://x/a.zip", "size": 900},
        {"name": "dic", "format": "CSV", "url": "https://x/d.csv", "size": 10},
        {"name": "json", "format": "JSON", "url": "https://x/b.json", "size": 50},
        {"name": "sem url", "format": "JSON"}]}}

    def obter(url, cabecalhos=None):
        pedidos.append((url, cabecalhos))
        if "package_show" in url:
            return Resposta(url, 200, "application/json", json.dumps(pacote).encode())
        return Resposta(url, 206, "application/zip", b"PK\x03\x04resto")

    r = sondar_pacote_ckan("https://stj", "p", obter, max_recursos=2)
    assert r["num_recursos"] == 3  # recurso sem url fica de fora
    assert [c["formato"] for c in r["cabecalhos"]] == ["csv", "json"]  # menores e legíveis primeiro
    assert all(c == {"Range": "bytes=0-4095"} for _, c in pedidos[1:])
    assert r["cabecalhos"][0]["magic_hex"] == "504b0304" and r["cabecalhos"][0]["ok"]


def test_fontes_json_tem_pacotes_de_familia():
    stj = next(f for f in carregar_fontes() if f["id"] == "stj")
    pacotes = {s["ckan_pacote"] for s in stj["sondar"] if s.get("ckan_pacote")}
    assert pacotes == {"precedentes-qualificados", "espelhos-de-acordaos-terceira-turma",
                       "espelhos-de-acordaos-quarta-turma", "espelhos-de-acordaos-segunda-secao"}


def test_sondagem_openapi_guarda_so_os_caminhos():
    from ordem.sondagem import sondar_openapi

    spec = {"info": {"title": "API Senado", "version": "1"}, "servers": [{"url": "https://x/dadosabertos"}],
            "paths": {"/legislacao/lista": {"get": {"summary": "Lista normas"}},
                      "/x": {"post": {"operationId": "op"}, "parameters": []}}}
    r = sondar_openapi("u", lambda u: Resposta(u, 200, "application/json", json.dumps(spec).encode()))
    assert r["ok"] and r["num_caminhos"] == 2
    assert r["caminhos"][0] == {"caminho": "/legislacao/lista", "metodos": ["get"], "parametros": [],
                                "produz": [], "resumo": "Lista normas"}
    assert sondar_openapi("u", lambda u: Resposta(u, 200, "text/html", b"<html>"))["ok"] is False


def test_openapi_guarda_parametros_e_tipo_de_resposta():
    from ordem.sondagem import sondar_openapi

    spec = {"paths": {"/legislacao/urn": {"get": {"summary": "Por URN",
            "parameters": [{"name": "urn", "in": "query", "required": True}],
            "responses": {"200": {"content": {"application/json": {}, "application/xml": {}}}}}}}}
    c = sondar_openapi("u", lambda u: Resposta(u, 200, "application/json", json.dumps(spec).encode()))["caminhos"][0]
    assert c["parametros"] == [{"nome": "urn", "em": "query", "obrigatorio": True}]
    assert c["produz"] == ["application/json", "application/xml"]


def test_estrutura_json_resume_forma_sem_copiar_o_texto():
    from ordem.sondagem import estrutura_json, sondar_json_estrutura

    dado = {"a": {"b": [{"texto": "x" * 500, "n": 1}, {"texto": "y"}]}, "vazio": []}
    est = estrutura_json(dado)
    assert est["a"]["b"]["__lista__"] == 2
    assert est["a"]["b"]["__item0__"]["texto"].startswith("str[500]:")
    assert len(json.dumps(est)) < 400
    r = sondar_json_estrutura("u", lambda u: Resposta(u, 200, "application/json", json.dumps(dado).encode()))
    assert r["ok"] and r["estrutura"]["vazio"] == {"__lista__": 0, "__item0__": None}
