#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════
#  🦁 MAER 4.0 — CONSOLA IA AVANZADA  (v2)
#  IA interna con voz · OCR profesional · Análisis de carpetas completas
#  Aprende de cada archivo · Vigilancia en tiempo real · Reportes HTML/PDF
#  Autocompletado · Extracción de tablas · Acceso total al sistema
#  Leonel Houssen Mojica — Ecatepec MX — 2026
# ══════════════════════════════════════════════════════════════════════
"""
COMANDOS DISPONIBLES:
  chat  <mensaje>         — Hablar con MAER IA
  voz                     — Activar reconocimiento de voz continuo
  analizar <ruta>         — OCR + análisis profundo de un archivo
  carpeta  <ruta>         — Analizar TODOS los archivos (subcarpetas incluidas)
  aprender <ruta>         — Aprendizaje profundo: indexa y memoriza todo
  vigilar  <ruta>         — Vigilar carpeta en tiempo real (aprende automáticamente)
  buscar   <término>      — Buscar en todo el conocimiento aprendido
  reporte  [html|pdf]     — Generar informe completo (HTML abre en browser)
  tablas   <ruta.pdf>     — Extraer tablas de un PDF/imagen IMSS
  deps                    — Verificar dependencias del sistema
  estado                  — Estado del servidor MAER + conocimiento
  historial               — Ver últimas 20 conversaciones
  limpiar                 — Limpiar pantalla
  ayuda                   — Mostrar esta ayuda
  salir                   — Salir de la consola

ATAJOS: escribe cualquier pregunta directamente y MAER responde.
  Tab = autocompletar comando/ruta   ↑↓ = historial de comandos
"""

import os, sys, re, json, time, threading, subprocess, hashlib, shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# ── Autocompletado con readline ────────────────────────────────────────
try:
    import readline
    _READLINE_OK = True
except ImportError:
    _READLINE_OK = False  # Windows sin pyreadline

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.resolve()
CONOCIMIENTO_DB = BASE_DIR / ".maer_conocimiento.json"
HISTORIAL_FILE  = BASE_DIR / ".maer_historial_consola.json"
PORT        = int(os.environ.get("MAER_WEB_PORT", "8765"))
API_BASE    = f"http://localhost:{PORT}"

# ── Comandos para autocompletado ─────────────────────────────────────
_TODOS_CMDS = [
    "chat ", "voz", "analizar ", "carpeta ", "aprender ", "vigilar ",
    "buscar ", "reporte", "reporte html", "reporte pdf",
    "tablas ", "deps", "estado", "historial", "limpiar", "ayuda", "salir",
]

def _setup_readline():
    """Configura readline con autocompletado de comandos y rutas."""
    if not _READLINE_OK:
        return
    try:
        import glob as _glob

        def _completer(text, state):
            """Completa comandos MAER y rutas del sistema de archivos."""
            # Si hay espacio ya (args), completar rutas
            line = readline.get_line_buffer()
            if " " in line:
                # Completar ruta
                rutas = _glob.glob(os.path.expanduser(text) + "*")
                opciones = [r + ("/" if os.path.isdir(r) else "") for r in rutas]
            else:
                # Completar comando
                opciones = [c for c in _TODOS_CMDS if c.startswith(text)]
            return opciones[state] if state < len(opciones) else None

        readline.set_completer(_completer)
        readline.set_completer_delims(" \t\n;")
        readline.parse_and_bind("tab: complete")
        # Historial persistente
        hist = Path.home() / ".maer_consola_hist"
        try:
            readline.read_history_file(str(hist))
        except FileNotFoundError:
            pass
        import atexit
        atexit.register(readline.write_history_file, str(hist))
        readline.set_history_length(500)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════
# ── COLORES ANSI (sin dependencia de rich) ────────────────────────────
# ══════════════════════════════════════════════════════════════════════
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    VERDE  = "\033[92m"
    AZUL   = "\033[94m"
    CYAN   = "\033[96m"
    ROJO   = "\033[91m"
    DORADO = "\033[93m"
    MAGENTA= "\033[95m"
    BLANCO = "\033[97m"
    GRIS   = "\033[90m"
    BG_VERDE= "\033[42m"
    BG_AZUL = "\033[44m"

def p(text, color=C.RESET, end="\n"):
    print(f"{color}{text}{C.RESET}", end=end, flush=True)

def barra(val, total, ancho=30, color=C.VERDE):
    lleno = int((val / max(total, 1)) * ancho)
    vacio = ancho - lleno
    return f"{color}{'█' * lleno}{C.GRIS}{'░' * vacio}{C.RESET} {val}/{total}"


# ══════════════════════════════════════════════════════════════════════
# ── BASE DE CONOCIMIENTO ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
class Conocimiento:
    """Base de datos de conocimiento persistente. Aprende de cada archivo analizado."""

    def __init__(self, db_path: Path):
        self.path = db_path
        self.datos: Dict[str, Any] = self._cargar()

    def _cargar(self) -> Dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "archivos":    {},   # hash → {ruta, texto, entidades, ts}
            "curps":       [],
            "rfcs":        [],
            "nss":         [],
            "semanas":     [],
            "nombres":     [],
            "estadisticas":{
                "archivos_analizados": 0,
                "bytes_procesados":    0,
                "ultima_sesion":       "",
            },
            "notas":       [],
        }

    def guardar(self):
        self.datos["estadisticas"]["ultima_sesion"] = datetime.now().isoformat()
        self.path.write_text(
            json.dumps(self.datos, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def registrar_archivo(self, ruta: str, texto: str, entidades: dict):
        h = hashlib.md5(ruta.encode()).hexdigest()
        ya_existe = h in self.datos["archivos"]
        self.datos["archivos"][h] = {
            "ruta":       ruta,
            "nombre":     Path(ruta).name,
            "texto":      texto[:8000],   # primeros 8K
            "entidades":  entidades,
            "ts":         datetime.now().isoformat(),
            "bytes":      len(texto),
        }
        # Agregar entidades al índice global
        for curp in entidades.get("curps", []):
            if curp not in self.datos["curps"]:
                self.datos["curps"].append(curp)
        for rfc in entidades.get("rfcs", []):
            if rfc not in self.datos["rfcs"]:
                self.datos["rfcs"].append(rfc)
        for nss in entidades.get("nss_encontrados", []):
            if nss not in self.datos["nss"]:
                self.datos["nss"].append(nss)
        for sem in entidades.get("semanas_mencionadas", []):
            if sem not in self.datos["semanas"]:
                self.datos["semanas"].append(sem)

        stats = self.datos["estadisticas"]
        if not ya_existe:
            stats["archivos_analizados"] += 1
        stats["bytes_procesados"] += len(texto)
        self.guardar()

    def buscar(self, termino: str) -> List[Dict]:
        """Busca un término en todos los archivos aprendidos."""
        termino_lower = termino.lower()
        resultados = []
        for h, arch in self.datos["archivos"].items():
            texto = arch.get("texto", "").lower()
            if termino_lower in texto or termino_lower in arch.get("ruta", "").lower():
                # Encontrar contexto alrededor del término
                idx = texto.find(termino_lower)
                contexto = arch["texto"][max(0, idx-80):idx+200] if idx >= 0 else ""
                resultados.append({
                    "nombre":   arch["nombre"],
                    "ruta":     arch["ruta"],
                    "contexto": contexto.replace("\n", " "),
                    "ts":       arch["ts"],
                })
        return resultados

    def resumen(self) -> str:
        s = self.datos["estadisticas"]
        return (
            f"📚 {s['archivos_analizados']} archivos · "
            f"{s['bytes_procesados']//1024} KB procesados · "
            f"{len(self.datos['curps'])} CURPs · "
            f"{len(self.datos['rfcs'])} RFCs · "
            f"{len(self.datos['nss'])} NSS"
        )


# ══════════════════════════════════════════════════════════════════════
# ── CLIENTE API MAER ──────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
class MaerAPI:
    def __init__(self, base: str):
        self.base    = base
        self._online = False

    def ping(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.base}/", timeout=3)
            self._online = True
            return True
        except Exception:
            self._online = False
            return False

    def chat(self, prompt: str, contexto: str = "") -> Dict:
        return self._post("/api/llm-chat", {"prompt": prompt, "texto": contexto})

    def analizar(self, ruta: str) -> Dict:
        return self._post("/api/analizar-documento", {"path": ruta})

    def extraer_texto(self, ruta: str) -> Dict:
        return self._post("/api/extract-text", {"path": ruta, "ocr_for_pdf": True})

    def exportar_pdf(self, payload: dict) -> Dict:
        return self._post("/api/exportar-pdf", payload)

    def verificar_deps(self) -> Dict:
        try:
            import urllib.request
            with urllib.request.urlopen(f"{self.base}/api/verificar-dependencias", timeout=10) as r:
                return json.loads(r.read())
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _post(self, ep: str, data: dict) -> Dict:
        try:
            import urllib.request, urllib.error
            body = json.dumps(data).encode()
            req  = urllib.request.Request(
                f"{self.base}{ep}", data=body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            return {"ok": False, "message": str(e), "data": {}}


# ══════════════════════════════════════════════════════════════════════
# ── OCR LOCAL (independiente del servidor) ────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def ocr_local(ruta: Path) -> str:
    """OCR avanzado directamente en la consola, sin depender del servidor."""
    ext = ruta.suffix.lower()
    texto = ""

    # ── Texto plano ──
    if ext in {".txt", ".csv", ".md", ".json", ".xml", ".html", ".py", ".js", ".log"}:
        try:
            return ruta.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"[ERROR leyendo {ruta.name}: {e}]"

    # ── PDF ──
    if ext == ".pdf":
        # Intentar extracción directa primero
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(ruta))
            texto = " ".join(p.extract_text() or "" for p in reader.pages[:40])
            if len(texto.strip()) > 100:
                return texto
        except Exception:
            pass

        # OCR con PyMuPDF + deskew
        try:
            import fitz, pytesseract, numpy as np, cv2, io
            from PIL import Image
            doc = fitz.open(str(ruta))
            paginas = []
            for i, pg in enumerate(doc):
                if i >= 30:
                    break
                mat = fitz.Matrix(300/72, 300/72)
                pix = pg.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                img_proc = _preprocesar(img)
                txt = pytesseract.image_to_string(img_proc, config="--oem 3 --psm 6 -l spa+eng")
                if txt.strip():
                    paginas.append(f"[Pág {i+1}]\n{txt}")
            doc.close()
            return "\n".join(paginas)
        except ImportError:
            pass
        try:
            from pdf2image import convert_from_path
            import pytesseract
            imgs = convert_from_path(str(ruta), dpi=300, last_page=20)
            return "\n".join(pytesseract.image_to_string(_preprocesar(img),
                             config="--oem 3 --psm 6 -l spa+eng")
                             for img in imgs)
        except Exception as e:
            return f"[ERROR OCR PDF: {e}]"

    # ── Imágenes ──
    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}:
        try:
            import pytesseract
            from PIL import Image
            img  = Image.open(str(ruta))
            proc = _preprocesar(img)
            return pytesseract.image_to_string(proc, config="--oem 3 --psm 6 -l spa+eng")
        except Exception as e:
            return f"[ERROR OCR imagen: {e}]"

    # ── DOCX ──
    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(str(ruta))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"[ERROR leyendo DOCX: {e}]"

    # ── XLSX ──
    if ext in {".xlsx", ".xls"}:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(ruta), data_only=True)
            filas = []
            for ws in wb.worksheets:
                filas.append(f"[Hoja: {ws.title}]")
                for row in ws.iter_rows(values_only=True, max_row=500):
                    r = " | ".join(str(c) for c in row if c is not None)
                    if r.strip():
                        filas.append(r)
            return "\n".join(filas)
        except Exception as e:
            return f"[ERROR leyendo Excel: {e}]"

    return f"[Tipo {ext} no soportado para OCR local]"


def _preprocesar(img):
    """Preprocesado avanzado: deskew + denoising + threshold adaptativo."""
    try:
        import numpy as np, cv2
        from PIL import Image
        img_np = np.array(img.convert("L"))
        try:
            from deskew import determine_skew
            angle = determine_skew(img_np)
            if angle is not None and abs(angle) > 0.3:
                h, w = img_np.shape
                M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
                img_np = cv2.warpAffine(img_np, M, (w, h),
                                        flags=cv2.INTER_CUBIC,
                                        borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            pass
        img_np = cv2.fastNlMeansDenoising(img_np, h=10)
        img_np = cv2.adaptiveThreshold(img_np, 255,
                                        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY, 31, 11)
        h, w = img_np.shape
        if w < 1800:
            scale = 1800 / w
            img_np = cv2.resize(img_np, (int(w*scale), int(h*scale)),
                                interpolation=cv2.INTER_LANCZOS4)
        from PIL import Image as PILImage
        return PILImage.fromarray(img_np)
    except Exception:
        return img


# ══════════════════════════════════════════════════════════════════════
# ── EXTRACTOR DE ENTIDADES ────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def extraer_entidades(texto: str) -> Dict:
    """Extrae CURP, RFC, NSS, semanas, fechas del texto."""
    CURP_RE  = re.compile(r'\b[A-Z]{4}\d{6}[HM][A-Z]{2}[A-Z0-9]{3}[A-Z0-9]\d\b')
    RFC_RE   = re.compile(r'\b[A-ZÑ&]{3,4}\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])[A-Z0-9]{3}\b', re.I)
    NSS_RE   = re.compile(r'\b\d{11}\b')
    SEM_RE   = re.compile(r'(\d{3,4})\s*semanas?\s*cotizadas?', re.I)
    FECHA_RE = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
    MONTO_RE = re.compile(r'\$[\d,]+\.?\d*')

    curps   = list({m.group() for m in CURP_RE.finditer(texto)})
    rfcs    = list({m.group().upper() for m in RFC_RE.finditer(texto)
                    if len(m.group()) >= 12})
    nss_all = [m.group() for m in NSS_RE.finditer(texto)]
    # Filtrar NSS válidos (empiezan con 01-99)
    nss_v   = list({n for n in nss_all if 10 <= int(n[:2]) <= 99 or 1 <= int(n[:2]) <= 9})
    semanas = [int(m.group(1)) for m in SEM_RE.finditer(texto) if 50 <= int(m.group(1)) <= 5000]
    fechas  = list({m.group() for m in FECHA_RE.finditer(texto)})[:10]
    montos  = list({m.group() for m in MONTO_RE.finditer(texto)})[:10]

    return {
        "curps":              curps,
        "rfcs":               rfcs,
        "nss_encontrados":    nss_v[:5],
        "semanas_mencionadas":semanas,
        "fechas":             fechas,
        "montos":             montos,
    }


# ══════════════════════════════════════════════════════════════════════
# ── EXTRACTOR DE TABLAS ───────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def extraer_tablas(ruta: Path) -> List[Dict]:
    """
    Extrae tablas de PDFs e imágenes. Útil para constancias IMSS,
    hojas de cálculo, nóminas, estados de cuenta AFORE.
    Devuelve lista de dicts: [{titulo, filas: [[col1,col2,...]], texto}]
    """
    tablas = []
    ext    = ruta.suffix.lower()

    # ── pdfplumber (mejor para tablas en PDFs digitales) ──
    if ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(str(ruta)) as pdf:
                for i, pg in enumerate(pdf.pages[:20]):
                    tbs = pg.extract_tables()
                    for j, tb in enumerate(tbs):
                        filas_limpias = []
                        for fila in tb:
                            fila_l = [str(c or "").strip() for c in fila]
                            if any(fila_l):
                                filas_limpias.append(fila_l)
                        if filas_limpias:
                            tablas.append({
                                "titulo":  f"Tabla {j+1} — Pág {i+1}",
                                "filas":   filas_limpias,
                                "pagina":  i + 1,
                                "texto":   "\n".join(" | ".join(f) for f in filas_limpias),
                            })
        except ImportError:
            pass
        except Exception:
            pass

    # ── PyMuPDF como fallback para PDFs ──
    if ext == ".pdf" and not tablas:
        try:
            import fitz
            doc = fitz.open(str(ruta))
            for i, pg in enumerate(doc[:10]):
                # Extraer texto estructurado
                blocks = pg.get_text("dict")["blocks"]
                for blk in blocks:
                    if blk.get("type") == 0:  # texto
                        lines = blk.get("lines", [])
                        filas = []
                        for ln in lines:
                            cols = [sp["text"].strip() for sp in ln.get("spans", [])
                                    if sp["text"].strip()]
                            if cols:
                                filas.append(cols)
                        if len(filas) > 3 and any(len(f) > 2 for f in filas):
                            tablas.append({
                                "titulo": f"Bloque texto Pág {i+1}",
                                "filas":  filas,
                                "pagina": i + 1,
                                "texto":  "\n".join(" | ".join(f) for f in filas),
                            })
            doc.close()
        except Exception:
            pass

    # ── Excel (nativo) ──
    if ext in {".xlsx", ".xls"}:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(ruta), data_only=True)
            for ws in wb.worksheets:
                filas = []
                for row in ws.iter_rows(values_only=True, max_row=200):
                    fila = [str(c) if c is not None else "" for c in row]
                    if any(fila):
                        filas.append(fila)
                if filas:
                    tablas.append({
                        "titulo": f"Hoja: {ws.title}",
                        "filas":  filas,
                        "pagina": 0,
                        "texto":  "\n".join(" | ".join(f) for f in filas),
                    })
        except Exception:
            pass

    # ── CSV ──
    if ext == ".csv":
        try:
            import csv
            with open(str(ruta), newline="", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                filas  = [row for row in reader if any(row)][:200]
            if filas:
                tablas.append({
                    "titulo": f"CSV: {ruta.name}",
                    "filas":  filas,
                    "pagina": 0,
                    "texto":  "\n".join(" | ".join(f) for f in filas),
                })
        except Exception:
            pass

    return tablas


def _formatear_tabla_consola(tabla: Dict, max_col: int = 20) -> str:
    """Formatea una tabla para mostrarla bonita en la consola."""
    filas  = tabla["filas"]
    if not filas:
        return ""
    # Calcular anchos de columnas
    num_cols = max(len(f) for f in filas)
    anchos   = [0] * num_cols
    for fila in filas:
        for ci, cel in enumerate(fila[:num_cols]):
            anchos[ci] = min(max_col, max(anchos[ci], len(str(cel))))

    sep   = "┼".join("─" * (a + 2) for a in anchos)
    lineas = [f"  ┌{sep}┐"]

    for ri, fila in enumerate(filas[:50]):
        celdas = []
        for ci in range(num_cols):
            val = str(fila[ci]) if ci < len(fila) else ""
            val = val[:max_col]
            celdas.append(f" {val:<{anchos[ci]}} ")
        lineas.append(f"  │{'│'.join(celdas)}│")
        if ri == 0:
            lineas.append(f"  ╞{sep.replace('─','═').replace('┼','╪')}╡")

    lineas.append(f"  └{sep}┘")
    return "\n".join(lineas)


# ══════════════════════════════════════════════════════════════════════
# ── GENERADOR DE REPORTE HTML ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
def generar_reporte_html(db: "Conocimiento", ruta_salida: Path) -> Path:
    """Genera un reporte HTML visual con charts, tablas y resumen completo."""
    archivos = list(db.datos["archivos"].values())
    curps    = list(set(db.datos["curps"]))
    rfcs     = list(set(db.datos["rfcs"]))
    nss      = list(set(db.datos["nss"]))
    semanas  = sorted(set(db.datos["semanas"]))
    stats    = db.datos["estadisticas"]
    ts_gen   = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── Filas de archivos para tabla ──
    filas_arch = ""
    for a in sorted(archivos, key=lambda x: x.get("ts",""), reverse=True)[:100]:
        curps_a = ", ".join(a.get("entidades",{}).get("curps",[])[:2]) or "—"
        sem_a   = ", ".join(str(s) for s in a.get("entidades",{}).get("semanas_mencionadas",[])[:2]) or "—"
        kb      = a.get("bytes", 0) // 1024
        ts_a    = a.get("ts","")[:16].replace("T"," ")
        filas_arch += f"""
        <tr>
          <td title="{a.get('ruta','')}">📄 {a.get('nombre','?')[:45]}</td>
          <td>{kb} KB</td>
          <td style="color:#f59e0b">{curps_a}</td>
          <td style="color:#34d399">{sem_a}</td>
          <td style="color:#94a3b8">{ts_a}</td>
        </tr>"""

    # ── CURPs badges ──
    curp_badges = " ".join(
        f'<span style="background:#1e3a5f;color:#60a5fa;padding:4px 10px;border-radius:20px;font-size:12px;font-family:monospace">{c}</span>'
        for c in curps[:20]) or '<span style="color:#64748b">Ninguna detectada</span>'

    # ── Barra progreso semanas (si hay) ──
    sem_html = ""
    if semanas:
        sem_max = max(semanas)
        for meta, label, color in [(500,"Mín Ley 73","#ef4444"),(1250,"Cesantía","#f59e0b"),(1750,"Plena","#22c55e")]:
            pct = min(100, round(sem_max/meta*100))
            sem_html += f"""
            <div style="margin-bottom:12px">
              <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                <span>{label} ({meta} sem)</span>
                <span style="color:{'#22c55e' if sem_max>=meta else '#ef4444'}">{sem_max}/{meta} — {pct}%</span>
              </div>
              <div style="background:#1e293b;border-radius:6px;height:14px;overflow:hidden">
                <div style="background:{color};width:{pct}%;height:100%;border-radius:6px;transition:.5s"></div>
              </div>
            </div>"""

    # ── HTML completo ──
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🦁 MAER — Informe de Conocimiento</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0 }}
  body {{ background:#0f1117; color:#e2e8f0; font-family:'Segoe UI',system-ui,sans-serif; padding:24px }}
  h1   {{ color:#00a65a; font-size:26px; margin-bottom:4px }}
  h2   {{ color:#34d399; font-size:17px; margin:24px 0 10px; border-bottom:1px solid #1e293b; padding-bottom:6px }}
  h3   {{ color:#60a5fa; font-size:14px; margin-bottom:8px }}
  .badge {{ display:inline-block; background:#0d2137; border:1px solid #1e3a5f;
            border-radius:8px; padding:14px 22px; margin:6px; text-align:center; min-width:140px }}
  .badge .num {{ font-size:32px; font-weight:900; color:#00a65a }}
  .badge .lbl {{ font-size:11px; color:#64748b; margin-top:2px }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px }}
  th    {{ background:#1e293b; padding:8px 12px; text-align:left; color:#94a3b8; font-weight:600 }}
  td    {{ padding:7px 12px; border-bottom:1px solid #1e293b }}
  tr:hover td {{ background:#1a1d27 }}
  .card {{ background:#161b27; border:1px solid #1e293b; border-radius:12px; padding:20px; margin-bottom:18px }}
  .tag  {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:11px; margin:2px }}
  .green {{ color:#00a65a }} .yellow {{ color:#f59e0b }} .red {{ color:#ef4444 }}
  .code {{ background:#0d1117; padding:2px 8px; border-radius:4px; font-family:monospace; font-size:12px }}
</style>
</head>
<body>

<div style="display:flex;align-items:center;gap:14px;margin-bottom:20px">
  <span style="font-size:42px">🦁</span>
  <div>
    <h1>MAER 4.0 — Informe de Conocimiento</h1>
    <div style="color:#64748b;font-size:13px">Generado: {ts_gen} · Sistema de Asistencia para Expedientes de Retiro IMSS</div>
  </div>
</div>

<!-- ESTADÍSTICAS PRINCIPALES -->
<div style="display:flex;flex-wrap:wrap;gap:0;margin-bottom:20px">
  <div class="badge"><div class="num">{stats.get('archivos_analizados',0)}</div><div class="lbl">Archivos analizados</div></div>
  <div class="badge"><div class="num">{stats.get('bytes_procesados',0)//1024}</div><div class="lbl">KB procesados</div></div>
  <div class="badge"><div class="num">{len(curps)}</div><div class="lbl">CURPs detectadas</div></div>
  <div class="badge"><div class="num">{len(rfcs)}</div><div class="lbl">RFCs detectados</div></div>
  <div class="badge"><div class="num">{len(nss)}</div><div class="lbl">NSS detectados</div></div>
  <div class="badge"><div class="num">{len(semanas)}</div><div class="lbl">Semanas distintas</div></div>
</div>

<!-- PROGRESO SEMANAS -->
{f'<div class="card"><h2>📊 Progreso de Semanas Cotizadas</h2>{sem_html}</div>' if sem_html else ''}

<!-- CURPs ENCONTRADAS -->
<div class="card">
  <h2>🔑 CURPs Detectadas ({len(curps)})</h2>
  <div style="margin-top:8px">{curp_badges}</div>
</div>

<!-- RFCs -->
{'<div class="card"><h2>🏢 RFCs Detectados (' + str(len(rfcs)) + ')</h2><div>' + " ".join(f"<span class='tag' style='background:#1e2a1e;color:#4ade80;border:1px solid #166534'>{r}</span>" for r in rfcs[:20]) + "</div></div>" if rfcs else ""}

<!-- ARCHIVOS PROCESADOS -->
<div class="card">
  <h2>📚 Archivos Procesados ({len(archivos)})</h2>
  <table>
    <thead><tr>
      <th>Archivo</th><th>Tamaño</th><th>CURP</th><th>Semanas</th><th>Fecha</th>
    </tr></thead>
    <tbody>{filas_arch}</tbody>
  </table>
</div>

<!-- SESIÓN -->
<div class="card" style="border-color:#1e3a2f">
  <h3>ℹ️ Información de sesión</h3>
  <div style="font-size:12px;color:#64748b;margin-top:6px">
    Última sesión: <span class="code">{stats.get('ultima_sesion','—')[:19]}</span> ·
    DB: <span class="code">{CONOCIMIENTO_DB}</span>
  </div>
  <div style="margin-top:10px;font-size:11px;color:#475569">
    Este informe es solo informativo. Para datos oficiales, visita
    <a href="https://serviciosdigitales.imss.gob.mx" style="color:#34d399">serviciosdigitales.imss.gob.mx</a>
  </div>
</div>

<div style="text-align:center;margin-top:30px;font-size:11px;color:#334155">
  🦁 MAER 4.0 · Generado {ts_gen} · Uso interno · No tiene validez oficial ante el IMSS
</div>

</body></html>"""

    ruta_salida.write_text(html, encoding="utf-8")
    return ruta_salida


# ══════════════════════════════════════════════════════════════════════
# ── VOZ ───────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
class Voz:
    """Reconocimiento y síntesis de voz. Múltiples backends."""

    def __init__(self):
        self._sr_ok  = False
        self._tts_ok = False
        self._inicializar()

    def _inicializar(self):
        try:
            import speech_recognition as sr
            self._sr  = sr
            self._rec = sr.Recognizer()
            self._sr_ok = True
        except ImportError:
            pass
        # TTS: macOS say, espeak, o pyttsx3
        if shutil.which("say"):
            self._tts_cmd = ["say", "-v", "Juan"]   # macOS español
            self._tts_ok  = True
        elif shutil.which("espeak"):
            self._tts_cmd = ["espeak", "-v", "es", "-s", "150"]
            self._tts_ok  = True
        else:
            try:
                import pyttsx3
                self._tts_engine = pyttsx3.init()
                self._tts_ok     = True
                self._tts_cmd    = None
            except ImportError:
                pass

    def hablar(self, texto: str):
        """Sintetiza voz."""
        if not self._tts_ok:
            return
        texto_limpio = re.sub(r'[🦁✅❌⚠️📄📂🔍🌐💻🤖]', '', texto)[:300]
        try:
            if hasattr(self, "_tts_cmd") and self._tts_cmd:
                subprocess.Popen(self._tts_cmd + [texto_limpio],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif hasattr(self, "_tts_engine"):
                self._tts_engine.say(texto_limpio)
                self._tts_engine.runAndWait()
        except Exception:
            pass

    def escuchar_una_vez(self, timeout: int = 8) -> Optional[str]:
        """Escucha hasta que el usuario habla."""
        if not self._sr_ok:
            return None
        sr = self._sr
        try:
            with sr.Microphone() as src:
                self._rec.adjust_for_ambient_noise(src, duration=0.5)
                p("🎤 Escuchando...", C.CYAN, end=" ")
                audio = self._rec.listen(src, timeout=timeout, phrase_time_limit=15)
            texto = self._rec.recognize_google(audio, language="es-MX")
            print(f"{C.BLANCO}{texto}{C.RESET}")
            return texto
        except sr.WaitTimeoutError:
            print(f"{C.GRIS}(silencio){C.RESET}")
            return None
        except sr.UnknownValueError:
            print(f"{C.GRIS}(no entendido){C.RESET}")
            return None
        except Exception as e:
            p(f"⚠ Voz: {e}", C.DORADO)
            return None

    @property
    def sr_disponible(self):
        return self._sr_ok

    @property
    def tts_disponible(self):
        return self._tts_ok


# ══════════════════════════════════════════════════════════════════════
# ── CONSOLA PRINCIPAL ─────────────────────────────────────════════════
# ══════════════════════════════════════════════════════════════════════
class MAERConsola:

    def __init__(self):
        self.api        = MaerAPI(API_BASE)
        self.db         = Conocimiento(CONOCIMIENTO_DB)
        self.voz        = Voz()
        self._modo_voz  = False
        self._corriendo = True
        self._historial: List[Dict] = self._cargar_historial()

    # ── HISTORIAL ────────────────────────────────────────────────────
    def _cargar_historial(self) -> List[Dict]:
        if HISTORIAL_FILE.exists():
            try:
                return json.loads(HISTORIAL_FILE.read_text(encoding="utf-8"))[-200:]
            except Exception:
                pass
        return []

    def _guardar_historial(self, rol: str, msg: str):
        self._historial.append({"rol": rol, "msg": msg, "ts": datetime.now().isoformat()})
        try:
            HISTORIAL_FILE.write_text(
                json.dumps(self._historial[-500:], ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception:
            pass

    # ── BANNER ───────────────────────────────────────────────────────
    def _banner(self):
        os.system("clear" if os.name != "nt" else "cls")
        ancho = 70
        print(f"\n{C.VERDE}{'═'*ancho}{C.RESET}")
        print(f"{C.BOLD}{C.VERDE}  🦁  MAER 4.0 — CONSOLA IA AVANZADA{C.RESET}")
        print(f"{C.GRIS}  Asistente IMSS · OCR · Aprendizaje · Voz · Acceso total{C.RESET}")
        print(f"{C.VERDE}{'─'*ancho}{C.RESET}")

        # Estado servidor
        servidor_ok = self.api.ping()
        srv_txt = f"{C.VERDE}✅ MAER activo en {API_BASE}{C.RESET}" if servidor_ok \
                  else f"{C.DORADO}⚠  Servidor offline — funciones locales disponibles{C.RESET}"
        print(f"  {srv_txt}")

        # Estado voz
        voz_txt = f"{C.VERDE}✅ Voz activada (microfono + TTS){C.RESET}" if self.voz.sr_disponible else \
                  f"{C.GRIS}🔇 Voz: instala 'speech_recognition pyaudio'{C.RESET}"
        print(f"  {voz_txt}")

        # Conocimiento acumulado
        print(f"  {C.CYAN}📚 {self.db.resumen()}{C.RESET}")
        print(f"{C.VERDE}{'─'*ancho}{C.RESET}")
        print(f"{C.GRIS}  Escribe 'ayuda' para ver todos los comandos.{C.RESET}")
        print(f"{C.VERDE}{'═'*ancho}{C.RESET}\n")

    # ── PROMPT ───────────────────────────────────────────────────────
    def _prompt(self) -> str:
        modo = f"{C.CYAN}[VOZ]{C.RESET} " if self._modo_voz else ""
        hora = datetime.now().strftime("%H:%M")
        try:
            return input(f"{C.GRIS}{hora}{C.RESET} {modo}{C.VERDE}🦁 MAER>{C.RESET} ")
        except (EOFError, KeyboardInterrupt):
            return "salir"

    # ══════════════════════════════════════════════════════════════════
    # ── COMANDOS ──────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════

    def cmd_ayuda(self, *_):
        p("\n📋 COMANDOS MAER CONSOLA", C.BOLD + C.VERDE)
        cmds = [
            ("chat <msg>",         "Hablar con la IA de MAER"),
            ("voz",                "Activar/desactivar modo voz continuo"),
            ("analizar <ruta>",    "OCR + análisis profundo de un archivo"),
            ("carpeta <ruta>",     "Analizar todos los archivos de una carpeta"),
            ("aprender <ruta>",    "Aprendizaje profundo — indexa y memoriza todo"),
            ("buscar <término>",   "Buscar en el conocimiento aprendido"),
            ("reporte",            "Generar informe PDF de todo lo aprendido"),
            ("reporte <ruta>",     "Reporte de una carpeta específica"),
            ("deps",               "Verificar dependencias del sistema"),
            ("estado",             "Estado del servidor MAER"),
            ("historial",          "Ver últimas 20 conversaciones"),
            ("limpiar",            "Limpiar pantalla"),
            ("ayuda",              "Mostrar esta ayuda"),
            ("salir",              "Salir de la consola"),
        ]
        for cmd, desc in cmds:
            print(f"  {C.DORADO}{cmd:<25}{C.RESET}  {C.GRIS}{desc}{C.RESET}")
        print(f"\n  {C.GRIS}También puedes escribir cualquier pregunta directamente.{C.RESET}\n")

    def cmd_chat(self, args: str):
        if not args:
            p("⚠ Escribe tu mensaje después de 'chat'", C.DORADO)
            return
        self._chat_ia(args)

    def cmd_voz(self, *_):
        if not self.voz.sr_disponible:
            p("⚠ speech_recognition no instalado.", C.DORADO)
            p("  Instala: pip install SpeechRecognition pyaudio", C.GRIS)
            return

        self._modo_voz = not self._modo_voz
        if self._modo_voz:
            p("🎤 Modo voz ACTIVADO — habla para enviar comandos. Di 'salir voz' para terminar.", C.CYAN)
            self.voz.hablar("Modo voz activado. Hola, soy MAER. ¿En qué te ayudo?")
            threading.Thread(target=self._bucle_voz, daemon=True).start()
        else:
            p("🔇 Modo voz DESACTIVADO.", C.GRIS)
            self.voz.hablar("Modo voz desactivado.")

    def _bucle_voz(self):
        """Escucha continuamente mientras el modo voz esté activo."""
        while self._modo_voz and self._corriendo:
            texto = self.voz.escuchar_una_vez(timeout=6)
            if texto:
                texto_lower = texto.lower().strip()
                if any(k in texto_lower for k in ["salir voz", "desactivar voz", "apagar voz"]):
                    self._modo_voz = False
                    p("\n🔇 Modo voz desactivado.", C.GRIS)
                    return
                print(f"\n{C.GRIS}[Voz detectada]{C.RESET} {texto}")
                self._procesar_entrada(texto)

    def cmd_analizar(self, args: str):
        ruta = Path(args.strip().strip('"').strip("'"))
        if not ruta.exists():
            # Intentar expandir ~ y variables
            ruta = Path(os.path.expandvars(os.path.expanduser(str(ruta))))
        if not ruta.exists():
            p(f"❌ Archivo no encontrado: {ruta}", C.ROJO)
            return

        p(f"\n🔍 Analizando: {ruta.name} ({ruta.stat().st_size//1024} KB)", C.CYAN)
        inicio = time.time()

        # 1. Extraer texto
        p("  1/4 Extrayendo texto (OCR mejorado)...", C.GRIS)
        texto = ocr_local(ruta)
        if not texto or texto.startswith("[ERROR"):
            # Intentar via servidor
            resp = self.api.extraer_texto(str(ruta))
            texto = resp.get("data", {}).get("text", "") or texto

        p(f"     {C.VERDE}✓{C.RESET} {len(texto)} caracteres extraídos", C.GRIS)

        # 2. Extraer entidades
        p("  2/4 Identificando entidades (CURP, RFC, NSS, semanas)...", C.GRIS)
        ents = extraer_entidades(texto)
        self._mostrar_entidades(ents)

        # 3. Análisis con IA
        p("  3/4 Analizando con IA...", C.GRIS)
        resumen_ia = self._resumir_con_ia(texto[:4000], str(ruta))

        # 4. Guardar en base de conocimiento
        p("  4/4 Guardando en base de conocimiento...", C.GRIS)
        self.db.registrar_archivo(str(ruta), texto, ents)

        elapsed = time.time() - inicio
        p(f"\n{'─'*60}", C.VERDE)
        p(f"✅ Análisis completo en {elapsed:.1f}s", C.VERDE + C.BOLD)
        p(f"\n📋 RESUMEN:", C.BOLD)
        print(f"  {resumen_ia}")
        p(f"\n💾 Conocimiento actualizado: {self.db.resumen()}", C.GRIS)

        if self.voz.tts_disponible:
            self.voz.hablar(f"Análisis de {ruta.name} completado.")
        print()

    def cmd_carpeta(self, args: str):
        """Analiza todos los archivos de una carpeta y sus subcarpetas."""
        ruta = Path(os.path.expandvars(os.path.expanduser(args.strip().strip('"'))))
        if not ruta.exists() or not ruta.is_dir():
            p(f"❌ Carpeta no encontrada: {ruta}", C.ROJO)
            return

        # Descubrir archivos
        EXTS = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg",
                ".csv", ".xlsx", ".xls", ".tiff", ".bmp", ".md", ".xml"}
        archivos = [f for f in ruta.rglob("*") if f.is_file() and f.suffix.lower() in EXTS]

        if not archivos:
            p(f"⚠ No se encontraron archivos soportados en {ruta}", C.DORADO)
            return

        total = len(archivos)
        tam_total = sum(f.stat().st_size for f in archivos)
        p(f"\n📂 Carpeta: {C.BOLD}{ruta}{C.RESET}", C.CYAN)
        p(f"   {total} archivos · {tam_total//1024} KB totales", C.GRIS)
        p(f"   {barra(0, total)}", C.GRIS)
        print()

        resultados  = []
        curps_all   = []
        rfcs_all    = []
        errores     = []

        for i, archivo in enumerate(archivos, 1):
            pct = int(i / total * 100)
            # Progress bar en la misma línea
            bar = barra(i, total, ancho=25)
            print(f"\r  {bar} {C.GRIS}{archivo.name[:35]:<35}{C.RESET}", end="", flush=True)

            try:
                texto = ocr_local(archivo)
                if not texto or len(texto.strip()) < 10:
                    resp  = self.api.extraer_texto(str(archivo))
                    texto = resp.get("data", {}).get("text", "") or texto

                ents = extraer_entidades(texto)
                self.db.registrar_archivo(str(archivo), texto, ents)
                curps_all.extend(ents.get("curps", []))
                rfcs_all.extend(ents.get("rfcs", []))
                resultados.append({
                    "archivo":   archivo.name,
                    "ruta":      str(archivo),
                    "kb":        archivo.stat().st_size // 1024,
                    "chars":     len(texto),
                    "curps":     ents.get("curps", []),
                    "rfcs":      ents.get("rfcs", []),
                    "nss":       ents.get("nss_encontrados", []),
                    "semanas":   ents.get("semanas_mencionadas", []),
                })
            except Exception as e:
                errores.append({"archivo": archivo.name, "error": str(e)})

        print()  # nueva línea tras barra
        print()

        # Resumen visual
        p("═"*60, C.VERDE)
        p(f"📂 ANÁLISIS COMPLETO — {ruta.name}", C.BOLD + C.VERDE)
        p("─"*60, C.VERDE)
        p(f"  Archivos analizados:  {len(resultados)}/{total}", C.BLANCO)
        p(f"  Errores:              {len(errores)}", C.ROJO if errores else C.GRIS)
        p(f"  CURPs encontradas:    {len(set(curps_all))}", C.CYAN)
        p(f"  RFCs encontrados:     {len(set(rfcs_all))}", C.CYAN)

        # Top archivos por tamaño
        top = sorted(resultados, key=lambda x: x["chars"], reverse=True)[:5]
        p(f"\n📄 Top archivos por contenido:", C.BOLD)
        for r in top:
            p(f"   • {r['archivo']:<40} {r['chars']:>6} chars  {r['kb']} KB", C.GRIS)

        # Entidades únicas
        curps_u = list(set(curps_all))
        rfcs_u  = list(set(rfcs_all))
        if curps_u:
            p(f"\n🔑 CURPs únicas ({len(curps_u)}):", C.BOLD)
            for c in curps_u[:10]:
                p(f"   {c}", C.DORADO)
        if rfcs_u:
            p(f"\n🏢 RFCs únicos ({len(rfcs_u)}):", C.BOLD)
            for r in rfcs_u[:10]:
                p(f"   {r}", C.DORADO)

        # Oferta de reporte
        p(f"\n💾 {self.db.resumen()}", C.VERDE)
        p(f"\n💡 Escribe 'reporte' para generar un PDF con este análisis.", C.GRIS)

        if self.voz.tts_disponible:
            self.voz.hablar(f"Análisis de {total} archivos completado. "
                            f"Encontré {len(curps_u)} CURPs y {len(rfcs_u)} RFCs.")
        print()

    def cmd_aprender(self, args: str):
        """Aprendizaje profundo: analiza TODO en una carpeta e indexa para búsqueda futura."""
        ruta = Path(os.path.expandvars(os.path.expanduser(args.strip().strip('"'))))
        if not ruta.exists():
            p(f"❌ Ruta no encontrada: {ruta}", C.ROJO)
            return

        if ruta.is_file():
            p(f"📖 Aprendiendo de archivo: {ruta.name}", C.CYAN)
            self.cmd_analizar(str(ruta))
            return

        p(f"\n📚 APRENDIZAJE PROFUNDO — {ruta}", C.BOLD + C.CYAN)
        p("   Indexando todo el contenido para búsqueda y memoria...\n", C.GRIS)

        EXTS_TODAS = {
            ".pdf", ".docx", ".doc", ".txt", ".csv", ".xlsx", ".xls",
            ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".md", ".xml",
            ".json", ".html", ".py", ".js", ".ts", ".log", ".rtf",
        }
        archivos = [f for f in ruta.rglob("*")
                    if f.is_file() and f.suffix.lower() in EXTS_TODAS
                    and f.stat().st_size < 50_000_000]  # <50MB

        total    = len(archivos)
        tam      = sum(f.stat().st_size for f in archivos)
        p(f"  Encontrados: {total} archivos  ({tam//1_048_576:.1f} MB)", C.BLANCO)

        if total == 0:
            p("⚠ No hay archivos para aprender.", C.DORADO)
            return

        # Confirmar si es muy grande
        if total > 200:
            resp = input(f"\n  {C.DORADO}Son {total} archivos. ¿Continuar? [S/n]: {C.RESET}").strip().lower()
            if resp == "n":
                p("Cancelado.", C.GRIS)
                return

        inicio   = time.time()
        proc     = 0
        errores  = 0

        for i, f in enumerate(archivos, 1):
            print(f"\r  {barra(i, total, 28)} {f.name[:30]:<30}", end="", flush=True)
            try:
                texto = ocr_local(f)
                if len(texto.strip()) > 20:
                    ents = extraer_entidades(texto)
                    self.db.registrar_archivo(str(f), texto, ents)
                    proc += 1
            except Exception:
                errores += 1

        elapsed = time.time() - inicio
        print()
        p(f"\n✅ Aprendizaje completado en {elapsed:.1f}s", C.VERDE + C.BOLD)
        p(f"   {proc} archivos procesados · {errores} errores", C.BLANCO)
        p(f"   {self.db.resumen()}", C.CYAN)
        p(f"\n💡 Ahora usa 'buscar <término>' para buscar en todo el conocimiento.", C.GRIS)

        if self.voz.tts_disponible:
            self.voz.hablar(f"Aprendizaje completo. {proc} archivos indexados.")
        print()

    def cmd_buscar(self, args: str):
        if not args.strip():
            p("⚠ Escribe el término a buscar.", C.DORADO)
            return
        termino = args.strip()
        p(f"\n🔍 Buscando '{termino}' en {len(self.db.datos['archivos'])} archivos...", C.CYAN)
        resultados = self.db.buscar(termino)

        if not resultados:
            p(f"  No se encontró '{termino}' en el conocimiento aprendido.", C.GRIS)
            p("  Usa 'aprender <carpeta>' para indexar más archivos.", C.GRIS)
            return

        p(f"\n✅ {len(resultados)} resultado(s):", C.VERDE + C.BOLD)
        for r in resultados[:15]:
            p(f"\n  📄 {r['nombre']}", C.DORADO + C.BOLD)
            p(f"     {C.GRIS}{r['ruta']}{C.RESET}", C.GRIS)
            if r["contexto"]:
                # Resaltar el término en el contexto
                ctx = r["contexto"].replace(termino, f"{C.ROJO}{termino}{C.RESET}")
                p(f"     ...{ctx}...", C.GRIS)
        print()

    def cmd_reporte(self, args: str = ""):
        """Genera informe completo: HTML (abre en browser) + intenta PDF via servidor."""
        modo = args.strip().lower()   # "html", "pdf" o vacío → html primero

        total_arch = len(self.db.datos["archivos"])
        if total_arch == 0:
            p("⚠ No hay archivos analizados aún. Usa 'analizar' o 'carpeta' primero.", C.DORADO)
            return

        curps_u   = list(set(self.db.datos["curps"]))
        rfcs_u    = list(set(self.db.datos["rfcs"]))
        nss_u     = list(set(self.db.datos["nss"]))
        semanas_u = list(set(self.db.datos["semanas"]))

        # ── 1. Siempre generar HTML (rápido, sin servidor) ──
        if modo != "pdf":
            ts_str   = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_out = BASE_DIR / f"reporte_maer_{ts_str}.html"
            p(f"\n🌐 Generando informe HTML...", C.CYAN)
            generar_reporte_html(self.db, html_out)
            p(f"✅ HTML listo: {html_out}", C.VERDE + C.BOLD)
            try:
                import webbrowser
                webbrowser.open(f"file://{html_out}")
                p("   Abierto en tu navegador.", C.GRIS)
            except Exception:
                p(f"   Abre manualmente: {html_out}", C.GRIS)

        # ── 2. También intentar PDF via servidor ──
        if modo != "html":
            p(f"\n📄 Generando PDF via servidor...", C.CYAN)
            payload = {
                "nombre":  "Informe MAER Consola",
                "semanas": semanas_u[0] if semanas_u else None,
                "curp":    curps_u[0]   if curps_u   else "",
                "nss":     nss_u[0]     if nss_u     else "",
                "notas":   f"Archivos: {total_arch} | CURPs: {len(curps_u)} | RFCs: {len(rfcs_u)}",
            }
            resp = self.api.exportar_pdf(payload)
            if resp.get("ok") and resp.get("data", {}).get("pdf_path"):
                pdf_path = resp["data"]["pdf_path"]
                p(f"✅ PDF: {pdf_path}", C.VERDE)
                try:
                    abrir = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.Popen([abrir, pdf_path])
                except Exception:
                    pass
            else:
                if modo == "pdf":
                    # Solo pedía PDF y falló — hacer txt de respaldo
                    self._reporte_texto(curps_u, rfcs_u, nss_u, semanas_u, total_arch)
                else:
                    p("   (PDF no disponible — servidor offline)", C.GRIS)

        if self.voz.tts_disponible:
            self.voz.hablar("Informe generado. Revisa tu navegador.")
        print()

    def cmd_vigilar(self, args: str):
        """
        Vigila una carpeta en tiempo real. Cada vez que se agrega o modifica
        un archivo, MAER lo analiza y aprende automáticamente.
        """
        ruta = Path(os.path.expandvars(os.path.expanduser(args.strip().strip('"'))))
        if not ruta.exists() or not ruta.is_dir():
            p(f"❌ Carpeta no encontrada: {ruta}", C.ROJO)
            return

        p(f"\n👁  Vigilando: {C.BOLD}{ruta}{C.RESET}", C.CYAN)
        p("   Cualquier archivo nuevo o modificado será analizado automáticamente.", C.GRIS)
        p("   Presiona Ctrl+C para dejar de vigilar.\n", C.GRIS)

        if self.voz.tts_disponible:
            self.voz.hablar(f"Vigilando carpeta {ruta.name}. Analizaré cada archivo nuevo.")

        EXTS = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg",
                ".csv", ".xlsx", ".xls", ".tiff", ".bmp", ".md"}

        # Estado inicial: snapshoot de lo que ya existe
        estado_inicial: Dict[str, float] = {}
        for f in ruta.rglob("*"):
            if f.is_file() and f.suffix.lower() in EXTS:
                try:
                    estado_inicial[str(f)] = f.stat().st_mtime
                except Exception:
                    pass

        p(f"  Estado base: {len(estado_inicial)} archivos en la carpeta.", C.GRIS)
        p(f"  {C.DORADO}Esperando cambios...{C.RESET}\n", C.GRIS)

        try:
            while True:
                time.sleep(2)
                estado_actual: Dict[str, float] = {}
                for f in ruta.rglob("*"):
                    if f.is_file() and f.suffix.lower() in EXTS:
                        try:
                            estado_actual[str(f)] = f.stat().st_mtime
                        except Exception:
                            pass

                # Detectar archivos nuevos o modificados
                for ruta_f, mtime in estado_actual.items():
                    if ruta_f not in estado_inicial or estado_inicial[ruta_f] != mtime:
                        f_path = Path(ruta_f)
                        ts     = datetime.now().strftime("%H:%M:%S")
                        accion = "NUEVO" if ruta_f not in estado_inicial else "MODIFICADO"
                        p(f"\n  [{ts}] 🔔 Archivo {accion}: {f_path.name}", C.DORADO + C.BOLD)

                        # Esperar un momento a que el archivo termine de escribirse
                        time.sleep(1)

                        try:
                            texto = ocr_local(f_path)
                            if len(texto.strip()) > 10:
                                ents = extraer_entidades(texto)
                                self.db.registrar_archivo(ruta_f, texto, ents)

                                # Mostrar resumen rápido
                                info = []
                                if ents.get("curps"):
                                    info.append(f"CURP: {ents['curps'][0]}")
                                if ents.get("semanas_mencionadas"):
                                    info.append(f"Semanas: {ents['semanas_mencionadas'][0]}")
                                if ents.get("rfcs"):
                                    info.append(f"RFC: {ents['rfcs'][0]}")

                                p(f"  ✅ Aprendido — {len(texto)} chars"
                                  + (f" | {' | '.join(info)}" if info else ""), C.VERDE)

                                if self.voz.tts_disponible and info:
                                    self.voz.hablar(f"Nuevo archivo detectado. {'. '.join(info)}")
                            else:
                                p(f"  ⚠ Archivo vacío o no legible.", C.GRIS)
                        except Exception as e:
                            p(f"  ⚠ Error al analizar: {e}", C.DORADO)

                        estado_inicial[ruta_f] = mtime

                # Detectar archivos eliminados
                eliminados = set(estado_inicial) - set(estado_actual)
                for e in eliminados:
                    p(f"  🗑 Eliminado del radar: {Path(e).name}", C.GRIS)
                    estado_inicial.pop(e, None)

        except KeyboardInterrupt:
            p(f"\n\n👁 Vigilancia detenida. {self.db.resumen()}", C.VERDE)
            self.db.guardar()
            print()

    def cmd_tablas(self, args: str):
        """Extrae y muestra tablas de un PDF, Excel o CSV."""
        ruta = Path(os.path.expandvars(os.path.expanduser(args.strip().strip('"'))))
        if not ruta.exists():
            p(f"❌ Archivo no encontrado: {ruta}", C.ROJO)
            return

        p(f"\n📊 Extrayendo tablas de: {ruta.name}", C.CYAN)
        tablas = extraer_tablas(ruta)

        if not tablas:
            p("  No se encontraron tablas estructuradas en este archivo.", C.GRIS)
            p("  Tip: funciona mejor con PDFs digitales, Excel y CSV.", C.GRIS)
            return

        p(f"  ✅ {len(tablas)} tabla(s) encontrada(s)\n", C.VERDE)

        for i, tabla in enumerate(tablas, 1):
            p(f"── Tabla {i}: {tabla['titulo']} ──", C.DORADO + C.BOLD)
            n_filas = len(tabla["filas"])
            n_cols  = max((len(f) for f in tabla["filas"]), default=0)
            p(f"  {n_filas} filas × {n_cols} columnas", C.GRIS)

            # Mostrar tabla formateada
            print(_formatear_tabla_consola(tabla, max_col=22))

            # Guardar en DB
            texto_tabla = tabla["texto"]
            ents = extraer_entidades(texto_tabla)
            self.db.registrar_archivo(
                f"{ruta}::tabla{i}", texto_tabla, ents)

            print()

        p(f"💾 Tablas guardadas en conocimiento MAER.", C.GRIS)

        # Exportar a CSV opcional
        try:
            csv_out = ruta.parent / f"{ruta.stem}_tablas_maer.csv"
            import csv as csv_mod
            with open(csv_out, "w", newline="", encoding="utf-8") as f:
                wr = csv_mod.writer(f)
                for tabla in tablas:
                    wr.writerow([f"# {tabla['titulo']}"])
                    for fila in tabla["filas"]:
                        wr.writerow(fila)
                    wr.writerow([])
            p(f"📁 Tablas exportadas a CSV: {csv_out}", C.VERDE)
        except Exception:
            pass
        print()

    def _reporte_texto(self, curps, rfcs, nss, semanas, total):
        """Reporte en texto si el servidor no está disponible."""
        ts    = datetime.now().strftime("%Y-%m-%d %H:%M")
        fname = BASE_DIR / f"reporte_maer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        lineas = [
            "═" * 60,
            f"🦁 MAER 4.0 — INFORME DE CONOCIMIENTO ACUMULADO",
            f"Generado: {ts}",
            "═" * 60,
            "",
            f"RESUMEN ESTADÍSTICO",
            f"  Archivos analizados:  {total}",
            f"  CURPs encontradas:    {len(curps)}",
            f"  RFCs encontrados:     {len(rfcs)}",
            f"  NSS encontrados:      {len(nss)}",
            f"  Semanas detectadas:   {len(semanas)}",
            "",
        ]
        if curps:
            lineas += ["CURPS ENCONTRADAS:", *[f"  {c}" for c in curps[:20]], ""]
        if rfcs:
            lineas += ["RFCS ENCONTRADOS:", *[f"  {r}" for r in rfcs[:20]], ""]
        if semanas:
            lineas += ["SEMANAS MENCIONADAS:", *[f"  {s}" for s in sorted(set(semanas))], ""]

        lineas += [
            "ARCHIVOS PROCESADOS:",
            *[f"  • {v['nombre']}" for v in list(self.db.datos["archivos"].values())[:50]],
            "",
            "═" * 60,
            "MAER 4.0 — Sistema de Asistencia para Expedientes de Retiro",
        ]
        contenido = "\n".join(lineas)
        fname.write_text(contenido, encoding="utf-8")
        p(f"✅ Reporte de texto guardado: {fname}", C.VERDE)
        print(contenido[:800])

    def cmd_deps(self, *_):
        p("\n🔧 Verificando dependencias...", C.CYAN)
        resp = self.api.verificar_deps()
        if resp.get("ok"):
            d   = resp.get("data", {})
            pkg = d.get("python_packages", {})
            ok  = sum(1 for v in pkg.values() if v)
            p(f"\n  Paquetes Python: {barra(ok, len(pkg))}", C.BLANCO)
            for nombre, estado in pkg.items():
                sym = f"{C.VERDE}✅" if estado else f"{C.ROJO}❌"
                print(f"    {sym} {nombre:<20}{C.RESET}")
            sistemas = [
                ("Tesseract OCR", d.get("tesseract_bin")),
                ("Java",          d.get("java")),
                ("Conda",         d.get("conda")),
                ("Ollama (LLM)",  d.get("ollama")),
                ("Chrome",        d.get("chrome")),
            ]
            p("\n  Herramientas del sistema:", C.BLANCO)
            for nom, ok_s in sistemas:
                sym = f"{C.VERDE}✅" if ok_s else f"{C.ROJO}❌"
                print(f"    {sym} {nom:<25}{C.RESET}")
        else:
            p(f"⚠ Servidor no disponible: {resp.get('message')}", C.DORADO)
            # Verificar localmente
            p("\n  Verificación local:", C.BLANCO)
            checks = [
                ("pytesseract",  "pytesseract"),
                ("PIL",          "PIL"),
                ("cv2",          "cv2"),
                ("fitz",         "fitz"),
                ("deskew",       "deskew"),
                ("reportlab",    "reportlab"),
                ("selenium",     "selenium"),
                ("pypdf",        "pypdf"),
                ("docx",         "docx"),
            ]
            for label, mod in checks:
                try:
                    __import__(mod)
                    print(f"    {C.VERDE}✅ {label}{C.RESET}")
                except ImportError:
                    print(f"    {C.ROJO}❌ {label}{C.RESET}")
        print()

    def cmd_estado(self, *_):
        p("\n⚙️  Estado del sistema MAER", C.BOLD)
        ok = self.api.ping()
        p(f"  Servidor MAER:    {'✅ Activo en ' + API_BASE if ok else '❌ Offline'}", C.VERDE if ok else C.ROJO)
        p(f"  Voz (entrada):    {'✅ speech_recognition' if self.voz.sr_disponible else '❌ No disponible'}", C.GRIS)
        p(f"  Voz (salida TTS): {'✅ ' + str(getattr(self.voz,'_tts_cmd',['pyttsx3'])[0]) if self.voz.tts_disponible else '❌ No disponible'}", C.GRIS)
        p(f"  Conocimiento:     {self.db.resumen()}", C.CYAN)
        p(f"  DB:               {CONOCIMIENTO_DB}", C.GRIS)
        p(f"  Historial:        {len(self._historial)} entradas", C.GRIS)
        print()

    def cmd_historial(self, *_):
        ult = self._historial[-20:]
        if not ult:
            p("Sin historial aún.", C.GRIS)
            return
        p(f"\n📜 Últimas {len(ult)} entradas:", C.BOLD)
        for h in ult:
            ts  = h.get("ts", "")[:16]
            rol = h.get("rol", "")
            msg = h.get("msg", "")[:120]
            color = C.AZUL if rol == "user" else C.VERDE
            p(f"  {C.GRIS}{ts}{C.RESET} {color}{rol:8}{C.RESET} {msg}", C.RESET)
        print()

    def cmd_limpiar(self, *_):
        self._banner()

    # ── IA INTERNA ───────────────────────────────────────────────────
    def _chat_ia(self, msg: str):
        """Envía mensaje a la IA de MAER y muestra respuesta."""
        self._guardar_historial("user", msg)

        # Construir contexto desde conocimiento acumulado
        ctx = ""
        relevantes = self.db.buscar(msg[:40])
        if relevantes:
            ctx = "Contexto del conocimiento aprendido:\n"
            for r in relevantes[:3]:
                ctx += f"- {r['nombre']}: ...{r['contexto'][:200]}...\n"

        p(f"\n{C.VERDE}🦁 MAER{C.RESET} {C.GRIS}pensando...{C.RESET}", end="\r")
        resp_data = self.api.chat(msg, ctx)

        if resp_data.get("ok"):
            resp    = resp_data.get("data", {}).get("response", "")
            engine  = resp_data.get("data", {}).get("engine", "?")
            nota    = resp_data.get("data", {}).get("nota", "")

            print(f"\r{' '*50}\r", end="")  # limpiar "pensando..."
            p(f"\n{C.VERDE}🦁 MAER {C.GRIS}[{engine}]{C.RESET}", C.BOLD)
            # Formatear respuesta con colores
            for linea in resp.split("\n"):
                if linea.startswith("•") or linea.startswith("-"):
                    p(f"  {linea}", C.BLANCO)
                elif linea.startswith("#"):
                    p(linea, C.VERDE + C.BOLD)
                else:
                    print(f"  {linea}")

            if nota:
                p(f"\n  💡 {nota}", C.GRIS)

            self._guardar_historial("maer", resp)

            if self.voz.tts_disponible:
                # Solo hablar las primeras 3 líneas no vacías
                primeras = [l for l in resp.split("\n") if l.strip()][:3]
                self.voz.hablar(" ".join(primeras))
        else:
            print(f"\r{' '*50}\r", end="")
            err = resp_data.get("message", "Error desconocido")
            p(f"\n⚠ MAER offline: {err}", C.DORADO)
            p("  Inicia el servidor con el lanzador o ejecuta server.py", C.GRIS)

            # Respuesta local de emergencia
            resp_local = self._respuesta_local(msg)
            if resp_local:
                p(f"\n🦁 MAER [local]", C.VERDE + C.BOLD)
                p(f"  {resp_local}", C.BLANCO)
                if self.voz.tts_disponible:
                    self.voz.hablar(resp_local[:200])

        print()

    def _respuesta_local(self, msg: str) -> str:
        """Respuestas básicas cuando el servidor no está disponible."""
        msg_l = msg.lower()
        if any(k in msg_l for k in ["ley 73", "semanas", "pension", "pensión"]):
            return ("Ley 73 del IMSS: requiere mínimo 500 semanas cotizadas para pensión "
                    "por vejez (65 años) o cesantía (60 años). "
                    "La Ley 73 aplica si tu primera afiliación al IMSS fue antes del 1 de julio de 1997.")
        if "curp" in msg_l:
            return ("La CURP es la Clave Única de Registro de Población, de 18 caracteres. "
                    "Contiene: apellidos, fecha de nacimiento, sexo, estado y número verificador.")
        if "nss" in msg_l or "número de seguridad" in msg_l:
            return ("El NSS (Número de Seguridad Social) es un código de 11 dígitos del IMSS. "
                    "Los primeros 2 dígitos identifican la subdelegación de afiliación.")
        if "afore" in msg_l:
            return ("El AFORE administra tu cuenta individual de ahorro para el retiro (SAR). "
                    "Con Ley 97, acumulas en tu AFORE. Consulta en www.e-sar.com.mx")
        return ""

    def _resumir_con_ia(self, texto: str, ruta: str) -> str:
        """Obtiene un resumen corto del texto analizado."""
        prompt = f"Resume en 2-3 líneas el siguiente documento ('{Path(ruta).name}'): {texto[:2000]}"
        resp   = self.api.chat(prompt)
        if resp.get("ok"):
            return resp.get("data", {}).get("response", "")[:400]
        # Resumen local si servidor no disponible
        primer_parrafo = " ".join(texto.split()[:80])
        return f"(Resumen local) {primer_parrafo}..."

    def _mostrar_entidades(self, ents: dict):
        if ents.get("curps"):
            p(f"     CURPs: {C.DORADO}{', '.join(ents['curps'][:5])}{C.RESET}", C.GRIS)
        if ents.get("rfcs"):
            p(f"     RFCs:  {C.DORADO}{', '.join(ents['rfcs'][:5])}{C.RESET}", C.GRIS)
        if ents.get("nss_encontrados"):
            p(f"     NSS:   {C.DORADO}{', '.join(ents['nss_encontrados'][:3])}{C.RESET}", C.GRIS)
        if ents.get("semanas_mencionadas"):
            p(f"     Sem:   {C.DORADO}{', '.join(str(s) for s in ents['semanas_mencionadas'][:5])}{C.RESET}", C.GRIS)
        if not any(ents.values()):
            p(f"     (no se detectaron CURP/RFC/NSS/semanas)", C.GRIS)

    # ══════════════════════════════════════════════════════════════════
    # ── LOOP PRINCIPAL ────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════
    def _procesar_entrada(self, entrada: str):
        """Parsea y ejecuta un comando."""
        entrada = entrada.strip()
        if not entrada:
            return

        partes = entrada.split(maxsplit=1)
        cmd    = partes[0].lower()
        args   = partes[1] if len(partes) > 1 else ""

        # Mapa de comandos
        CMDS = {
            "chat":      self.cmd_chat,
            "hablar":    self.cmd_chat,
            "pregunta":  self.cmd_chat,
            "voz":       self.cmd_voz,
            "micro":     self.cmd_voz,
            "analizar":  self.cmd_analizar,
            "ocr":       self.cmd_analizar,
            "archivo":   self.cmd_analizar,
            "carpeta":   self.cmd_carpeta,
            "folder":    self.cmd_carpeta,
            "aprender":  self.cmd_aprender,
            "indexar":   self.cmd_aprender,
            "buscar":    self.cmd_buscar,
            "search":    self.cmd_buscar,
            "reporte":   self.cmd_reporte,
            "informe":   self.cmd_reporte,
            "html":      self.cmd_reporte,
            "pdf":       self.cmd_reporte,
            "vigilar":   self.cmd_vigilar,
            "watch":     self.cmd_vigilar,
            "monitorear":self.cmd_vigilar,
            "tablas":    self.cmd_tablas,
            "tabla":     self.cmd_tablas,
            "extraer":   self.cmd_tablas,
            "deps":      self.cmd_deps,
            "dependencias": self.cmd_deps,
            "estado":    self.cmd_estado,
            "status":    self.cmd_estado,
            "historial": self.cmd_historial,
            "historia":  self.cmd_historial,
            "limpiar":   self.cmd_limpiar,
            "clear":     self.cmd_limpiar,
            "ayuda":     self.cmd_ayuda,
            "help":      self.cmd_ayuda,
            "?":         self.cmd_ayuda,
            "salir":     self._salir,
            "exit":      self._salir,
            "quit":      self._salir,
        }

        if cmd in CMDS:
            CMDS[cmd](args)
        else:
            # No reconocido como comando → chat directo
            self._chat_ia(entrada)

    def _salir(self, *_):
        p("\n👋 ¡Hasta luego! MAER guarda tu conocimiento automáticamente.", C.VERDE)
        if self.voz.tts_disponible:
            self.voz.hablar("Hasta luego. Tu progreso ha sido guardado.")
        self.db.guardar()
        self._corriendo = False

    def run(self):
        """Bucle principal de la consola."""
        # Activar autocompletado TAB + historial ↑↓
        _setup_readline()

        self._banner()

        # Saludo de voz
        if self.voz.tts_disponible:
            threading.Thread(
                target=lambda: self.voz.hablar(
                    "Hola, soy MAER, tu asistente de pensión IMSS. ¿En qué te ayudo?"),
                daemon=True
            ).start()

        while self._corriendo:
            try:
                if self._modo_voz:
                    # En modo voz, el input viene del bucle de voz
                    time.sleep(0.2)
                    continue
                entrada = self._prompt()
                self._procesar_entrada(entrada)
            except KeyboardInterrupt:
                print()
                resp = input(f"  {C.DORADO}¿Salir de MAER? [S/n]: {C.RESET}").strip().lower()
                if resp != "n":
                    self._salir()
            except EOFError:
                self._salir()


# ══════════════════════════════════════════════════════════════════════
# ── MAIN ──────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Auto-instalar dependencias mínimas
    _faltantes = []
    for _pkg, _imp in [("requests", "requests"), ("pypdf", "pypdf")]:
        try:
            __import__(_imp)
        except ImportError:
            _faltantes.append(_pkg)

    if _faltantes:
        print(f"Instalando dependencias: {', '.join(_faltantes)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               *_faltantes, "-q", "--break-system-packages"],
                              stdout=subprocess.DEVNULL)

    consola = MAERConsola()
    consola.run()
