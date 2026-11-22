"""STJ offline: fixtures SINTÉTICAS no formato real conferido na sondagem (não são acórdãos reais)."""

import io
import json
import zipfile

from ordem import knowledge
from ordem.connectors.stj import (escolher_mais_recente, escolher_recursos_espelho, julgados_do_espelho,
                                  ler_json_espelho, ler_zip_espelhos, precedentes_de_familia, temas_do_texto)
from ordem.mcp_server.server import TOOLS, tool_buscar_jurisprudencia
from ordem.storage.jurisprudencia import RepositorioJurisprudencia, abrir_jurisprudencia, caminho_csv_julgados

ESPELHO = [
    {"id": "000001", "numeroProcesso": "111", "numeroRegistro": "2022000001", "siglaClasse": "REsp",
     "nomeOrgaoJulgador": "TERCEIRA TURMA", "ministroRelator": "RELATOR FICTICIO",
     "ementa": "FAMILIA. GUARDA COMPARTILHADA. Texto ficticio sobre convivência.", "dataDecisao": "20240226"},
    {"id": "000002", "numeroProcesso": "222", "siglaClasse": "REsp", "ementa": "PENAL. Texto ficticio de furto."},
    {"Obs": "Sem lançamentos para o mês", "id": "", "ementa": ""},
    {"id": "000003", "numeroProcesso": "333", "siglaClasse": "AgInt",
     "ementa": "ALIMENTOS. Pensão alimentícia ficticia."},
]
TEMAS = ("sequencialPrecedente;tipoPrecedente;numeroPrecedente;dataJulgamento;"
         "questaoSubmetidaAJulgamento;teseFirmada\n"
         "10;Tema Repetitivo;999;2024-01-01;Definir guarda compartilhada (ficticio);Tese ficticia sobre guarda.\n"
         "11;Tema Repetitivo;998;2024-01-02;Tributario ficticio;Tese tributaria.\n")
PROCESSOS = ("sequencialPrecedente,tipoPrecedente,numeroPrecedente,Processo,numeroRegistro,ministroRelator,leadingCase\n"
             "10,,999,REsp 1,2022111,RELATOR A,N\n10,,999,REsp 2,2022222,RELATOR B,S\n")


def test_filtro_de_temas():
    assert temas_do_texto("GUARDA COMPARTILHADA e Pensão Alimentícia") == ["guarda", "alimentos"]
    assert temas_do_texto("Direito tributário") == []
    assert temas_do_texto("a adoção da data da intimação; filiação partidária") == []  # falsos positivos reais
    assert temas_do_texto("Adoção de criança e filiação socioafetiva") == ["poder_familiar"]


def test_espelho_filtra_familia_e_ignora_mes_vazio():
    js = list(julgados_do_espelho(ESPELHO, "https://x/a.json", "2026-11-22T00:00:00+00:00"))
    assert [j.fonte_id for j in js] == ["000001", "000003"]
    assert js[0].data == "2024-02-26" and "guarda" in js[0].temas and js[0].processo == "REsp 111"


def test_leitura_de_json_com_bom_e_zip():
    bruto = b"\xef\xbb\xbf" + json.dumps(ESPELHO).encode()
    assert len(ler_json_espelho(bruto)) == 4
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("a.json", json.dumps(ESPELHO))
        z.writestr("leia.txt", "x")
    assert [len(x) for x in ler_zip_espelhos(buf.getvalue())] == [4]


def test_escolha_de_recursos():
    lista = [
        {"recurso": "d.csv", "formato": "csv", "url": "u0", "modificado": "1"},
        {"recurso": "20220531.json", "formato": "json", "url": "u1", "modificado": "2022"},
        {"recurso": "20220531.json", "formato": "json", "url": "u2", "modificado": "2025"},
        {"recurso": "20220508.zip", "formato": "zip", "url": "u3", "modificado": "1"},
        {"recurso": "Temas.csv", "formato": "csv", "url": "t1", "modificado": "2024"},
        {"recurso": "Temas.csv", "formato": "csv", "url": "t2", "modificado": "2026"},
    ]
    assert [r["url"] for r in escolher_recursos_espelho(lista)] == ["u3", "u2"]
    assert escolher_mais_recente(lista, "temas.csv")["url"] == "t2"


def test_precedentes_join_e_leading_case():
    ps = list(precedentes_de_familia(TEMAS, PROCESSOS, "https://x/temas.csv", "q"))
    assert len(ps) == 1 and ps[0].fonte_id == "10" and ps[0].processo == "REsp 2"  # leading case
    assert ps[0].classe == "Tema Repetitivo 999" and "Tese:" in ps[0].ementa


def test_busca_csv_e_mcp():
    assert knowledge.buscar_jurisprudencia("guarda")["resultados"] == []
    assert "PENDENTE" in knowledge.buscar_jurisprudencia("guarda")["erro"]
    repo = RepositorioJurisprudencia()
    repo.upsert(julgados_do_espelho(ESPELHO, "https://x/a.json", "q"))
    repo.upsert(precedentes_de_familia(TEMAS, PROCESSOS, "https://x/t.csv", "q"))
    assert repo.contagem() == {"acordao": 2, "precedente": 1}
    repo.exportar_csv(caminho_csv_julgados())
    assert abrir_jurisprudencia().contagem() == {"acordao": 2, "precedente": 1}
    assert tool_buscar_jurisprudencia in TOOLS
    res = tool_buscar_jurisprudencia("pensao alimenticia")
    assert [r["processo"] for r in res["resultados"]] == ["AgInt 333"]
    assert res["resultados"][0]["url_oficial"] == "https://x/a.json"
