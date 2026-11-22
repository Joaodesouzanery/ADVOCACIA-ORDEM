"""Repositório SQLite com busca de texto FTS5 (sem acentos, português).

O arquivo `data/corpus.sqlite` NÃO é versionado: é reconstruído a partir de
`data/corpus.csv` (versionado, gerado pela ingestão no GitHub Actions).
"""

from __future__ import annotations

import csv
import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable

from .base import Registro, Repositorio, numero_artigo

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dispositivos (
    id INTEGER PRIMARY KEY,
    norma_id TEXT NOT NULL,
    norma TEXT NOT NULL,
    caminho TEXT NOT NULL,
    numero INTEGER,
    texto TEXT NOT NULL,
    url_oficial TEXT NOT NULL,
    fonte TEXT NOT NULL,
    coletado_em TEXT NOT NULL,
    UNIQUE (norma_id, caminho)
);
CREATE INDEX IF NOT EXISTS ix_disp_norma_num ON dispositivos (norma_id, numero);
CREATE VIRTUAL TABLE IF NOT EXISTS dispositivos_fts USING fts5(
    texto, caminho, norma, content='dispositivos', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS disp_ai AFTER INSERT ON dispositivos BEGIN
  INSERT INTO dispositivos_fts(rowid, texto, caminho, norma) VALUES (new.id, new.texto, new.caminho, new.norma);
END;
CREATE TRIGGER IF NOT EXISTS disp_ad AFTER DELETE ON dispositivos BEGIN
  INSERT INTO dispositivos_fts(dispositivos_fts, rowid, texto, caminho, norma) VALUES ('delete', old.id, old.texto, old.caminho, old.norma);
END;
CREATE TRIGGER IF NOT EXISTS disp_au AFTER UPDATE ON dispositivos BEGIN
  INSERT INTO dispositivos_fts(dispositivos_fts, rowid, texto, caminho, norma) VALUES ('delete', old.id, old.texto, old.caminho, old.norma);
  INSERT INTO dispositivos_fts(rowid, texto, caminho, norma) VALUES (new.id, new.texto, new.caminho, new.norma);
END;
"""

_COLS = "norma_id, norma, caminho, numero, texto, url_oficial, fonte, coletado_em"
CAMPOS_CSV = ["norma_id", "norma", "caminho", "texto", "url_oficial", "fonte", "coletado_em"]


def diretorio_dados() -> Path:
    env = os.environ.get("ORDEM_DATA_DIR")
    return Path(env) if env else Path(__file__).resolve().parents[3] / "data"


def caminho_csv() -> Path:
    return diretorio_dados() / "corpus.csv"


def _consulta_fts(consulta: str) -> str:
    termos = re.findall(r"\w+", consulta, flags=re.UNICODE)
    return " ".join(f'"{t}"' for t in termos)


class RepositorioSQLite(Repositorio):
    def __init__(self, caminho: str | Path = ":memory:"):
        self.caminho = str(caminho)
        self.con = sqlite3.connect(self.caminho)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(_SCHEMA)

    def _reg(self, r: sqlite3.Row) -> Registro:
        return Registro(r["norma_id"], r["norma"], r["caminho"], r["numero"], r["texto"],
                        r["url_oficial"], r["fonte"], r["coletado_em"])

    def upsert(self, registros: Iterable[Registro]) -> int:
        n = 0
        with self.con:
            for g in registros:
                self.con.execute(
                    f"INSERT INTO dispositivos ({_COLS}) VALUES (?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(norma_id, caminho) DO UPDATE SET norma=excluded.norma, "
                    "numero=excluded.numero, texto=excluded.texto, url_oficial=excluded.url_oficial, "
                    "fonte=excluded.fonte, coletado_em=excluded.coletado_em",
                    (g.norma_id, g.norma, g.caminho, g.numero, g.texto, g.url_oficial, g.fonte, g.coletado_em),
                )
                n += 1
        return n

    def buscar(self, consulta: str, limite: int = 10, norma_id: str | None = None) -> list[Registro]:
        q = _consulta_fts(consulta)
        if not q:
            return []
        sql = (f"SELECT d.* FROM dispositivos_fts f JOIN dispositivos d ON d.id = f.rowid "
               f"WHERE dispositivos_fts MATCH ?")
        args: list = [q]
        if norma_id:
            sql += " AND d.norma_id = ?"
            args.append(norma_id)
        sql += " ORDER BY bm25(dispositivos_fts) LIMIT ?"
        args.append(limite)
        return [self._reg(r) for r in self.con.execute(sql, args)]

    def obter_intervalo(self, norma_id: str, inicio: int, fim: int) -> list[Registro]:
        rows = self.con.execute(
            "SELECT * FROM dispositivos WHERE norma_id=? AND numero BETWEEN ? AND ? ORDER BY numero, caminho",
            (norma_id, inicio, fim),
        )
        return [self._reg(r) for r in rows]

    def todos(self, norma_id: str | None = None) -> list[Registro]:
        if norma_id:
            rows = self.con.execute("SELECT * FROM dispositivos WHERE norma_id=? ORDER BY numero, caminho", (norma_id,))
        else:
            rows = self.con.execute("SELECT * FROM dispositivos ORDER BY norma_id, numero, caminho")
        return [self._reg(r) for r in rows]

    def contagem(self) -> dict[str, int]:
        return {r[0]: r[1] for r in self.con.execute("SELECT norma_id, count(*) FROM dispositivos GROUP BY norma_id")}

    def importar_csv(self, arquivo: str | Path) -> int:
        with open(arquivo, newline="", encoding="utf-8") as f:
            regs = [
                Registro(l["norma_id"], l["norma"], l["caminho"], numero_artigo(l["caminho"]), l["texto"],
                         l["url_oficial"], l["fonte"], l["coletado_em"])
                for l in csv.DictReader(f)
            ]
        return self.upsert(regs)


def abrir_repositorio(caminho_db: str | Path | None = None) -> RepositorioSQLite | None:
    """Abre o corpus local. Reconstrói o SQLite a partir do CSV quando necessário.

    Retorna None se ainda não houve ingestão (nem SQLite nem CSV).
    """
    dados = diretorio_dados()
    db = Path(caminho_db or os.environ.get("ORDEM_DB") or dados / "corpus.sqlite")
    csv_ = caminho_csv()
    if not db.exists() and not csv_.exists():
        return None
    precisa_importar = csv_.exists() and (not db.exists() or db.stat().st_mtime < csv_.stat().st_mtime)
    if precisa_importar and db.exists():
        db.unlink()
    db.parent.mkdir(parents=True, exist_ok=True)
    repo = RepositorioSQLite(db)
    if precisa_importar:
        repo.importar_csv(csv_)
    return repo
