import pytest

from ordem import knowledge


@pytest.fixture(autouse=True)
def _sem_corpus_por_padrao(tmp_path, monkeypatch):
    """Isola testes do corpus real em data/: cada teste começa sem corpus."""
    monkeypatch.setenv("ORDEM_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("ORDEM_DB", raising=False)
    knowledge.definir_repositorio(None)
    yield
    knowledge._repo_cache.clear()
