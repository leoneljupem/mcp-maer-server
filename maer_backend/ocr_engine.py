#!/usr/bin/env python3
# 🦁 MAER OCR ENGINE — Motor OCR Multimodal
# Leonel Mojica — Ecatepec MX — 2026

"""
Motor OCR con múltiples backends:
  1. Tesseract (primario, ya instalado)
  2. EasyOCR (fallback para layouts complejos)
  3. PaddleOCR (tercer motor, máxima precisión)

Incluye:
  - Preprocesamiento OpenCV (binarización, ruido, skew)
  - Cacheo inteligente por hash SHA-256
  - Selección automática de motor
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import cv2
from PIL import Image

logger = logging.getLogger("maer.ocr")

# ── Configuración ──
OCR_CACHE_FILE = os.environ.get("MAER_OCR_CACHE", "maer_ocr_cache.json")
OCR_LANGS = os.environ.get("MAER_OCR_LANGS", "spa+eng")
OCR_DPI = int(os.environ.get("MAER_OCR_DPI", "300"))
OCR_MAX_PAGES = int(os.environ.get("MAER_OCR_MAX_PAGES", "50"))

# ── Cache global ──
_ocr_cache = {}
_cache_loaded = False


def _load_cache(cache_path: str = None):
    """Carga el cache OCR desde disco."""
    global _ocr_cache, _cache_loaded
    if _cache_loaded:
        return
    cp = Path(cache_path or OCR_CACHE_FILE)
    if cp.exists():
        try:
            with open(cp, "r", encoding="utf-8") as f:
                _ocr_cache = json.load(f)
        except Exception:
            _ocr_cache = {}
    _cache_loaded = True


def _save_cache(cache_path: str = None):
    """Guarda el cache OCR a disco."""
    cp = Path(cache_path or OCR_CACHE_FILE)
    try:
        cp.parent.mkdir(parents=True, exist_ok=True)
        with open(cp, "w", encoding="utf-8") as f:
            json.dump(_ocr_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"No se pudo guardar cache OCR: {e}")


def file_hash(path: Path) -> str:
    """SHA-256 del archivo para cacheo."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_cached_ocr(path: Path, cache_path: str = None) -> Optional[str]:
    """Retorna texto OCR cacheado si existe y el archivo no cambió."""
    _load_cache(cache_path)
    fh = file_hash(path)
    entry = _ocr_cache.get(str(path))
    if entry and entry.get("hash") == fh:
        logger.info(f"Cache hit OCR: {path.name}")
        return entry.get("text")
    return None


def set_cached_ocr(path: Path, text: str, engine: str, cache_path: str = None):
    """Guarda resultado OCR en cache."""
    _load_cache(cache_path)
    fh = file_hash(path)
    _ocr_cache[str(path)] = {
        "hash": fh,
        "engine": engine,
        "text": text[:50000],  # Limitar tamaño del cache
        "chars": len(text),
    }
    _save_cache(cache_path)


# ═══════════════════════════════════════════════
# Preprocesamiento con OpenCV
# ═══════════════════════════════════════════════

def preprocess_image(img_array: np.ndarray) -> np.ndarray:
    """
    Pipeline de preprocesamiento para mejorar OCR:
    1. Escala de grises
    2. Eliminación de ruido (bilateral filter)
    3. Binarización adaptativa
    4. Corrección de skew
    """
    # Si ya es grayscale, no convertir
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array.copy()

    # Eliminación de ruido
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)

    # Binarización adaptativa (mejor para documentos escaneados)
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Corrección de skew
    binary = correct_skew(binary)

    return binary


def correct_skew(image: np.ndarray, max_angle: float = 5.0) -> np.ndarray:
    """Corrige la inclinación del texto en una imagen."""
    try:
        # Detectar ángulo con Hough lines
        coords = np.column_stack(np.where(image < 128))
        if len(coords) < 100:
            return image

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Solo corregir si el ángulo es razonable
        if abs(angle) > max_angle or abs(angle) < 0.1:
            return image

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        logger.info(f"Skew corregido: {angle:.2f}°")
        return rotated
    except Exception:
        return image


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    """Convierte PIL Image a array OpenCV."""
    return np.array(pil_img)


def cv2_to_pil(cv2_img: np.ndarray) -> Image.Image:
    """Convierte array OpenCV a PIL Image."""
    return Image.fromarray(cv2_img)


# ═══════════════════════════════════════════════
# Motores OCR
# ═══════════════════════════════════════════════

def ocr_tesseract(image: Image.Image, lang: str = None) -> str:
    """OCR con Tesseract."""
    import pytesseract
    lang = lang or OCR_LANGS.replace("+", "+")
    try:
        # Preprocesar
        cv2_img = pil_to_cv2(image)
        processed = preprocess_image(cv2_img)
        processed_pil = cv2_to_pil(processed)
        text = pytesseract.image_to_string(processed_pil, lang=lang)
        return text.strip()
    except Exception as e:
        logger.error(f"Error Tesseract: {e}")
        return ""


def ocr_easyocr(image: Image.Image, langs: list = None) -> str:
    """OCR con EasyOCR (mejor para layouts complejos)."""
    try:
        import easyocr
        lang_list = langs or ["es", "en"]
        reader = easyocr.Reader(lang_list, gpu=False)
        cv2_img = pil_to_cv2(image)
        processed = preprocess_image(cv2_img)
        results = reader.readtext(processed)
        text = "\n".join([r[1] for r in results])
        return text.strip()
    except ImportError:
        logger.warning("EasyOCR no disponible")
        return ""
    except Exception as e:
        logger.error(f"Error EasyOCR: {e}")
        return ""


def ocr_paddleocr(image: Image.Image, lang: str = None) -> str:
    """OCR con PaddleOCR (máxima precisión)."""
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang=lang or "es", show_log=False)
        cv2_img = pil_to_cv2(image)
        processed = preprocess_image(cv2_img)
        results = ocr.ocr(processed, cls=True)
        lines = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) > 1:
                    lines.append(line[1][0])
        return "\n".join(lines).strip()
    except ImportError:
        logger.warning("PaddleOCR no disponible")
        return ""
    except Exception as e:
        logger.error(f"Error PaddleOCR: {e}")
        return ""


# ═══════════════════════════════════════════════
# Motor selector automático
# ═══════════════════════════════════════════════

def ocr_auto(image: Image.Image, lang: str = None) -> dict:
    """
    Ejecuta OCR con múltiples motores y selecciona el mejor resultado.
    Retorna: {engine, text, confidence, all_results}
    """
    results = {}

    # Tesseract (siempre disponible)
    text_tess = ocr_tesseract(image, lang)
    results["tesseract"] = text_tess

    # EasyOCR (si disponible)
    text_easy = ocr_easyocr(image)
    if text_easy:
        results["easyocr"] = text_easy

    # PaddleOCR (si disponible)
    text_paddle = ocr_paddleocr(image, lang)
    if text_paddle:
        results["paddleocr"] = text_paddle

    # Seleccionar el mejor resultado por longitud y calidad
    best_engine = "tesseract"
    best_text = text_tess

    for engine, text in results.items():
        if len(text) > len(best_text) * 1.2:  # 20% más texto = probablemente mejor
            best_engine = engine
            best_text = text

    return {
        "engine": best_engine,
        "text": best_text,
        "all_results": {k: len(v) for k, v in results.items()},
    }


def ocr_single_engine(image: Image.Image, engine: str = "tesseract", lang: str = None) -> str:
    """OCR con un motor específico."""
    if engine == "easyocr":
        return ocr_easyocr(image)
    elif engine == "paddleocr":
        return ocr_paddleocr(image, lang)
    elif engine == "auto":
        result = ocr_auto(image, lang)
        return result["text"]
    else:
        return ocr_tesseract(image, lang)


# ═══════════════════════════════════════════════
# OCR de PDF completo
# ═══════════════════════════════════════════════

def ocr_pdf(path: Path, engine: str = "auto", max_pages: int = None,
            use_cache: bool = True, cache_path: str = None) -> dict:
    """
    OCR completo de un PDF con motor seleccionable.
    Retorna: {ok, text, engine, pages_processed, cached}
    """
    from pypdf import PdfReader
    from pdf2image import convert_from_path

    max_pages = max_pages or OCR_MAX_PAGES

    # Verificar cache
    if use_cache:
        cached = get_cached_ocr(path, cache_path)
        if cached is not None:
            return {
                "ok": True, "text": cached, "engine": "cache",
                "pages_processed": 0, "cached": True
            }

    # Intentar texto directo primero
    text_direct = ""
    try:
        reader = PdfReader(str(path))
        num_pages = min(len(reader.pages), max_pages)
        for i in range(num_pages):
            text_direct += reader.pages[i].extract_text() or ""
    except Exception:
        pass

    if text_direct and len(text_direct.strip()) > 100:
        if use_cache:
            set_cached_ocr(path, text_direct, "direct", cache_path)
        return {
            "ok": True, "text": text_direct, "engine": "direct",
            "pages_processed": num_pages, "cached": False
        }

    # OCR con motor seleccionado
    try:
        pages = convert_from_path(
            str(path), dpi=OCR_DPI,
            first_page=1, last_page=max_pages
        )
    except Exception as e:
        return {
            "ok": False, "text": text_direct,
            "error": f"Error convirtiendo PDF: {e}",
            "engine": "none", "pages_processed": 0, "cached": False
        }

    all_text = []
    used_engine = engine

    for idx, page_img in enumerate(pages):
        if engine == "auto":
            result = ocr_auto(page_img)
            all_text.append(result["text"])
            used_engine = result["engine"]
        else:
            text = ocr_single_engine(page_img, engine)
            all_text.append(text)

    final_text = text_direct + "\n" + "\n".join(all_text)

    if use_cache:
        set_cached_ocr(path, final_text, used_engine, cache_path)

    return {
        "ok": True, "text": final_text, "engine": used_engine,
        "pages_processed": len(pages), "cached": False
    }


def ocr_image(path: Path, engine: str = "auto",
              use_cache: bool = True, cache_path: str = None) -> dict:
    """
    OCR de una imagen (JPG, PNG, etc.).
    Retorna: {ok, text, engine, cached}
    """
    if use_cache:
        cached = get_cached_ocr(path, cache_path)
        if cached is not None:
            return {"ok": True, "text": cached, "engine": "cache", "cached": True}

    try:
        img = Image.open(str(path))
    except Exception as e:
        return {"ok": False, "text": "", "error": f"Error abriendo imagen: {e}",
                "engine": "none", "cached": False}

    if engine == "auto":
        result = ocr_auto(img)
        text = result["text"]
        used_engine = result["engine"]
    else:
        text = ocr_single_engine(img, engine)
        used_engine = engine

    if use_cache:
        set_cached_ocr(path, text, used_engine, cache_path)

    return {"ok": True, "text": text, "engine": used_engine, "cached": False}
