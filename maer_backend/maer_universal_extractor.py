#!/usr/bin/env python3
# 🦁 MAER Universal Extractor — Extrae texto de CUALQUIER tipo de archivo
# Leonel Mojica — Ecatepec MX — 2026

"""
Extrae texto de todos los formatos conocidos:
  PDF, Word, Excel, PowerPoint, TXT, CSV, JSON, XML, HTML,
  RTF, EPUB, ODF, Email (.eml/.msg), Markdown, imágenes (OCR),
  audio (Whisper), código fuente, ZIP/RAR (recursivo).
"""

import logging
import os
import zipfile
from pathlib import Path

logger = logging.getLogger("maer.extractor")

# Tesseract con modelos best si están disponibles
TESSDATA_BEST = os.path.expanduser("~/tessdata_best")
TESSERACT_BEST_LANGS = "spa+eng" if os.path.isdir(TESSDATA_BEST) else None


# ═══════════════════════════════════════════════════════════════════════════════
# Router principal
# ═══════════════════════════════════════════════════════════════════════════════


def extract_text(path: Path, ocr: bool = True, whisper: bool = False) -> dict:
    """
    Extrae texto de cualquier archivo.
    Retorna: {ok, text, method, pages, lang, error}
    """
    path = Path(path)
    if not path.exists():
        return {
            "ok": False,
            "text": "",
            "error": f"No existe: {path}",
            "method": "none",
        }

    ext = path.suffix.lower().lstrip(".")
    size = path.stat().st_size

    # Detectar tipo real con libmagic (más fiable que extensión)
    real_type = _detect_type(path)

    result = _route(path, ext, real_type, size, ocr, whisper)
    result["path"] = str(path)
    result["file_name"] = path.name
    result["ext"] = ext
    result["size"] = size
    result["real_type"] = real_type
    if "text" not in result:
        result["text"] = ""
    result["chars"] = len(result.get("text", ""))
    return result


def _detect_type(path: Path) -> str:
    try:
        import magic

        return magic.from_file(str(path), mime=True)
    except Exception as e:
        pass
    try:
        import filetype

        kind = filetype.guess(str(path))
        return kind.mime if kind else ""
    except Exception as e:
        return ""


def _route(
    path: Path, ext: str, real_type: str, size: int, ocr: bool, whisper: bool
) -> dict:
    # ── PDF ───────────────────────────────────────────────────────────────────
    if ext == "pdf" or "pdf" in real_type:
        return _extract_pdf(path, ocr)

    # ── Word ──────────────────────────────────────────────────────────────────
    if ext in ("docx", "doc") or "word" in real_type or "wordprocessing" in real_type:
        return _extract_word(path)

    # ── Excel ─────────────────────────────────────────────────────────────────
    if (
        ext in ("xlsx", "xls", "xlsm")
        or "spreadsheet" in real_type
        or "excel" in real_type
    ):
        return _extract_excel(path)

    # ── PowerPoint ────────────────────────────────────────────────────────────
    if ext in ("pptx", "ppt") or "presentation" in real_type:
        return _extract_pptx(path)

    # ── Imágenes → OCR ────────────────────────────────────────────────────────
    if ext in (
        "jpg",
        "jpeg",
        "png",
        "bmp",
        "tiff",
        "tif",
        "gif",
        "webp",
        "heic",
        "heif",
    ) or real_type.startswith("image/"):
        if ocr:
            return _extract_image_ocr(path)
        return {"ok": True, "text": "", "method": "skip_ocr"}

    # ── Audio → Whisper ───────────────────────────────────────────────────────
    if ext in (
        "mp3",
        "wav",
        "m4a",
        "ogg",
        "flac",
        "aac",
        "wma",
        "opus",
    ) or real_type.startswith("audio/"):
        if whisper:
            return _extract_audio(path)
        return {"ok": True, "text": "", "method": "skip_audio"}

    # ── Video → frames ────────────────────────────────────────────────────────
    if ext in ("mp4", "avi", "mov", "mkv", "webm") or real_type.startswith("video/"):
        if whisper:
            return _extract_video_audio(path)
        return {"ok": True, "text": "", "method": "skip_video"}

    # ── Email .eml ────────────────────────────────────────────────────────────
    if ext == "eml" or "message/rfc822" in real_type:
        return _extract_eml(path)

    # ── Email .msg (Outlook) ──────────────────────────────────────────────────
    if ext == "msg":
        return _extract_msg(path)

    # ── EPUB ──────────────────────────────────────────────────────────────────
    if ext == "epub" or "epub" in real_type:
        return _extract_epub(path)

    # ── RTF ───────────────────────────────────────────────────────────────────
    if ext == "rtf" or "rtf" in real_type:
        return _extract_rtf(path)

    # ── ODF (LibreOffice) ─────────────────────────────────────────────────────
    if ext in ("odt", "ods", "odp") or "opendocument" in real_type:
        return _extract_odf(path)

    # ── CSV ───────────────────────────────────────────────────────────────────
    if ext == "csv":
        return _extract_csv(path)

    # ── JSON ──────────────────────────────────────────────────────────────────
    if ext == "json" or "json" in real_type:
        return _extract_json(path)

    # ── XML / HTML ────────────────────────────────────────────────────────────
    if ext in ("xml", "html", "htm") or "xml" in real_type or "html" in real_type:
        return _extract_markup(path)

    # ── Markdown ──────────────────────────────────────────────────────────────
    if ext in ("md", "markdown"):
        return _extract_markdown(path)

    # ── ZIP / archivos comprimidos (recursivo, sin descomprimir) ─────────────
    if ext in ("zip",) or "zip" in real_type:
        return _extract_zip(path, ocr)

    # ── Texto plano / código fuente ───────────────────────────────────────────
    if ext in (
        "txt",
        "text",
        "log",
        "csv",
        "tsv",
        "py",
        "js",
        "ts",
        "java",
        "c",
        "cpp",
        "h",
        "go",
        "rs",
        "rb",
        "php",
        "swift",
        "kt",
        "sh",
        "bash",
        "zsh",
        "yaml",
        "yml",
        "toml",
        "ini",
        "cfg",
        "conf",
        "env",
    ) or real_type.startswith("text/"):
        return _extract_plain(path)

    # ── Fallback: intentar como texto ─────────────────────────────────────────
    return _extract_plain(path, strict=False)


# ═══════════════════════════════════════════════════════════════════════════════
# Extractores específicos
# ═══════════════════════════════════════════════════════════════════════════════


def _extract_pdf(path: Path, ocr: bool = True) -> dict:
    try:
        from maer_backend.maer_pdf_analyzer import extract_pdf_text_enhanced

        text = extract_pdf_text_enhanced(path)
        if text and len(text.strip()) > 50:
            return {"ok": True, "text": text, "method": "pdfplumber"}
    except Exception as e:
        pass
    if ocr:
        try:
            from maer_backend.maer_ocr_advanced import ocr_document_advanced

            r = ocr_document_advanced(path)
            return {
                "ok": r.get("ok", False),
                "text": r.get("text", ""),
                "method": r.get("engine", "ocr"),
            }
        except Exception as e:
            return {"ok": False, "text": "", "error": str(e), "method": "none"}
    return {"ok": True, "text": "", "method": "no_ocr"}


def _extract_word(path: Path) -> dict:
    try:
        from docx import Document

        doc = Document(str(path))
        parts = []
        for p in doc.paragraphs:
            if p.text.strip():
                parts.append(p.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    c.text.strip() for c in row.cells if c.text.strip()
                )
                if row_text:
                    parts.append(row_text)
        return {"ok": True, "text": "\n".join(parts), "method": "python-docx"}
    except ImportError:
        return {
            "ok": False,
            "text": "",
            "error": "python-docx no instalado",
            "method": "none",
        }
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_excel(path: Path) -> dict:
    try:
        import openpyxl

        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        parts = []
        for sheet in wb.worksheets:
            parts.append(f"[Hoja: {sheet.title}]")
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c) for c in row if c is not None]
                if cells:
                    parts.append(" | ".join(cells))
        return {"ok": True, "text": "\n".join(parts), "method": "openpyxl"}
    except Exception as e:
        # Fallback para .xls
        try:
            import xlrd

            wb = xlrd.open_workbook(str(path))
            parts = []
            for sheet in wb.sheets():
                parts.append(f"[Hoja: {sheet.name}]")
                for row_idx in range(sheet.nrows):
                    row = [
                        str(sheet.cell_value(row_idx, c)) for c in range(sheet.ncols)
                    ]
                    parts.append(" | ".join(row))
            return {"ok": True, "text": "\n".join(parts), "method": "xlrd"}
        except Exception as e2:
            return {"ok": False, "text": "", "error": str(e2), "method": "none"}


def _extract_pptx(path: Path) -> dict:
    try:
        from pptx import Presentation

        prs = Presentation(str(path))
        parts = []
        for i, slide in enumerate(prs.slides, 1):
            parts.append(f"[Diapositiva {i}]")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    parts.append(shape.text.strip())
        return {"ok": True, "text": "\n".join(parts), "method": "python-pptx"}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_image_ocr(path: Path) -> dict:
    try:
        from maer_backend.maer_ocr_advanced import ocr_document_advanced

        r = ocr_document_advanced(path)
        return {
            "ok": r.get("ok", False),
            "text": r.get("text", ""),
            "method": r.get("engine", "ocr"),
            "quality": r.get("quality", 0),
        }
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_audio(path: Path) -> dict:
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(str(path), language="es", fp16=False)
        text = result.get("text", "").strip()
        return {
            "ok": True,
            "text": text,
            "method": "whisper",
            "lang": result.get("language"),
        }
    except ImportError:
        return {
            "ok": False,
            "text": "",
            "error": "openai-whisper no instalado",
            "method": "none",
        }
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_video_audio(path: Path) -> dict:
    """Extrae audio de video y lo transcribe con Whisper. Usa moviepy primero, ffmpeg como fallback."""
    import tempfile

    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            audio_path = Path(f.name)

        extracted = False

        # — moviepy (más robusto, maneja codecs y metadatos correctamente)
        try:
            from moviepy import VideoFileClip

            with VideoFileClip(str(path)) as clip:
                if clip.audio is None:
                    return {"ok": True, "text": "", "method": "moviepy_no_audio"}
                clip.audio.write_audiofile(
                    str(audio_path),
                    fps=16000,
                    nbytes=2,
                    ffmpeg_params=["-ac", "1"],
                    logger=None,
                )
            extracted = audio_path.exists() and audio_path.stat().st_size > 1000
        except Exception as e:
            pass

        # — ffmpeg directo como fallback
        if not extracted:
            import subprocess

            proc = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(path),
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-y",
                    str(audio_path),
                ],
                capture_output=True,
                timeout=120,
            )
            extracted = (
                proc.returncode == 0
                and audio_path.exists()
                and audio_path.stat().st_size > 1000
            )

        if not extracted:
            return {
                "ok": False,
                "text": "",
                "error": "No se pudo extraer audio del video",
                "method": "none",
            }

        result = _extract_audio(audio_path)
        result["method"] = (
            "moviepy+whisper"
            if "moviepy" in str(result.get("method", ""))
            else "ffmpeg+whisper"
        )
        return result

    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}
    finally:
        if audio_path and audio_path.exists():
            audio_path.unlink(missing_ok=True)


def _extract_eml(path: Path) -> dict:
    try:
        import email

        with open(str(path), "rb") as f:
            msg = email.message_from_bytes(f.read())
        parts = [
            f"De: {msg.get('From','')}",
            f"Para: {msg.get('To','')}",
            f"Asunto: {msg.get('Subject','')}",
            f"Fecha: {msg.get('Date','')}",
        ]
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                try:
                    parts.append(
                        part.get_payload(decode=True).decode("utf-8", errors="replace")
                    )
                except Exception as e:
                    pass
        return {"ok": True, "text": "\n".join(parts), "method": "email"}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_msg(path: Path) -> dict:
    try:
        import extract_msg

        with extract_msg.openMsg(str(path)) as msg:
            parts = [
                f"De: {msg.sender}",
                f"Para: {msg.to}",
                f"Asunto: {msg.subject}",
                f"Fecha: {msg.date}",
                msg.body or "",
            ]
        return {
            "ok": True,
            "text": "\n".join(str(p) for p in parts if p),
            "method": "extract-msg",
        }
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_epub(path: Path) -> dict:
    try:
        from html.parser import HTMLParser

        import ebooklib
        from ebooklib import epub

        class _Strip(HTMLParser):
            def __init__(self):
                super().__init__()
                self._text = []

            def handle_data(self, d):
                self._text.append(d)

            def get_text(self):
                return " ".join(self._text)

        book = epub.read_epub(str(path))
        parts = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                p = _Strip()
                p.feed(item.get_content().decode("utf-8", errors="ignore"))
                t = p.get_text().strip()
                if t:
                    parts.append(t)
        return {"ok": True, "text": "\n".join(parts), "method": "ebooklib"}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_rtf(path: Path) -> dict:
    try:
        from striprtf.striprtf import rtf_to_text

        with open(str(path), encoding="utf-8", errors="replace") as f:
            rtf = f.read()
        return {"ok": True, "text": rtf_to_text(rtf), "method": "striprtf"}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_odf(path: Path) -> dict:
    try:
        from odf import teletype
        from odf.opendocument import load
        from odf.text import P

        doc = load(str(path))
        parts = [teletype.extractText(el) for el in doc.getElementsByType(P)]
        return {
            "ok": True,
            "text": "\n".join(p for p in parts if p.strip()),
            "method": "odfpy",
        }
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_csv(path: Path) -> dict:
    try:
        import csv

        import chardet

        with open(str(path), "rb") as f:
            enc = chardet.detect(f.read(10000)).get("encoding", "utf-8") or "utf-8"
        with open(str(path), newline="", encoding=enc, errors="replace") as f:
            reader = csv.reader(f)
            rows = [" | ".join(row) for row in reader if any(c.strip() for c in row)]
        return {"ok": True, "text": "\n".join(rows), "method": "csv"}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_json(path: Path) -> dict:
    try:
        import json

        with open(str(path), encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        return {"ok": True, "text": text[:100000], "method": "json"}
    except Exception as e:
        return _extract_plain(path)


def _extract_markup(path: Path) -> dict:
    try:
        from html.parser import HTMLParser

        class _Strip(HTMLParser):
            def __init__(self):
                super().__init__()
                self._t = []

            def handle_data(self, d):
                self._t.append(d)

            def get(self):
                return " ".join(self._t)

        with open(str(path), encoding="utf-8", errors="replace") as f:
            raw = f.read()
        p = _Strip()
        p.feed(raw)
        text = p.get().strip()
        if not text:
            text = raw
        return {"ok": True, "text": text[:100000], "method": "html.parser"}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_markdown(path: Path) -> dict:
    try:
        from html.parser import HTMLParser

        import markdown

        with open(str(path), encoding="utf-8", errors="replace") as f:
            md = f.read()
        html = markdown.markdown(md)

        class _Strip(HTMLParser):
            def __init__(self):
                super().__init__()
                self._t = []

            def handle_data(self, d):
                self._t.append(d)

            def get(self):
                return " ".join(self._t)

        p = _Strip()
        p.feed(html)
        return {"ok": True, "text": p.get() or md, "method": "markdown"}
    except Exception as e:
        return _extract_plain(path)


def _extract_zip(path: Path, ocr: bool = True) -> dict:
    try:
        texts = []
        with zipfile.ZipFile(str(path), "r") as zf:
            for name in zf.namelist():
                if name.endswith("/") or "__MACOSX" in name:
                    continue
                try:
                    with zf.open(name) as f:
                        import tempfile

                        suffix = Path(name).suffix
                        with tempfile.NamedTemporaryFile(
                            suffix=suffix, delete=False
                        ) as tmp:
                            tmp.write(f.read())
                            tmp_path = Path(tmp.name)
                        sub = extract_text(tmp_path, ocr=ocr)
                        tmp_path.unlink(missing_ok=True)
                        if sub.get("text", "").strip():
                            texts.append(f"[{name}]\n{sub['text']}")
                except Exception as e:
                    pass
        return {"ok": True, "text": "\n\n".join(texts), "method": "zip-recursive"}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "method": "none"}


def _extract_plain(path: Path, strict: bool = True) -> dict:
    try:
        import chardet

        with open(str(path), "rb") as f:
            raw = f.read(50000)
        enc = chardet.detect(raw).get("encoding") or "utf-8"
        with open(str(path), encoding=enc, errors="replace") as f:
            text = f.read(200000)
        return {"ok": True, "text": text, "method": "plain-text", "encoding": enc}
    except Exception as e:
        if strict:
            return {"ok": False, "text": "", "error": str(e), "method": "none"}
        return {
            "ok": False,
            "text": "",
            "error": f"Formato no soportado: {path.suffix}",
            "method": "none",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Tesseract con modelos best
# ═══════════════════════════════════════════════════════════════════════════════


def ocr_tesseract_best(image_path: Path, lang: str = "spa+eng") -> str:
    """
    OCR con Tesseract usando modelos tessdata-best (mayor precisión que los estándar).
    Fallback automático a modelos estándar si no están disponibles.
    """
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(str(image_path))

        # Intentar con tessdata-best
        if os.path.isdir(TESSDATA_BEST):
            config = f"--tessdata-dir {TESSDATA_BEST} --oem 1 --psm 3"
            try:
                text = pytesseract.image_to_string(img, lang=lang, config=config)
                if text.strip():
                    return text.strip()
            except Exception as e:
                pass

        # Fallback a tessdata estándar
        text = pytesseract.image_to_string(img, lang=lang, config="--oem 1 --psm 3")
        return text.strip()
    except Exception as e:
        logger.error(f"Tesseract best falló: {e}")
        return ""
