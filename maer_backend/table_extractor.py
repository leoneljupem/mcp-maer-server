#!/usr/bin/env python3
# 🦁 MAER TABLE EXTRACTOR — Extracción de tablas y formularios
# Leonel Mojica — Ecatepec MX — 2026

"""
Extrae tablas de PDFs usando pdfplumber.
Retorna tablas como listas de diccionarios (JSON-friendly).
"""

import logging
from pathlib import Path

logger = logging.getLogger("maer.tables")


def extract_tables_from_pdf(path: Path, max_pages: int = 50, min_rows: int = 2) -> dict:
    """
    Extrae todas las tablas de un PDF.

    Retorna: {
        ok: bool,
        tables: [
            {
                page: int,
                table_index: int,
                headers: [str],
                rows: [[str]],
                row_count: int,
                col_count: int
            }
        ],
        total_tables: int
    }
    """
    try:
        import pdfplumber
    except ImportError:
        return {"ok": False, "error": "pdfplumber no instalado", "tables": []}

    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}", "tables": []}

    if path.suffix.lower() != ".pdf":
        return {"ok": False, "error": "Solo se soportan PDFs", "tables": []}

    tables_found = []

    try:
        with pdfplumber.open(str(path)) as pdf:
            pages_to_process = min(len(pdf.pages), max_pages)

            for page_num in range(pages_to_process):
                page = pdf.pages[page_num]
                page_tables = page.extract_tables()

                if not page_tables:
                    continue

                for table_idx, table in enumerate(page_tables):
                    if not table or len(table) < min_rows:
                        continue

                    # Limpiar celdas
                    cleaned = []
                    for row in table:
                        cleaned_row = [(cell.strip() if cell else "") for cell in row]
                        cleaned.append(cleaned_row)

                    # Primera fila como headers
                    headers = cleaned[0] if cleaned else []
                    rows = cleaned[1:] if len(cleaned) > 1 else []

                    tables_found.append(
                        {
                            "page": page_num + 1,
                            "table_index": table_idx,
                            "headers": headers,
                            "rows": rows,
                            "row_count": len(rows),
                            "col_count": len(headers),
                        }
                    )

    except Exception as e:
        logger.error(f"Error extrayendo tablas: {e}")
        return {"ok": False, "error": f"Error: {e}", "tables": tables_found}

    return {
        "ok": True,
        "path": str(path),
        "total_tables": len(tables_found),
        "tables": tables_found,
    }


def tables_to_dicts(table_data: dict) -> list:
    """
    Convierte tablas extraídas a listas de diccionarios
    (más fácil de consumir en APIs).
    """
    result = []
    for table in table_data.get("tables", []):
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        dicts = []
        for row in rows:
            d = {}
            for i, header in enumerate(headers):
                key = header or f"col_{i}"
                d[key] = row[i] if i < len(row) else ""
            dicts.append(d)
        result.append(
            {
                "page": table["page"],
                "table_index": table["table_index"],
                "records": dicts,
            }
        )
    return result


def extract_text_with_layout(path: Path, max_pages: int = 50) -> dict:
    """
    Extrae texto preservando el layout espacial (útil para formularios).
    """
    try:
        import pdfplumber
    except ImportError:
        return {"ok": False, "error": "pdfplumber no instalado"}

    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}"}

    text_parts = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            pages_to_process = min(len(pdf.pages), max_pages)
            for page_num in range(pages_to_process):
                page = pdf.pages[page_num]
                text = page.extract_text(layout=True)
                if text:
                    text_parts.append(f"--- Página {page_num + 1} ---\n{text}")
    except Exception as e:
        return {"ok": False, "error": f"Error: {e}"}

    return {
        "ok": True,
        "path": str(path),
        "text": "\n\n".join(text_parts),
        "pages": len(text_parts),
    }
