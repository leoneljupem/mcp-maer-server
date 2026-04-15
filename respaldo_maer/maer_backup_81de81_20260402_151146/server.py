#!/usr/bin/env python3
# 🦁 MAER Web Dashboard — FastAPI Server
# Leonel Mojica — Ecatepec MX — 2026

"""
Dashboard web para MAER MCP Server.
Expone todas las herramientas como API REST + interfaz visual.
"""

import os
import sys
import subprocess
import json
import shutil
import tempfile
from pathlib import Path

# Agregar project root al path para imports
_project_root = str(Path(__file__).parent.parent.parent.resolve())
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# Importar acciones del backend
from maer_backend.maer_files import (
    action_search_files, action_analyze_file, action_fix_code_file,
    action_extract_text, action_index_full, action_search_index,
    action_detect_ids, action_detect_related, action_curp_renapo_check,
    action_ocr_multimodal, action_extract_tables, action_nlp_entities,
    action_image_duplicates, action_face_detect, action_cluster_files,
    action_llm_summarize, action_llm_extract_json, action_renapo_verify_identity,
    make_response,
)

app = FastAPI(
    title="🦁 MAER Dashboard",
    description="Motor Multimodal de Análisis Documental",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Anti-cache para desarrollo: forzar recarga de JS/CSS/HTML
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if any(request.url.path.endswith(ext) for ext in ('.js', '.css', '.html')):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# Directorios base
STATIC_DIR = Path(__file__).parent / "static"
BASE_DIR   = Path(__file__).parent.parent.parent.resolve()   # raíz del proyecto (mcp-maer-server/)
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Montar estáticos
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Sube un archivo para análisis."""
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return make_response(True, "UPLOAD_OK", f"Archivo subido: {file.filename}", {
        "path": str(dest), "name": file.filename, "size": dest.stat().st_size,
    })


@app.post("/api/search")
async def api_search(payload: dict):
    return action_search_files(payload)


@app.post("/api/analyze")
async def api_analyze(payload: dict):
    return action_analyze_file(payload)


@app.post("/api/extract-text")
async def api_extract_text(payload: dict):
    return action_extract_text(payload)


@app.post("/api/detect-ids")
async def api_detect_ids(payload: dict):
    return action_detect_ids(payload)


@app.post("/api/detect-related")
async def api_detect_related(payload: dict):
    return action_detect_related(payload)


@app.post("/api/ocr")
async def api_ocr(payload: dict):
    return action_ocr_multimodal(payload)


@app.post("/api/tables")
async def api_tables(payload: dict):
    return action_extract_tables(payload)


@app.post("/api/nlp")
async def api_nlp(payload: dict):
    return action_nlp_entities(payload)


@app.post("/api/duplicates")
async def api_duplicates(payload: dict):
    return action_image_duplicates(payload)


@app.post("/api/faces")
async def api_faces(payload: dict):
    return action_face_detect(payload)


@app.post("/api/cluster")
async def api_cluster(payload: dict):
    return action_cluster_files(payload)


@app.post("/api/index")
async def api_index(payload: dict):
    return action_index_full(payload)


@app.post("/api/search-index")
async def api_search_index(payload: dict):
    return action_search_index(payload)


@app.post("/api/curp-check")
async def api_curp_check(payload: dict):
    return action_curp_renapo_check(payload)


@app.post("/api/llm-summarize")
async def api_llm_summarize(payload: dict):
    return action_llm_summarize(payload)


@app.post("/api/llm-extract")
async def api_llm_extract(payload: dict):
    return action_llm_extract_json(payload)


@app.post("/api/renapo-verify")
async def api_renapo_verify(payload: dict):
    return action_renapo_verify_identity(payload)


@app.post("/api/open")
async def api_open(payload: dict):
    """Abre un archivo remotamente en la computadora."""
    path = payload.get("path")
    if not path or not Path(path).exists():
        return make_response(False, "NOT_FOUND", "Archivo no encontrado para abrir.")
    try:
        if os.name == 'nt':
            os.startfile(path)
        else:
            subprocess.Popen(['open', path])
        # Responder inmediatamente
        return make_response(True, "OPEN_OK", f"Archivo abierto: {path}")
    except Exception as e:
        return make_response(False, "OPEN_ERROR", str(e))



@app.get("/api/select-file")
async def api_select_file():
    """Abre el Finder nativo de MacOS para escoger un archivo, en vez de obligar a escribir la ruta entera."""
    try:
        cmd = ["osascript", "-e", "POSIX path of (choose file)"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        path = result.stdout.strip()
        if path:
            return make_response(True, "OK", "", path)
        return make_response(False, "CANCEL", "Cerrado por el usuario", "")
    except Exception as e:
        return make_response(False, "ERROR", str(e))

@app.get("/api/select-dir")
async def api_select_dir():
    """Abre el Finder nativo de MacOS para escoger una carpeta."""
    try:
        cmd = ["osascript", "-e", "POSIX path of (choose folder)"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        path = result.stdout.strip()
        if path:
            return make_response(True, "OK", "", path)
        return make_response(False, "CANCEL", "Cerrado por el usuario", "")
    except Exception as e:
        return make_response(False, "ERROR", str(e))

@app.get("/api/status")
async def api_status():
    """Estado del servidor y módulos disponibles."""
    modules = {}

    try:
        import pytesseract
        modules["tesseract"] = True
    except ImportError:
        modules["tesseract"] = False

    try:
        import easyocr
        modules["easyocr"] = True
    except ImportError:
        modules["easyocr"] = False

    try:
        from paddleocr import PaddleOCR
        modules["paddleocr"] = True
    except ImportError:
        modules["paddleocr"] = False

    try:
        import spacy
        spacy.load("es_core_news_md")
        modules["spacy"] = True
    except Exception:
        modules["spacy"] = False

    try:
        from deepface import DeepFace
        modules["deepface"] = True
    except ImportError:
        modules["deepface"] = False

    try:
        import imagehash
        modules["imagehash"] = True
    except ImportError:
        modules["imagehash"] = False

    try:
        import cv2
        modules["opencv"] = True
    except ImportError:
        modules["opencv"] = False

    try:
        import pdfplumber
        modules["pdfplumber"] = True
    except ImportError:
        modules["pdfplumber"] = False

    return make_response(True, "STATUS_OK", "Servidor MAER activo", {
        "version": "2.0.0",
        "modules": modules,
    })


@app.post("/api/llm-chat")
async def api_llm_chat(payload: dict):
    from maer_backend.maer_files import action_llm_chat
    return action_llm_chat(payload)


@app.get("/favicon.ico")
async def favicon():
    """Favicon para evitar errores 404."""
    from fastapi.responses import Response
    # SVG favicon incrustado como ICO simulado (PNG base64 1x1 amarillo-azul)
    ico = b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x18\x00h\x03\x00\x006\x00\x00\x00'
    return Response(content=ico, media_type="image/x-icon")


@app.post("/api/move-files")
async def api_move_files(payload: dict):
    """Mueve archivos a una carpeta destino."""
    import shutil
    # Acepta tanto "rutas" (JS) como "files" (legacy)
    files       = payload.get("rutas", payload.get("files", []))
    destination = payload.get("destino", payload.get("destination", "")).strip()
    moved, errors = [], []
    if not destination:
        return make_response(False, "NO_DEST", "Se requiere carpeta destino.")
    dest_path = Path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)
    for f in files:
        src = Path(f)
        if not src.exists():
            errors.append(f"No encontrado: {f}")
            continue
        try:
            shutil.move(str(src), str(dest_path / src.name))
            moved.append(str(dest_path / src.name))
        except Exception as e:
            errors.append(f"{src.name}: {e}")
    return make_response(len(errors) == 0, "MOVE_OK", f"{len(moved)} archivos movidos.",
                         {"moved": moved, "errors": errors})


@app.post("/api/copy-files")
async def api_copy_files(payload: dict):
    """Copia y organiza archivos a carpeta destino (safe — originals intactos)."""
    import shutil
    from collections import defaultdict

    # Acepta modo simple (files + destination) o modo organización (origen + destino + grupos)
    origen      = payload.get("origen", "")
    destination = payload.get("destino", payload.get("destination", "")).strip()
    grupos      = payload.get("grupos", [])    # [ {nombre, archivos:[...]} ]
    files       = payload.get("files", [])

    copied, errors = [], []
    if not destination:
        return make_response(False, "NO_DEST", "Se requiere carpeta destino.")
    dest_root = Path(destination)
    dest_root.mkdir(parents=True, exist_ok=True)

    # Modo organización por grupos
    if grupos and origen:
        origen_path = Path(origen)
        carpetas_creadas = set()
        for grupo in grupos:
            nombre_carpeta = grupo.get("nombre", "Otros")
            archivos_grupo = grupo.get("archivos", [])
            carpeta_dest = dest_root / nombre_carpeta
            carpeta_dest.mkdir(parents=True, exist_ok=True)
            carpetas_creadas.add(nombre_carpeta)
            for nombre_archivo in archivos_grupo:
                src = origen_path / nombre_archivo
                if not src.exists():
                    # Buscar recursivamente
                    encontrados = list(origen_path.rglob(nombre_archivo))
                    src = encontrados[0] if encontrados else src
                if src.exists():
                    try:
                        shutil.copy2(str(src), str(carpeta_dest / src.name))
                        copied.append(str(carpeta_dest / src.name))
                    except Exception as e:
                        errors.append(f"{src.name}: {e}")
                else:
                    errors.append(f"No encontrado: {nombre_archivo}")
        return make_response(len(errors) == 0, "COPY_OK",
                             f"{len(copied)} archivos organizados en {len(carpetas_creadas)} carpetas.",
                             {"copiados": len(copied), "carpetas": len(carpetas_creadas), "errors": errors})

    # Modo simple: lista de rutas
    for f in files:
        src = Path(f)
        if not src.exists():
            errors.append(f"No encontrado: {f}")
            continue
        try:
            shutil.copy2(str(src), str(dest_root / src.name))
            copied.append(str(dest_root / src.name))
        except Exception as e:
            errors.append(f"{src.name}: {e}")
    return make_response(len(errors) == 0, "COPY_OK", f"{len(copied)} archivos copiados.",
                         {"copied": copied, "errors": errors})


@app.post("/api/learn-file")
async def api_learn_file(file: UploadFile = File(...), label: str = Form("")):
    """Extrae texto de un archivo para que MAER lo aprenda."""
    import tempfile
    ext = Path(file.filename).suffix.lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    shutil.copyfileobj(file.file, tmp)
    tmp.close()
    tmp_path = tmp.name
    text = ""
    try:
        if ext == ".pdf":
            import pdfplumber
            with pdfplumber.open(tmp_path) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        elif ext in [".txt", ".md", ".csv", ".json", ".js", ".py", ".html"]:
            text = Path(tmp_path).read_text("utf-8", errors="replace")
        elif ext in [".docx"]:
            try:
                import docx
                doc = docx.Document(tmp_path)
                text = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                text = f"[DOCX sin módulo python-docx]"
        else:
            # Try OCR
            from maer_backend.maer_files import action_ocr_multimodal
            r = action_ocr_multimodal({"path": tmp_path})
            text = r.get("data", {}).get("text", "No se pudo extraer texto.")
        if not text.strip():
            text = "[Archivo sin texto extraíble]"
    except Exception as e:
        text = f"Error al procesar: {e}"
    finally:
        try: os.unlink(tmp_path)
        except: pass
    summary = text[:8000]  # max chars to store
    return make_response(True, "LEARN_OK", f"Texto extraído: {len(text)} caracteres", {
        "filename": file.filename, "label": label or file.filename,
        "text": summary, "chars": len(text),
    })


def _normalizar(texto: str) -> str:
    """Normaliza texto: minúsculas + quita acentos para búsquedas sin acentuar."""
    import unicodedata
    return unicodedata.normalize("NFD", texto.lower()).encode("ascii", "ignore").decode("ascii")


@app.post("/api/busqueda-masiva")
async def api_busqueda_masiva(payload: dict):
    """Búsqueda masiva por contenido en directorio, filtrando por tipo.
    Soporta búsqueda con o sin acentos en texto español."""
    # Acepta tanto "carpeta"/"termino" (JS 3.1) como "base_dir"/"query" (legacy)
    base_dir     = payload.get("carpeta", payload.get("base_dir", "."))
    query_raw    = payload.get("termino", payload.get("query", ""))
    query        = _normalizar(query_raw)          # normalizado sin acentos
    tipos        = payload.get("tipos", [])
    en_nombre    = payload.get("en_nombre", True)
    en_contenido = payload.get("en_contenido", False)
    max_results  = payload.get("max_results", 200)
    results = []
    ext_map = {
        "pdf": [".pdf"], "txt": [".txt", ".md", ".csv"], "imagen": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "word": [".docx", ".doc"], "excel": [".xlsx", ".xls"], "json": [".json"],
        "zip": [".zip", ".rar", ".7z"], "codigo": [".py", ".js", ".html", ".css"],
    }
    allowed_exts = set()
    for t in tipos:
        allowed_exts.update(ext_map.get(t, [f".{t}"]))
    try:
        base = Path(base_dir)
        if not base.exists():
            return make_response(False, "DIR_NOT_FOUND", f"Directorio no encontrado: {base_dir}")
        for f in base.rglob("*"):
            if not f.is_file(): continue
            if allowed_exts and f.suffix.lower() not in allowed_exts: continue
            # Búsqueda en nombre (normalizada)
            match_name    = (query in _normalizar(f.name)) if (query and en_nombre) else (not query)
            match_content = False
            if query and en_contenido and not match_name:
                try:
                    if f.suffix.lower() in [".txt",".md",".csv",".json",".js",".py",".html",".css"]:
                        content = f.read_text("utf-8", errors="replace")
                        match_content = query in _normalizar(content)
                    elif f.suffix.lower() == ".pdf":
                        import pdfplumber
                        with pdfplumber.open(str(f)) as pdf:
                            for page in pdf.pages[:5]:
                                t_page = page.extract_text() or ""
                                if query in _normalizar(t_page): match_content = True; break
                    elif f.suffix.lower() in [".docx"]:
                        try:
                            import docx as _docx
                            doc = _docx.Document(str(f))
                            text_doc = " ".join(p.text for p in doc.paragraphs)
                            match_content = query in _normalizar(text_doc)
                        except Exception: pass
                except: pass
            if match_name or match_content or not query:
                stat = f.stat()
                size_fmt = (f"{stat.st_size//1024} KB" if stat.st_size >= 1024 else f"{stat.st_size} B")
                fragmento = ""
                if match_content:
                    try:
                        txt = f.read_text("utf-8", errors="replace")
                        txt_norm = _normalizar(txt)
                        idx = txt_norm.find(query)
                        if idx >= 0:
                            fragmento = txt[max(0,idx-40):idx+80].replace('\n',' ')
                    except: pass
                results.append({
                    "ruta":      str(f),
                    "nombre":    f.name,
                    "ext":       f.suffix.lower(),
                    "tamaño":    size_fmt,
                    "tipo":      f.suffix.lstrip(".").upper(),
                    "match":     "nombre" if match_name else "contenido",
                    "fragmento": fragmento,
                })
            if len(results) >= max_results: break
    except Exception as e:
        return make_response(False, "SEARCH_ERR", str(e))
    return make_response(True, "SEARCH_OK", f"{len(results)} resultados encontrados.",
                         {"resultados": results, "total": len(results)})


@app.post("/api/organizar-sugerir")
async def api_organizar_sugerir(payload: dict):
    """Sugiere cómo organizar archivos en una carpeta y devuelve grupos listos para /api/copy-files."""
    from collections import defaultdict
    # Acepta "carpeta" (JS 3.1) o "base_dir" (legacy)
    base_dir = payload.get("carpeta", payload.get("base_dir", ""))
    if not base_dir or not Path(base_dir).exists():
        return make_response(False, "NOT_FOUND", f"Directorio no encontrado: {base_dir}")

    archivos_lista = []
    for f in Path(base_dir).rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            archivos_lista.append({"name": f.name, "ext": f.suffix.lower(), "size": f.stat().st_size})
    if not archivos_lista:
        return make_response(False, "EMPTY", "Carpeta vacía.")

    # Agrupar por categoría legible
    CAT_MAP = {
        ".pdf":  "PDFs",  ".docx": "Documentos", ".doc": "Documentos",
        ".xlsx": "Hojas", ".xls":  "Hojas",       ".csv": "Hojas",
        ".jpg":  "Imágenes", ".jpeg":"Imágenes",  ".png":"Imágenes",
        ".gif":  "Imágenes", ".webp":"Imágenes",  ".bmp":"Imágenes",
        ".mp3":  "Audio",    ".wav": "Audio",      ".ogg":"Audio",
        ".mp4":  "Video",    ".avi": "Video",      ".mkv":"Video",
        ".zip":  "Comprimidos", ".rar":"Comprimidos", ".7z":"Comprimidos",
        ".py":   "Código",   ".js":  "Código",     ".html":"Código",
        ".json": "JSON",     ".txt": "Texto",      ".md":  "Texto",
    }
    grupos_dict = defaultdict(list)
    for f in archivos_lista:
        cat = CAT_MAP.get(f["ext"], "Otros")
        grupos_dict[cat].append(f["name"])

    grupos_out = []
    total_size = 0
    for nombre, archivos in grupos_dict.items():
        sz = sum(a["size"] for a in archivos_lista if a["name"] in archivos)
        total_size += sz
        grupos_out.append({
            "nombre":      nombre,
            "archivos":    archivos,
            "tamaño_total": f"{sz//1024} KB" if sz >= 1024 else f"{sz} B",
        })
    grupos_out.sort(key=lambda g: -len(g["archivos"]))

    destino_sugerido = str(Path(base_dir).parent / (Path(base_dir).name + "_ORGANIZADO_MAER"))
    return make_response(True, "ORG_OK", f"Sugerencia para {len(archivos_lista)} archivos.", {
        "grupos":            grupos_out,
        "total":             len(archivos_lista),
        "destino_sugerido":  destino_sugerido,
        "tamaño_total":      f"{total_size//1024} KB" if total_size >= 1024 else f"{total_size} B",
    })

def _sugerir_carpeta(ext):
    m = {".pdf":"Documentos/PDF",".docx":"Documentos/Word",".doc":"Documentos/Word",
         ".xlsx":"Documentos/Excel",".xls":"Documentos/Excel",".jpg":"Imagenes",
         ".jpeg":"Imagenes",".png":"Imagenes",".gif":"Imagenes",".mp4":"Videos",
         ".mp3":"Audio",".zip":"Archivos_Comprimidos",".py":"Codigo/Python",
         ".js":"Codigo/JavaScript",".txt":"Texto",".csv":"Datos",".json":"Datos/JSON"}
    return m.get(ext, f"Otros/{ext.lstrip('.').upper() or 'Sin_Extension'}")


@app.get("/api/backup")
async def api_backup():
    """Crea un respaldo de los archivos estáticos MAER en la carpeta respaldo_maer."""
    import shutil, zipfile
    from datetime import datetime
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    respaldo_dir = BASE_DIR / "respaldo_maer"
    respaldo_dir.mkdir(parents=True, exist_ok=True)
    zip_path    = respaldo_dir / f"maer_backup_{ts}.zip"
    dirs_to_backup = [
        BASE_DIR / "maer_backend" / "web_ui" / "static",
        BASE_DIR / "maer_backend" / "web_ui" / "server.py",
    ]
    try:
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for src in dirs_to_backup:
                if src.is_dir():
                    for f in src.rglob("*"):
                        if f.is_file() and not f.name.startswith("."):
                            zf.write(str(f), str(f.relative_to(BASE_DIR)))
                elif src.is_file():
                    zf.write(str(src), str(src.relative_to(BASE_DIR)))
        size = zip_path.stat().st_size
        return make_response(True, "BACKUP_OK", f"Respaldo creado: {zip_path.name}",
                             {"ruta": str(zip_path), "nombre": zip_path.name,
                              "tamaño": f"{size//1024} KB"})
    except Exception as e:
        return make_response(False, "BACKUP_ERR", str(e))


@app.post("/api/tasker-receive")
async def api_tasker_receive(payload: dict):
    """Endpoint para recibir mensajes desde Tasker/AutoRemote en Android."""
    # Acepta "mensaje" (JS 3.1) o "message" (legacy)
    mensaje   = payload.get("mensaje",   payload.get("message", ""))
    device    = payload.get("dispositivo", payload.get("device", "android"))
    fuente    = payload.get("fuente",    "tasker")
    timestamp = payload.get("timestamp", "")
    # Store message
    TASKER_LOG_FILE = UPLOAD_DIR.parent / "tasker_messages.json"
    try:
        import datetime as dt
        existing = json.loads(TASKER_LOG_FILE.read_text()) if TASKER_LOG_FILE.exists() else []
        existing.append({
            "id":       len(existing) + 1,
            "mensaje":  mensaje,
            "fuente":   fuente,
            "device":   device,
            "ts":       dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "leido":    False,
        })
        existing = existing[-100:]  # keep last 100
        TASKER_LOG_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    except Exception:
        pass
    # Process with LLM if possible
    reply = f"MAER recibido: {mensaje[:50]}"
    try:
        from maer_backend.maer_files import action_llm_chat
        r = action_llm_chat({"prompt": mensaje})
        if r.get("ok"): reply = r["data"]["response"][:500]
    except: pass
    return make_response(True, "TASKER_OK", "Mensaje recibido.", {"reply": reply})


@app.get("/api/tasker-messages")
async def api_tasker_messages():
    """Obtiene mensajes recibidos de Tasker (últimos 30)."""
    TASKER_LOG_FILE = UPLOAD_DIR.parent / "tasker_messages.json"
    try:
        msgs = json.loads(TASKER_LOG_FILE.read_text()) if TASKER_LOG_FILE.exists() else []
        # Marcar como leídos
        for m in msgs:
            m["leido"] = True
        TASKER_LOG_FILE.write_text(json.dumps(msgs, ensure_ascii=False, indent=2))
        return make_response(True, "OK", f"{len(msgs[-30:])} mensajes.", {"mensajes": msgs[-30:]})
    except Exception as e:
        return make_response(False, "ERR", str(e))


def main():
    host = os.environ.get("MAER_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("MAER_WEB_PORT", "8765"))
    print(f"🦁 MAER Dashboard iniciando en http://localhost:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
