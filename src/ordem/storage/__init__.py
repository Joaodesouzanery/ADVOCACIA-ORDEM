"""Armazenamento do corpus público (texto de lei).

Hoje: SQLite local (+ CSV/XLSX versionados em `data/`). Depois: Supabase,
implementando a mesma interface `Repositorio`.
"""

from .base import Registro, Repositorio, numero_artigo
from .sqlite import RepositorioSQLite, abrir_repositorio, caminho_csv, diretorio_dados

__all__ = [
    "Registro",
    "Repositorio",
    "RepositorioSQLite",
    "abrir_repositorio",
    "caminho_csv",
    "diretorio_dados",
    "numero_artigo",
]
