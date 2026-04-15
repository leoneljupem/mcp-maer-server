#!/usr/bin/env python3
# 🦁 MAER NLP ENGINE — Clasificación de entidades con NLP
# Leonel Mojica — Ecatepec MX — 2026

"""
Motor NLP para clasificación de entidades en texto.
Usa spaCy con modelo español para detectar:
  - Personas (nombres completos)
  - Fechas
  - Ubicaciones
  - Organizaciones
  - Cantidades monetarias
Complementa las regex existentes de CURP/RFC/INE.
"""

import logging
from typing import Optional

logger = logging.getLogger("maer.nlp")

_nlp = None
_nlp_loaded = False


def _load_nlp():
    """Carga el modelo spaCy de forma lazy."""
    global _nlp, _nlp_loaded
    if _nlp_loaded:
        return _nlp

    try:
        import spacy
        _nlp = spacy.load("es_core_news_md")
        _nlp_loaded = True
        logger.info("Modelo spaCy es_core_news_md cargado")
    except OSError:
        try:
            import spacy
            _nlp = spacy.load("es_core_news_sm")
            _nlp_loaded = True
            logger.info("Modelo spaCy es_core_news_sm cargado (fallback)")
        except Exception:
            logger.warning("No se pudo cargar modelo spaCy para español")
            _nlp_loaded = True  # Evitar reintentos
            _nlp = None
    except ImportError:
        logger.warning("spaCy no instalado")
        _nlp_loaded = True
        _nlp = None

    return _nlp


def extract_entities(text: str, max_chars: int = 50000) -> dict:
    """
    Extrae entidades nombradas de un texto.

    Retorna: {
        ok: bool,
        entities: {
            personas: [{text, start, end, label}],
            organizaciones: [...],
            ubicaciones: [...],
            fechas: [...],
            cantidades: [...],
            otros: [...]
        },
        summary: {
            total: int,
            by_type: {PER: int, ORG: int, LOC: int, ...}
        }
    }
    """
    nlp = _load_nlp()
    if nlp is None:
        return {
            "ok": False,
            "error": "Modelo NLP no disponible. Instala spaCy y descarga: python3 -m spacy download es_core_news_md",
            "entities": {},
        }

    # Limitar texto para performance
    text_truncated = text[:max_chars]

    try:
        doc = nlp(text_truncated)
    except Exception as e:
        return {"ok": False, "error": f"Error procesando NLP: {e}", "entities": {}}

    entities = {
        "personas": [],
        "organizaciones": [],
        "ubicaciones": [],
        "fechas": [],
        "cantidades": [],
        "otros": [],
    }

    LABEL_MAP = {
        "PER": "personas",
        "ORG": "organizaciones",
        "LOC": "ubicaciones",
        "GPE": "ubicaciones",
        "DATE": "fechas",
        "MONEY": "cantidades",
        "CARDINAL": "cantidades",
    }

    seen = set()  # Evitar duplicados
    for ent in doc.ents:
        key = (ent.text.strip(), ent.label_)
        if key in seen or not ent.text.strip():
            continue
        seen.add(key)

        entry = {
            "text": ent.text.strip(),
            "start": ent.start_char,
            "end": ent.end_char,
            "label": ent.label_,
        }

        category = LABEL_MAP.get(ent.label_, "otros")
        entities[category].append(entry)

    # Summary
    by_type = {}
    total = 0
    for cat, items in entities.items():
        if items:
            by_type[cat] = len(items)
            total += len(items)

    return {
        "ok": True,
        "entities": entities,
        "summary": {
            "total": total,
            "by_type": by_type,
        },
    }


def extract_key_phrases(text: str, max_phrases: int = 20) -> dict:
    """
    Extrae frases clave del texto basándose en noun chunks de spaCy.
    """
    nlp = _load_nlp()
    if nlp is None:
        return {"ok": False, "error": "Modelo NLP no disponible", "phrases": []}

    try:
        doc = nlp(text[:50000])
        chunks = []
        seen = set()
        for chunk in doc.noun_chunks:
            clean = chunk.text.strip().lower()
            if clean not in seen and len(clean) > 2:
                seen.add(clean)
                chunks.append({
                    "text": chunk.text.strip(),
                    "root": chunk.root.text,
                    "root_pos": chunk.root.pos_,
                })
                if len(chunks) >= max_phrases:
                    break

        return {"ok": True, "phrases": chunks, "total": len(chunks)}
    except Exception as e:
        return {"ok": False, "error": f"Error: {e}", "phrases": []}


def classify_document(text: str) -> dict:
    """
    Clasificación básica de documento por contenido.
    Analiza entidades y patrones para sugerir tipo de documento.
    """
    entities_result = extract_entities(text)
    if not entities_result.get("ok"):
        return {"ok": False, "error": "No se pudo analizar", "type": "unknown"}

    entities = entities_result["entities"]
    summary = entities_result["summary"]

    # Heurísticas de clasificación
    doc_type = "general"
    confidence = 0.3

    n_personas = len(entities.get("personas", []))
    n_orgs = len(entities.get("organizaciones", []))
    n_fechas = len(entities.get("fechas", []))
    n_cantidades = len(entities.get("cantidades", []))

    text_lower = text.lower()

    if any(kw in text_lower for kw in ["curp", "rfc", "ine", "credencial", "nacimiento"]):
        doc_type = "identificacion"
        confidence = 0.8
    elif any(kw in text_lower for kw in ["factura", "cfdi", "iva", "subtotal", "total"]):
        doc_type = "factura"
        confidence = 0.8
    elif any(kw in text_lower for kw in ["contrato", "cláusula", "partes", "vigencia"]):
        doc_type = "contrato"
        confidence = 0.7
    elif n_cantidades > 5 and n_fechas > 2:
        doc_type = "financiero"
        confidence = 0.6
    elif n_personas > 3 and n_orgs > 1:
        doc_type = "directorio"
        confidence = 0.5
    elif n_fechas > 5:
        doc_type = "cronologia"
        confidence = 0.5

    return {
        "ok": True,
        "type": doc_type,
        "confidence": confidence,
        "entities_summary": summary,
    }
