"""Armazenamento de julgados (acórdãos e precedentes) em SQLite + FTS5, com CSV versionado.

Só guardamos o que passou no filtro de Família (ver `connectors/stj.py`); o histórico
completo do STJ não entra no repositório. `data/jurisprudencia.csv` é a fonte; o SQLite
é reconstruído a partir dele (mesmo padrão do corpus de leis).
"""

from __future__ import annotations

import csv
import re
import sqlite3
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

from .sqlite import diretorio_dados


@dataclass(frozen=True)
class Julgado:
    tipo: str  # "acordao" | "precedente"
    tribunal: str  # "STJ"
    fonte_id: str  # id do acórdão / sequencialPrecedente
    orgao: str
    classe: str
    processo: str
    registro: str
    relator: str
    data: str  # ISO quando conhecida (AAAA-MM-DD), senão texto original
    ementa: str
    temas: str  # ex.: "guarda;alimentos"
    url_oficial: str
    coletado_em: str


CAMPOS = [f.name for f in fields(Julgado)]
_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS julgados (
    id INTEGER PRIMARY KEY,
    {', '.join(f'{c} TEXT NOT NULL DEFAULT ""' for c in CAMPOS)},
    UNIQUE (tribunal, tipo, fonte_id)
);
CREATE VIRTUAL TABLE IF NOT EXISTS julgados_fts USING fts5(
    ementa, processo, temas, content='julgados', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS jul_ai AFTER INSERT ON julgados BEGIN
  INSERT INTO julgados_fts(rowid, ementa, processo, temas) VALUES (new.id, new.ementa, new.processo, new.temas);
END;
CREATE TRIGGER IF NOT EXISTS jul_ad AFTER DELETE ON julgados BEGIN
  INSERT INTO julgados_fts(julgados_fts, rowid, ementa, processo, temas) VALUES ('delete', old.id, old.ementa, old.processo, old.temas);
END;
CREATE TRIGGER IF NOT EXISTS jul_au AFTER UPDATE ON julgados BEGIN
  INSERT INTO julgados_fts(julgados_fts, rowid, ementa, processo, temas) VALUES ('delete', old.id, old.ementa, old.processo, old.temas);
  INSERT INTO julgados_fts(rowid, ementa, processo, temas) VALUES (new.id, new.ementa, new.processo, new.temas);
END;
"""


def caminho_csv_julgados() -> Path:
    return diretorio_dados() / "jurisprudencia.csv"


class RepositorioJurisprudencia:
    def __init__(self, caminho: str | Path = ":memory:"):
        self.con = sqlite3.connect(str(caminho))
        self.con.row_factory = sqlite3.Row
        self.con.executescript(_SCHEMA)

    @staticmethod
    def _j(r: sqlite3.Row) -> Julgado:
        return Julgado(**{c: r[c] for c in CAMPOS})

    def upsert(self, julgados: Iterable[Julgado]) -> int:
        n = 0
        sets = ", ".join(f"{c}=excluded.{c}" for c in CAMPOS if c not in ("tribunal", "tipo", "fonte_id"))
        with self.con:
            for j in julgados:
                self.con.execute(
                    f"INSERT INTO julgados ({', '.join(CAMPOS)}) VALUES ({', '.join('?' * len(CAMPOS))}) "
                    f"ON CONFLICT(tribunal, tipo, fonte_id) DO UPDATE SET {sets}",
                    [asdict(j)[c] for c in CAMPOS])
                n += 1
        return n

    def buscar(self, consulta: str, limite: int = 10, tipo: str | None = None) -> list[Julgado]:
        q = " ".join(f'"{t}"' for t in re.findall(r"\w+", consulta))
        if not q:
            return []
        sql = ("SELECT j.* FROM julgados_fts f JOIN julgados j ON j.id = f.rowid WHERE julgados_fts MATCH ?")
        args: list = [q]
        if tipo:
            sql += " AND j.tipo = ?"
            args.append(tipo)
        sql += " ORDER BY bm25(julgados_fts) LIMIT ?"
        args.append(limite)
        return [self._j(r) for r in self.con.execute(sql, args)]

    def todos(self) -> list[Julgado]:
        return [self._j(r) for r in self.con.execute("SELECT * FROM julgados ORDER BY tipo, data DESC, fonte_id")]

    def contagem(self) -> dict[str, int]:
        return {r[0]: r[1] for r in self.con.execute("SELECT tipo, count(*) FROM julgados GROUP BY tipo")}

    def exportar_csv(self, destino: str | Path) -> int:
        regs = self.todos()
        Path(destino).parent.mkdir(parents=True, exist_ok=True)
        with open(destino, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            for j in regs:
                w.writerow(asdict(j))
        return len(regs)

    def importar_csv(self, arquivo: str | Path) -> int:
        with open(arquivo, newline="", encoding="utf-8") as f:
            return self.upsert(Julgado(**{c: linha.get(c, "") for c in CAMPOS}) for linha in csv.DictReader(f))


def abrir_jurisprudencia(caminho_db: str | Path | None = None) -> RepositorioJurisprudencia | None:
    """Abre (ou reconstrói a partir do CSV) a base de julgados; None se ainda não houve ingestão."""
    csv_ = caminho_csv_julgados()
    db = Path(caminho_db or diretorio_dados() / "jurisprudencia.sqlite")
    if not db.exists() and not csv_.exists():
        return None
    precisa = csv_.exists() and (not db.exists() or db.stat().st_mtime < csv_.stat().st_mtime)
    if precisa and db.exists():
        db.unlink()
    db.parent.mkdir(parents=True, exist_ok=True)
    repo = RepositorioJurisprudencia(db)
    if precisa:
        repo.importar_csv(csv_)
    return repo
