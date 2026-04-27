#!/usr/bin/env python3
"""
maer_clasificador.py — Clasificador automático de documentos IMSS/México
═══════════════════════════════════════════════════════════════════════════
Identifica el tipo de documento, extrae campos estructurados
y sugiere carpeta de organización.

Uso:
    from maer_backend.maer_clasificador import clasificar_texto, clasificar_archivo

Leonel Houssen Mojica — Ecatepec MX — 2026
"""

import re
import unicodedata
from pathlib import Path
from typing import Optional


# ── Normalización ─────────────────────────────────────────────────────────────
def _norm(text: str) -> str:
    """Minúsculas + quita acentos para matching robusto."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return nfkd.encode("ascii", "ignore").decode("ascii")


# ── Catálogo de tipos de documento ───────────────────────────────────────────
# Cada tipo tiene: emoji, carpeta sugerida, lista de (patrón, peso)
# Peso 3 = muy diagnóstico, 2 = diagnóstico, 1 = indicativo
TIPOS: dict = {
    "curp": {
        "emoji": "🪪",
        "label": "CURP",
        "carpeta": "Identidad",
        "patrones": [
            ("clave unica de registro de poblacion", 3),
            ("curp", 2),
            ("registro nacional de poblacion", 2),
            ("renapo", 2),
            ("clave de registro", 1),
        ],
    },
    "nss_imss": {
        "emoji": "🏥",
        "label": "Número de Seguridad Social (NSS)",
        "carpeta": "Identidad",
        "patrones": [
            ("numero de seguridad social", 3),
            ("afiliacion imss", 3),
            ("nss", 2),
            ("instituto mexicano del seguro social", 1),
            ("afiliado", 1),
        ],
    },
    "credencial_imss": {
        "emoji": "💳",
        "label": "Credencial IMSS",
        "carpeta": "Identidad",
        "patrones": [
            ("clinica", 1),
            ("unidad de medicina familiar", 2),
            ("umf", 2),
            ("vigencia", 1),
            ("derechohabiente", 2),
            ("instituto mexicano del seguro social", 1),
        ],
    },
    "acta_nacimiento": {
        "emoji": "📜",
        "label": "Acta de Nacimiento",
        "carpeta": "Identidad",
        "patrones": [
            ("acta de nacimiento", 3),
            ("registro civil", 2),
            ("nacido", 2),
            ("nacio en", 2),
            ("oficial del registro civil", 2),
            ("inscripcion", 1),
            ("municipio", 1),
        ],
    },
    "credencial_ine": {
        "emoji": "🪪",
        "label": "Credencial INE/IFE",
        "carpeta": "Identidad",
        "patrones": [
            ("instituto nacional electoral", 3),
            ("ine", 2),
            ("ife", 2),
            ("credencial para votar", 3),
            ("clave de elector", 3),
            ("seccion", 1),
            ("folio", 1),
        ],
    },
    "pasaporte": {
        "emoji": "🛂",
        "label": "Pasaporte",
        "carpeta": "Identidad",
        "patrones": [
            ("pasaporte", 3),
            ("secretaria de relaciones exteriores", 2),
            ("sre", 1),
            ("documento de viaje", 2),
            ("nationality", 2),
            ("passport", 3),
        ],
    },
    "constancia_semanas": {
        "emoji": "📋",
        "label": "Constancia de Semanas Cotizadas",
        "carpeta": "IMSS_Tramites",
        "patrones": [
            ("semanas cotizadas", 3),
            ("constancia de semanas", 3),
            ("numero de semanas", 3),
            ("semanas reconocidas", 3),
            ("cotizacion", 2),
            ("subcuenta de retiro", 2),
            ("aportaciones", 2),
            ("semanas", 1),
        ],
    },
    "resolucion_pension": {
        "emoji": "⚖️",
        "label": "Resolución de Pensión",
        "carpeta": "IMSS_Tramites",
        "patrones": [
            ("resolucion de pension", 3),
            ("pension por vejez", 3),
            ("pension de invalidez", 3),
            ("pension por viudez", 3),
            ("pension por orfandad", 3),
            ("resolucion", 2),
            ("dictamen de incapacidad permanente", 3),
            ("pension vitalicia", 3),
            ("importe de pension", 3),
            ("fecha de resolucion", 2),
            ("folio de resolucion", 2),
        ],
    },
    "solicitud_pension": {
        "emoji": "📝",
        "label": "Solicitud de Pensión IMSS",
        "carpeta": "IMSS_Tramites",
        "patrones": [
            ("solicitud de pension", 3),
            ("tramite de pension", 3),
            ("solicito", 1),
            ("pension por cesantia", 3),
            ("pension por vejez", 2),
            ("conservacion de derechos", 2),
            ("ley del seguro social", 2),
        ],
    },
    "dictamen_medico": {
        "emoji": "🩺",
        "label": "Dictamen Médico IMSS",
        "carpeta": "IMSS_Tramites",
        "patrones": [
            ("dictamen medico", 3),
            ("dictamen de incapacidad", 3),
            ("incapacidad permanente", 3),
            ("invalidez", 2),
            ("incapacidad parcial", 2),
            ("valuacion medica", 3),
            ("comision mixta", 2),
            ("medico tratante", 2),
            ("diagnostico", 1),
        ],
    },
    "incapacidad_temporal": {
        "emoji": "🏨",
        "label": "Incapacidad Temporal (ST/IMSS)",
        "carpeta": "IMSS_Tramites",
        "patrones": [
            ("incapacidad temporal", 3),
            ("subsidio por incapacidad", 3),
            ("dias de incapacidad", 3),
            ("certificado de incapacidad", 3),
            ("riesgo de trabajo", 2),
            ("enfermedad general", 2),
            ("maternidad", 2),
        ],
    },
    "recibo_nomina": {
        "emoji": "💰",
        "label": "Recibo de Nómina",
        "carpeta": "Empleo",
        "patrones": [
            ("recibo de nomina", 3),
            ("nomina", 2),
            ("percepciones", 2),
            ("deducciones", 2),
            ("salario neto", 3),
            ("cuota imss", 2),
            ("imss obrero", 2),
            ("infonavit", 2),
            ("isr", 1),
            ("periodo de pago", 2),
            ("sueldo", 1),
        ],
    },
    "carta_patronal": {
        "emoji": "🏢",
        "label": "Carta Patronal / Constancia Laboral",
        "carpeta": "Empleo",
        "patrones": [
            ("carta patronal", 3),
            ("constancia de trabajo", 3),
            ("constancia laboral", 3),
            ("registro patronal", 3),
            ("numero de registro patronal", 3),
            ("relacion laboral", 2),
            ("empresa", 1),
            ("puesto", 1),
            ("antiguedad", 2),
        ],
    },
    "contrato_trabajo": {
        "emoji": "📃",
        "label": "Contrato de Trabajo",
        "carpeta": "Empleo",
        "patrones": [
            ("contrato individual de trabajo", 3),
            ("contrato colectivo", 3),
            ("patron", 2),
            ("trabajador", 1),
            ("prestaciones de ley", 2),
            ("ley federal del trabajo", 3),
            ("jornada de trabajo", 2),
            ("clausula", 1),
        ],
    },
    "estado_cuenta_afore": {
        "emoji": "💼",
        "label": "Estado de Cuenta AFORE",
        "carpeta": "AFORE",
        "patrones": [
            ("afore", 3),
            ("estado de cuenta", 2),
            ("subcuenta de retiro", 3),
            ("subcuenta de vivienda", 2),
            ("fondo de ahorro", 2),
            ("saldo total", 2),
            ("aportaciones voluntarias", 2),
            ("consar", 2),
            ("rendimientos", 2),
        ],
    },
    "recibo_afore": {
        "emoji": "🧾",
        "label": "Recibo / Comprobante AFORE",
        "carpeta": "AFORE",
        "patrones": [
            ("afore", 2),
            ("recibo", 1),
            ("deposito", 1),
            ("aportacion", 2),
            ("retiro", 2),
            ("folio de operacion", 2),
        ],
    },
    "comprobante_domicilio": {
        "emoji": "🏠",
        "label": "Comprobante de Domicilio",
        "carpeta": "Domicilio",
        "patrones": [
            ("comprobante de domicilio", 3),
            ("cfe", 2),
            ("telmex", 2),
            ("izzi", 2),
            ("totalplay", 2),
            ("megacable", 2),
            ("agua y drenaje", 2),
            ("sistema de aguas", 2),
            ("servicio de", 1),
            ("domicilio de suministro", 2),
            ("cuenta de contrato", 2),
        ],
    },
    "estado_cuenta_banco": {
        "emoji": "🏦",
        "label": "Estado de Cuenta Bancario",
        "carpeta": "Banco",
        "patrones": [
            ("estado de cuenta", 2),
            ("banco", 2),
            ("banamex", 2),
            ("bancomer", 2),
            ("bbva", 2),
            ("santander", 2),
            ("hsbc", 2),
            ("banorte", 2),
            ("saldo", 2),
            ("movimientos", 1),
            ("clabe interbancaria", 3),
            ("clabe", 2),
        ],
    },
    "fe_vida": {
        "emoji": "✅",
        "label": "Fe de Vida / Supervivencia",
        "carpeta": "IMSS_Tramites",
        "patrones": [
            ("fe de vida", 3),
            ("supervivencia", 3),
            ("constancia de vida", 3),
            ("pensionado", 2),
            ("beneficiario", 1),
            ("vivo", 1),
        ],
    },
    "poder_notarial": {
        "emoji": "⚖️",
        "label": "Poder Notarial",
        "carpeta": "Legal",
        "patrones": [
            ("poder notarial", 3),
            ("notario publico", 3),
            ("protocolo notarial", 3),
            ("apoderado", 2),
            ("poderdante", 2),
            ("facultades", 1),
            ("notaria", 2),
        ],
    },
    "acta_matrimonio": {
        "emoji": "💍",
        "label": "Acta de Matrimonio",
        "carpeta": "Identidad",
        "patrones": [
            ("acta de matrimonio", 3),
            ("matrimonio", 2),
            ("contrayentes", 3),
            ("desposaron", 2),
            ("conyuge", 2),
            ("registro civil", 1),
        ],
    },
    "acta_defuncion": {
        "emoji": "🖤",
        "label": "Acta de Defunción",
        "carpeta": "Identidad",
        "patrones": [
            ("acta de defuncion", 3),
            ("defuncion", 3),
            ("fallecio", 2),
            ("fallecimiento", 2),
            ("causa de muerte", 3),
            ("registro civil", 1),
        ],
    },
    "carta_no_pension": {
        "emoji": "📋",
        "label": "Carta de No Pensión",
        "carpeta": "IMSS_Tramites",
        "patrones": [
            ("carta de no pension", 3),
            ("no es pensionado", 3),
            ("no cuenta con pension", 3),
            ("no goza de pension", 3),
            ("no percibe pension", 3),
            ("constancia de no pension", 3),
        ],
    },
    "formato_imss": {
        "emoji": "📑",
        "label": "Formato IMSS",
        "carpeta": "IMSS_Tramites",
        "patrones": [
            ("instituto mexicano del seguro social", 2),
            ("imss", 1),
            ("clave del formato", 2),
            ("folio", 1),
            ("firma del asegurado", 2),
            ("subdelegacion", 2),
            ("delegacion", 1),
        ],
    },
}


# ── Clasificador principal ────────────────────────────────────────────────────
def clasificar_texto(texto: str) -> dict:
    """
    Clasifica un texto y extrae campos estructurados.

    Returns:
        {
          tipo, label, emoji, carpeta, confianza (0-1),
          campos: {curp, nss, rfc, nombre, fecha, ...},
          resumen
        }
    """
    if not texto or not texto.strip():
        return _resultado_vacio("sin_texto")

    texto_norm = _norm(texto)

    # ── Scoring ──────────────────────────────────────────────────────────────
    scores: dict[str, int] = {}
    for tipo, meta in TIPOS.items():
        score = sum(peso for pat, peso in meta["patrones"] if pat in texto_norm)
        if score > 0:
            scores[tipo] = score

    if not scores:
        return _resultado_vacio("documento_general")

    tipo_ganador = max(scores, key=scores.get)
    score_max = scores[tipo_ganador]

    # Confianza: puntaje / suma máxima teórica del tipo (todos los patrones)
    suma_teorica = sum(p for _, p in TIPOS[tipo_ganador]["patrones"])
    confianza = min(score_max / max(suma_teorica, 1), 1.0)

    # Segundo candidato (para mostrar alternativa)
    alternativas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    segundo = alternativas[1][0] if len(alternativas) > 1 else None

    meta = TIPOS[tipo_ganador]
    campos = _extraer_campos(texto, tipo_ganador)
    resumen = _generar_resumen(tipo_ganador, campos, meta["label"])

    return {
        "tipo": tipo_ganador,
        "label": meta["label"],
        "emoji": meta["emoji"],
        "carpeta": meta["carpeta"],
        "confianza": round(confianza, 2),
        "score": score_max,
        "segundo": segundo,
        "campos": campos,
        "resumen": resumen,
    }


def _resultado_vacio(tipo: str) -> dict:
    return {
        "tipo": tipo,
        "label": "Documento general",
        "emoji": "📄",
        "carpeta": "Documentos",
        "confianza": 0.0,
        "score": 0,
        "segundo": None,
        "campos": {},
        "resumen": "No se pudo determinar el tipo de documento.",
    }


# ── Extracción de campos ──────────────────────────────────────────────────────
def _extraer_campos(texto: str, tipo: str) -> dict:
    campos: dict = {}
    texto_up = texto.upper()

    # ── Campos universales ────────────────────────────────────────────────
    # CURP
    m = re.search(
        r"\b[A-Z][AEIOU][A-Z]{2}\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"
        r"[HM](?:AS|B[CS]|C[CLMSH]|D[FG]|G[TR]|HG|JC|M[CNS]|N[ETL]|OC|PL|Q[TR]"
        r"|S[PLR]|T[CSL]|VZ|YN|ZS|NE)[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9]\d\b",
        texto_up,
    )
    if m:
        campos["curp"] = m.group(0)

    # NSS (11 dígitos, evitar números de teléfono/cuenta)
    # El NSS IMSS comienza con 2 dígitos de subdelegación (01-99) + año (00-99)
    nss_matches = re.findall(r"\b(\d{11})\b", texto)
    for nss in nss_matches:
        # Heurística: NSS válido si no empieza con 0 y no es secuencial
        if nss[0] != "0" and len(set(nss)) > 3:
            campos["nss"] = nss
            break

    # RFC
    m = re.search(r"\b[A-ZÁÉÍÓÚÑ&]{3,4}\d{6}[A-Z0-9]{3}\b", texto_up)
    if m:
        campos["rfc"] = m.group(0)

    # Fechas (DD/MM/YYYY o DD-MM-YYYY)
    fechas = re.findall(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b", texto)
    if fechas:
        campos["fecha"] = fechas[0]
        if len(fechas) > 1:
            campos["fechas_adicionales"] = fechas[1:4]

    # ── Campos específicos por tipo ───────────────────────────────────────
    if tipo in ("recibo_nomina",):
        campos.update(_campos_nomina(texto))
    elif tipo == "constancia_semanas":
        campos.update(_campos_semanas(texto))
    elif tipo == "resolucion_pension":
        campos.update(_campos_pension(texto))
    elif tipo == "estado_cuenta_afore":
        campos.update(_campos_afore(texto))
    elif tipo == "comprobante_domicilio":
        campos.update(_campos_domicilio(texto))
    elif tipo == "estado_cuenta_banco":
        campos.update(_campos_banco(texto))
    elif tipo == "carta_patronal":
        campos.update(_campos_patronal(texto))

    # Nombre (heurística: línea con NOMBRE: o NOMBRE COMPLETO:)
    if "nombre" not in campos:
        m = re.search(
            r"(?:NOMBRE(?:\s+COMPLETO)?|APELLIDOS?\s+Y\s+NOMBRE)[:\s]+([A-ZÁÉÍÓÚÑ ]{8,50})",
            texto_up,
            re.IGNORECASE,
        )
        if m:
            campos["nombre"] = m.group(1).strip().title()

    return campos


def _campos_nomina(texto: str) -> dict:
    c: dict = {}
    t = texto.upper()

    # Periodo
    m = re.search(
        r"PERIODO\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}\s*(?:AL|A|-)\s*\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        t,
    )
    if m:
        c["periodo"] = m.group(1).strip()

    # Salario neto
    m = re.search(
        r"(?:NETO\s+A\s+PAGAR|SALARIO\s+NETO|TOTAL\s+NETO)[:\s]+\$?\s*([\d,]+\.?\d*)", t
    )
    if m:
        c["salario_neto"] = m.group(1).replace(",", "")

    # Salario diario / base
    m = re.search(r"(?:SALARIO\s+DIARIO|SBC|S\.D\.I)[:\s]+\$?\s*([\d,]+\.?\d*)", t)
    if m:
        c["salario_diario"] = m.group(1)

    # Empleador
    m = re.search(
        r"(?:EMPRESA|RAZON\s+SOCIAL|PATRON)[:\s]+([A-ZÁÉÍÓÚÑ ,\.S\.A\.DE]{5,60})", t
    )
    if m:
        c["empresa"] = m.group(1).strip().title()

    return c


def _campos_semanas(texto: str) -> dict:
    c: dict = {}
    t = texto.upper()

    # Total de semanas
    m = re.search(
        r"(?:TOTAL\s+DE\s+SEMANAS|SEMANAS\s+COTIZADAS|SEMANAS\s+RECONOCIDAS)[:\s]+(\d+)",
        t,
    )
    if m:
        c["semanas_cotizadas"] = m.group(1)

    # Periodo
    m = re.search(r"(?:PERIODO|DESDE|DEL)[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})", t)
    if m:
        c["periodo_inicio"] = m.group(1)
    m = re.search(r"(?:HASTA|AL)[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})", t)
    if m:
        c["periodo_fin"] = m.group(1)

    # Salario base de cotización
    m = re.search(
        r"(?:SALARIO\s+BASE\s+DE\s+COTIZACION|SBC)[:\s]+\$?\s*([\d,]+\.?\d*)", t
    )
    if m:
        c["sbc"] = m.group(1)

    return c


def _campos_pension(texto: str) -> dict:
    c: dict = {}
    t = texto.upper()

    # Tipo de pensión
    for tp in ["VEJEZ", "INVALIDEZ", "VIUDEZ", "ORFANDAD", "CESANTIA EN EDAD AVANZADA"]:
        if tp in t:
            c["tipo_pension"] = tp.title()
            break

    # Monto
    m = re.search(
        r"(?:IMPORTE|MONTO|CUANTIA)\s+(?:DE\s+)?(?:PENSION|MENSUAL)[:\s]+\$?\s*([\d,]+\.?\d*)",
        t,
    )
    if m:
        c["monto_pension"] = m.group(1)

    # Folio
    m = re.search(r"(?:FOLIO|NUMERO\s+DE\s+RESOLUCION)[:\s]+([A-Z0-9/-]{5,20})", t)
    if m:
        c["folio"] = m.group(1)

    return c


def _campos_afore(texto: str) -> dict:
    c: dict = {}
    t = texto.upper()

    # Nombre de AFORE
    for afore in [
        "SURA",
        "PRINCIPAL",
        "BANAMEX",
        "COPPEL",
        "AZTECA",
        "PROFUTURO",
        "XXI BANORTE",
        "INBURSA",
        "INVERCAP",
        "PensionISSSTE",
    ]:
        if afore.upper() in t:
            c["afore"] = afore
            break

    # Saldo
    m = re.search(r"(?:SALDO\s+TOTAL|SALDO\s+ACUMULADO)[:\s]+\$?\s*([\d,]+\.?\d*)", t)
    if m:
        c["saldo_total"] = m.group(1)

    return c


def _campos_domicilio(texto: str) -> dict:
    c: dict = {}
    t = texto.upper()

    # Servicio
    for sv in ["CFE", "TELMEX", "IZZI", "TOTALPLAY", "MEGACABLE", "AGUAS", "GAS"]:
        if sv in t:
            c["servicio"] = sv
            break

    # Período
    m = re.search(r"(?:PERIODO|BIMESTRE|MES)[:\s]+([A-ZÁÉÍÓÚ]+\s+\d{4}|\d{2}/\d{4})", t)
    if m:
        c["periodo"] = m.group(1)

    return c


def _campos_banco(texto: str) -> dict:
    c: dict = {}
    t = texto.upper()

    # Banco
    for banco in [
        "BBVA",
        "BANCOMER",
        "BANAMEX",
        "CITIBANAMEX",
        "SANTANDER",
        "HSBC",
        "BANORTE",
        "SCOTIABANK",
        "INBURSA",
        "BAJIO",
    ]:
        if banco in t:
            c["banco"] = banco
            break

    # CLABE
    m = re.search(r"(?:CLABE|CLABE INTERBANCARIA)[:\s]+(\d{18})", t)
    if m:
        c["clabe"] = m.group(1)

    # Saldo
    m = re.search(
        r"(?:SALDO\s+FINAL|SALDO\s+ACTUAL|SALDO\s+DISPONIBLE)[:\s]+\$?\s*([\d,]+\.?\d*)",
        t,
    )
    if m:
        c["saldo"] = m.group(1)

    return c


def _campos_patronal(texto: str) -> dict:
    c: dict = {}
    t = texto.upper()

    # Registro patronal
    m = re.search(r"(?:REGISTRO\s+PATRONAL|R\.?P\.?)[:\s]+([A-Z0-9-]{5,20})", t)
    if m:
        c["registro_patronal"] = m.group(1)

    # Puesto
    m = re.search(r"(?:PUESTO|CARGO)[:\s]+([A-ZÁÉÍÓÚÑ ]{4,50})", t)
    if m:
        c["puesto"] = m.group(1).strip().title()

    # Antigüedad / fecha ingreso
    m = re.search(
        r"(?:FECHA\s+DE\s+INGRESO|INGRESO)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})", t
    )
    if m:
        c["fecha_ingreso"] = m.group(1)

    return c


# ── Resumen ───────────────────────────────────────────────────────────────────
def _generar_resumen(tipo: str, campos: dict, label: str) -> str:
    partes = [f"Tipo: {label}"]
    if campos.get("nombre"):
        partes.append(f"Nombre: {campos['nombre']}")
    if campos.get("curp"):
        partes.append(f"CURP: {campos['curp']}")
    if campos.get("nss"):
        partes.append(f"NSS: {campos['nss']}")
    if campos.get("semanas_cotizadas"):
        partes.append(f"Semanas: {campos['semanas_cotizadas']}")
    if campos.get("salario_neto"):
        partes.append(f"Neto: ${campos['salario_neto']}")
    if campos.get("tipo_pension"):
        partes.append(f"Pensión: {campos['tipo_pension']}")
    if campos.get("monto_pension"):
        partes.append(f"Monto: ${campos['monto_pension']}")
    if campos.get("fecha"):
        partes.append(f"Fecha: {campos['fecha']}")
    return " · ".join(partes)


# ── Clasificar desde archivo ──────────────────────────────────────────────────
def clasificar_archivo(path: Path, texto_previo: Optional[str] = None) -> dict:
    """
    Clasifica un archivo. Acepta texto ya extraído (texto_previo) o lo extrae.
    Agrega nombre del archivo y extensión al resultado.
    """
    path = Path(path)
    resultado = {"archivo": path.name, "extension": path.suffix.lower()}

    texto = texto_previo or ""
    if not texto and path.exists():
        texto = _extraer_texto(path)

    if not texto.strip():
        resultado.update(_resultado_vacio("sin_texto"))
        resultado["advertencia"] = "No se pudo extraer texto del archivo"
        return resultado

    resultado.update(clasificar_texto(texto))
    resultado["chars_extraidos"] = len(texto)
    return resultado


def _extraer_texto(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            try:
                import pdfplumber

                with pdfplumber.open(str(path)) as pdf:
                    return "\n".join(p.extract_text() or "" for p in pdf.pages[:20])
            except Exception as e:
                pass
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(path))
                return "\n".join(p.extract_text() or "" for p in reader.pages[:20])
            except Exception as e:
                return ""
        elif ext in (".txt", ".md", ".csv"):
            return path.read_text("utf-8", errors="replace")[:50000]
        elif ext in (".docx", ".doc"):
            try:
                from docx import Document

                doc = Document(str(path))
                return "\n".join(p.text for p in doc.paragraphs)
            except Exception as e:
                return ""
        elif ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"):
            try:
                import pytesseract
                from PIL import Image

                img = Image.open(str(path))
                return pytesseract.image_to_string(
                    img, lang="spa+eng", config="--psm 3"
                )
            except Exception as e:
                return ""
    except Exception as e:
        pass
    return ""


# ── Acceso al catálogo de tipos ───────────────────────────────────────────────
def listar_tipos() -> list:
    return [
        {"tipo": k, "label": v["label"], "emoji": v["emoji"], "carpeta": v["carpeta"]}
        for k, v in TIPOS.items()
    ]
