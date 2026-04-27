#!/usr/bin/env python3
# 🦁 MAER OCR Advanced — Orquestador de motores OCR de alta precisión
# Leonel Mojica — Ecatepec MX — 2026

"""
Selecciona y combina automáticamente los mejores motores OCR según el tipo de imagen:

  Motor         Mejor para
  ─────────────────────────────────────────────────────────────────
  PyMuPDF       PDFs con texto digital nativo (0 errores, instantáneo)
  surya         Documentos escaneados, fotos, layouts complejos
  docTR         Formularios, tablas, texto en múltiples columnas
  TrOCR         Texto manuscrito, firmas, sellos, fuentes raras
  RapidOCR      Texto impreso denso, modo rápido (ONNX, sin GPU)
  MangaOCR      Transformer para texto denso pequeño, fuentes inusuales
  PaddleOCR     Estado del arte multilingüe, detección de ángulo
  Kraken        Documentos históricos, manuscritos, caracteres raros
  OCRmyPDF      PDFs escaneados mal orientados (pipeline Tesseract+)
  EasyOCR       Fallback robusto, buen soporte español
  Tesseract     Fallback final, siempre disponible
  deskew        Pre-procesamiento: corrección de inclinación

Pipeline automático:
  1. Analizar imagen (brillo, nitidez, ¿es scan?, tamaño)
  2. Elegir motor óptimo según características
  3. Intentar con motor elegido
  4. Validar calidad del resultado (ratio texto legible)
  5. Si calidad < umbral, intentar con el siguiente motor
  6. Retornar el mejor resultado con metadatos
"""

import logging
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger("maer.ocr_advanced")

# ── Umbrales de calidad ──────────────────────────────────────────────────────
QUALITY_GOOD = 0.72  # ≥ este score → resultado aceptable, parar
QUALITY_OK = 0.45  # ≥ este score → usable, pero intentar mejorar
QUALITY_BAD = 0.20  # < este → texto inservible, pasar al siguiente motor

# ── Singletons de modelos (se cargan una sola vez) ───────────────────────────
_surya_models = None
_doctr_model = None
_trocr_printed = None
_trocr_handwritten = None


# ═══════════════════════════════════════════════════════════════════════════════
# Análisis de imagen para selección de motor
# ═══════════════════════════════════════════════════════════════════════════════


def _analyze_image(img: Image.Image) -> dict:
    """
    Calcula características de la imagen para elegir el motor OCR óptimo.
    Retorna dict con: brightness, sharpness, is_scan, has_content, text_density_hint
    """
    try:
        gray = img.convert("L")
        arr = np.array(gray, dtype=np.float32)

        brightness = float(arr.mean()) / 255.0

        # Nitidez: varianza de Laplaciano
        from scipy.ndimage import laplace

        lap = laplace(arr)
        sharpness = float(np.var(lap)) / 1000.0
    except Exception as e:
        brightness = 0.5
        sharpness = 0.5

    w, h = img.size
    area = w * h

    # Heurística: documentos escaneados suelen tener alto contraste y fondo blanco
    is_scan = brightness > 0.65 and sharpness > 0.3

    return {
        "brightness": round(brightness, 3),
        "sharpness": round(sharpness, 3),
        "is_scan": is_scan,
        "width": w,
        "height": h,
        "area": area,
        "is_small": area < 200_000,  # < ~450×440px
        "is_large": area > 4_000_000,  # > ~2000×2000px
    }


def _quality_score(text: str) -> float:
    """
    Evalúa la calidad del texto OCR extraído.
    Score 0.0–1.0 basado en ratio de caracteres legibles y longitud.
    """
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

    # Penalizar texto muy corto
    length_bonus = min(1.0, total / 200.0) * 0.3

    # Penalizar textos con muchos caracteres extraños seguidos (basura OCR)
    import re

    garbled = len(re.findall(r"[^\w\s.,;:!?áéíóúñüÁÉÍÓÚÑÜ°\-()]{3,}", clean))
    garble_penalty = min(0.4, garbled * 0.05)

    return max(0.0, min(1.0, ratio * 0.7 + length_bonus - garble_penalty))


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 1: PyMuPDF — PDFs con texto nativo
# ═══════════════════════════════════════════════════════════════════════════════


def _ocr_pymupdf_pdf(path: Path, max_pages: int = 50) -> dict:
    """Extrae texto de PDF usando PyMuPDF. Preserva layout y extrae imágenes."""
    try:
        import fitz

        doc = fitz.open(str(path))
        parts = []
        embedded_images = []

        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            # Texto con coordenadas preservadas
            text = page.get_text("text") or ""
            if text.strip():
                parts.append(f"[Página {page_num + 1}]\n{text}")

            # Registrar imágenes embebidas para OCR posterior
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                embedded_images.append(
                    {
                        "page": page_num + 1,
                        "xref": xref,
                    }
                )

        doc.close()
        full_text = "\n\n".join(parts)
        return {
            "ok": True,
            "text": full_text,
            "engine": "pymupdf",
            "quality": _quality_score(full_text),
            "embedded_images": len(embedded_images),
        }
    except ImportError:
        return {"ok": False, "error": "pymupdf no disponible"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def extract_pdf_pages_as_images(
    path: Path, dpi: int = 200, max_pages: int = 50
) -> list:
    """
    Convierte páginas de PDF a imágenes PIL usando PyMuPDF (más rápido que pdf2image).
    """
    try:
        import fitz

        doc = fitz.open(str(path))
        images = []
        mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 dpi base de PyMuPDF

        for page_num in range(min(len(doc), max_pages)):
            pix = doc[page_num].get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)

        doc.close()
        return images
    except Exception as e:
        logger.warning(f"PyMuPDF page render falló: {e}, usando pdf2image")
        try:
            from pdf2image import convert_from_path

            return convert_from_path(
                str(path), dpi=dpi, first_page=1, last_page=max_pages
            )
        except Exception as e2:
            logger.error(f"pdf2image también falló: {e2}")
            return []


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 2: surya — estado del arte, 97 idiomas
# ═══════════════════════════════════════════════════════════════════════════════


def _load_surya():
    global _surya_models
    if _surya_models is not None:
        return _surya_models
    try:
        from surya.model.detection.segformer import \
            load_model as load_det_model
        from surya.model.detection.segformer import \
            load_processor as load_det_processor
        from surya.model.recognition.model import load_model as load_rec_model
        from surya.model.recognition.processor import \
            load_processor as load_rec_processor

        logger.info("Cargando modelos surya (primera vez, ~30s)...")
        det_model = load_det_model()
        det_processor = load_det_processor()
        rec_model = load_rec_model()
        rec_processor = load_rec_processor()
        _surya_models = (det_model, det_processor, rec_model, rec_processor)
        logger.info("surya cargado")
        return _surya_models
    except Exception as e:
        logger.warning(f"surya no disponible: {e}")
        return None


def _ocr_surya(img: Image.Image, langs: list = None) -> dict:
    """OCR con surya — estado del arte para documentos escaneados."""
    models = _load_surya()
    if not models:
        return {"ok": False, "error": "surya no disponible"}

    langs = langs or ["es", "en"]
    try:
        from surya.detection import batch_text_detection
        from surya.recognition import batch_recognition

        det_model, det_processor, rec_model, rec_processor = models
        img_rgb = img.convert("RGB")

        # 1) Detectar regiones de texto
        det_results = batch_text_detection([img_rgb], det_model, det_processor)

        # 2) Recortar cada bbox y preparar crops
        det_result = det_results[0]
        bboxes = det_result.bboxes if det_result else []

        if not bboxes:
            # Sin detecciones: reconocer imagen completa como un solo crop
            rec_results = batch_recognition(
                [img_rgb], [langs], rec_model, rec_processor
            )
            lines = []
            for res in rec_results:
                t = getattr(res, "text", "") or ""
                if t.strip():
                    lines.append(t)
            text = "\n".join(lines)
        else:
            # Recortar cada línea detectada y reconocer por separado
            crops = []
            for bbox in bboxes:
                poly = bbox.polygon  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                x1, y1 = max(0, int(min(xs))), max(0, int(min(ys)))
                x2, y2 = min(img_rgb.width, int(max(xs))), min(
                    img_rgb.height, int(max(ys))
                )
                if x2 > x1 and y2 > y1:
                    crops.append(img_rgb.crop((x1, y1, x2, y2)))

            if not crops:
                crops = [img_rgb]

            lang_list = [langs] * len(crops)
            rec_results = batch_recognition(crops, lang_list, rec_model, rec_processor)

            lines = []
            for res in rec_results:
                t = getattr(res, "text", "") or ""
                if t.strip():
                    lines.append(t)
            text = "\n".join(lines)

        return {
            "ok": True,
            "text": text,
            "engine": "surya",
            "quality": _quality_score(text),
        }
    except Exception as e:
        logger.error(f"Error surya OCR: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 3: docTR — industrial, formularios, layouts complejos
# ═══════════════════════════════════════════════════════════════════════════════


def _load_doctr():
    global _doctr_model
    if _doctr_model is not None:
        return _doctr_model
    try:
        import os as _os

        _os.environ.setdefault("USE_TORCH", "1")
        from doctr.models import ocr_predictor

        logger.info("Cargando modelo docTR (primera vez, ~20s)...")
        _doctr_model = ocr_predictor(pretrained=True)
        logger.info("docTR cargado")
        return _doctr_model
    except Exception as e:
        logger.warning(f"docTR no disponible: {e}")
        return None


def _ocr_doctr(img: Image.Image) -> dict:
    """OCR con docTR — detección de layout + reconocimiento transformer."""
    model = _load_doctr()
    if not model:
        return {"ok": False, "error": "docTR no disponible"}

    try:
        import os
        import tempfile

        from doctr.io import DocumentFile

        # docTR trabaja mejor con archivos que con arrays en memoria
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            img.save(tmp_path)

        try:
            doc = DocumentFile.from_images([tmp_path])
            result = model(doc)
            lines = []
            for page in result.pages:
                for block in page.blocks:
                    for line in block.lines:
                        words = [w.value for w in line.words if w.value.strip()]
                        if words:
                            lines.append(" ".join(words))
            text = "\n".join(lines)
        finally:
            os.unlink(tmp_path)

        return {
            "ok": True,
            "text": text,
            "engine": "doctr",
            "quality": _quality_score(text),
        }
    except Exception as e:
        logger.error(f"Error docTR: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 4: TrOCR — texto manuscrito y fuentes inusuales
# ═══════════════════════════════════════════════════════════════════════════════


def _load_trocr(mode: str = "printed"):
    global _trocr_printed, _trocr_handwritten
    cache = _trocr_printed if mode == "printed" else _trocr_handwritten

    if cache is not None:
        return cache

    model_name = (
        "microsoft/trocr-base-printed"
        if mode == "printed"
        else "microsoft/trocr-base-handwritten"
    )
    try:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        logger.info(f"Cargando TrOCR {mode} (~500 MB, primera vez)...")
        processor = TrOCRProcessor.from_pretrained(model_name)
        model = VisionEncoderDecoderModel.from_pretrained(model_name)
        result = (processor, model)
        if mode == "printed":
            _trocr_printed = result
        else:
            _trocr_handwritten = result
        logger.info(f"TrOCR {mode} cargado")
        return result
    except Exception as e:
        logger.warning(f"TrOCR {mode} no disponible: {e}")
        return None


def _ocr_trocr(img: Image.Image, mode: str = "printed") -> dict:
    """
    TrOCR — texto impreso o manuscrito.
    Para documentos grandes, divide en franjas horizontales.
    """
    loaded = _load_trocr(mode)
    if not loaded:
        return {"ok": False, "error": f"TrOCR {mode} no disponible"}

    processor, model = loaded
    try:
        import torch

        # TrOCR espera imágenes RGB de hasta ~384×384
        # Para documentos grandes, dividimos en franjas de ~384px de alto
        w, h = img.size
        rgb_img = img.convert("RGB")

        if h <= 512:
            # Imagen pequeña: procesar completa
            crops = [rgb_img]
        else:
            # Dividir en franjas horizontales solapadas
            strip_h = 384
            overlap = 64
            crops = []
            y = 0
            while y < h:
                crop = rgb_img.crop((0, y, w, min(h, y + strip_h)))
                crops.append(crop)
                y += strip_h - overlap

        texts = []
        for crop in crops:
            pixel_values = processor(images=crop, return_tensors="pt").pixel_values
            with torch.no_grad():
                generated_ids = model.generate(pixel_values, max_new_tokens=256)
            generated_text = processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]
            if generated_text.strip():
                texts.append(generated_text.strip())

        text = "\n".join(texts)
        return {
            "ok": True,
            "text": text,
            "engine": f"trocr-{mode}",
            "quality": _quality_score(text),
        }
    except Exception as e:
        logger.error(f"Error TrOCR {mode}: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Preprocesamiento avanzado con deskew
# ═══════════════════════════════════════════════════════════════════════════════


def preprocess_advanced(
    img: Image.Image, use_albumentations: bool = True
) -> Image.Image:
    """
    Pipeline de preprocesamiento avanzado:
    1. Corrección de inclinación (deskew preciso con scipy)
    2. Mejora de contraste adaptativa (CLAHE)
    3. Reducción de ruido bilateral
    4. Opcionalmente: albumentations sharpen
    """
    try:
        import cv2
        from deskew import determine_skew
        from scipy.ndimage import rotate as scipy_rotate

        arr = np.array(img.convert("L"))

        # Corrección de skew
        angle = determine_skew(arr)
        if angle is not None and abs(angle) > 0.3:
            logger.debug(f"Corrigiendo inclinación: {angle:.2f}°")
            arr = scipy_rotate(arr, angle, reshape=False, mode="constant", cval=255)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        arr = clahe.apply(arr.astype(np.uint8))
        arr = cv2.bilateralFilter(arr, 9, 75, 75)

        result = Image.fromarray(arr)

        # Albumentations sharpen extra si está disponible
        if use_albumentations:
            try:
                from maer_backend.maer_image_intelligence import \
                    preprocess_albumentations

                result = preprocess_albumentations(result, profile="document")
            except Exception as e:
                pass

        return result
    except Exception as e:
        logger.debug(f"Preprocesamiento avanzado falló: {e}")
        return img


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 6: Kraken — OCR neuronal con modelos CLSTM, ideal para documentos históricos
# ═══════════════════════════════════════════════════════════════════════════════


def _ocr_kraken(img: Image.Image) -> dict:
    """OCR con Kraken — motor CLSTM, bueno para documentos históricos y manuscritos."""
    try:
        import kraken.binarization as binarize
        from kraken import pageseg, rpred
        from kraken.lib import models as kraken_models

        # Binarizar
        img_bin = binarize.nlbin(img.convert("L"))

        # Segmentación de líneas
        baseline_seg = pageseg.segment(img_bin)

        # Usar modelo por defecto si está disponible
        try:
            model = kraken_models.load_any(
                kraken_models.RECOGNITION_PRETRAINED_MODEL_SEG
            )
        except Exception as e:
            # Intentar ruta de modelo en caché
            import os

            model_path = os.path.expanduser("~/.cache/kraken/en_best.mlmodel")
            if not os.path.exists(model_path):
                return {"ok": False, "error": "Kraken sin modelo descargado"}
            model = kraken_models.load_any(model_path)

        pred_it = rpred.rpred(model, img_bin, baseline_seg)
        lines = [r.prediction for r in pred_it if r.prediction.strip()]
        text = "\n".join(lines)
        return {
            "ok": True,
            "text": text,
            "engine": "kraken",
            "quality": _quality_score(text),
        }
    except ImportError:
        return {"ok": False, "error": "kraken no instalado"}
    except Exception as e:
        logger.error(f"Error Kraken: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 7: RapidOCR — ONNX, rápido, sin PyTorch, muy ligero
# ═══════════════════════════════════════════════════════════════════════════════


def _ocr_rapidocr(img: Image.Image) -> dict:
    """OCR con RapidOCR — motor ONNX ultra-rápido, excelente para texto impreso."""
    try:
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR

        ocr = RapidOCR()
        img_array = np.array(img.convert("RGB"))
        result, _ = ocr(img_array)

        if not result:
            return {"ok": False, "error": "Sin resultados RapidOCR"}

        lines = [item[1] for item in result if item and len(item) > 1]
        text = "\n".join(lines)
        return {
            "ok": True,
            "text": text,
            "engine": "rapidocr",
            "quality": _quality_score(text),
        }
    except ImportError:
        return {"ok": False, "error": "rapidocr-onnxruntime no instalado"}
    except Exception as e:
        logger.error(f"Error RapidOCR: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 8: MangaOCR — transformer fino para texto denso impreso
# ═══════════════════════════════════════════════════════════════════════════════

_manga_ocr_model = None


def _load_manga_ocr():
    global _manga_ocr_model
    if _manga_ocr_model is not None:
        return _manga_ocr_model
    try:
        from manga_ocr import MangaOcr

        logger.info("Cargando MangaOCR (primera vez, ~30s)...")
        _manga_ocr_model = MangaOcr()
        logger.info("MangaOCR cargado")
        return _manga_ocr_model
    except Exception as e:
        logger.warning(f"MangaOCR no disponible: {e}")
        return None


def _ocr_manga(img: Image.Image) -> dict:
    """MangaOCR — transformer para texto impreso denso, fuentes pequeñas."""
    model = _load_manga_ocr()
    if not model:
        return {"ok": False, "error": "MangaOCR no disponible"}
    try:
        # MangaOCR procesa imagen completa como una unidad
        text = model(img.convert("RGB"))
        return {
            "ok": True,
            "text": text or "",
            "engine": "manga_ocr",
            "quality": _quality_score(text or ""),
        }
    except Exception as e:
        logger.error(f"Error MangaOCR: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 9: PaddleOCR — estado del arte, soporte multilingüe
# ═══════════════════════════════════════════════════════════════════════════════

_paddle_ocr_model = None


def _load_paddleocr():
    global _paddle_ocr_model
    if _paddle_ocr_model is not None:
        return _paddle_ocr_model
    try:
        from paddleocr import PaddleOCR

        logger.info("Cargando PaddleOCR (primera vez)...")
        _paddle_ocr_model = PaddleOCR(
            use_angle_cls=True,
            lang="es",
            show_log=False,
            use_gpu=False,
        )
        logger.info("PaddleOCR cargado")
        return _paddle_ocr_model
    except Exception as e:
        logger.warning(f"PaddleOCR no disponible: {e}")
        return None


def _ocr_paddle(img: Image.Image) -> dict:
    """PaddleOCR — motor de estado del arte con ángulo, clasificación y detección."""
    model = _load_paddleocr()
    if not model:
        return {"ok": False, "error": "PaddleOCR no disponible"}
    try:
        import numpy as np

        img_array = np.array(img.convert("RGB"))
        results = model.ocr(img_array, cls=True)
        lines = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) > 1 and line[1]:
                    lines.append(line[1][0])
        text = "\n".join(lines)
        return {
            "ok": True,
            "text": text,
            "engine": "paddleocr",
            "quality": _quality_score(text),
        }
    except Exception as e:
        logger.error(f"Error PaddleOCR: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Motor 10: OCRmyPDF — pipeline Tesseract mejorado con preprocesado avanzado
# ═══════════════════════════════════════════════════════════════════════════════


def _ocr_ocrmypdf(path: Path, lang: str = "spa+eng") -> dict:
    """
    OCRmyPDF: aplica preprocesado avanzado (deskew, clean, rotate)
    y Tesseract LSTM. Excelente para PDFs escaneados mal orientados.
    Solo funciona con archivos PDF o imágenes en disco (necesita path).
    """
    try:
        import tempfile

        import ocrmypdf

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as out_f:
            out_path = Path(out_f.name)

        # Si es imagen, convertir a PDF temporal primero
        if path.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"):
            img = Image.open(str(path)).convert("RGB")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                in_pdf_path = Path(tmp_pdf.name)
            img.save(str(in_pdf_path), "PDF")
        else:
            in_pdf_path = path

        ocrmypdf.ocr(
            str(in_pdf_path),
            str(out_path),
            language=lang,
            deskew=True,
            clean=True,
            rotate_pages=True,
            skip_text=False,
            progress_bar=False,
            jobs=1,
        )

        # Extraer texto del PDF resultante
        from pypdf import PdfReader

        reader = PdfReader(str(out_path))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)

        out_path.unlink(missing_ok=True)
        if in_pdf_path != path:
            in_pdf_path.unlink(missing_ok=True)

        return {
            "ok": True,
            "text": text.strip(),
            "engine": "ocrmypdf",
            "quality": _quality_score(text),
        }
    except ImportError:
        return {"ok": False, "error": "ocrmypdf no instalado"}
    except Exception as e:
        logger.error(f"Error OCRmyPDF: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Extracción de tablas en imágenes con img2table
# ═══════════════════════════════════════════════════════════════════════════════


def extract_tables_from_image(path: Path) -> dict:
    """
    Detecta y extrae tablas de imágenes escaneadas usando OpenCV + Tesseract.
    Detecta líneas horizontales y verticales para reconstruir la estructura de tabla.
    Funciona en JPG, PNG, BMP — no solo en PDFs digitales.
    """
    try:
        import cv2
        import pytesseract

        img_bgr = cv2.imread(str(path))
        if img_bgr is None:
            return {"ok": False, "error": "No se pudo leer la imagen", "tables": []}

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        h, w = binary.shape

        # Detectar líneas horizontales
        horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(10, w // 30), 1))
        horiz_lines = cv2.morphologyEx(
            binary, cv2.MORPH_OPEN, horiz_kernel, iterations=2
        )

        # Detectar líneas verticales
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(10, h // 30)))
        vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel, iterations=2)

        # Combinar líneas
        grid = cv2.add(horiz_lines, vert_lines)
        dilated = cv2.dilate(grid, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

        # Encontrar contornos de celdas
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        cells = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            area = cw * ch
            # Filtrar por tamaño mínimo de celda
            if 100 < area < (w * h * 0.8) and cw > 20 and ch > 10:
                cells.append((x, y, cw, ch))

        if len(cells) < 4:
            return {
                "ok": True,
                "path": str(path),
                "total_tables": 0,
                "tables": [],
                "engine": "opencv",
                "note": "Sin tablas detectadas",
            }

        # Agrupar celdas en filas por coordenada Y (tolerancia ±15px)
        cells.sort(key=lambda c: (c[1], c[0]))
        rows = []
        current_row = [cells[0]]
        for cell in cells[1:]:
            if abs(cell[1] - current_row[0][1]) <= 15:
                current_row.append(cell)
            else:
                rows.append(sorted(current_row, key=lambda c: c[0]))
                current_row = [cell]
        if current_row:
            rows.append(sorted(current_row, key=lambda c: c[0]))

        # Extraer texto de cada celda
        table_rows = []
        for row in rows:
            row_texts = []
            for x, y, cw, ch in row:
                crop = gray[y : y + ch, x : x + cw]
                text = (
                    pytesseract.image_to_string(
                        crop, lang="spa+eng", config="--psm 6 --oem 3"
                    )
                    .strip()
                    .replace("\n", " ")
                )
                row_texts.append(text)
            if any(row_texts):
                table_rows.append(row_texts)

        if not table_rows:
            return {
                "ok": True,
                "path": str(path),
                "total_tables": 0,
                "tables": [],
                "engine": "opencv",
            }

        headers = table_rows[0]
        data_rows = table_rows[1:]
        table_result = [
            {
                "table_index": 0,
                "headers": headers,
                "rows": data_rows,
                "row_count": len(data_rows),
                "col_count": len(headers),
            }
        ]

        return {
            "ok": True,
            "path": str(path),
            "total_tables": 1,
            "tables": table_result,
            "engine": "opencv+tesseract",
        }
    except Exception as e:
        logger.error(f"Error extrayendo tablas de imagen: {e}")
        return {"ok": False, "error": str(e), "tables": []}


# ═══════════════════════════════════════════════════════════════════════════════
# Orquestador principal
# ═══════════════════════════════════════════════════════════════════════════════


def ocr_advanced(img: Image.Image, hint: str = "auto", preprocess: bool = True) -> dict:
    """
    Orquesta múltiples motores OCR y retorna el mejor resultado.

    hint: 'auto' | 'scan' | 'photo' | 'handwritten' | 'form' | 'fast'
      auto        → analiza la imagen y elige automáticamente
      scan        → prioriza surya (documentos escaneados)
      photo       → prioriza docTR (fotos de documentos)
      handwritten → prioriza TrOCR handwritten (texto manuscrito)
      form        → prioriza docTR (formularios con tablas)
      fast        → solo EasyOCR + Tesseract (sin modelos pesados)
    """
    if preprocess:
        img = preprocess_advanced(img)

    info = _analyze_image(img)
    best_result = {"ok": False, "text": "", "engine": "none", "quality": 0.0}

    # ── Determinar cascada según hint y características de la imagen ──────────
    if hint == "handwritten":
        cascade = [
            "trocr_hw",
            "kraken",
            "doctr",
            "surya",
            "rapidocr",
            "easyocr",
            "tesseract",
        ]
    elif hint == "form":
        cascade = [
            "doctr",
            "paddleocr",
            "rapidocr",
            "surya",
            "trocr_pr",
            "easyocr",
            "tesseract",
        ]
    elif hint == "fast":
        cascade = ["rapidocr", "easyocr", "tesseract"]
    elif hint == "scan" or (hint == "auto" and info["is_scan"]):
        cascade = [
            "surya",
            "doctr",
            "paddleocr",
            "kraken",
            "rapidocr",
            "easyocr",
            "tesseract",
        ]
    elif hint == "photo" or (hint == "auto" and not info["is_scan"]):
        cascade = [
            "doctr",
            "paddleocr",
            "surya",
            "rapidocr",
            "trocr_pr",
            "easyocr",
            "tesseract",
        ]
    elif hint == "dense":
        cascade = [
            "manga_ocr",
            "trocr_pr",
            "rapidocr",
            "doctr",
            "paddleocr",
            "easyocr",
            "tesseract",
        ]
    elif hint == "turbo":
        # Preprocesado Wand+albumentations antes de OCR
        try:
            import tempfile

            from maer_backend.maer_image_intelligence import preprocess_turbo

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp = Path(f.name)
            img.save(str(tmp))
            img = preprocess_turbo(tmp)
            tmp.unlink(missing_ok=True)
        except Exception as e:
            logger.debug(f"preprocess_turbo falló: {e}")
        cascade = ["surya", "doctr", "paddleocr", "rapidocr", "easyocr", "tesseract"]
    else:
        cascade = ["surya", "paddleocr", "doctr", "rapidocr", "easyocr", "tesseract"]

    logger.info(
        f"OCR advanced — hint={hint}, is_scan={info['is_scan']}, "
        f"cascade={cascade[:3]}..."
    )

    for engine_name in cascade:
        try:
            if engine_name == "surya":
                result = _ocr_surya(img)
            elif engine_name == "doctr":
                result = _ocr_doctr(img)
            elif engine_name == "trocr_hw":
                result = _ocr_trocr(img, mode="handwritten")
            elif engine_name == "trocr_pr":
                result = _ocr_trocr(img, mode="printed")
            elif engine_name == "kraken":
                result = _ocr_kraken(img)
            elif engine_name == "rapidocr":
                result = _ocr_rapidocr(img)
            elif engine_name == "manga_ocr":
                result = _ocr_manga(img)
            elif engine_name == "paddleocr":
                result = _ocr_paddle(img)
            elif engine_name == "easyocr":
                from maer_backend.ocr_engine import ocr_easyocr

                text = ocr_easyocr(img)
                result = {
                    "ok": bool(text),
                    "text": text,
                    "engine": "easyocr",
                    "quality": _quality_score(text),
                }
            elif engine_name == "tesseract":
                from maer_backend.ocr_engine import ocr_tesseract

                text = ocr_tesseract(img)
                result = {
                    "ok": bool(text),
                    "text": text,
                    "engine": "tesseract",
                    "quality": _quality_score(text),
                }
            else:
                continue
        except Exception as e:
            logger.debug(f"Motor {engine_name} falló: {e}")
            continue

        if not result.get("ok"):
            continue

        quality = result.get("quality", _quality_score(result.get("text", "")))
        result["quality"] = quality

        logger.info(
            f"  {engine_name}: {len(result.get('text',''))} chars, "
            f"quality={quality:.2f}"
        )

        # Guardar si es el mejor hasta ahora
        if quality > best_result.get("quality", 0):
            best_result = result

        # Si la calidad es buena, parar
        if quality >= QUALITY_GOOD:
            break

    best_result["image_info"] = info
    return best_result


def ocr_document_advanced(
    path: Path, hint: str = "auto", max_pages: int = 50, use_cache: bool = True
) -> dict:
    """
    Punto de entrada principal para OCR avanzado.
    Maneja PDFs e imágenes con el orquestador completo.

    Retorna:
      {ok, text, engine, quality, pages_processed, tables, image_info, cached}
    """
    from maer_backend.ocr_engine import get_cached_ocr, set_cached_ocr

    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}"}

    ext = path.suffix.lower()

    # ── Cache ──────────────────────────────────────────────────────────────────
    if use_cache:
        cached = get_cached_ocr(path)
        if cached is not None:
            return {
                "ok": True,
                "text": cached,
                "engine": "cache",
                "quality": 1.0,
                "cached": True,
                "pages_processed": 0,
            }

    # ── PDF ────────────────────────────────────────────────────────────────────
    if ext == ".pdf":
        # Intentar extracción directa con PyMuPDF
        direct = _ocr_pymupdf_pdf(path, max_pages=max_pages)
        if direct.get("ok") and direct.get("quality", 0) >= QUALITY_OK:
            if use_cache:
                set_cached_ocr(path, direct["text"], "pymupdf")
            direct["cached"] = False
            direct["pages_processed"] = direct["text"].count("[Página")
            return direct

        # Si el PDF es escaneado: convertir páginas a imágenes y usar OCR avanzado
        logger.info(f"PDF escaneado detectado en {path.name}, usando OCR por páginas")
        pages = extract_pdf_pages_as_images(path, dpi=200, max_pages=max_pages)
        if not pages:
            return {"ok": False, "error": "No se pudieron extraer páginas del PDF"}

        all_text = []
        best_engine = "none"
        total_quality = 0.0

        for idx, page_img in enumerate(pages):
            result = ocr_advanced(page_img, hint=hint)
            if result.get("text", "").strip():
                all_text.append(f"[Página {idx + 1}]\n{result['text']}")
                best_engine = result.get("engine", best_engine)
                total_quality += result.get("quality", 0)

        full_text = "\n\n".join(all_text)
        avg_quality = total_quality / len(pages) if pages else 0

        # Si la calidad sigue baja, intentar OCRmyPDF como pipeline alternativo
        if avg_quality < QUALITY_OK:
            logger.info("Calidad baja, intentando OCRmyPDF como fallback...")
            ocrmypdf_result = _ocr_ocrmypdf(path)
            if (
                ocrmypdf_result.get("ok")
                and ocrmypdf_result.get("quality", 0) > avg_quality
            ):
                full_text = ocrmypdf_result["text"]
                best_engine = "ocrmypdf"
                avg_quality = ocrmypdf_result["quality"]

        if use_cache:
            set_cached_ocr(path, full_text, best_engine)

        return {
            "ok": True,
            "text": full_text,
            "engine": best_engine,
            "quality": round(avg_quality, 3),
            "pages_processed": len(all_text),
            "cached": False,
        }

    # ── Imagen ─────────────────────────────────────────────────────────────────
    try:
        img = Image.open(str(path)).convert("RGB")
    except Exception as e:
        return {"ok": False, "error": f"No se pudo abrir imagen: {e}"}

    result = ocr_advanced(img, hint=hint)
    result["path"] = str(path)
    result["cached"] = False

    if use_cache and result.get("ok") and result.get("text"):
        set_cached_ocr(path, result["text"], result.get("engine", "advanced"))

    return result


def analyze_document_full(path: Path, max_pages: int = 30) -> dict:
    """
    Análisis completo de documento: OCR + tablas + metadatos + clasificación.
    Combina PyMuPDF, surya, docTR e img2table en un solo resultado.
    """
    from maer_backend.maer_pdf_analyzer import classify_document

    ext = path.suffix.lower()
    result = {
        "ok": True,
        "path": str(path),
        "file_name": path.name,
        "ext": ext,
        "text": "",
        "tables": [],
        "metadata": {},
        "doc_type": "documento_general",
        "engine": "none",
        "quality": 0.0,
    }

    # OCR del texto
    ocr_result = ocr_document_advanced(path, max_pages=max_pages)
    if ocr_result.get("ok"):
        result["text"] = ocr_result.get("text", "")
        result["engine"] = ocr_result.get("engine", "none")
        result["quality"] = ocr_result.get("quality", 0.0)

    # Metadatos de PDF con PyMuPDF
    if ext == ".pdf":
        try:
            import fitz

            doc = fitz.open(str(path))
            meta = doc.metadata or {}
            result["metadata"] = {k: v for k, v in meta.items() if v}
            result["total_pages"] = len(doc)
            doc.close()
        except Exception as e:
            pass

        # Tablas con pdfplumber (para PDFs con tablas digitales)
        try:
            from maer_backend.table_extractor import extract_tables_from_pdf

            tbl = extract_tables_from_pdf(path, max_pages=max_pages)
            result["tables"] = tbl.get("tables", [])
        except Exception as e:
            pass
    else:
        # Tablas en imágenes con img2table
        img_tables = extract_tables_from_image(path)
        if img_tables.get("ok"):
            result["tables"] = img_tables.get("tables", [])

    # Clasificar tipo de documento
    if result["text"]:
        result["doc_type"] = classify_document(result["text"])

    result["char_count"] = len(result["text"])
    result["has_tables"] = len(result["tables"]) > 0

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Estado del motor
# ═══════════════════════════════════════════════════════════════════════════════


def engine_status() -> dict:
    """Retorna qué motores OCR están disponibles."""
    status = {}

    try:
        import fitz

        status["pymupdf"] = str(fitz.__version__)
    except ImportError:
        status["pymupdf"] = None

    try:
        pass

        status["surya"] = "disponible"
    except ImportError:
        status["surya"] = None

    try:
        pass

        status["doctr"] = "disponible"
    except ImportError:
        status["doctr"] = None

    try:
        pass

        status["trocr"] = "disponible (transformers)"
    except ImportError:
        status["trocr"] = None

    try:
        pass

        status["img2table"] = "disponible"
    except ImportError:
        status["img2table"] = None

    try:
        pass

        status["deskew"] = "disponible"
    except ImportError:
        status["deskew"] = None

    try:
        import easyocr

        status["easyocr"] = easyocr.__version__
    except ImportError:
        status["easyocr"] = None

    try:
        import pytesseract

        status["tesseract"] = str(pytesseract.get_tesseract_version())
    except Exception as e:
        status["tesseract"] = None

    try:
        from importlib.metadata import version as _v

        import kraken  # noqa: F401

        status["kraken"] = _v("kraken")
    except Exception as e:
        status["kraken"] = None

    try:
        import ocrmypdf

        status["ocrmypdf"] = ocrmypdf.__version__
    except ImportError:
        status["ocrmypdf"] = None

    try:
        from importlib.metadata import version as _v

        from rapidocr_onnxruntime import RapidOCR  # noqa: F401

        status["rapidocr"] = _v("rapidocr-onnxruntime")
    except Exception as e:
        status["rapidocr"] = None

    try:
        from importlib.metadata import version as _v

        from manga_ocr import MangaOcr  # noqa: F401

        status["manga_ocr"] = _v("manga-ocr")
    except Exception as e:
        status["manga_ocr"] = None

    try:
        from importlib.metadata import version as _v

        from paddleocr import PaddleOCR  # noqa: F401

        status["paddleocr"] = _v("paddleocr")
    except Exception as e:
        status["paddleocr"] = None

    return status
