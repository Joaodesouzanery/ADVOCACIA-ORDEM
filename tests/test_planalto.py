from ordem.connectors import dividir_artigos, html_para_texto

# Fixture SINTÉTICA (não é texto de lei real): valida só o parser.
HTML = """
<p>Art. 1&ordm;. Texto ficticio um.</p>
<p>&nbsp;&nbsp;&sect; 1&ordm; Paragrafo ficticio.</p>
<p>Art. 1.583. Texto ficticio dois.<br>Art. 33-A. Texto ficticio tres.</p>
"""


def test_divide_artigos_e_paragrafos():
    arts = dividir_artigos(html_para_texto(HTML))
    assert [c for c, _ in arts] == ["Art. 1º", "Art. 1.583", "Art. 33-A"]
    assert "Paragrafo ficticio" in arts[0][1]
    assert "dois" in arts[1][1] and "tres" not in arts[1][1]
