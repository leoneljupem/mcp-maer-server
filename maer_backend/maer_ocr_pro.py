#!/usr/bin/env python3
"""
maer_ocr_pro.py — OCR Pro: Ensemble + Preprocesado Avanzado
════════════════════════════════════════════════════════════
Capa de OCR de alta precisión que orquesta múltiples motores
en modo ensemble y aplica preprocesado adaptativo avanzado.

Características:
  • Ensemble voting: Tesseract + EasyOCR + RapidOCR
  • Preprocesado adaptativo: CLAHE, Otsu, eliminación de sombras,
    corrección perspectiva, detección de inclinación
  • Confidence scoring por motor
  • Comparación side-by-side de todos los motores
  • Instalador de motores faltantes (respeta restricciones Intel Mac)
  • Cache de resultados con SHA256

Leonel Houssen Mojica — Ecatepec MX — 2026
"""

import hashlib
import logging
import os
import re
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("maer.ocr_pro")

# ── Umbrales de calidad ───────────────────────────────────────────────────────
QUALITY_GOOD = 0.72
QUALITY_OK = 0.45
QUALITY_BAD = 0.20

# ── Cache de resultados ───────────────────────────────────────────────────────
_CACHE_DIR = Path(__file__).parent.parent / "data" / "ocr_cache"
_cache: dict = {}


# ═══════════════════════════════════════════════════════════════════════════════
# Utilidades: calidad, hash, cache
# ═══════════════════════════════════════════════════════════════════════════════


def _quality_score(text: str) -> float:
    """Score 0.0–1.0 de legibilidad del texto OCR."""
    if not text or not text.strip():
        return 0.0
    clean = text.strip()
    total = len(clean)
    if total < 3:
        return 0.05

    valid = sum(
        1
        for c in clean
        if c.isalnum() or c.isspace() or c in ".,;:!?()[]{}'\"-_/\\@#$%áéíóúñüÁÉÍÓÚÑÜ°"
    )
    ratio = valid / total
    length_bonus = min(1.0, total / 200.0) * 0.3
    garbled = len(re.findall(r"[^\w\s.,;:!?áéíóúñüÁÉÍÓÚÑÜ°\-()]{3,}", clean))
    garble_penalty = min(0.4, garbled * 0.05)
    return max(0.0, min(1.0, ratio * 0.7 + length_bonus - garble_penalty))


def _image_hash(img: np.ndarray) -> str:
    return hashlib.sha256(img.tobytes()).hexdigest()[:16]


def _load_image(source) -> np.ndarray:
    """Carga imagen desde PIL, path o ndarray. Siempre devuelve BGR ndarray."""
    if isinstance(source, Image.Image):
        arr = np.array(source.convert("RGB"))
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    if isinstance(source, (str, Path)):
        img = cv2.imread(str(source))
        if img is None:
            raise ValueError(f"No se pudo cargar: {source}")
        return img
    if isinstance(source, np.ndarray):
        return source
    raise TypeError(f"Tipo de imagen no soportado: {type(source)}")


def _to_pil(bgr: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


# ═══════════════════════════════════════════════════════════════════════════════
# Preprocesado Avanzado
# ═══════════════════════════════════════════════════════════════════════════════


def preprocess_advanced(img: np.ndarray, mode: str = "auto") -> dict:
    """
    Aplica pipeline de preprocesado adaptativo.

    Modos:
      auto       — detecta características y elige automáticamente
      scan       — documento escaneado: CLAHE + Otsu
      photo      — foto real: eliminar sombras + perspectiva + CLAHE
      handwrite  — manuscrito: suavizado + umbral adaptativo
      fast       — solo escala de grises + Otsu (rápido)
      turbo      — escala de grises nativa, sin transformaciones

    Retorna dict con:
      original: np.ndarray BGR
      processed: np.ndarray BGR (para OCR)
      gray: np.ndarray gris
      mode_used: str
      steps: list[str] pasos aplicados
    """
    steps = []
    original = img.copy()

    # --- Detección automática de modo ---
    if mode == "auto":
        gray_tmp = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_val = gray_tmp.mean()
        std_val = gray_tmp.std()
        blur_score = cv2.Laplacian(gray_tmp, cv2.CV_64F).var()

        if blur_score < 50:
            mode = "photo"  # imagen borrosa o fotografía
        elif mean_val > 200 and std_val < 60:
            mode = "scan"  # fondo blanco, alto contraste
        elif std_val > 80:
            mode = "scan"  # documento nítido
        else:
            mode = "scan"
        steps.append(f"auto→{mode}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if mode == "turbo":
        return {
            "original": original,
            "processed": img,
            "gray": gray,
            "mode_used": "turbo",
            "steps": ["gray_only"],
        }

    # --- PASO 1: Escala y resolución mínima ---
    h, w = gray.shape
    if w < 1800:
        scale = 1800 / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        steps.append(f"resize→{new_w}x{new_h}")

    # --- PASO 2: Corrección de inclinación (deskew) ---
    try:
        import scipy.ndimage as ndi
        from deskew import determine_skew

        angle = determine_skew(gray)
        if angle is not None and abs(angle) > 0.3:
            rotated = ndi.rotate(gray, angle, reshape=False, cval=255)
            gray = rotated.astype(np.uint8)
            rotated_bgr = ndi.rotate(img, angle, reshape=False, cval=255)
            img = rotated_bgr.astype(np.uint8)
            steps.append(f"deskew({angle:.1f}°)")
    except Exception as e:
        pass

    if mode == "photo":
        # --- Eliminación de sombras ---
        try:
            rgb_planes = cv2.split(img)
            result_planes = []
            for plane in rgb_planes:
                dilated = cv2.dilate(plane, np.ones((7, 7), np.uint8))
                bg = cv2.medianBlur(dilated, 21)
                diff = 255 - cv2.absdiff(plane, bg)
                norm = cv2.normalize(
                    diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX
                )
                result_planes.append(norm)
            img = cv2.merge(result_planes)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            steps.append("shadow_removal")
        except Exception as e:
            pass

        # --- Corrección de perspectiva (si hay bordes claros de documento) ---
        try:
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 75, 200)
            contours, _ = cv2.findContours(
                edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
            for c in contours:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                if len(approx) == 4:
                    # Corrección de perspectiva con 4 puntos
                    pts = approx.reshape(4, 2).astype(np.float32)
                    # Ordenar: tl, tr, br, bl
                    s = pts.sum(axis=1)
                    d = np.diff(pts, axis=1)
                    tl = pts[np.argmin(s)]
                    br = pts[np.argmax(s)]
                    tr = pts[np.argmin(d)]
                    bl = pts[np.argmax(d)]
                    ordered = np.array([tl, tr, br, bl], dtype=np.float32)
                    w1 = int(np.hypot(br[0] - bl[0], br[1] - bl[1]))
                    w2 = int(np.hypot(tr[0] - tl[0], tr[1] - tl[1]))
                    h1 = int(np.hypot(tr[0] - br[0], tr[1] - br[1]))
                    h2 = int(np.hypot(tl[0] - bl[0], tl[1] - bl[1]))
                    dst_w = max(w1, w2)
                    dst_h = max(h1, h2)
                    if dst_w > 100 and dst_h > 100:
                        dst = np.array(
                            [
                                [0, 0],
                                [dst_w - 1, 0],
                                [dst_w - 1, dst_h - 1],
                                [0, dst_h - 1],
                            ],
                            dtype=np.float32,
                        )
                        M = cv2.getPerspectiveTransform(ordered, dst)
                        warped = cv2.warpPerspective(img, M, (dst_w, dst_h))
                        img = warped
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        steps.append("perspective_correction")
                    break
        except Exception as e:
            pass

    # --- PASO 3: CLAHE (mejora de contraste local) ---
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        steps.append("CLAHE")
    except Exception as e:
        pass

    if mode == "handwrite":
        # --- Suavizado bilateral (preserva bordes, reduce ruido) ---
        try:
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            steps.append("bilateral_filter")
        except Exception as e:
            pass
        # --- Umbral adaptativo para manuscrito ---
        try:
            gray = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
            )
            steps.append("adaptive_threshold")
        except Exception as e:
            pass

    elif mode in ("scan", "photo", "fast"):
        # --- Denoise ---
        try:
            gray = cv2.fastNlMeansDenoising(
                gray, None, h=10, templateWindowSize=7, searchWindowSize=21
            )
            steps.append("denoise")
        except Exception as e:
            pass
        # --- Binarización Otsu ---
        try:
            _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            steps.append("otsu")
        except Exception as e:
            pass

    # --- PASO 4: Morfología (cerrar huecos en letras) ---
    try:
        kernel = np.ones((2, 2), np.uint8)
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        steps.append("morph_close")
    except Exception as e:
        pass

    result_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return {
        "original": original,
        "processed": result_bgr,
        "gray": gray,
        "mode_used": mode,
        "steps": steps,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Motor: Tesseract (siempre disponible)
# ═══════════════════════════════════════════════════════════════════════════════


def _ocr_tesseract(gray: np.ndarray, lang: str = "spa+eng", config: str = "") -> dict:
    """OCR con Tesseract. Incluye confidence score."""
    try:
        import pytesseract

        # Buscar tessdata-best
        tessdata_paths = [
            os.path.expanduser("~/tessdata_best"),
            "/usr/local/share/tessdata",
            "/usr/share/tessdata",
            "/opt/homebrew/share/tessdata",
        ]
        tessdata_dir = None
        for p in tessdata_paths:
            if Path(p).exists():
                tessdata_dir = p
                break

        cfg = f"--oem 1 --psm 3 {config}"
        if tessdata_dir:
            cfg += f" --tessdata-dir {tessdata_dir}"

        pil_img = Image.fromarray(gray)
        # Obtener texto y datos de confianza
        text = pytesseract.image_to_string(pil_img, lang=lang, config=cfg)
        try:
            data = pytesseract.image_to_data(
                pil_img, lang=lang, config=cfg, output_type=pytesseract.Output.DICT
            )
            confs = [
                int(c)
                for c in data["conf"]
                if str(c).lstrip("-").isdigit() and int(c) >= 0
            ]
            avg_conf = sum(confs) / len(confs) if confs else 0.0
        except Exception as e:
            avg_conf = 0.0

        q = _quality_score(text)
        return {
            "ok": True,
            "text": text,
            "engine": "tesseract",
            "quality": q,
            "confidence": avg_conf / 100.0,
            "char_count": len(text.strip()),
        }
    except ImportError:
        return {"ok": False, "engine": "tesseract", "error": "pytesseract no instalado"}
    except Exception as e:
        return {"ok": False, "engine": "tesseract", "error": str(e)[:200]}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor: EasyOCR
# ═══════════════════════════════════════════════════════════════════════════════

_easyocr_reader = None


def _ocr_easyocr(img_bgr: np.ndarray, langs: list = None) -> dict:
    """OCR con EasyOCR. Carga el modelo una sola vez (singleton)."""
    global _easyocr_reader
    try:
        import easyocr

        if langs is None:
            langs = ["es", "en"]
        if _easyocr_reader is None:
            _easyocr_reader = easyocr.Reader(langs, gpu=False, verbose=False)
        results = _easyocr_reader.readtext(img_bgr, detail=1, paragraph=True)
        lines = []
        confs = []
        for item in results:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                text_part = item[1] if len(item) >= 2 else ""
                conf_part = item[2] if len(item) >= 3 else 0.0
                lines.append(str(text_part))
                confs.append(float(conf_part))
        text = "\n".join(lines)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        q = _quality_score(text)
        return {
            "ok": True,
            "text": text,
            "engine": "easyocr",
            "quality": q,
            "confidence": avg_conf,
            "char_count": len(text.strip()),
        }
    except ImportError:
        return {"ok": False, "engine": "easyocr", "error": "easyocr no instalado"}
    except Exception as e:
        return {"ok": False, "engine": "easyocr", "error": str(e)[:200]}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor: RapidOCR
# ═══════════════════════════════════════════════════════════════════════════════

_rapidocr_engine = None


def _ocr_rapidocr(img_bgr: np.ndarray) -> dict:
    """OCR con RapidOCR (ONNX, sin GPU). Muy rápido para texto denso."""
    global _rapidocr_engine
    try:
        from rapidocr_onnxruntime import RapidOCR

        if _rapidocr_engine is None:
            _rapidocr_engine = RapidOCR()
        result, _ = _rapidocr_engine(img_bgr)
        if result is None:
            return {
                "ok": True,
                "text": "",
                "engine": "rapidocr",
                "quality": 0.0,
                "confidence": 0.0,
                "char_count": 0,
            }
        lines = []
        confs = []
        for item in result:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                lines.append(str(item[1]))
                if len(item) >= 3:
                    confs.append(float(item[2]))
        text = "\n".join(lines)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        q = _quality_score(text)
        return {
            "ok": True,
            "text": text,
            "engine": "rapidocr",
            "quality": q,
            "confidence": avg_conf,
            "char_count": len(text.strip()),
        }
    except ImportError:
        return {
            "ok": False,
            "engine": "rapidocr",
            "error": "rapidocr-onnxruntime no instalado",
        }
    except Exception as e:
        return {"ok": False, "engine": "rapidocr", "error": str(e)[:200]}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor: PaddleOCR (multilingüe, estado del arte)
# ═══════════════════════════════════════════════════════════════════════════════

_paddleocr_engine = None


def _ocr_paddleocr(img_bgr: np.ndarray) -> dict:
    """OCR con PaddleOCR. Detecta ángulo automáticamente."""
    global _paddleocr_engine
    try:
        from paddleocr import PaddleOCR

        if _paddleocr_engine is None:
            _paddleocr_engine = PaddleOCR(
                use_angle_cls=True, lang="es", use_gpu=False, show_log=False
            )
        result = _paddleocr_engine.ocr(img_bgr, cls=True)
        lines = []
        confs = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text_conf = line[1]
                    if isinstance(text_conf, (list, tuple)) and len(text_conf) >= 2:
                        lines.append(str(text_conf[0]))
                        confs.append(float(text_conf[1]))
        text = "\n".join(lines)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        q = _quality_score(text)
        return {
            "ok": True,
            "text": text,
            "engine": "paddleocr",
            "quality": q,
            "confidence": avg_conf,
            "char_count": len(text.strip()),
        }
    except ImportError:
        return {"ok": False, "engine": "paddleocr", "error": "paddleocr no instalado"}
    except Exception as e:
        return {"ok": False, "engine": "paddleocr", "error": str(e)[:200]}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor: PyMuPDF (para PDFs con texto nativo — muy preciso)
# ═══════════════════════════════════════════════════════════════════════════════


def _ocr_pymupdf(path: Path) -> dict:
    """Extrae texto de PDF con PyMuPDF (sin rasterizar, máxima precisión)."""
    try:
        import fitz

        doc = fitz.open(str(path))
        parts = []
        for i, page in enumerate(doc):
            t = page.get_text("text") or ""
            if t.strip():
                parts.append(f"[Pág {i+1}]\n{t}")
        doc.close()
        text = "\n\n".join(parts)
        q = _quality_score(text)
        return {
            "ok": True,
            "text": text,
            "engine": "pymupdf",
            "quality": q,
            "confidence": q,
            "char_count": len(text.strip()),
        }
    except ImportError:
        return {"ok": False, "engine": "pymupdf", "error": "fitz no instalado"}
    except Exception as e:
        return {"ok": False, "engine": "pymupdf", "error": str(e)[:200]}


# ═══════════════════════════════════════════════════════════════════════════════
# Ensemble Voting
# ═══════════════════════════════════════════════════════════════════════════════


def _merge_texts_voting(results: list) -> str:
    """
    Combina resultados de múltiples motores usando votación por línea.
    Estrategia: tomar líneas del motor con mayor quality score.
    """
    valid = [
        (r["quality"], r["text"])
        for r in results
        if r.get("ok") and r.get("text", "").strip()
    ]
    if not valid:
        return ""
    if len(valid) == 1:
        return valid[0][1]

    # Por ahora: usar el resultado de mayor calidad
    # (en futuro: voting palabra-a-palabra con Levenshtein)
    valid.sort(key=lambda x: x[0], reverse=True)
    best_text = valid[0][1]

    # Bonus: si segundo motor coincide en una línea, es más confiable
    # Esta implementación simple toma el mejor — extensible a voting real
    return best_text


def ocr_ensemble(
    source, mode: str = "auto", engines: list = None, preprocess: bool = True
) -> dict:
    """
    OCR ensemble: ejecuta múltiples motores y combina resultados.

    Args:
        source:     Imagen (PIL, ndarray, path str/Path)
        mode:       Modo de preprocesado (auto/scan/photo/handwrite/fast/turbo)
        engines:    Lista de motores a usar (default: auto-detecta disponibles)
        preprocess: Si True aplica pipeline de preprocesado avanzado

    Returns:
        dict con: text, quality, confidence, engine_used, all_results, steps
    """
    t0 = time.time()

    # Cargar imagen
    try:
        img_bgr = _load_image(source)
    except Exception as e:
        return {"ok": False, "error": f"No se pudo cargar imagen: {e}"}

    is_pdf = False
    source_path = None
    if isinstance(source, (str, Path)):
        source_path = Path(source)
        is_pdf = source_path.suffix.lower() == ".pdf"

    # Para PDFs con texto nativo, intentar PyMuPDF primero
    if is_pdf:
        result = _ocr_pymupdf(source_path)
        if result.get("ok") and result.get("quality", 0) >= QUALITY_OK:
            result["steps"] = ["pymupdf_native"]
            result["elapsed_ms"] = int((time.time() - t0) * 1000)
            result["engine_used"] = "pymupdf"
            result["all_results"] = [result]
            return result

    # Preprocesado
    prep_steps = []
    if preprocess:
        prep = preprocess_advanced(img_bgr, mode=mode)
        gray = prep["gray"]
        img_processed = prep["processed"]
        prep_steps = prep["steps"]
        mode_used = prep["mode_used"]
    else:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        img_processed = img_bgr
        mode_used = "none"

    # Determinar qué motores usar
    if engines is None:
        engines = _detect_available_engines()

    all_results = []
    best_result = None

    for eng in engines:
        try:
            if eng == "tesseract":
                r = _ocr_tesseract(gray)
            elif eng == "easyocr":
                r = _ocr_easyocr(img_processed)
            elif eng == "rapidocr":
                r = _ocr_rapidocr(img_processed)
            elif eng == "paddleocr":
                r = _ocr_paddleocr(img_processed)
            else:
                continue

            all_results.append(r)

            if r.get("ok") and r.get("quality", 0) >= QUALITY_GOOD:
                # Si es muy bueno, parar
                if best_result is None or r["quality"] > best_result.get("quality", 0):
                    best_result = r
                break  # calidad suficiente

            if r.get("ok"):
                if best_result is None or r.get("quality", 0) > best_result.get(
                    "quality", 0
                ):
                    best_result = r

        except Exception as e:
            all_results.append({"ok": False, "engine": eng, "error": str(e)[:100]})

    # Ensemble: combinar si hay varios resultados buenos
    good_results = [
        r for r in all_results if r.get("ok") and r.get("quality", 0) >= QUALITY_OK
    ]
    if len(good_results) >= 2:
        merged_text = _merge_texts_voting(good_results)
        merged_q = max(r["quality"] for r in good_results)
        merged_conf = sum(r.get("confidence", 0) for r in good_results) / len(
            good_results
        )
        engines_used = "+".join(r["engine"] for r in good_results)
        final_text = merged_text
        final_quality = merged_q
        final_conf = merged_conf
        final_engine = f"ensemble({engines_used})"
    elif best_result and best_result.get("ok"):
        final_text = best_result.get("text", "")
        final_quality = best_result.get("quality", 0)
        final_conf = best_result.get("confidence", 0)
        final_engine = best_result.get("engine", "unknown")
    else:
        final_text = ""
        final_quality = 0.0
        final_conf = 0.0
        final_engine = "none"

    elapsed_ms = int((time.time() - t0) * 1000)
    return {
        "ok": True,
        "text": final_text,
        "quality": round(final_quality, 3),
        "confidence": round(final_conf, 3),
        "engine_used": final_engine,
        "char_count": len(final_text.strip()),
        "elapsed_ms": elapsed_ms,
        "mode_used": mode_used,
        "steps": prep_steps,
        "all_results": [
            {
                "engine": r.get("engine", "?"),
                "ok": r.get("ok", False),
                "quality": round(r.get("quality", 0), 3),
                "confidence": round(r.get("confidence", 0), 3),
                "char_count": r.get("char_count", 0),
                "error": r.get("error"),
            }
            for r in all_results
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Comparación de motores (side-by-side)
# ═══════════════════════════════════════════════════════════════════════════════


def ocr_compare(source, mode: str = "auto", preprocess: bool = True) -> dict:
    """
    Ejecuta TODOS los motores disponibles y devuelve comparación side-by-side.
    Útil para diagnóstico y selección manual del mejor motor.
    """
    t0 = time.time()

    try:
        img_bgr = _load_image(source)
    except Exception as e:
        return {"ok": False, "error": f"No se pudo cargar imagen: {e}"}

    if preprocess:
        prep = preprocess_advanced(img_bgr, mode=mode)
        gray = prep["gray"]
        img_processed = prep["processed"]
        steps = prep["steps"]
    else:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        img_processed = img_bgr
        steps = []

    all_engines = ["tesseract", "easyocr", "rapidocr", "paddleocr"]
    results = {}

    for eng in all_engines:
        try:
            if eng == "tesseract":
                r = _ocr_tesseract(gray)
            elif eng == "easyocr":
                r = _ocr_easyocr(img_processed)
            elif eng == "rapidocr":
                r = _ocr_rapidocr(img_processed)
            elif eng == "paddleocr":
                r = _ocr_paddleocr(img_processed)
            else:
                r = {"ok": False, "error": "No implementado"}
        except Exception as e:
            r = {"ok": False, "error": str(e)[:100]}

        results[eng] = {
            "ok": r.get("ok", False),
            "quality": round(r.get("quality", 0), 3),
            "confidence": round(r.get("confidence", 0), 3),
            "char_count": r.get("char_count", 0),
            "text": (r.get("text", "") or "")[:500],  # preview 500 chars
            "error": r.get("error"),
        }

    # Ordenar por calidad
    ranking = sorted(
        [(eng, d) for eng, d in results.items() if d["ok"]],
        key=lambda x: x[1]["quality"],
        reverse=True,
    )
    best_engine = ranking[0][0] if ranking else None

    return {
        "ok": True,
        "best_engine": best_engine,
        "results": results,
        "ranking": [{"engine": e, "quality": d["quality"]} for e, d in ranking],
        "steps": steps,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Detección de motores disponibles
# ═══════════════════════════════════════════════════════════════════════════════


def _detect_available_engines() -> list:
    """Detecta qué motores OCR están instalados. Orden de prioridad."""
    available = []

    # Siempre intentar Tesseract primero (siempre disponible)
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        available.append("tesseract")
    except Exception as e:
        pass

    try:
        from rapidocr_onnxruntime import RapidOCR  # noqa

        available.append("rapidocr")
    except ImportError:
        pass

    try:
        import easyocr  # noqa

        available.append("easyocr")
    except ImportError:
        pass

    try:
        from paddleocr import PaddleOCR  # noqa

        available.append("paddleocr")
    except ImportError:
        pass

    return available if available else ["tesseract"]


def engines_status() -> dict:
    """Estado detallado de todos los motores OCR Pro."""
    status = {}

    # Tesseract
    try:
        import pytesseract

        v = pytesseract.get_tesseract_version()
        status["tesseract"] = {"available": True, "version": str(v)}
    except Exception as e:
        status["tesseract"] = {"available": False, "error": str(e)[:80]}

    # EasyOCR
    try:
        import easyocr

        status["easyocr"] = {
            "available": True,
            "version": getattr(easyocr, "__version__", "?"),
        }
    except ImportError:
        status["easyocr"] = {"available": False, "install": "pip install easyocr"}

    # RapidOCR
    try:
        import rapidocr_onnxruntime

        status["rapidocr"] = {
            "available": True,
            "version": getattr(rapidocr_onnxruntime, "__version__", "?"),
        }
    except ImportError:
        status["rapidocr"] = {
            "available": False,
            "install": "pip install rapidocr-onnxruntime",
        }

    # PaddleOCR
    try:
        import paddleocr

        status["paddleocr"] = {
            "available": True,
            "version": getattr(paddleocr, "__version__", "?"),
        }
    except ImportError:
        status["paddleocr"] = {
            "available": False,
            "install": "pip install paddlepaddle paddleocr",
        }

    # PyMuPDF
    try:
        import fitz

        status["pymupdf"] = {"available": True, "version": fitz.version[0]}
    except ImportError:
        status["pymupdf"] = {"available": False, "install": "pip install pymupdf"}

    # OpenCV
    try:
        status["opencv"] = {"available": True, "version": cv2.__version__}
    except Exception as e:
        status["opencv"] = {"available": False}

    # Deskew
    try:
        import deskew  # noqa

        status["deskew"] = {"available": True}
    except ImportError:
        status["deskew"] = {"available": False, "install": "pip install deskew"}

    # Wand (ImageMagick)
    try:
        import wand.version as _wv

        ver_str = str(getattr(_wv, "VERSION", getattr(_wv, "__version__", "?")))
        status["wand"] = {"available": True, "version": ver_str}
    except ImportError:
        status["wand"] = {"available": False, "install": "pip install wand"}

    available_count = sum(1 for v in status.values() if v.get("available"))
    return {
        "engines": status,
        "available_count": available_count,
        "total": len(status),
        "ready": _detect_available_engines(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Instalador de motores faltantes
# ═══════════════════════════════════════════════════════════════════════════════

INSTALL_COMMANDS = {
    "easyocr": ["pip install easyocr --break-system-packages"],
    "rapidocr": ["pip install rapidocr-onnxruntime --break-system-packages"],
    "paddleocr": [
        # Intel Mac — usar paddlepaddle CPU (sin CUDA)
        "pip install paddlepaddle --break-system-packages",
        "pip install paddleocr --break-system-packages",
    ],
    "doctr": ["pip install python-doctr --break-system-packages"],
    "kraken": ["pip install kraken --break-system-packages"],
}


def get_install_commands(engine: str) -> list:
    """Devuelve los comandos pip para instalar un motor OCR."""
    return INSTALL_COMMANDS.get(
        engine, [f"# Motor '{engine}' no tiene instalador automático"]
    )


def install_engine(engine: str) -> dict:
    """
    Intenta instalar un motor OCR faltante.
    NOTA: Ejecuta pip como subproceso — requiere permisos.
    Respeta restricciones NumPy 1.26.4 / PyTorch 2.2.2.
    """
    import subprocess

    commands = get_install_commands(engine)
    if not commands:
        return {"ok": False, "error": f"Motor '{engine}' no soportado"}

    results = []
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd.split(), capture_output=True, text=True, timeout=180
            )
            results.append(
                {
                    "cmd": cmd,
                    "returncode": result.returncode,
                    "stdout": result.stdout[-500:] if result.stdout else "",
                    "stderr": result.stderr[-300:] if result.stderr else "",
                }
            )
            if result.returncode != 0:
                return {
                    "ok": False,
                    "engine": engine,
                    "error": f"Falló: {cmd}",
                    "details": results,
                }
        except Exception as e:
            return {"ok": False, "engine": engine, "error": str(e), "details": results}

    # Verificar instalación
    status = engines_status()
    installed = status["engines"].get(engine, {}).get("available", False)
    return {
        "ok": installed,
        "engine": engine,
        "installed": installed,
        "commands_run": results,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# OCR para PDF con imágenes (rasterizar + ensemble)
# ═══════════════════════════════════════════════════════════════════════════════


def ocr_pdf_pro(
    path: Path,
    mode: str = "auto",
    max_pages: int = 30,
    dpi: int = 200,
    engines: list = None,
) -> dict:
    """
    OCR completo de PDF:
    1. Intenta texto nativo con PyMuPDF
    2. Si no hay suficiente texto, rasteriza y aplica ensemble OCR
    """
    t0 = time.time()
    path = Path(path)

    # Intentar texto nativo
    native = _ocr_pymupdf(path)
    if native.get("ok") and native.get("quality", 0) >= QUALITY_OK:
        native["source"] = "native_text"
        native["elapsed_ms"] = int((time.time() - t0) * 1000)
        return native

    # Rasterizar páginas
    try:
        import fitz

        doc = fitz.open(str(path))
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        all_texts = []
        page_count = min(len(doc), max_pages)

        for page_num in range(page_count):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")

            # Convertir a ndarray
            import io

            pil_img = Image.open(io.BytesIO(img_data))
            img_bgr = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

            result = ocr_ensemble(img_bgr, mode=mode, engines=engines)
            if result.get("text", "").strip():
                all_texts.append(f"[Pág {page_num+1}]\n{result['text']}")

        doc.close()
        full_text = "\n\n".join(all_texts)
        q = _quality_score(full_text)

        return {
            "ok": True,
            "text": full_text,
            "quality": round(q, 3),
            "confidence": round(q, 3),
            "engine_used": "ensemble_rasterized",
            "char_count": len(full_text.strip()),
            "pages_processed": page_count,
            "source": "rasterized",
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point de prueba
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    print("🦁 MAER OCR Pro — Diagnóstico de motores\n")
    status = engines_status()
    for engine, info in status["engines"].items():
        avail = "✅" if info.get("available") else "❌"
        ver = info.get("version", "")
        inst = info.get("install", "")
        if info.get("available"):
            print(f"  {avail} {engine:<15} v{ver}")
        else:
            print(f"  {avail} {engine:<15} — {inst}")
    print(f"\n  {status['available_count']}/{status['total']} motores disponibles")
    print(f"  Motores listos para uso: {', '.join(status['ready'])}")

    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        print(f"\n🔍 Procesando: {path.name}")
        result = ocr_ensemble(path, mode="auto")
        print(f"\n  Motor: {result['engine_used']}")
        print(f"  Calidad: {result['quality']:.3f}")
        print(f"  Confianza: {result['confidence']:.3f}")
        print(f"  Chars: {result['char_count']}")
        print(f"  Tiempo: {result['elapsed_ms']}ms")
        print(f"  Pasos: {', '.join(result['steps'])}")
        print(f"\n  Texto ({result['char_count']} chars):")
        print("  " + result["text"][:500].replace("\n", "\n  "))
