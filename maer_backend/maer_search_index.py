#!/usr/bin/env python3
# 🦁 MAER Search Index — Índice FTS5 de búsqueda en cualquier archivo
# Leonel Mojica — Ecatepec MX — 2026

"""
Índice de búsqueda full-text con:
  - SQLite FTS5 (tokenizador unicode61, sin dependencias externas)
  - Fuzzy matching (fuzzywuzzy / Levenshtein)
  - Normalización española (acentos, ñ, mayúsculas)
  - Soporte para CUALQUIER tipo de archivo vía maer_universal_extractor
  - Snippets con contexto alrededor del match
  - Ranking BM25 nativo de FTS5
"""

import logging
import os
import re
import sqlite3
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

logger = logging.getLogger("maer.search_index")

_db_write_lock = threading.Lock()

INDEX_DB = os.environ.get("MAER_SEARCH_INDEX", "data/search_index.db")


# ═══════════════════════════════════════════════════════════════════════════════
# Normalización de texto español
# ═══════════════════════════════════════════════════════════════════════════════


def normalize(text: str) -> str:
    """Normaliza texto: minúsculas, sin acentos, sin caracteres especiales."""
    text = text.lower()
    # Mantener ñ → n  para búsquedas, pero preservar texto original
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    ascii_text = re.sub(r"[^\w\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def normalize_query(q: str) -> str:
    """Normaliza una query manteniendo operadores FTS5."""
    # Preservar comillas para frases exactas
    parts = re.split(r'(".*?")', q)
    result = []
    for part in parts:
        if part.startswith('"'):
            result.append(part)
        else:
            result.append(normalize(part))
    return " ".join(result)


# ═══════════════════════════════════════════════════════════════════════════════
# Gestión de la base de datos
# ═══════════════════════════════════════════════════════════════════════════════


def _get_conn(db_path: str = None) -> sqlite3.Connection:
    db = db_path or INDEX_DB
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection):
    conn.execute("PRAGMA journal_mode=WAL").fetchone()
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            path        TEXT UNIQUE NOT NULL,
            file_name   TEXT,
            ext         TEXT,
            size        INTEGER,
            method      TEXT,
            chars       INTEGER,
            indexed_at  REAL DEFAULT (unixepoch('now')),
            modified_at REAL,
            doc_type    TEXT DEFAULT 'documento_general'
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
            path UNINDEXED,
            file_name,
            text,
            text_norm,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS index_meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# Indexación
# ═══════════════════════════════════════════════════════════════════════════════


def index_file(
    path: Path, db_path: str = None, ocr: bool = True, whisper: bool = False
) -> dict:
    """Indexa un archivo extrayendo su texto y guardándolo en FTS5."""
    from maer_backend.maer_universal_extractor import extract_text

    path = Path(path)
    if not path.exists():
        return {"ok": False, "error": f"No existe: {path}"}

    mtime = path.stat().st_mtime

    # Extraer texto
    extraction = extract_text(path, ocr=ocr, whisper=whisper)
    text = extraction.get("text", "") or ""
    text_norm = normalize(text)

    # Clasificar tipo de documento
    doc_type = "documento_general"
    if text:
        try:
            from maer_backend.maer_pdf_analyzer import classify_document

            doc_type = classify_document(text)
        except Exception as e:
            pass

    conn = _get_conn(db_path)
    try:
        cur = conn.cursor()

        # Verificar si ya existe y no cambió
        row = cur.execute(
            "SELECT id, modified_at FROM documents WHERE path = ?", (str(path),)
        ).fetchone()

        if row and abs(row["modified_at"] - mtime) < 1:
            return {"ok": True, "status": "unchanged", "path": str(path)}

        if row:
            # Actualizar
            cur.execute(
                """
                UPDATE documents
                SET file_name=?, ext=?, size=?, method=?, chars=?,
                    modified_at=?, doc_type=?, indexed_at=unixepoch('now')
                WHERE path=?
            """,
                (
                    path.name,
                    path.suffix.lower().lstrip("."),
                    path.stat().st_size,
                    extraction.get("method", ""),
                    len(text),
                    mtime,
                    doc_type,
                    str(path),
                ),
            )

            doc_id = row["id"]
            cur.execute("DELETE FROM docs_fts WHERE rowid = ?", (doc_id,))
            cur.execute(
                "INSERT INTO docs_fts(rowid, path, file_name, text, text_norm) VALUES (?,?,?,?,?)",
                (doc_id, str(path), path.name, text[:500000], text_norm[:500000]),
            )
            status = "updated"
        else:
            # Insertar nuevo
            cur.execute(
                """
                INSERT INTO documents(path, file_name, ext, size, method, chars, modified_at, doc_type)
                VALUES (?,?,?,?,?,?,?,?)
            """,
                (
                    str(path),
                    path.name,
                    path.suffix.lower().lstrip("."),
                    path.stat().st_size,
                    extraction.get("method", ""),
                    len(text),
                    mtime,
                    doc_type,
                ),
            )
            doc_id = cur.lastrowid
            cur.execute(
                "INSERT INTO docs_fts(rowid, path, file_name, text, text_norm) VALUES (?,?,?,?,?)",
                (doc_id, str(path), path.name, text[:500000], text_norm[:500000]),
            )
            status = "indexed"

        conn.commit()
        return {
            "ok": True,
            "status": status,
            "path": str(path),
            "chars": len(text),
            "method": extraction.get("method"),
            "doc_type": doc_type,
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error indexando {path}: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def _extract_for_index(path: Path, db_path: str, ocr: bool, whisper: bool):
    """Extrae texto de un archivo (fase CPU/IO). No escribe en DB."""
    from maer_backend.maer_universal_extractor import extract_text

    mtime = path.stat().st_mtime

    # Saltar si no cambió (lectura rápida sin lock)
    try:
        conn_ro = sqlite3.connect(db_path or INDEX_DB)
        conn_ro.row_factory = sqlite3.Row
        row = conn_ro.execute(
            "SELECT modified_at FROM documents WHERE path = ?", (str(path),)
        ).fetchone()
        conn_ro.close()
        if row and abs(row["modified_at"] - mtime) < 1:
            return {"ok": True, "status": "unchanged", "path": str(path), "_skip": True}
    except Exception as e:
        pass

    extraction = extract_text(path, ocr=ocr, whisper=whisper)
    text = extraction.get("text", "") or ""
    text_norm = normalize(text)
    doc_type = "documento_general"
    if text:
        try:
            from maer_backend.maer_pdf_analyzer import classify_document

            doc_type = classify_document(text)
        except Exception as e:
            pass

    return {
        "ok": True,
        "path": str(path),
        "file_name": path.name,
        "ext": path.suffix.lower().lstrip("."),
        "size": path.stat().st_size,
        "method": extraction.get("method", ""),
        "text": text[:500000],
        "text_norm": text_norm[:500000],
        "chars": len(text),
        "mtime": mtime,
        "doc_type": doc_type,
        "_skip": False,
    }


def _write_to_db(data: dict, db_path: str) -> dict:
    """Escribe resultado de extracción en la DB (serializado con lock)."""
    with _db_write_lock:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            row = cur.execute(
                "SELECT id, modified_at FROM documents WHERE path = ?", (data["path"],)
            ).fetchone()

            if row and abs(row["modified_at"] - data["mtime"]) < 1:
                return {"ok": True, "status": "unchanged"}

            if row:
                cur.execute(
                    """
                    UPDATE documents
                    SET file_name=?, ext=?, size=?, method=?, chars=?,
                        modified_at=?, doc_type=?, indexed_at=unixepoch('now')
                    WHERE path=?
                """,
                    (
                        data["file_name"],
                        data["ext"],
                        data["size"],
                        data["method"],
                        data["chars"],
                        data["mtime"],
                        data["doc_type"],
                        data["path"],
                    ),
                )
                doc_id = row["id"]
                cur.execute("DELETE FROM docs_fts WHERE rowid = ?", (doc_id,))
                cur.execute(
                    "INSERT INTO docs_fts(rowid, path, file_name, text, text_norm) VALUES (?,?,?,?,?)",
                    (
                        doc_id,
                        data["path"],
                        data["file_name"],
                        data["text"],
                        data["text_norm"],
                    ),
                )
                status = "updated"
            else:
                cur.execute(
                    """
                    INSERT INTO documents(path, file_name, ext, size, method, chars, modified_at, doc_type)
                    VALUES (?,?,?,?,?,?,?,?)
                """,
                    (
                        data["path"],
                        data["file_name"],
                        data["ext"],
                        data["size"],
                        data["method"],
                        data["chars"],
                        data["mtime"],
                        data["doc_type"],
                    ),
                )
                doc_id = cur.lastrowid
                cur.execute(
                    "INSERT INTO docs_fts(rowid, path, file_name, text, text_norm) VALUES (?,?,?,?,?)",
                    (
                        doc_id,
                        data["path"],
                        data["file_name"],
                        data["text"],
                        data["text_norm"],
                    ),
                )
                status = "indexed"

            conn.commit()
            return {"ok": True, "status": status}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error escribiendo en DB {data['path']}: {e}")
            return {"ok": False, "error": str(e)}
        finally:
            conn.close()


def index_directory(
    base_dir: Path,
    db_path: str = None,
    ocr: bool = True,
    extensions: list = None,
    max_files: int = 5000,
    workers: int = 4,
) -> dict:
    """Indexa recursivamente todos los archivos de un directorio, en paralelo."""
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return {"ok": False, "error": f"Directorio no existe: {base_dir}"}

    SKIP_EXTS = {
        ".pyc",
        ".pyo",
        ".so",
        ".dylib",
        ".exe",
        ".bin",
        ".dat",
        ".db",
        ".sqlite",
        ".lock",
        ".pid",
        ".log",
    }
    SKIP_DIRS = {
        "__pycache__",
        ".git",
        ".tox",
        "node_modules",
        ".cache",
        "venv",
        "env",
        "miniforge3_x86",
        "site-packages",
    }

    # Recopilar archivos elegibles primero
    eligible = []
    skipped = 0
    for path in base_dir.rglob("*"):
        if len(eligible) >= max_files:
            break
        if path.is_dir():
            continue
        if any(d in path.parts for d in SKIP_DIRS):
            skipped += 1
            continue
        if path.suffix.lower() in SKIP_EXTS:
            skipped += 1
            continue
        if extensions and path.suffix.lower().lstrip(".") not in extensions:
            skipped += 1
            continue
        if path.stat().st_size > 100 * 1024 * 1024:
            skipped += 1
            continue
        eligible.append(path)

    results = {
        "indexed": 0,
        "updated": 0,
        "unchanged": 0,
        "errors": 0,
        "skipped": skipped,
    }

    # OCR es pesado: no más de 2 workers cuando ocr=True para no saturar RAM
    effective_workers = min(workers, 2) if ocr else min(workers, 8)

    def _process(path):
        try:
            data = _extract_for_index(path, db_path, ocr=ocr, whisper=False)
            if data.get("_skip"):
                return "unchanged"
            wr = _write_to_db(data, db_path)
            return wr.get("status", "indexed") if wr.get("ok") else "error"
        except Exception as e:
            logger.error(f"Error procesando {path}: {e}")
            return "error"

    with ThreadPoolExecutor(max_workers=effective_workers) as pool:
        futures = {pool.submit(_process, p): p for p in eligible}
        for future in as_completed(futures):
            status = future.result()
            results[status] = results.get(status, 0) + 1

    results["total"] = len(eligible)
    results["ok"] = True
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Búsqueda
# ═══════════════════════════════════════════════════════════════════════════════


def search(
    query: str,
    db_path: str = None,
    limit: int = 50,
    fuzzy: bool = True,
    doc_type: str = None,
    ext_filter: list = None,
) -> dict:
    """
    Búsqueda full-text con FTS5 + fuzzy fallback.
    Retorna lista de {path, file_name, ext, snippet, score, doc_type}.
    """
    if not query.strip():
        return {"ok": False, "results": [], "error": "Query vacía"}

    conn = _get_conn(db_path)
    try:
        results = _search_fts5(conn, query, limit, doc_type, ext_filter)

        # Si FTS5 no da suficientes resultados, intentar con query normalizada
        if len(results) < 5:
            q_norm = normalize_query(query)
            if q_norm != query.lower():
                extra = _search_fts5(
                    conn, q_norm, limit - len(results), doc_type, ext_filter
                )
                seen = {r["path"] for r in results}
                results += [r for r in extra if r["path"] not in seen]

        # Fuzzy fallback si FTS5 no encontró nada
        if not results and fuzzy:
            results = _search_fuzzy(conn, query, limit, doc_type)

        return {
            "ok": True,
            "results": results[:limit],
            "total": len(results),
            "query": query,
            "fuzzy_used": not results,
        }
    finally:
        conn.close()


def _search_fts5(
    conn, query: str, limit: int, doc_type: str = None, ext_filter: list = None
) -> list:
    try:
        # Escapar query para FTS5 (comillas simples)
        safe_q = query.replace('"', '""')

        sql = """
            SELECT d.path, d.file_name, d.ext, d.doc_type,
                   bm25(docs_fts) AS score,
                   snippet(docs_fts, 2, '<b>', '</b>', '…', 20) AS snippet
            FROM docs_fts
            JOIN documents d ON docs_fts.rowid = d.id
            WHERE docs_fts MATCH ?
        """
        params = [f'"{safe_q}"']

        if doc_type:
            sql += " AND d.doc_type = ?"
            params.append(doc_type)
        if ext_filter:
            placeholders = ",".join("?" * len(ext_filter))
            sql += f" AND d.ext IN ({placeholders})"
            params.extend(ext_filter)

        sql += " ORDER BY score LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.debug(f"FTS5 error: {e}")
        # Intentar sin comillas
        try:
            safe_q2 = re.sub(r"[^\w\s]", " ", query)
            rows = conn.execute(
                "SELECT d.path, d.file_name, d.ext, d.doc_type, bm25(docs_fts) AS score,"
                " snippet(docs_fts, 2, '<b>', '</b>', '…', 20) AS snippet"
                " FROM docs_fts JOIN documents d ON docs_fts.rowid = d.id"
                " WHERE docs_fts MATCH ? ORDER BY score LIMIT ?",
                [safe_q2, limit],
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            return []


def _search_fuzzy(conn, query: str, limit: int, doc_type: str = None) -> list:
    """Búsqueda fuzzy como último recurso (busca en todos los textos indexados)."""
    try:
        from fuzzywuzzy import fuzz

        q_norm = normalize(query)
        sql = "SELECT path, file_name, ext, doc_type, text FROM docs_fts"
        if doc_type:
            sql += f" JOIN documents d ON docs_fts.rowid = d.id WHERE d.doc_type = '{doc_type}'"

        rows = conn.execute(sql).fetchall()
        scored = []
        for row in rows:
            text_norm = normalize(str(row["text"] or ""))
            score = fuzz.partial_ratio(q_norm, text_norm[:5000])
            if score >= 60:
                # Encontrar snippet
                idx = text_norm.find(q_norm[:20])
                snippet_start = max(0, idx - 80)
                snippet = (row["text"] or "")[snippet_start : snippet_start + 200]
                scored.append(
                    {
                        "path": row["path"],
                        "file_name": row["file_name"],
                        "ext": row["ext"],
                        "doc_type": row["doc_type"],
                        "score": score / 100,
                        "snippet": snippet,
                        "fuzzy": True,
                    }
                )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]
    except Exception as e:
        logger.debug(f"Fuzzy search error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Estado del índice
# ═══════════════════════════════════════════════════════════════════════════════


def index_stats(db_path: str = None) -> dict:
    """Estadísticas del índice de búsqueda."""
    try:
        conn = _get_conn(db_path)
        cur = conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        by_ext = cur.execute(
            "SELECT ext, COUNT(*) as n FROM documents GROUP BY ext ORDER BY n DESC LIMIT 15"
        ).fetchall()
        by_type = cur.execute(
            "SELECT doc_type, COUNT(*) as n FROM documents GROUP BY doc_type ORDER BY n DESC"
        ).fetchall()
        total_chars = cur.execute("SELECT SUM(chars) FROM documents").fetchone()[0] or 0
        conn.close()
        return {
            "ok": True,
            "total_files": total,
            "total_chars": total_chars,
            "by_extension": [dict(r) for r in by_ext],
            "by_doc_type": [dict(r) for r in by_type],
            "db_path": db_path or INDEX_DB,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
