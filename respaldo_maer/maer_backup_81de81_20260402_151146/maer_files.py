#!/usr/bin/env python3
# 🦁 MAER FILES BACKEND v2.0 — Motor de análisis documental multimodal
# Leonel Mojica — Ecatepec MX — 2026

import os
import sys
import json
import re
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Asegurar que el directorio padre está en sys.path para imports de maer_backend.*
_THIS_DIR = Path(__file__).parent.resolve()
_PROJECT_DIR = _THIS_DIR.parent.resolve()
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))


# ── Logging JSON estructurado ──
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","msg":"%(message)s"}',
    stream=sys.stderr,
)
logger = logging.getLogger("maer")

# ── Cargar .env si existe ──
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Cargado .env desde {env_path}")
except ImportError:
    pass

# ── Imports base ──
from pypdf import PdfReader
from docx import Document
from PIL import Image
import requests

# ── Config ──
API_CURP_URL = os.environ.get("API_CURP_URL", "https://api-curp-renapo.ejemplo.com/curp")
API_CURP_TOKEN = os.environ.get("API_CURP_TOKEN", "")
MAER_OCR_ENGINE = os.environ.get("MAER_OCR_ENGINE", "auto")

TEXT_EXTS = {
    ".txt", ".md", ".log",
    ".py", ".js", ".mjs", ".ts", ".mts", ".jsx", ".tsx",
    ".html", ".htm", ".css",
    ".json", ".yml", ".yaml", ".xml",
    ".c", ".cpp", ".h", ".hpp",
    ".java", ".php", ".rb", ".go", ".rs",
    ".sh", ".bash", ".zsh",
    ".sql", ".csv", ".tsv",
}

DOC_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}

# ── Directorios excluidos de indexación ──
EXCLUDED_DIRS = set(
    os.environ.get("MAER_EXCLUDED_DIRS",
                   ".git,.svn,.hg,node_modules,__pycache__,.venv,venv,.ssh,.gnupg,.aws,.config,.Trash,Library").split(",")
)

EXCLUDED_EXTS = {".key", ".pem", ".p12", ".pfx", ".keystore", ".DS_Store"}


# ═══════════════════════════════════════════════════════════
# Respuesta uniforme
# ═══════════════════════════════════════════════════════════

def make_response(ok: bool, code: str, message: str, data: dict = None) -> dict:
    """Esquema de respuesta uniforme para TODAS las acciones."""
    return {
        "ok": ok,
        "code": code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data or {},
    }


# ═══════════════════════════════════════════════════════════
# Regex documentos oficiales MX
# ═══════════════════════════════════════════════════════════

CURP_REGEX_COMPLETA = re.compile(
    r"^"
    r"([A-Z][AEIOU][A-Z]{2}"
    r"\d{2}"
    r"(?:0[1-9]|1[0-2])"
    r"(?:0[1-9]|[12]\d|3[01])"
    r"[HM]"
    r"(?:AS|B[CS]|C[CLMSH]|D[FG]|G[TR]|"
    r"HG|JC|M[CNS]|N[ETL]|OC|PL|Q[TR]|"
    r"S[PLR]|T[CSL]|VZ|YN|ZS|NE)"  # NE = nacido en el extranjero
    r"[B-DF-HJ-NP-TV-Z]{3}"
    r"[A-Z0-9])"
    r"(\d)"
    r"$",
    re.IGNORECASE,
)

CURP_REGEX_SEARCH = re.compile(
    r"\b[A-Z][AEIOU][A-Z]{2}\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])[HM]"
    r"(?:AS|B[CS]|C[CLMSH]|D[FG]|G[TR]|HG|JC|M[CNS]|N[ETL]|OC|PL|Q[TR]|S[PLR]|"
    r"T[CSL]|VZ|YN|ZS|NE)[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9]\d\b",
    re.IGNORECASE,
)

RFC_REGEX = re.compile(
    r"\b"
    r"[A-ZÑ&]{3,4}"
    r"\d{2}"
    r"(0[1-9]|1[0-2])"
    r"(0[1-9]|[12]\d|3[01])"
    r"[A-Z0-9]{3}"
    r"\b",
    re.IGNORECASE,
)

# INE: Clave de elector tiene formato específico (sección electoral + año + secuencial)
INE_CLAVE_REGEX = re.compile(
    r"\b(?:IDMEX)?\d{6}[A-Z]\d{8}[HM]\d{3}\b",
    re.IGNORECASE,
)

# Datos asociados
EMAIL_REGEX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_REGEX = re.compile(r"\b(?:\+?52)?[\s-]?(?:\d[\s-]?){8,12}\d\b")
NSS_REGEX = re.compile(r"\b\d{11}\b")


# ═══════════════════════════════════════════════════════════
# Validaciones
# ═══════════════════════════════════════════════════════════

RFC_DIC = "0123456789ABCDEFGHIJKLMN&OPQRSTUVWXYZ Ñ"

def normalize_id(s: str) -> str:
    return s.strip().upper().replace("-", "").replace(" ", "")


def rfc_valido(rfc: str, aceptar_generico: bool = True):
    rfc = normalize_id(rfc)
    m = re.match(r"^([A-ZÑ&]{3,4})(\d{6})([A-Z0-9]{3})$", rfc)
    if not m:
        return False

    cuerpo = m.group(0)[:-1]
    dv_real = m.group(0)[-1]
    len_cuerpo = len(cuerpo)

    suma = 0 if len_cuerpo == 12 else 481
    for i, ch in enumerate(cuerpo):
        v = RFC_DIC.find(ch)
        if v == -1:
            return False
        suma += v * (len_cuerpo + 1 - i)

    dig_esp = 11 - (suma % 11)
    if dig_esp == 11:
        dig_esp = "0"
    elif dig_esp == 10:
        dig_esp = "A"
    else:
        dig_esp = str(dig_esp)

    if dv_real != dig_esp:
        if not aceptar_generico:
            return False
        if rfc not in ("XAXX010101000", "XEXX010101000"):
            return False
    return rfc


CURP_DIC = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"

def curp_valida(curp: str):
    curp = normalize_id(curp)
    m = CURP_REGEX_COMPLETA.match(curp)
    if not m:
        return False

    curp17 = curp[:17]
    suma = 0
    for i, ch in enumerate(curp17):
        idx = CURP_DIC.find(ch)
        if idx == -1:
            return False
        suma += idx * (18 - i)
    dig = 10 - (suma % 10)
    if dig == 10:
        dig = 0
    dv_esp = str(dig)
    dv_real = curp[17]
    if dv_real != dv_esp:
        return False
    return curp


def curp_tronco(curp: str):
    curp = normalize_id(curp)
    return curp[:16] if len(curp) >= 16 else curp


# ═══════════════════════════════════════════════════════════
# Utilidades
# ═══════════════════════════════════════════════════════════

def is_text_like(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTS


def safe_read_text(path: Path, max_bytes: int = 512 * 1024) -> str:
    try:
        with open(path, "rb") as f:
            data = f.read(max_bytes)
        return data.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[ERROR LEYENDO ARCHIVO: {e}]"


def walk_files(base: Path, max_files: int = 5000):
    """Recorre archivos con exclusiones de seguridad."""
    count = 0
    for root, dirs, files in os.walk(base):
        # Filtrar directorios sensibles IN-PLACE
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for name in files:
            if count >= max_files:
                return
            p = Path(root) / name
            if p.suffix.lower() in EXCLUDED_EXTS:
                continue
            count += 1
            yield p


def file_hash_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ═══════════════════════════════════════════════════════════
# Extracción de texto
# ═══════════════════════════════════════════════════════════

def extract_text_from_pdf(path: Path, ocr_if_needed: bool = True, max_pages: int = 50) -> str:
    text_direct = ""
    try:
        reader = PdfReader(str(path))
        num_pages = min(len(reader.pages), max_pages)
        for i in range(num_pages):
            page = reader.pages[i]
            text_direct += page.extract_text() or ""
    except Exception:
        text_direct = ""

    if text_direct and len(text_direct.strip()) > 100:
        return text_direct

    if not ocr_if_needed:
        return text_direct

    # Usar motor OCR multimodal
    try:
        from maer_backend.ocr_engine import ocr_pdf
        result = ocr_pdf(path, engine=MAER_OCR_ENGINE, max_pages=max_pages)
        if result.get("ok"):
            return result["text"]
    except ImportError:
        pass

    # Fallback a Tesseract directo
    try:
        import pytesseract
        from pdf2image import convert_from_path

        pages = convert_from_path(str(path), dpi=300, first_page=1, last_page=max_pages)
        ocr_text = []
        for idx, img in enumerate(pages):
            if idx >= max_pages:
                break
            try:
                img = img.convert("L")
                txt = pytesseract.image_to_string(img, lang="spa+eng")
                ocr_text.append(txt)
            except Exception as e:
                ocr_text.append(f"[ERROR OCR PÁGINA {idx+1}: {e}]")
        return text_direct + "\n" + "\n".join(ocr_text)
    except Exception as e:
        return text_direct + f"\n[ERROR OCR-PDF: {e}]"


def extract_text_from_docx(path: Path) -> str:
    try:
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception as e:
        return f"[ERROR LEYENDO DOCX: {e}]"


def extract_text_generic(path: Path, use_ocr_for_pdf: bool = True) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path, ocr_if_needed=use_ocr_for_pdf)
    if ext == ".docx":
        return extract_text_from_docx(path)
    if ext in IMAGE_EXTS:
        try:
            from maer_backend.ocr_engine import ocr_image
            result = ocr_image(path, engine=MAER_OCR_ENGINE)
            if result.get("ok"):
                return result["text"]
        except ImportError:
            pass
        # Fallback Tesseract directo
        try:
            import pytesseract
            img = Image.open(str(path)).convert("L")
            return pytesseract.image_to_string(img, lang="spa+eng")
        except Exception as e:
            return f"[ERROR OCR IMAGEN: {e}]"
    if is_text_like(path):
        return safe_read_text(path)
    return "[TIPO DE ARCHIVO NO SOPORTADO PARA EXTRACCIÓN DIRECTA]"


# ═══════════════════════════════════════════════════════════
# Detección de IDs
# ═══════════════════════════════════════════════════════════

def detect_ids_in_text(text: str):
    curp_candidates = set(m.group(0).upper() for m in CURP_REGEX_SEARCH.finditer(text))
    curps_validas = []
    curps_invalidas = []
    for c in curp_candidates:
        ok = curp_valida(c)
        if ok:
            curps_validas.append(ok)
        else:
            curps_invalidas.append(c)

    homonimias = {}
    troncos = {}
    for c in curps_validas:
        t = curp_tronco(c)
        troncos.setdefault(t, []).append(c)
    for t, lista in troncos.items():
        if len(lista) > 1:
            homonimias[t] = sorted(lista)

    rfc_candidates = set(m.group(0).upper() for m in RFC_REGEX.finditer(text))
    rfcs_validos = []
    for r in rfc_candidates:
        ok = rfc_valido(r)
        if ok:
            rfcs_validos.append(ok)

    ines = list(set(m.group(0).upper() for m in INE_CLAVE_REGEX.finditer(text)))

    return {
        "curp_validas": sorted(set(curps_validas)),
        "curp_invalidas": sorted(set(curps_invalidas)),
        "curp_homonimias": homonimias,
        "rfc_validos": sorted(set(rfcs_validos)),
        "ine_clave": ines,
    }


def extract_related_info(text: str):
    emails = list(set(m.group(0) for m in EMAIL_REGEX.finditer(text)))
    phones = list(set(m.group(0) for m in PHONE_REGEX.finditer(text)))
    nss = list(set(m.group(0) for m in NSS_REGEX.finditer(text)))
    return {"emails": emails, "phones": phones, "nss_candidates": nss}


# ═══════════════════════════════════════════════════════════
# Acciones (todas con respuesta uniforme)
# ═══════════════════════════════════════════════════════════

def action_search_files(payload: dict):
    base_dir = Path(payload.get("base_dir") or str(Path.home()))
    query = str(payload.get("query") or "").strip()
    mode = payload.get("mode") or "both"
    max_results = int(payload.get("max_results") or 100)

    if not query:
        return make_response(False, "SEARCH_EMPTY", "Query vacío", {"results": []})

    q_lower = query.lower()
    results = []

    for path in walk_files(base_dir):
        if len(results) >= max_results:
            break

        name_match = q_lower in path.name.lower()
        content_match = False

        if mode in ("content", "both") and is_text_like(path):
            text = safe_read_text(path)
            if q_lower in text.lower():
                content_match = True

        if mode == "name" and name_match:
            results.append({"path": str(path), "match": "name"})
        elif mode == "content" and content_match:
            results.append({"path": str(path), "match": "content"})
        elif mode == "both" and (name_match or content_match):
            results.append({
                "path": str(path),
                "match": "name+content" if (name_match and content_match) else ("name" if name_match else "content"),
            })

    return make_response(True, "SEARCH_OK", f"{len(results)} resultados encontrados", {
        "query": query, "base_dir": str(base_dir), "mode": mode, "results": results
    })


def action_analyze_file(payload: dict):
    path = Path(payload.get("path") or "")
    if not path.exists():
        return make_response(False, "FILE_NOT_FOUND", f"Archivo no existe: {path}")

    info = {
        "path": str(path),
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "ext": path.suffix.lower(),
        "is_text_like": is_text_like(path),
        "hash_sha256": file_hash_sha256(path),
    }

    if is_text_like(path):
        text = safe_read_text(path, max_bytes=256 * 1024)
        info["preview"] = "\n".join(text.splitlines()[:50])
        info["line_count"] = text.count("\n") + 1
    elif path.suffix.lower() in IMAGE_EXTS:
        try:
            img = Image.open(str(path))
            info["width"] = img.width
            info["height"] = img.height
            info["image_mode"] = img.mode
        except Exception:
            pass
        info["preview"] = "[ARCHIVO IMAGEN]"
    else:
        info["preview"] = "[ARCHIVO NO TEXTO]"
        info["line_count"] = None

    return make_response(True, "ANALYZE_OK", f"Análisis completo: {path.name}", {"info": info})


def action_fix_code_file(payload: dict):
    path = Path(payload.get("path") or "")
    mode = payload.get("mode") or "strip_trailing"

    if not path.exists():
        return make_response(False, "FILE_NOT_FOUND", f"Archivo no existe: {path}")
    if not is_text_like(path):
        return make_response(False, "NOT_TEXT_FILE", "Solo se corrigen archivos de texto/código")

    text = safe_read_text(path)
    original = text

    if mode == "strip_trailing":
        fixed_lines = [line.rstrip() for line in text.splitlines()]
        fixed_text = "\n".join(fixed_lines) + ("\n" if text.endswith("\n") else "")
    else:
        return make_response(False, "UNSUPPORTED_MODE", f"Modo no soportado: {mode}")

    if fixed_text == original:
        return make_response(True, "FIX_NO_CHANGE", "No hubo cambios", {
            "changed": False, "path": str(path)
        })

    backup_path = path.with_suffix(path.suffix + ".maer.bak")
    try:
        backup_path.write_text(original, encoding="utf-8", errors="ignore")
        path.write_text(fixed_text, encoding="utf-8", errors="ignore")
    except Exception as e:
        return make_response(False, "FIX_ERROR", f"Error escribiendo archivo: {e}")

    return make_response(True, "FIX_OK", "Archivo corregido correctamente", {
        "changed": True, "path": str(path), "backup": str(backup_path),
        "details": f"Se quitaron espacios finales de cada línea. Backup en {backup_path}",
    })


def action_extract_text(payload: dict):
    path = Path(payload.get("path") or "")
    if not path.exists():
        return make_response(False, "FILE_NOT_FOUND", f"Archivo no existe: {path}")

    ocr_for_pdf = payload.get("ocr_for_pdf", True)
    max_chars = int(payload.get("max_chars") or 0)

    text = extract_text_generic(path, use_ocr_for_pdf=ocr_for_pdf)
    truncated = False
    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars]
        truncated = True

    return make_response(True, "EXTRACT_OK", f"Texto extraído: {len(text)} caracteres", {
        "path": str(path), "ext": path.suffix.lower(), "length": len(text),
        "truncated": truncated, "text": text
    })


def action_index_full(payload: dict):
    base_dir = Path(payload.get("base_dir") or str(Path.home()))
    out_file = Path(payload.get("out_file") or (base_dir / "maer_index.json"))
    max_files = int(payload.get("max_files") or 500)
    ocr_for_pdf = payload.get("ocr_for_pdf", True)
    snippet_chars = int(payload.get("snippet_chars") or 1000)

    index_entries = []
    processed = 0
    errors = 0

    for path in walk_files(base_dir, max_files=max_files):
        ext = path.suffix.lower()
        if not (is_text_like(path) or ext in {".pdf", ".docx"} or ext in IMAGE_EXTS):
            continue
        try:
            text = extract_text_generic(path, use_ocr_for_pdf=ocr_for_pdf)
        except Exception as e:
            text = f"[ERROR: {e}]"
            errors += 1
        snippet = text[:snippet_chars]
        entry = {
            "path": str(path),
            "ext": ext,
            "size_bytes": path.stat().st_size,
            "hash": file_hash_sha256(path),
            "snippet": snippet,
        }
        # Metadatos extra para imágenes
        if ext in IMAGE_EXTS:
            try:
                img = Image.open(str(path))
                entry["width"] = img.width
                entry["height"] = img.height
            except Exception:
                pass
        index_entries.append(entry)
        processed += 1

    out_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(index_entries, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return make_response(False, "INDEX_WRITE_ERROR", f"Error escribiendo índice: {e}")

    return make_response(True, "INDEX_OK", f"Indexación completa: {processed} archivos", {
        "base_dir": str(base_dir), "out_file": str(out_file),
        "processed": processed, "errors": errors,
    })


def action_search_index(payload: dict):
    index_file = payload.get("index_file")
    base_dir = payload.get("base_dir")
    query = str(payload.get("query") or "").strip()
    max_results = int(payload.get("max_results") or 50)

    if not index_file:
        if not base_dir:
            return make_response(False, "MISSING_PARAMS", "Debe proporcionar 'index_file' o 'base_dir'")
        index_file = str(Path(base_dir) / "maer_index.json")

    idx_path = Path(index_file)
    if not idx_path.exists():
        return make_response(False, "INDEX_NOT_FOUND", f"Índice JSON no existe: {idx_path}")
    if not query:
        return make_response(False, "SEARCH_EMPTY", "Query vacío")

    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except Exception as e:
        return make_response(False, "INDEX_READ_ERROR", f"Error leyendo índice: {e}")

    q_lower = query.lower()
    results = []
    for entry in entries:
        if len(results) >= max_results:
            break
        snippet = str(entry.get("snippet") or "")
        if q_lower in snippet.lower() or q_lower in str(entry.get("path", "")).lower():
            results.append({
                "path": entry.get("path"),
                "ext": entry.get("ext"),
                "size_bytes": entry.get("size_bytes"),
                "snippet_preview": snippet[:300],
            })

    return make_response(True, "SEARCH_INDEX_OK", f"{len(results)} resultados en índice", {
        "query": query, "index_file": str(idx_path), "results": results,
    })


def action_detect_ids(payload: dict):
    mode = payload.get("mode") or "file"

    if mode == "file":
        path = Path(payload.get("path") or "")
        if not path.exists():
            return make_response(False, "FILE_NOT_FOUND", f"Archivo no existe: {path}")
        ocr_for_pdf = payload.get("ocr_for_pdf", True)
        text = extract_text_generic(path, use_ocr_for_pdf=ocr_for_pdf)
        ids = detect_ids_in_text(text)
        related = extract_related_info(text)
        return make_response(True, "DETECT_IDS_OK", "IDs detectados en archivo", {
            "mode": "file", "path": str(path), "ids": ids, "related": related,
        })

    elif mode == "index":
        index_file = payload.get("index_file")
        base_dir = payload.get("base_dir")
        max_entries = int(payload.get("max_entries") or 500)

        if not index_file:
            if not base_dir:
                return make_response(False, "MISSING_PARAMS", "Debe proporcionar 'index_file' o 'base_dir' en modo index")
            index_file = str(Path(base_dir) / "maer_index.json")

        idx_path = Path(index_file)
        if not idx_path.exists():
            return make_response(False, "INDEX_NOT_FOUND", f"Índice no existe: {idx_path}")

        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception as e:
            return make_response(False, "INDEX_READ_ERROR", f"Error leyendo índice: {e}")

        found = []
        for entry in entries[:max_entries]:
            snippet = str(entry.get("snippet") or "")
            ids = detect_ids_in_text(snippet)
            if ids["curp_validas"] or ids["curp_invalidas"] or ids["rfc_validos"] or ids["ine_clave"]:
                related = extract_related_info(snippet)
                found.append({
                    "path": entry.get("path"),
                    "ext": entry.get("ext"),
                    "ids": ids,
                    "related": related,
                })

        return make_response(True, "DETECT_IDS_INDEX_OK",
                           f"{len(found)} archivos con IDs detectados", {
            "mode": "index", "index_file": str(idx_path),
            "checked_entries": min(len(entries), max_entries), "matches": found,
        })
    else:
        return make_response(False, "UNSUPPORTED_MODE", f"Modo no soportado: {mode}")


def action_detect_related(payload: dict):
    id_value = normalize_id(payload.get("id_value") or "")
    if not id_value:
        return make_response(False, "EMPTY_ID", "id_value vacío")

    id_type = None
    if curp_valida(id_value):
        id_type = "CURP_VALIDA"
    elif CURP_REGEX_SEARCH.match(id_value):
        id_type = "CURP_INVALIDA"
    elif rfc_valido(id_value):
        id_type = "RFC_VALIDO"
    elif INE_CLAVE_REGEX.match(id_value):
        id_type = "INE_CLAVE"
    else:
        id_type = "UNKNOWN_FORMAT"

    index_file = payload.get("index_file")
    base_dir = payload.get("base_dir")
    max_entries = int(payload.get("max_entries") or 500)

    if not index_file:
        if not base_dir:
            return make_response(False, "MISSING_PARAMS", "Debe proporcionar 'index_file' o 'base_dir'")
        index_file = str(Path(base_dir) / "maer_index.json")

    idx_path = Path(index_file)
    if not idx_path.exists():
        return make_response(False, "INDEX_NOT_FOUND", f"Índice no existe: {idx_path}")

    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except Exception as e:
        return make_response(False, "INDEX_READ_ERROR", f"Error leyendo índice: {e}")

    matches = []
    for entry in entries[:max_entries]:
        snippet = str(entry.get("snippet") or "")
        if id_value in snippet.replace(" ", "").upper() or id_value in snippet.upper():
            related = extract_related_info(snippet)
            matches.append({
                "path": entry.get("path"),
                "ext": entry.get("ext"),
                "snippet_preview": snippet[:300],
                "related": related,
            })

    return make_response(True, "DETECT_RELATED_OK",
                       f"{len(matches)} archivos con {id_type}", {
        "id_value": id_value, "id_type": id_type,
        "index_file": str(idx_path),
        "checked_entries": min(len(entries), max_entries),
        "matches": matches,
    })


def action_curp_renapo_check(payload: dict):
    curp = payload.get("curp") or ""
    if not curp:
        return make_response(False, "EMPTY_CURP", "CURP vacío")

    curp = normalize_id(curp)
    if not curp_valida(curp):
        return make_response(False, "INVALID_CURP", "La CURP no pasa validación local", {
            "curp": curp, "source": "local", "status": "INVALID_LOCAL",
        })

    headers = {"Accept": "application/json"}
    if API_CURP_TOKEN:
        headers["Authorization"] = f"Bearer {API_CURP_TOKEN}"

    try:
        resp = requests.get(
            API_CURP_URL, params={"curp": curp},
            headers=headers, timeout=10,
        )
    except Exception as e:
        return make_response(False, "API_ERROR", f"Error al llamar API CURP: {e}", {
            "curp": curp, "source": "remote", "status": "ERROR",
        })

    try:
        data = resp.json()
    except Exception:
        return make_response(False, "API_PARSE_ERROR", "Respuesta no JSON", {
            "curp": curp, "source": "remote", "raw": resp.text[:500],
        })

    status = data.get("status") or ("VALID" if data.get("success") else "INVALID")
    return make_response(bool(data.get("success", False)), "RENAPO_CHECK_OK",
                       f"CURP verificada: {status}", {
        "curp": curp, "source": "remote", "status": status, "raw": data,
    })


# ═══════════════════════════════════════════════════════════
# Nuevas acciones multimodales
# ═══════════════════════════════════════════════════════════

def action_ocr_multimodal(payload: dict):
    """OCR con selección de motor."""
    path = Path(payload.get("path") or "")
    engine = payload.get("engine") or MAER_OCR_ENGINE
    use_cache = payload.get("use_cache", True)

    if not path.exists():
        return make_response(False, "FILE_NOT_FOUND", f"Archivo no existe: {path}")

    ext = path.suffix.lower()
    try:
        from maer_backend.ocr_engine import ocr_pdf, ocr_image
        if ext == ".pdf":
            result = ocr_pdf(path, engine=engine, use_cache=use_cache)
        elif ext in IMAGE_EXTS:
            result = ocr_image(path, engine=engine, use_cache=use_cache)
        else:
            return make_response(False, "UNSUPPORTED_TYPE",
                               f"OCR no soportado para: {ext}")

        return make_response(result.get("ok", False), "OCR_OK", "OCR completado", result)
    except ImportError:
        return make_response(False, "OCR_ENGINE_MISSING",
                           "Motor OCR no disponible. Verifica instalación.")


def action_extract_tables(payload: dict):
    """Extrae tablas de un PDF."""
    path = Path(payload.get("path") or "")
    if not path.exists():
        return make_response(False, "FILE_NOT_FOUND", f"Archivo no existe: {path}")

    try:
        from maer_backend.table_extractor import extract_tables_from_pdf
        result = extract_tables_from_pdf(path, max_pages=int(payload.get("max_pages") or 50))
        return make_response(result.get("ok", False), "TABLES_OK",
                           f"{result.get('total_tables', 0)} tablas encontradas", result)
    except ImportError:
        return make_response(False, "PDFPLUMBER_MISSING", "pdfplumber no instalado")


def action_nlp_entities(payload: dict):
    """Detecta entidades con NLP."""
    text = payload.get("text") or ""
    path = payload.get("path")

    if path:
        p = Path(path)
        if p.exists():
            text = extract_text_generic(p)

    if not text:
        return make_response(False, "EMPTY_TEXT", "Texto vacío para NLP")

    try:
        from maer_backend.nlp_engine import extract_entities, classify_document
        entities = extract_entities(text)
        classification = classify_document(text)
        return make_response(True, "NLP_OK", "Entidades extraídas", {
            "entities": entities, "classification": classification,
        })
    except ImportError:
        return make_response(False, "SPACY_MISSING", "spaCy no instalado")


def action_image_duplicates(payload: dict):
    """Encuentra imágenes duplicadas."""
    base_dir = Path(payload.get("base_dir") or "")
    threshold = int(payload.get("threshold") or 10)
    max_files = int(payload.get("max_files") or 1000)

    if not base_dir.exists():
        return make_response(False, "DIR_NOT_FOUND", f"Directorio no existe: {base_dir}")

    try:
        from maer_backend.image_analyzer import find_duplicates
        result = find_duplicates(base_dir, threshold=threshold, max_files=max_files)
        return make_response(result.get("ok", False), "DUPLICATES_OK",
                           f"{result.get('total_groups', 0)} grupos de duplicados", result)
    except ImportError:
        return make_response(False, "IMAGEHASH_MISSING", "imagehash no instalado")


def action_face_detect(payload: dict):
    """Detecta y agrupa rostros."""
    path = payload.get("path")
    base_dir = payload.get("base_dir")

    if path:
        p = Path(path)
        if not p.exists():
            return make_response(False, "FILE_NOT_FOUND", f"Archivo no existe: {p}")
        try:
            from maer_backend.image_analyzer import detect_faces
            result = detect_faces(p)
            return make_response(result.get("ok", False), "FACES_OK",
                               f"{result.get('total_faces', 0)} rostros detectados", result)
        except ImportError:
            return make_response(False, "DEEPFACE_MISSING", "DeepFace no instalado")

    elif base_dir:
        bd = Path(base_dir)
        if not bd.exists():
            return make_response(False, "DIR_NOT_FOUND", f"Directorio no existe: {bd}")
        try:
            from maer_backend.image_analyzer import find_and_group_faces
            result = find_and_group_faces(bd, max_files=int(payload.get("max_files") or 200))
            return make_response(result.get("ok", False), "FACES_GROUP_OK",
                               f"{result.get('total_groups', 0)} grupos de rostros", result)
        except ImportError:
            return make_response(False, "DEEPFACE_MISSING", "DeepFace no instalado")

    return make_response(False, "MISSING_PARAMS", "Proporciona 'path' o 'base_dir'")


def action_cluster_files(payload: dict):
    """Clustering automático de archivos."""
    base_dir = Path(payload.get("base_dir") or "")
    cluster_type = payload.get("type") or "images"  # images, text, all

    if not base_dir.exists():
        return make_response(False, "DIR_NOT_FOUND", f"Directorio no existe: {base_dir}")

    if cluster_type == "images":
        try:
            from maer_backend.image_analyzer import cluster_images
            result = cluster_images(base_dir, max_files=int(payload.get("max_files") or 500))
            return make_response(result.get("ok", False), "CLUSTER_OK",
                               f"{result.get('total_clusters', 0)} clusters de imágenes", result)
        except ImportError:
            return make_response(False, "SKLEARN_MISSING", "scikit-learn no instalado")

    return make_response(False, "UNSUPPORTED_TYPE", f"Tipo de clustering no soportado: {cluster_type}")


def action_llm_summarize(payload: dict):
    path = payload.get("path")
    text = payload.get("text")
    if path:
        p = Path(path)
        if p.exists():
            text = extract_text_generic(p)
    if not text:
        return make_response(False, "EMPTY_TEXT", "Proporciona text o un path válido")
        
    try:
        from maer_backend.llm_engine import get_llm_engine
        engine = get_llm_engine()
        res = engine.summarize_text(text)
        return make_response(res.get("ok", False), "LLM_SUMMARIZE_OK" if res.get("ok") else "LLM_ERROR", 
                             "Resumen generado" if res.get("ok") else res.get("error", ""), res)
    except ImportError as e:
        return make_response(False, "LLM_MISSING", f"Librerías LLM no instaladas: {e}")
    except Exception as e:
        return make_response(False, "LLM_FAIL", str(e))

def action_llm_extract_json(payload: dict):
    path = payload.get("path")
    text = payload.get("text")
    schema_desc = payload.get("schema_description", "Extrae todas las entidades clave")
    if path:
        p = Path(path)
        if p.exists():
            text = extract_text_generic(p)
    if not text:
        return make_response(False, "EMPTY_TEXT", "Proporciona text o un path válido")
        
    try:
        from maer_backend.llm_engine import get_llm_engine
        engine = get_llm_engine()
        res = engine.extract_structured_data(text, schema_desc)
        return make_response(res.get("ok", False), "LLM_EXTRACT_OK" if res.get("ok") else "LLM_ERROR", 
                             "Datos extraídos" if res.get("ok") else res.get("error", ""), res)
    except ImportError as e:
        return make_response(False, "LLM_MISSING", f"Librerías LLM no instaladas: {e}")
    except Exception as e:
        return make_response(False, "LLM_FAIL", str(e))

def action_renapo_verify_identity(payload: dict):
    """Acción compuesta: OCR -> Detect IDs -> Verificación LLM"""
    path = payload.get("path")
    if not path or not Path(path).exists():
        return make_response(False, "FILE_NOT_FOUND", "Archivo no proporcionado o no existe")
        
    # 1. Extraer texto
    p = Path(path)
    text = extract_text_generic(p)
    if not text.strip():
        return make_response(False, "EMPTY_TEXT", "No se pudo extraer texto del archivo")
        
    # 2. Detectar IDs
    ids_info = detect_ids_in_text(text)
    curps = ids_info.get("curp_validas", [])
    
    if not curps:
        return make_response(False, "NO_CURP_FOUND", "No se encontraron CURPs válidas en el documento", {"text_preview": text[:200]})
        
    # 3. Validar la primera CURP con "Renapo"
    target_curp = curps[0]
    renapo_res = action_curp_renapo_check({"curp": target_curp})
    status = renapo_res.get("data", {}).get("status", "UNKNOWN")
    
    # 4. Usar LLM para verificar correspondencia
    try:
        from maer_backend.llm_engine import get_llm_engine
        engine = get_llm_engine()
        schema = "Crea un JSON con: {'nombre_completo': '...', 'fecha_nacimiento': '...', 'es_curp_coherente_con_nombre': true o false}"
        llm_res = engine.extract_structured_data(text, schema)
        
        return make_response(True, "RENAPO_VERIFY_OK", "Verificación de identidad completada", {
            "curp_analizada": target_curp,
            "renapo_status": status,
            "llm_analysis": llm_res.get("json", {}),
            "otras_curps_encontradas": curps[1:]
        })
    except ImportError:
        return make_response(True, "RENAPO_VERIFY_PARTIAL", "Verificación básica completada (sin LLM cruzado)", {
            "curp_analizada": target_curp,
            "renapo_status": status,
            "llm_analysis": "Librería LLM no instalada"
        })
    except Exception as e:
         return make_response(False, "RENAPO_VERIFY_FAIL", str(e))


# ═══════════════════════════════════════════════════════════
# Dispatcher
# ═══════════════════════════════════════════════════════════

def action_llm_chat(args):
    """
    args = {"prompt": "...", "path": "opcional"}
    """
    prompt = args.get("prompt", "")
    path = args.get("path")
    context = ""

    if path and Path(path).exists():
        file_path = Path(path)
        if file_path.suffix.lower() == ".pdf":
            import pdfplumber
            try:
                with pdfplumber.open(file_path) as pdf:
                    context = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
            except Exception as e:
                return make_response(False, "PDF_ERROR", f"Error leyendo PDF: {e}")
        else:
            try:
                context = file_path.read_text("utf-8")
            except Exception as e:
                return make_response(False, "READ_ERROR", f"Error leyendo txt: {e}")
    
    final_prompt = prompt
    if context:
        final_prompt = f"Contexto del documento:\n{context[:4000]}\n\nInstrucción: {prompt}"

    try:
        from maer_backend.llm_engine import get_llm_engine
        engine = get_llm_engine()
        result = engine.generate_response(
            prompt=final_prompt,
            system_prompt="Eres un asistente experto de MAER para JUPEM. Responde usando el contexto si se provee, o tu conocimiento general.",
            max_tokens=2048,
            temperature=0.6
        )
        if result.get("ok"):
            return make_response(True, "CHAT_OK", "Chat procesado", {"response": result["text"]})
        else:
            return make_response(False, "CHAT_ERR", result.get("error", "Error desconocido"))
    except Exception as e:
        return make_response(False, "LLM_FAIL", str(e))

ACTIONS = {
    "search_files": action_search_files,
    "analyze_file": action_analyze_file,
    "fix_code_file": action_fix_code_file,
    "extract_text": action_extract_text,
    "index_full": action_index_full,
    "search_index": action_search_index,
    "detect_ids": action_detect_ids,
    "detect_related": action_detect_related,
    "curp_renapo_check": action_curp_renapo_check,
    # Nuevas acciones multimodales
    "ocr_multimodal": action_ocr_multimodal,
    "extract_tables": action_extract_tables,
    "nlp_entities": action_nlp_entities,
    "image_duplicates": action_image_duplicates,
    "face_detect": action_face_detect,
    "cluster_files": action_cluster_files,
    # LLM y Avanzado
    "llm_summarize": action_llm_summarize,
    "llm_extract_json": action_llm_extract_json,
    "llm_chat": action_llm_chat,
    "renapo_verify_identity": action_renapo_verify_identity,
}


def main():
    if len(sys.argv) < 2:
        print(json.dumps(make_response(False, "USAGE_ERROR",
              "Uso: maer_files.py <accion> [json_payload]")))
        return

    action = sys.argv[1]
    payload_raw = sys.argv[2] if len(sys.argv) >= 3 else "{}"

    try:
        payload = json.loads(payload_raw)
    except Exception:
        payload = {}

    func = ACTIONS.get(action)
    if not func:
        print(json.dumps(make_response(False, "UNKNOWN_ACTION",
              f"Acción desconocida: {action}")))
        return

    try:
        result = func(payload)
    except Exception as e:
        logger.error(f"Excepción en {action}: {e}")
        result = make_response(False, "INTERNAL_ERROR", f"Excepción interna: {e}")

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
