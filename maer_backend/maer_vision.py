#!/usr/bin/env python3
# 🦁 MAER Vision — Análisis de imágenes con Claude Vision
# Leonel Mojica — Ecatepec MX — 2026

"""
Análisis visual de imágenes y documentos escaneados usando Claude Vision.
Va mucho más allá del OCR clásico:
- Describe el contenido visual completo de la imagen
- Extrae texto de imágenes borrosas, inclinadas o mal escaneadas
- Clasifica automáticamente el tipo de documento
- Extrae campos específicos de formularios y credenciales
- Detecta sellos, firmas, tablas y estructuras visuales
"""

import base64
import logging
import os
from pathlib import Path

logger = logging.getLogger("maer.vision")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}
PDF_EXT = ".pdf"

_VISION_SYSTEM = (
    "Eres MAER Vision, un asistente experto en análisis de documentos mexicanos. "
    "Analizas imágenes de documentos IMSS, credenciales, actas, recibos y cualquier "
    "tipo de documento o fotografía. Respondes siempre en español, con precisión y detalle."
)


def _get_anthropic_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada en .env")
    try:
        import anthropic

        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        raise ImportError("SDK anthropic no instalado")


def _image_to_base64(path: Path) -> tuple:
    """Convierte imagen a base64 y retorna (base64_str, media_type)."""
    ext = path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_types.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def _pdf_page_to_image(path: Path, page_num: int = 0, dpi: int = 150) -> tuple:
    """Convierte página de PDF a imagen base64."""
    try:
        from pdf2image import convert_from_path

        pages = convert_from_path(
            str(path), dpi=dpi, first_page=page_num + 1, last_page=page_num + 1
        )
        if not pages:
            return None, None
        import io

        buf = io.BytesIO()
        pages[0].save(buf, format="PNG")
        data = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
        return data, "image/png"
    except Exception as e:
        logger.error(f"Error convirtiendo PDF a imagen: {e}")
        return None, None


def _call_vision(
    image_b64: str, media_type: str, prompt: str, max_tokens: int = 1500
) -> str:
    """Llama a Claude Vision con una imagen."""
    client = _get_anthropic_client()
    model = os.environ.get(
        "ANTHROPIC_VISION_MODEL",
        os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
    )
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_VISION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return response.content[0].text


# ── API pública ──────────────────────────────────────────────────────────────


def analyze_image(path: Path, prompt: str = None) -> dict:
    """
    Análisis completo de una imagen o primera página de PDF.
    Describe el contenido visual, texto visible, tipo de documento detectado.
    """
    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}"}

    ext = path.suffix.lower()
    if ext == PDF_EXT:
        b64, mtype = _pdf_page_to_image(path, page_num=0)
        source = "pdf_page_1"
    elif ext in IMAGE_EXTS:
        b64, mtype = _image_to_base64(path)
        source = "image"
    else:
        return {"ok": False, "error": f"Formato no soportado: {ext}"}

    if not b64:
        return {"ok": False, "error": "No se pudo convertir el archivo a imagen"}

    default_prompt = (
        "Analiza esta imagen en detalle:\n"
        "1. Describe qué tipo de documento o imagen es\n"
        "2. Extrae TODO el texto visible (incluyendo texto pequeño, sellos y firmas)\n"
        "3. Describe elementos visuales importantes (logos, tablas, fotografías de personas)\n"
        "4. Indica si hay información personal visible (nombres, números, fechas)\n"
        "5. Evalúa la calidad/legibilidad de la imagen (1-10)\n"
        "Responde de forma estructurada."
    )

    try:
        text = _call_vision(b64, mtype, prompt or default_prompt, max_tokens=2000)
        return {
            "ok": True,
            "path": str(path),
            "source": source,
            "analysis": text,
            "engine": "claude-vision",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(path)}


def extract_text_vision(path: Path) -> dict:
    """
    Extrae todo el texto visible de una imagen usando Claude Vision.
    Mejor que OCR clásico para imágenes borrosas, inclinadas o con fuentes raras.
    """
    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}"}

    ext = path.suffix.lower()
    if ext == PDF_EXT:
        b64, mtype = _pdf_page_to_image(path, page_num=0)
    elif ext in IMAGE_EXTS:
        b64, mtype = _image_to_base64(path)
    else:
        return {"ok": False, "error": f"Formato no soportado: {ext}"}

    if not b64:
        return {"ok": False, "error": "No se pudo procesar el archivo"}

    prompt = (
        "Extrae TODO el texto que puedas ver en esta imagen, exactamente como aparece. "
        "Incluye números, fechas, nombres, códigos, sellos y cualquier texto pequeño. "
        "Mantén el orden de lectura natural (de arriba a abajo, izquierda a derecha). "
        "Si hay tablas, represéntalas con espacios. "
        "Responde SOLO con el texto extraído, sin comentarios adicionales."
    )

    try:
        text = _call_vision(b64, mtype, prompt, max_tokens=3000)
        return {
            "ok": True,
            "path": str(path),
            "text": text,
            "engine": "claude-vision",
            "chars": len(text),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(path), "text": ""}


def classify_document_image(path: Path) -> dict:
    """
    Identifica automáticamente el tipo de documento en una imagen.
    Retorna: tipo, institución emisora, datos clave detectados.
    """
    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}"}

    ext = path.suffix.lower()
    if ext == PDF_EXT:
        b64, mtype = _pdf_page_to_image(path, page_num=0)
    elif ext in IMAGE_EXTS:
        b64, mtype = _image_to_base64(path)
    else:
        return {"ok": False, "error": f"Formato no soportado: {ext}"}

    if not b64:
        return {"ok": False, "error": "No se pudo procesar el archivo"}

    prompt = (
        "Analiza este documento e identifica:\n"
        "- TIPO: (acta_nacimiento / curp / credencial_ine / nss_imss / recibo_nomina / "
        "estado_cuenta_afore / resolucion_imss / comprobante_domicilio / contrato_trabajo / "
        "pasaporte / acta_matrimonio / carta_trabajo / otro)\n"
        "- INSTITUCIÓN: quién lo emitió\n"
        "- NOMBRE_TITULAR: nombre de la persona (si aparece)\n"
        "- FECHA: fecha del documento (si aparece)\n"
        "- DATOS_CLAVE: 2-3 datos importantes visibles (NSS, CURP, folio, etc.)\n"
        "- LEGIBILIDAD: (buena / regular / mala)\n"
        "Responde en formato:\nTIPO: ...\nINSTITUCIÓN: ...\nNOMBRE_TITULAR: ...\n"
        "FECHA: ...\nDATOS_CLAVE: ...\nLEGIBILIDAD: ..."
    )

    try:
        text = _call_vision(b64, mtype, prompt, max_tokens=500)
        # Parsear respuesta
        result = {
            "ok": True,
            "path": str(path),
            "raw_classification": text,
            "engine": "claude-vision",
        }
        for line in text.split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                key_clean = key.strip().lower().replace(" ", "_")
                result[key_clean] = val.strip()
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(path)}


def extract_fields_from_image(path: Path, fields: list) -> dict:
    """
    Extrae campos específicos de una imagen de documento.
    fields: lista de campos a buscar, e.g. ["NSS", "CURP", "nombre completo", "fecha de nacimiento"]
    """
    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}"}

    ext = path.suffix.lower()
    if ext == PDF_EXT:
        b64, mtype = _pdf_page_to_image(path, page_num=0)
    elif ext in IMAGE_EXTS:
        b64, mtype = _image_to_base64(path)
    else:
        return {"ok": False, "error": f"Formato no soportado: {ext}"}

    if not b64:
        return {"ok": False, "error": "No se pudo procesar el archivo"}

    campos_str = "\n".join(f"- {f}" for f in fields)
    prompt = (
        f"Busca en esta imagen los siguientes campos y extrae su valor exacto:\n"
        f"{campos_str}\n\n"
        "Para cada campo responde en formato:\nCAMPO: valor_encontrado\n"
        "Si un campo no aparece en la imagen, escribe: CAMPO: No encontrado\n"
        "Responde SOLO con los campos y valores, sin texto adicional."
    )

    try:
        text = _call_vision(b64, mtype, prompt, max_tokens=800)
        extracted = {}
        for line in text.split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                extracted[key.strip()] = val.strip()
        return {
            "ok": True,
            "path": str(path),
            "fields_requested": fields,
            "fields_extracted": extracted,
            "raw_response": text,
            "engine": "claude-vision",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(path)}


def ocr_vision_fallback(path: Path) -> dict:
    """
    OCR usando Claude Vision como último recurso cuando los motores clásicos fallan.
    Retorna formato compatible con ocr_engine.ocr_image()
    """
    result = extract_text_vision(path)
    if result.get("ok"):
        return {
            "ok": True,
            "text": result.get("text", ""),
            "engine": "claude-vision",
            "cached": False,
        }
    return {
        "ok": False,
        "text": "",
        "engine": "claude-vision-failed",
        "error": result.get("error", ""),
        "cached": False,
    }


def analyze_pdf_pages_vision(path: Path, max_pages: int = 5) -> dict:
    """
    Analiza múltiples páginas de un PDF con Claude Vision.
    Útil para PDFs escaneados donde el texto directo no es extraíble.
    """
    if not path.exists():
        return {"ok": False, "error": f"Archivo no existe: {path}"}
    if path.suffix.lower() != PDF_EXT:
        return {"ok": False, "error": "Solo PDFs"}

    try:
        from pypdf import PdfReader

        total = len(PdfReader(str(path)).pages)
    except Exception as e:
        total = max_pages

    pages_to_analyze = min(total, max_pages)
    all_text = []
    errors = []

    for page_num in range(pages_to_analyze):
        b64, mtype = _pdf_page_to_image(path, page_num=page_num)
        if not b64:
            errors.append(f"Página {page_num + 1}: no se pudo convertir")
            continue
        prompt = (
            f"Extrae TODO el texto de la página {page_num + 1} de este documento, "
            "exactamente como aparece. Incluye tablas, sellos y texto pequeño."
        )
        try:
            text = _call_vision(b64, mtype, prompt, max_tokens=2000)
            if text.strip():
                all_text.append(f"[Página {page_num + 1}]\n{text}")
        except Exception as e:
            errors.append(f"Página {page_num + 1}: {str(e)[:80]}")

    full_text = "\n\n".join(all_text)
    return {
        "ok": True,
        "path": str(path),
        "pages_analyzed": len(all_text),
        "total_pages": total,
        "full_text": full_text,
        "char_count": len(full_text),
        "errors": errors,
        "engine": "claude-vision",
    }
