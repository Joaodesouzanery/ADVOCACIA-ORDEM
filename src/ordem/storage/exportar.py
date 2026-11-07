"""Exporta o corpus para CSV (sempre) e XLSX (extra opcional `excel`)."""

from __future__ import annotations

import csv
from pathlib import Path

from .base import Repositorio
from .sqlite import CAMPOS_CSV


def exportar_csv(repo: Repositorio, destino: str | Path) -> int:
    regs = repo.todos()
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
        w.writeheader()
        for r in regs:
            w.writerow(r.como_dict())
    return len(regs)


def exportar_xlsx(repo: Repositorio, destino: str | Path) -> int:
    from openpyxl import Workbook  # extra "excel"

    wb = Workbook()
    ws = wb.active
    ws.title = "dispositivos"
    ws.append(CAMPOS_CSV + ["verificado_por_advogado"])
    regs = repo.todos()
    for r in regs:
        d = r.como_dict()
        ws.append([d[c][:32000] for c in CAMPOS_CSV] + ["não"])  # limite de célula do Excel
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for col, largura in zip("ABCDEFGH", (10, 30, 14, 90, 50, 10, 22, 14)):
        ws.column_dimensions[col].width = largura
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return len(regs)
