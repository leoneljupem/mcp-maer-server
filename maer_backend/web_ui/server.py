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
from datetime import datetime, timezone

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


@app.get("/api/ngrok-url")
async def api_ngrok_url():
    """Devuelve la URL pública de ngrok si está activa."""
    url_file = Path(__file__).parent.parent.parent / ".maer_ngrok_url.txt"
    if url_file.exists():
        url = url_file.read_text().strip()
        if url:
            return make_response(True, "NGROK_OK", "Túnel ngrok activo", {"url": url})
    # Intentar obtenerla de pyngrok en tiempo real
    try:
        from pyngrok import ngrok
        tunnels = ngrok.get_tunnels()
        if tunnels:
            return make_response(True, "NGROK_OK", "Túnel activo", {"url": tunnels[0].public_url})
    except Exception:
        pass
    return make_response(False, "NGROK_OFF", "ngrok no activo — usa iniciar_maer_ngrok.py", {"url": None})


@app.get("/service-worker.js")
async def service_worker():
    """Sirve el service worker desde la raíz (necesario para el scope PWA)."""
    from fastapi.responses import FileResponse
    sw_path = STATIC_DIR / "service-worker.js"
    if sw_path.exists():
        return FileResponse(str(sw_path), media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/"})
    return {"error": "service-worker.js no encontrado"}


@app.get("/manifest.json")
async def manifest_json():
    """Sirve el manifest.json desde la raíz."""
    from fastapi.responses import FileResponse
    m_path = STATIC_DIR / "manifest.json"
    if m_path.exists():
        return FileResponse(str(m_path), media_type="application/manifest+json")
    return {"error": "manifest.json no encontrado"}


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



# ═══════════════════════════════════════════════════════════════════════════
# 🔬 NUEVOS ENDPOINTS REALES — MAER PODER (Fase 4)
# ═══════════════════════════════════════════════════════════════════════════

def _decodificar_curp(curp: str) -> dict:
    """Decodifica toda la información contenida en una CURP sin llamadas externas."""
    from maer_backend.maer_files import normalize_id
    curp = normalize_id(curp)
    if len(curp) < 18:
        return {"error": "CURP muy corta"}

    # Mapa de estados INEGI
    estados = {
        "AS":"Aguascalientes","BC":"Baja California","BS":"Baja California Sur",
        "CC":"Campeche","CL":"Coahuila","CM":"Colima","CS":"Chiapas",
        "CH":"Chihuahua","DF":"Ciudad de México","DG":"Durango","GT":"Guanajuato",
        "GR":"Guerrero","HG":"Hidalgo","JC":"Jalisco","MC":"Estado de México",
        "MN":"Michoacán","MS":"Morelos","NT":"Nayarit","NL":"Nuevo León",
        "OC":"Oaxaca","PL":"Puebla","QT":"Querétaro","QR":"Quintana Roo",
        "SP":"San Luis Potosí","SL":"Sinaloa","SR":"Sonora","TC":"Tabasco",
        "TS":"Tamaulipas","TL":"Tlaxcala","VZ":"Veracruz","YN":"Yucatán",
        "ZS":"Zacatecas","NE":"Nacido en el Extranjero",
    }
    try:
        letra1  = curp[0]
        vocal1  = curp[1]
        letra2  = curp[2]
        letra3  = curp[3]
        anio    = curp[4:6]
        mes     = curp[6:8]
        dia     = curp[8:10]
        sexo_c  = curp[10]
        estado_c= curp[11:13]
        sexo_desc = "Hombre" if sexo_c.upper() == "H" else "Mujer"
        estado_desc = estados.get(estado_c.upper(), estado_c)
        # Año completo — si > año actual short, es 1900s
        import datetime
        yr_short = int(anio)
        yr_full  = (1900 + yr_short) if yr_short >= 30 else (2000 + yr_short)
        try:
            fecha_nac = datetime.date(yr_full, int(mes), int(dia))
            hoy = datetime.date.today()
            edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            fecha_str = fecha_nac.strftime("%d/%m/%Y")
        except Exception:
            fecha_str = f"{dia}/{mes}/{yr_full}"
            edad = None

        return {
            "curp":          curp,
            "fecha_nacimiento": fecha_str,
            "edad":          edad,
            "sexo":          sexo_desc,
            "estado":        estado_desc,
            "codigo_estado": estado_c.upper(),
            "valida_formato": True,
        }
    except Exception as e:
        return {"error": str(e), "curp": curp}


@app.post("/api/analizar-documento")
async def api_analizar_documento(file: UploadFile = File(...)):
    """
    🔬 Análisis completo de cualquier documento:
    Extrae texto, detecta CURP/NSS/RFC/fechas/teléfonos,
    valida identidades, clasifica tipo de documento.
    Soporta: PDF, JPG, PNG, DOCX, TXT.
    """
    import re
    import tempfile
    from maer_backend.maer_files import (
        curp_valida, rfc_valido, normalize_id,
        CURP_REGEX_SEARCH, RFC_REGEX, NSS_REGEX, EMAIL_REGEX,
        extract_text_generic,
    )

    ext = Path(file.filename).suffix.lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    shutil.copyfileobj(file.file, tmp)
    tmp.close()
    tmp_path = Path(tmp.name)

    try:
        texto = ""

        # 1. Extraer texto según tipo
        if ext == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(str(tmp_path)) as pdf:
                    texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
            except Exception:
                pass
            if not texto.strip():
                texto = extract_text_generic(tmp_path, use_ocr_for_pdf=True)

        elif ext in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}:
            try:
                import pytesseract
                from PIL import Image as PILImage
                import cv2, numpy as np
                img = cv2.imread(str(tmp_path))
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    pil_img = PILImage.fromarray(thresh)
                    texto = pytesseract.image_to_string(pil_img, lang="spa+eng", config="--psm 3")
                else:
                    from PIL import Image as PILImage
                    pil_img = PILImage.open(str(tmp_path))
                    texto = pytesseract.image_to_string(pil_img, lang="spa+eng")
            except Exception as e:
                texto = f"[OCR error: {e}]"

        elif ext in {".docx", ".doc"}:
            texto = extract_text_generic(tmp_path)

        elif ext in {".txt", ".md", ".csv"}:
            texto = tmp_path.read_text("utf-8", errors="replace")

        else:
            texto = extract_text_generic(tmp_path)

        # 2. Detectar identificadores
        texto_upper = texto.upper()

        curps_raw = CURP_REGEX_SEARCH.findall(texto_upper)
        curps_validas = []
        for c in set(curps_raw):
            c_norm = normalize_id(c)
            valida = bool(curp_valida(c_norm))
            info = _decodificar_curp(c_norm)
            curps_validas.append({
                "curp": c_norm,
                "valida": valida,
                "info": info,
            })

        rfcs_raw = RFC_REGEX.findall(texto_upper)
        rfcs_validos = []
        for r in set(rfcs_raw):
            r_norm = normalize_id(r)
            valido = bool(rfc_valido(r_norm))
            rfcs_validos.append({"rfc": r_norm, "valido": valido})

        nss_matches = NSS_REGEX.findall(texto)
        nss_candidatos = list(set([n for n in nss_matches if len(n) == 11]))

        emails = list(set(EMAIL_REGEX.findall(texto)))

        # Detectar teléfonos MX (10 dígitos)
        tel_raw = re.findall(r'\b\d{10}\b', texto)
        telefonos = list(set(tel_raw))[:5]

        # Detectar semanas cotizadas IMSS
        semanas = []
        sem_patterns = [
            r'(?:semanas?\s+cotizadas?[:\s]+)(\d{2,4})',
            r'(\d{3,4})\s*(?:semanas?\s+cotizadas?)',
            r'SEMANAS\s+(?:RECONOCIDAS?|COTIZADAS?)[:\s]+(\d{2,4})',
        ]
        for pat in sem_patterns:
            found = re.findall(pat, texto, re.IGNORECASE)
            semanas.extend(found)
        semanas = list(set(semanas))

        # Detectar fechas
        fechas = re.findall(r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b', texto)
        fechas = list(set(fechas))[:10]

        # Detectar montos ($)
        montos = re.findall(r'\$\s*[\d,]+\.?\d*', texto)
        montos = list(set(montos))[:10]

        # Detectar salario
        salarios = re.findall(r'(?:salario|sueldo|sbc|salario\s+base)[:\s]+\$?\s*([\d,]+\.?\d*)',
                              texto, re.IGNORECASE)

        # 3. Clasificar tipo de documento
        texto_l = texto.lower()
        tipo_doc = "Documento General"
        if any(w in texto_l for w in ["instituto mexicano del seguro social", "imss", "número de seguridad social"]):
            if any(w in texto_l for w in ["semanas", "cotizad", "asegurado"]):
                tipo_doc = "📋 Constancia IMSS / Semanas Cotizadas"
            else:
                tipo_doc = "🏥 Documento IMSS"
        elif any(w in texto_l for w in ["servicio de administración tributaria", "sat ", "rfc:", "registro federal"]):
            tipo_doc = "💼 Documento SAT / Fiscal"
        elif any(w in texto_l for w in ["credencial para votar", "ine ", "instituto nacional electoral", "clave de elector"]):
            tipo_doc = "🪪 Credencial INE / IFE"
        elif any(w in texto_l for w in ["acta de nacimiento", "registro civil", "nacimiento"]):
            tipo_doc = "📜 Acta de Nacimiento"
        elif any(w in texto_l for w in ["curp", "clave única de registro"]):
            tipo_doc = "🆔 Documento CURP"
        elif any(w in texto_l for w in ["infonavit", "crédito hipotecario", "fovissste"]):
            tipo_doc = "🏠 Documento INFONAVIT/FOVISSSTE"
        elif any(w in texto_l for w in ["profedet", "secretaría del trabajo", "conciliación"]):
            tipo_doc = "⚖️ Documento PROFEDET / Laboral"
        elif any(w in texto_l for w in ["pensión", "jubilación", "retiro", "afore"]):
            tipo_doc = "🏛️ Documento de Pensión / Jubilación"
        elif ext in {".jpg", ".jpeg", ".png"}:
            tipo_doc = "🖼️ Imagen / Foto de Documento"

        # 4. Análisis de pensión IMSS si aplica
        pension_info = {}
        if semanas:
            max_sem = max(int(s.replace(",","")) for s in semanas if s.replace(",","").isdigit())
            ley = "Ley 97 (AFORE)" if max_sem >= 1250 else "Ley 73 o en transición"
            pension_info = {
                "semanas_detectadas": max_sem,
                "ley_aplicable": ley,
                "requisito_pension": 1250,
                "faltan_semanas": max(0, 1250 - max_sem),
                "porcentaje_completado": round(min(100, max_sem / 1250 * 100), 1),
            }

        return make_response(True, "ANALISIS_OK", f"Análisis completo: {file.filename}", {
            "archivo":       file.filename,
            "tipo_documento": tipo_doc,
            "texto_extraido": texto[:3000],
            "chars_total":   len(texto),
            "curps":         curps_validas,
            "rfcs":          rfcs_validos,
            "nss":           nss_candidatos[:5],
            "emails":        emails[:5],
            "telefonos":     telefonos,
            "semanas":       semanas,
            "fechas":        fechas,
            "montos":        montos[:5],
            "salarios":      salarios[:3],
            "pension_info":  pension_info,
        })

    except Exception as e:
        return make_response(False, "ANALISIS_ERROR", str(e))
    finally:
        try: os.unlink(str(tmp_path))
        except: pass


@app.post("/api/curp-decodificar")
async def api_curp_decodificar(payload: dict):
    """Decodifica y valida una CURP sin necesidad de APIs externas."""
    from maer_backend.maer_files import curp_valida, normalize_id
    curp = normalize_id(payload.get("curp", ""))
    if not curp:
        return make_response(False, "EMPTY", "CURP vacía")
    valida = bool(curp_valida(curp))
    info = _decodificar_curp(curp)
    info["valida"] = valida
    return make_response(valida, "CURP_OK" if valida else "CURP_INVALIDA",
                         f"CURP {'válida' if valida else 'inválida'}: {curp}", info)


@app.post("/api/buscar-duplicados")
async def api_buscar_duplicados(payload: dict):
    """
    Encuentra archivos DUPLICADOS (idénticos por contenido) en una carpeta.
    Agrupa por hash SHA-256. Funciona con cualquier tipo de archivo.
    """
    import hashlib
    from collections import defaultdict

    carpeta = payload.get("carpeta", "")
    if not carpeta or not Path(carpeta).exists():
        return make_response(False, "DIR_NOT_FOUND", f"Carpeta no encontrada: {carpeta}")

    hashes = defaultdict(list)
    total = 0
    errores = []

    try:
        for f in Path(carpeta).rglob("*"):
            if not f.is_file() or f.name.startswith("."):
                continue
            if total > 5000:
                break
            try:
                h = hashlib.sha256()
                with open(str(f), "rb") as fh:
                    for chunk in iter(lambda: fh.read(8192), b""):
                        h.update(chunk)
                hashes[h.hexdigest()].append({
                    "ruta": str(f),
                    "nombre": f.name,
                    "tamaño": f.stat().st_size,
                    "tamaño_fmt": f"{f.stat().st_size//1024} KB" if f.stat().st_size >= 1024 else f"{f.stat().st_size} B",
                })
                total += 1
            except Exception as e:
                errores.append(str(e))
    except Exception as e:
        return make_response(False, "SCAN_ERR", str(e))

    grupos_dup = [{"hash": h[:12]+"...", "archivos": files, "count": len(files)}
                  for h, files in hashes.items() if len(files) > 1]
    grupos_dup.sort(key=lambda g: -g["count"])

    archivos_dup_total = sum(len(g["archivos"]) - 1 for g in grupos_dup)
    espacio_recuperable = sum(
        (len(g["archivos"]) - 1) * g["archivos"][0]["tamaño"]
        for g in grupos_dup
    )

    return make_response(True, "DUPLICADOS_OK",
                         f"{len(grupos_dup)} grupos de duplicados · {archivos_dup_total} archivos redundantes",
                         {
                             "grupos": grupos_dup[:50],
                             "total_archivos": total,
                             "grupos_duplicados": len(grupos_dup),
                             "archivos_redundantes": archivos_dup_total,
                             "espacio_recuperable_bytes": espacio_recuperable,
                             "espacio_recuperable_fmt": f"{espacio_recuperable//1024//1024} MB" if espacio_recuperable >= 1024*1024 else f"{espacio_recuperable//1024} KB",
                             "errores": errores[:5],
                         })


@app.post("/api/imagenes-similares")
async def api_imagenes_similares(payload: dict):
    """
    Encuentra imágenes SIMILARES (no solo idénticas) usando perceptual hashing.
    Agrupa por similitud visual — útil para encontrar fotos duplicadas o variantes.
    """
    carpeta = payload.get("carpeta", "")
    umbral = int(payload.get("umbral", 8))  # 0=idéntico, >10=muy diferente

    if not carpeta or not Path(carpeta).exists():
        return make_response(False, "DIR_NOT_FOUND", f"Carpeta no encontrada: {carpeta}")

    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".gif"}

    try:
        import imagehash
        from PIL import Image as PILImage
        from collections import defaultdict

        hashes_img = []
        errores = []

        for f in Path(carpeta).rglob("*"):
            if not f.is_file() or f.suffix.lower() not in img_exts:
                continue
            if len(hashes_img) > 2000:
                break
            try:
                img = PILImage.open(str(f))
                h = imagehash.phash(img)
                hashes_img.append({"path": str(f), "nombre": f.name, "hash": h,
                                    "tamaño": f.stat().st_size})
                img.close()
            except Exception as e:
                errores.append(f"{f.name}: {e}")

        # Agrupar similares
        used = set()
        grupos = []
        for i, a in enumerate(hashes_img):
            if i in used:
                continue
            grupo = [a]
            used.add(i)
            for j, b in enumerate(hashes_img):
                if j <= i or j in used:
                    continue
                diff = a["hash"] - b["hash"]
                if diff <= umbral:
                    grupo.append(b)
                    used.add(j)
            if len(grupo) > 1:
                grupos.append({
                    "archivos": [
                        {"ruta": x["path"], "nombre": x["nombre"],
                         "tamaño": x["tamaño"],
                         "tamaño_fmt": f"{x['tamaño']//1024} KB"}
                        for x in grupo
                    ],
                    "count": len(grupo),
                })

        grupos.sort(key=lambda g: -g["count"])

        return make_response(True, "SIMILARES_OK",
                             f"{len(grupos)} grupos de imágenes similares en {len(hashes_img)} imágenes",
                             {
                                 "grupos": grupos[:30],
                                 "total_imagenes": len(hashes_img),
                                 "grupos_similares": len(grupos),
                                 "umbral_usado": umbral,
                                 "errores": errores[:5],
                             })
    except ImportError:
        return make_response(False, "IMAGEHASH_MISSING",
                             "Librería imagehash no disponible. Ejecuta: pip install imagehash")
    except Exception as e:
        return make_response(False, "SIMILARES_ERR", str(e))


@app.post("/api/ocr-imagen")
async def api_ocr_imagen(file: UploadFile = File(...)):
    """
    OCR potente: extrae TODO el texto de una imagen.
    Incluye preprocesamiento OpenCV para mejorar calidad.
    Funciona con fotos de documentos tomadas con celular.
    """
    ext = Path(file.filename).suffix.lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    shutil.copyfileobj(file.file, tmp)
    tmp.close()
    tmp_path = Path(tmp.name)

    try:
        import pytesseract
        import cv2, numpy as np
        from PIL import Image as PILImage

        # Preprocesamiento para mejorar OCR
        img_cv = cv2.imread(str(tmp_path))
        if img_cv is not None:
            # Convertir a escala de grises
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            # Ruido
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            # Umbral adaptativo
            thresh = cv2.adaptiveThreshold(denoised, 255,
                                           cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
            # Convertir a PIL
            pil_img = PILImage.fromarray(thresh)
        else:
            pil_img = PILImage.open(str(tmp_path)).convert("L")

        # OCR en español
        texto = pytesseract.image_to_string(pil_img, lang="spa+eng",
                                            config="--psm 3 --oem 3")

        # También detectar IDs en el texto
        from maer_backend.maer_files import CURP_REGEX_SEARCH, RFC_REGEX, NSS_REGEX
        texto_u = texto.upper()
        curps = list(set(CURP_REGEX_SEARCH.findall(texto_u)))
        rfcs  = list(set(RFC_REGEX.findall(texto_u)))
        nss   = list(set(m for m in NSS_REGEX.findall(texto) if len(m) == 11))

        return make_response(True, "OCR_OK", f"Texto extraído: {len(texto)} chars",
                             {"texto": texto, "chars": len(texto),
                              "curps": curps, "rfcs": rfcs, "nss": nss})

    except Exception as e:
        return make_response(False, "OCR_ERR", str(e))
    finally:
        try: os.unlink(str(tmp_path))
        except: pass


@app.post("/api/expediente-imss")
async def api_expediente_imss(payload: dict):
    """
    Analiza una carpeta y determina qué documentos de pensión IMSS tiene
    el usuario, cuáles faltan, y genera un resumen del expediente.
    """
    carpeta = payload.get("carpeta", "")
    if not carpeta or not Path(carpeta).exists():
        return make_response(False, "DIR_NOT_FOUND", f"Carpeta no encontrada: {carpeta}")

    documentos_requeridos = [
        {"id": "nss", "nombre": "Número de Seguridad Social (NSS)", "keywords": ["seguridad social", "nss", "afiliacion"], "urgencia": "🔴 Crítico"},
        {"id": "curp", "nombre": "CURP", "keywords": ["curp", "clave unica", "registro de poblacion"], "urgencia": "🔴 Crítico"},
        {"id": "acta", "nombre": "Acta de Nacimiento", "keywords": ["acta", "nacimiento", "registro civil"], "urgencia": "🔴 Crítico"},
        {"id": "ine", "nombre": "Identificación Oficial (INE/IFE/Pasaporte)", "keywords": ["elector", "ine", "ife", "pasaporte"], "urgencia": "🔴 Crítico"},
        {"id": "semanas", "nombre": "Constancia de Semanas Cotizadas IMSS", "keywords": ["semanas cotizadas", "constancia imss", "asegurado"], "urgencia": "🔴 Crítico"},
        {"id": "estado_cuenta", "nombre": "Estado de Cuenta AFORE", "keywords": ["afore", "estado de cuenta", "saldo"], "urgencia": "🟡 Importante"},
        {"id": "rfc", "nombre": "RFC y Constancia Fiscal SAT", "keywords": ["rfc", "sat", "fiscal", "constancia fiscal"], "urgencia": "🟡 Importante"},
        {"id": "comprobante", "nombre": "Comprobante de Domicilio", "keywords": ["domicilio", "cfe", "telmex", "predial"], "urgencia": "🟡 Importante"},
        {"id": "talones", "nombre": "Talones de Pago / Nómina", "keywords": ["nomina", "recibo de pago", "talon", "percepciones"], "urgencia": "🟠 Recomendado"},
        {"id": "infonavit", "nombre": "Estado de Cuenta INFONAVIT", "keywords": ["infonavit", "credito", "vivienda"], "urgencia": "🔵 Opcional"},
    ]

    # Escanear archivos
    archivos = []
    for f in Path(carpeta).rglob("*"):
        if f.is_file() and f.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".doc"}:
            archivos.append({"nombre": f.name, "ruta": str(f), "tamaño": f.stat().st_size})

    # Buscar matches por nombre
    encontrados = {}
    for doc in documentos_requeridos:
        for archivo in archivos:
            nombre_lower = archivo["nombre"].lower()
            if any(kw in nombre_lower for kw in doc["keywords"]):
                encontrados[doc["id"]] = archivo
                break

    # Resumen
    total_req = len(documentos_requeridos)
    total_ok  = len(encontrados)
    faltantes = [d for d in documentos_requeridos if d["id"] not in encontrados]
    criticos_faltantes = [d for d in faltantes if "Crítico" in d["urgencia"]]

    porcentaje = round(total_ok / total_req * 100)

    return make_response(True, "EXPEDIENTE_OK",
                         f"Expediente {porcentaje}% completo · {total_ok}/{total_req} documentos",
                         {
                             "porcentaje": porcentaje,
                             "total_archivos_carpeta": len(archivos),
                             "documentos_encontrados": total_ok,
                             "documentos_requeridos": total_req,
                             "encontrados": encontrados,
                             "faltantes": faltantes,
                             "criticos_faltantes": criticos_faltantes,
                             "archivos_escaneados": archivos[:30],
                         })


@app.post("/api/rfc-validar")
async def api_rfc_validar(payload: dict):
    """Valida un RFC con verificación de dígito verificador."""
    from maer_backend.maer_files import rfc_valido, normalize_id
    rfc = normalize_id(payload.get("rfc", ""))
    if not rfc:
        return make_response(False, "EMPTY", "RFC vacío")
    valido = bool(rfc_valido(rfc))
    tipo = "Persona Física" if len(rfc) == 13 else "Persona Moral" if len(rfc) == 12 else "Desconocido"
    return make_response(valido, "RFC_OK" if valido else "RFC_INVALIDO",
                         f"RFC {'válido' if valido else 'inválido'}: {rfc}",
                         {"rfc": rfc, "valido": valido, "tipo": tipo, "longitud": len(rfc)})


@app.post("/api/imss-consulta")
async def api_imss_consulta(payload: dict):
    """
    Intenta consultar semanas cotizadas en IMSS usando CURP + NSS.
    Decodifica la CURP localmente (sin API externa) y trata de contactar
    el portal de servicios digitales del IMSS.
    """
    curp = (payload.get("curp") or "").strip().upper()
    nss  = (payload.get("nss")  or "").strip()

    if not curp or len(curp) < 18:
        return make_response(False, "EMPTY", "CURP requerida")

    # 1. Decodificar CURP localmente
    estados = {
        "AS":"Aguascalientes","BC":"Baja California","BS":"Baja California Sur",
        "CM":"Campeche","CO":"Coahuila","CL":"Colima","CS":"Chiapas","CH":"Chihuahua",
        "DF":"Ciudad de México","DG":"Durango","GJ":"Guanajuato","GR":"Guerrero",
        "HG":"Hidalgo","JC":"Jalisco","MC":"Estado de México","MN":"Michoacán",
        "MS":"Morelos","NT":"Nayarit","NL":"Nuevo León","OC":"Oaxaca",
        "PL":"Puebla","QO":"Querétaro","QR":"Quintana Roo","SP":"San Luis Potosí",
        "SL":"Sinaloa","SO":"Sonora","TC":"Tabasco","TS":"Tamaulipas","TL":"Tlaxcala",
        "VZ":"Veracruz","YN":"Yucatán","ZS":"Zacatecas","NE":"Extranjero"
    }
    # Mapa estado CURP → subdelegación IMSS (primeros 2 dígitos del NSS)
    subdeleg_map = {
        "DF":"01","MC":"02","JC":"03","NL":"04","VZ":"05","PL":"06","GJ":"07",
        "CO":"08","SL":"09","SO":"10","CH":"11","TL":"12","HG":"13","OC":"14",
        "BC":"15","DG":"16","ZS":"17","MN":"18","GR":"19","YN":"20","SP":"21",
        "QO":"22","TC":"23","MS":"24","NT":"25","CS":"26","QR":"27","AS":"28",
        "BS":"29","TS":"30","CM":"31","CL":"32","NE":"97"
    }
    meses = ["","enero","febrero","marzo","abril","mayo","junio","julio",
             "agosto","septiembre","octubre","noviembre","diciembre"]
    try:
        a2   = int(curp[4:6])
        mm   = int(curp[6:8])
        dd   = int(curp[8:10])
        year = (2000 + a2) if a2 <= 25 else (1900 + a2)
        sexo_c = curp[10]
        ent_c  = curp[11:13]
        fecha  = f"{dd} de {meses[mm] if 1<=mm<=12 else mm} de {year}"
        from datetime import date
        hoy    = date.today()
        edad   = hoy.year - year - (1 if (hoy.month, hoy.day) < (mm, dd) else 0)
        sexo   = "Hombre" if sexo_c == "H" else "Mujer" if sexo_c == "M" else sexo_c
        estado_nombre = estados.get(ent_c, ent_c)
        subdeleg = subdeleg_map.get(ent_c, "?")
        curp_info = {
            "curp": curp, "valida": True,
            "fecha_nacimiento": fecha, "edad": edad,
            "sexo": sexo, "estado": estado_nombre,
            "año_nacimiento": year,
        }
    except Exception as e:
        curp_info = {"curp": curp, "valida": False, "error": str(e)}
        subdeleg  = "?"

    # 2. Decodificar NSS si se proporciona
    nss_info = None
    if nss and len(nss) >= 10:
        try:
            sub = nss[0:2]
            año_alta = int(nss[2:4])
            año_alta_full = (2000 + año_alta) if año_alta <= 30 else (1900 + año_alta)
            nss_info = {
                "nss": nss,
                "subdelegacion": sub,
                "año_alta_imss": año_alta_full,
                "estructura": f"{nss[0:2]}-{nss[2:4]}-{nss[4:9]}-{nss[9:11] if len(nss)>=11 else nss[9:]}",
            }
        except Exception:
            nss_info = {"nss": nss}

    # 3. Estimar NSS si no se proporcionó (solo los primeros 2 dígitos)
    nss_estimado = None
    if not nss:
        nss_estimado = {
            "subdelegacion_probable": subdeleg,
            "nota": f"El NSS de {estado_nombre} generalmente empieza con {subdeleg}. El número exacto lo asignó el IMSS al afiliarte.",
        }

    # 4. Intentar consulta de semanas en IMSS (best-effort, puede fallar por CAPTCHA)
    semanas_imss = None
    semanas_error = None
    if nss:
        try:
            import httpx
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://serviciosdigitales.imss.gob.mx/",
                "Origin":  "https://serviciosdigitales.imss.gob.mx",
            }
            # Endpoint público IMSS semanas cotizadas (sin CAPTCHA, solo lectura)
            url = "https://serviciosdigitales.imss.gob.mx/semanascotizadas-web/usuarios/ConsultaSemanas"
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.post(url, json={"curp": curp, "nss": nss}, headers=headers)
                if resp.status_code == 200:
                    rjson = resp.json()
                    semanas_imss = rjson.get("semanas") or rjson.get("semanasTotal") or rjson.get("numSemanas")
                    if semanas_imss is None and isinstance(rjson, dict):
                        # Buscar cualquier clave con "semana"
                        for k, v in rjson.items():
                            if "semana" in k.lower() and isinstance(v, (int, float, str)):
                                semanas_imss = int(v)
                                break
                else:
                    semanas_error = f"IMSS respondió {resp.status_code} — puede requerir CAPTCHA"
        except ImportError:
            semanas_error = "httpx no disponible — instala: pip install httpx"
        except Exception as e:
            semanas_error = f"Portal IMSS no alcanzable: {str(e)[:80]}"

    resultado = {
        "curp_info":       curp_info,
        "nss_info":        nss_info,
        "nss_estimado":    nss_estimado,
        "semanas_imss":    semanas_imss,
        "semanas_error":   semanas_error,
        "portal_imss_url": "https://serviciosdigitales.imss.gob.mx/gob.mx/IMSS/semanascotizadas",
        "subdeleg_curp":   subdeleg,
    }
    return make_response(True, "IMSS_OK", "Consulta procesada", resultado)


@app.post("/api/sinavid-consulta")
async def api_sinavid_consulta(payload: dict):
    """
    Consulta SINAVID (IMSS Sistema Nacional de Vigencia de Derechos).
    Intenta obtener derechos vigentes del asegurado.
    Endpoint: https://serviciosdigitales.imss.gob.mx/
    """
    curp = (payload.get("curp") or "").strip().upper()
    nss  = (payload.get("nss")  or "").strip()

    if not curp and not nss:
        return make_response(False, "EMPTY", "Se requiere CURP o NSS para consultar SINAVID")

    # Portal SINAVID oficial
    SINAVID_URL = "https://serviciosdigitales.imss.gob.mx/gob.mx/IMSS/vigencia_derechos"

    resultado = {
        "curp":         curp,
        "nss":          nss,
        "portal_url":   SINAVID_URL,
        "status":       "pendiente",
        "vigencia":     None,
        "derechos":     None,
        "error":        None,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }

    # Intento 1: API REST pública SINAVID (sin CAPTCHA — solo disponible si IMSS tiene servicio público)
    try:
        import httpx
        headers = {
            "User-Agent":  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept":      "application/json",
            "Referer":     "https://serviciosdigitales.imss.gob.mx/",
        }
        # Endpoint de vigencia de derechos
        endpoints_sinavid = [
            "https://serviciosdigitales.imss.gob.mx/sinavid-web/vigencia",
            "https://serviciosdigitales.imss.gob.mx/sinavid-web/derechos",
        ]
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            for ep in endpoints_sinavid:
                try:
                    body = {}
                    if curp: body["curp"] = curp
                    if nss:  body["nss"]  = nss
                    resp = await client.post(ep, json=body, headers=headers)
                    if resp.status_code == 200:
                        rj = resp.json()
                        resultado["status"]   = "encontrado"
                        resultado["vigencia"] = rj.get("vigente") or rj.get("tieneVigencia")
                        resultado["derechos"] = rj
                        break
                    elif resp.status_code in (401, 403):
                        resultado["error"] = "SINAVID requiere autenticación. Visita el portal oficial."
                        break
                except Exception:
                    continue
    except ImportError:
        resultado["error"] = "httpx no disponible"
    except Exception as e:
        resultado["error"] = str(e)[:120]

    if resultado["status"] == "pendiente" and not resultado["error"]:
        resultado["status"] = "requiere_portal"
        resultado["error"]  = (
            "SINAVID requiere CAPTCHA o autenticación en el portal. "
            "Haz clic en 'Abrir portal SINAVID' para verificar manualmente con tu CURP/NSS."
        )

    # Instrucciones para el usuario
    pasos_manuales = [
        f"1. Abre: {SINAVID_URL}",
        "2. Selecciona 'Vigencia de Derechos'",
        f"3. Ingresa CURP: {curp or '(tu CURP)'}",
        f"4. Ingresa NSS: {nss or '(tu NSS)'}",
        "5. Resuelve el CAPTCHA y haz clic en Consultar",
    ]

    resultado["pasos_manuales"] = pasos_manuales
    return make_response(True, "SINAVID_OK", "Consulta SINAVID procesada", resultado)


@app.post("/api/exportar-pdf")
async def api_exportar_pdf(payload: dict):
    """
    Exporta un expediente IMSS completo a PDF profesional usando reportlab.
    Incluye: tarjeta CURP, semanas cotizadas, checklist de documentos, recomendaciones.
    """
    curp     = (payload.get("curp")     or "").strip().upper()
    nss      = (payload.get("nss")      or "").strip()
    nombre   = (payload.get("nombre")   or "Asegurado MAER").strip()
    semanas  = payload.get("semanas")
    ley      = payload.get("ley", "Verificar")
    docs     = payload.get("documentos", {})   # dict {id: {nombre, ruta}}
    faltantes = payload.get("faltantes", [])
    notas    = payload.get("notas", "")

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import tempfile, io

        buf = io.BytesIO()
        doc_pdf = SimpleDocTemplate(buf, pagesize=letter,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        # Colores IMSS
        IMSS_VERDE  = colors.HexColor("#00703c")
        IMSS_GRIS   = colors.HexColor("#4a4a4a")
        IMSS_CLARO  = colors.HexColor("#e8f5ee")
        GOLD        = colors.HexColor("#c8a415")

        titulo_style = ParagraphStyle("Titulo", parent=styles["Title"],
                                      textColor=IMSS_VERDE, fontSize=18, spaceAfter=6,
                                      alignment=TA_CENTER)
        sub_style    = ParagraphStyle("Sub", parent=styles["Normal"],
                                      textColor=IMSS_GRIS, fontSize=10,
                                      alignment=TA_CENTER, spaceAfter=2)
        h2_style     = ParagraphStyle("H2", parent=styles["Heading2"],
                                      textColor=IMSS_VERDE, fontSize=13, spaceBefore=12, spaceAfter=4)
        body_style   = ParagraphStyle("Body", parent=styles["Normal"],
                                      fontSize=9.5, leading=14, spaceAfter=4)
        label_style  = ParagraphStyle("Label", parent=styles["Normal"],
                                      fontSize=8.5, textColor=IMSS_GRIS, leading=12)

        fecha_hoy = datetime.now().strftime("%d de %B de %Y")
        story = []

        # ── ENCABEZADO ──
        story.append(Paragraph("🦁 MAER — Expediente de Pensión IMSS", titulo_style))
        story.append(Paragraph(f"Generado el {fecha_hoy} · Uso informativo · No oficial", sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=IMSS_VERDE, spaceAfter=10))

        # ── DATOS DEL ASEGURADO ──
        story.append(Paragraph("Datos del Asegurado", h2_style))
        datos_tabla = [
            ["Campo", "Valor"],
            ["Nombre / Referencia", nombre or "—"],
            ["CURP", curp or "—"],
            ["NSS", nss or "—"],
            ["Ley Aplicable", ley or "—"],
            ["Semanas Cotizadas (estimadas)", str(semanas) if semanas is not None else "No consultadas"],
        ]
        t = Table(datos_tabla, colWidths=[5*cm, 11*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0),  IMSS_VERDE),
            ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
            ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [IMSS_CLARO, colors.white]),
            ("GRID",         (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("PADDING",      (0,0), (-1,-1), 5),
        ]))
        story.append(t)

        # ── SEMANAS Y PROGRESO ──
        if semanas is not None:
            story.append(Spacer(1, 12))
            story.append(Paragraph("Progreso de Semanas Cotizadas", h2_style))
            sem_int   = int(semanas) if semanas else 0
            meta_500  = min(sem_int, 500)
            meta_1250 = min(sem_int, 1250)
            progreso_500  = round(meta_500 / 500 * 100)
            progreso_1250 = round(meta_1250 / 1250 * 100)
            barras = [
                ["Meta", "Semanas requeridas", "Tus semanas", "Progreso", "Estado"],
                ["Ley 73 — Mínimo",    "500",  str(sem_int), f"{progreso_500}%",
                 "✅ Cumplida" if sem_int >= 500  else f"Faltan {500-sem_int}"],
                ["Cesantía/Vejez",     "1,250", str(sem_int), f"{progreso_1250}%",
                 "✅ Cumplida" if sem_int >= 1250 else f"Faltan {1250-sem_int}"],
                ["Pensión plena (ref)","1,750", str(sem_int),
                 f"{round(min(sem_int,1750)/1750*100)}%",
                 "✅ Cumplida" if sem_int >= 1750 else f"Faltan {1750-sem_int}"],
            ]
            tb = Table(barras, colWidths=[3.5*cm, 3.5*cm, 3*cm, 2.5*cm, 4*cm])
            tb.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0),  IMSS_VERDE),
                ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
                ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 8.5),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [IMSS_CLARO, colors.white]),
                ("GRID",          (0,0),(-1,-1),  0.4, colors.lightgrey),
                ("PADDING",       (0,0),(-1,-1),  4),
                ("ALIGN",         (1,0),(-1,-1),  "CENTER"),
            ]))
            story.append(tb)

        # ── CHECKLIST DE DOCUMENTOS ──
        story.append(Spacer(1, 12))
        story.append(Paragraph("Checklist de Documentos para Pensión", h2_style))
        docs_req = [
            ("NSS",         "Número de Seguridad Social",             "🔴 Crítico"),
            ("curp",        "CURP",                                    "🔴 Crítico"),
            ("acta",        "Acta de Nacimiento",                      "🔴 Crítico"),
            ("ine",         "Identificación Oficial (INE/Pasaporte)",   "🔴 Crítico"),
            ("semanas",     "Constancia de Semanas IMSS",              "🔴 Crítico"),
            ("estado_cuenta","Estado de Cuenta AFORE",                 "🟡 Importante"),
            ("rfc",         "RFC y Constancia Fiscal SAT",             "🟡 Importante"),
            ("comprobante", "Comprobante de Domicilio",                "🟡 Importante"),
            ("talones",     "Talones de Pago / Nómina",                "🟠 Recomendado"),
            ("infonavit",   "Estado de Cuenta INFONAVIT",              "🔵 Opcional"),
        ]
        ids_faltantes = {f.get("id") for f in faltantes} if faltantes else set()
        check_rows = [["Estado", "Documento", "Prioridad"]]
        for did, dnom, durge in docs_req:
            if did in docs:
                estado = "✅ Encontrado"
                color_fila = colors.HexColor("#e8f5ee")
            elif did in ids_faltantes:
                estado = "❌ Faltante"
                color_fila = colors.HexColor("#fff0f0")
            else:
                estado = "⬜ No verificado"
                color_fila = colors.white
            check_rows.append([estado, dnom, durge])

        tc = Table(check_rows, colWidths=[3*cm, 9*cm, 4.5*cm])
        tc.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  IMSS_VERDE),
            ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 8.5),
            ("GRID",          (0,0), (-1,-1), 0.3, colors.lightgrey),
            ("PADDING",       (0,0), (-1,-1), 4),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.HexColor("#e8f5ee"), colors.white]),
        ]))
        story.append(tc)

        # ── RECOMENDACIONES ──
        story.append(Spacer(1, 12))
        story.append(Paragraph("Recomendaciones MAER", h2_style))
        recs = [
            "Verifica tus semanas cotizadas en el portal IMSS (serviciosdigitales.imss.gob.mx) o en tu AFORE.",
            "Si cumples 500 semanas bajo Ley 73, tienes derecho a pensión por cesantía/vejez.",
            "Conserva todos los documentos originales y digitalizados en un lugar seguro.",
            "Solicita tu Resolución de Semanas en cualquier subdelegación IMSS con CURP + NSS.",
            "Si tienes dudas, acude al IMSS más cercano o al Centro de Orientación al Derechohabiente (COD).",
        ]
        if notas:
            story.append(Paragraph(f"<b>Notas adicionales:</b> {notas}", body_style))
        for r in recs:
            story.append(Paragraph(f"• {r}", body_style))

        # ── PIE ──
        story.append(Spacer(1, 18))
        story.append(HRFlowable(width="100%", thickness=1, color=IMSS_GRIS))
        story.append(Paragraph(
            f"<font color='grey' size='8'>MAER 4.0 — Sistema de Asistencia para Expedientes de Retiro · "
            f"{fecha_hoy} · Este documento es informativo y no tiene validez oficial ante el IMSS.</font>",
            ParagraphStyle("Pie", parent=styles["Normal"], alignment=TA_CENTER, fontSize=7.5)
        ))

        doc_pdf.build(story)
        pdf_bytes = buf.getvalue()

        # Guardar en carpeta de trabajo
        out_dir  = Path("/sessions/modest-upbeat-thompson/mnt/mcp-maer-server")
        pdf_name = f"expediente_imss_{curp or 'maer'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = out_dir / pdf_name
        pdf_path.write_bytes(pdf_bytes)

        return make_response(True, "PDF_OK", f"PDF generado: {pdf_name}",
                             {"pdf_path": str(pdf_path), "pdf_nombre": pdf_name,
                              "pdf_size_kb": round(len(pdf_bytes)/1024, 1)})

    except ImportError as e:
        return make_response(False, "REPORTLAB_MISSING",
                             f"reportlab no instalado: pip install reportlab — {e}")
    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        return make_response(False, "PDF_ERROR", f"Error al generar PDF: {e}")


@app.post("/api/imss-selenium")
async def api_imss_selenium(payload: dict):
    """
    Intenta consultar semanas cotizadas automatizando el portal IMSS con Selenium.
    Requiere Chrome instalado. Intenta sin CAPTCHA primero; si hay CAPTCHA, devuelve
    instrucciones y el campo de la URL para completar manualmente.
    """
    curp = (payload.get("curp") or "").strip().upper()
    nss  = (payload.get("nss")  or "").strip()

    if not curp or not nss:
        return make_response(False, "EMPTY", "CURP y NSS requeridos para consulta Selenium")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        import time

        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,900")
        opts.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")

        try:
            svc = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=svc, options=opts)
        except Exception as e_drv:
            return make_response(False, "WEBDRIVER_ERROR",
                                 f"ChromeDriver no disponible: {e_drv}. "
                                 "Instala Chrome en tu equipo.", {
                "instrucciones": [
                    "1. Instala Google Chrome en tu equipo",
                    "2. Reinicia el servidor MAER",
                    "3. Intenta nuevamente la consulta automática"
                ],
                "portal_manual": "https://serviciosdigitales.imss.gob.mx/gob.mx/IMSS/semanascotizadas"
            })

        PORTAL = "https://serviciosdigitales.imss.gob.mx/gob.mx/IMSS/semanascotizadas"
        semanas_encontradas = None
        captcha_detectado   = False
        error_msg           = None
        screenshot_b64      = None

        try:
            driver.get(PORTAL)
            time.sleep(3)

            # Detectar CAPTCHA
            page_src = driver.page_source.lower()
            if "captcha" in page_src or "recaptcha" in page_src:
                captcha_detectado = True
            else:
                wait = WebDriverWait(driver, 10)
                # Intentar llenar CURP
                try:
                    campo_curp = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[name*='curp'], input[id*='curp'], input[placeholder*='CURP']")
                    ))
                    campo_curp.clear()
                    campo_curp.send_keys(curp)
                    time.sleep(0.5)
                except Exception:
                    pass

                # Intentar llenar NSS
                try:
                    campo_nss = driver.find_element(By.CSS_SELECTOR,
                        "input[name*='nss'], input[id*='nss'], input[placeholder*='NSS'], input[placeholder*='seguridad']")
                    campo_nss.clear()
                    campo_nss.send_keys(nss)
                    time.sleep(0.5)
                except Exception:
                    pass

                # Intentar click en botón consultar
                try:
                    btn = driver.find_element(By.CSS_SELECTOR,
                        "button[type='submit'], input[type='submit'], button:contains('Consultar')")
                    btn.click()
                    time.sleep(3)
                except Exception:
                    pass

                # Buscar semanas en resultado
                result_text = driver.page_source
                import re as _re
                m = _re.search(r'(\d{3,4})\s*semanas?\s*cotizadas?', result_text, _re.IGNORECASE)
                if not m:
                    m = _re.search(r'semanasTotal["\s:]+(\d+)', result_text)
                if m:
                    semanas_encontradas = int(m.group(1))

                # Screenshot (base64)
                try:
                    import base64
                    screenshot_b64 = base64.b64encode(driver.get_screenshot_as_png()).decode()
                except Exception:
                    pass

        except Exception as e:
            error_msg = str(e)[:120]
        finally:
            try:
                driver.quit()
            except Exception:
                pass

        resultado = {
            "curp":                curp,
            "nss":                 nss,
            "semanas_encontradas": semanas_encontradas,
            "captcha_detectado":   captcha_detectado,
            "error":               error_msg,
            "portal_url":          PORTAL,
            "screenshot_b64":      screenshot_b64,
        }

        if semanas_encontradas:
            msg = f"✅ Semanas encontradas automáticamente: {semanas_encontradas}"
        elif captcha_detectado:
            msg = "CAPTCHA detectado — consulta manual requerida en el portal IMSS"
        else:
            msg = "Consulta procesada — verifica resultados en el portal"

        return make_response(True, "SELENIUM_OK", msg, resultado)

    except ImportError as e:
        return make_response(False, "SELENIUM_MISSING",
                             f"Selenium no instalado: pip install selenium webdriver-manager — {e}",
                             {"portal_manual": "https://serviciosdigitales.imss.gob.mx/gob.mx/IMSS/semanascotizadas"})
    except Exception as e:
        return make_response(False, "SELENIUM_ERROR", f"Error Selenium: {e}")


@app.get("/api/verificar-dependencias")
async def api_verificar_dependencias():
    """Verifica todas las dependencias críticas de MAER (Python, Java, Conda, etc.)."""
    import shutil, subprocess
    result = {}

    # Python packages
    py_pkgs = [
        "fastapi", "uvicorn", "pypdf", "docx", "PIL", "pytesseract",
        "cv2", "deskew", "fitz", "reportlab", "selenium", "httpx",
        "pandas", "numpy", "requests", "dotenv"
    ]
    py_ok = {}
    for pkg in py_pkgs:
        try:
            __import__(pkg.replace("docx", "docx").replace("PIL", "PIL"))
            py_ok[pkg] = True
        except ImportError:
            py_ok[pkg] = False

    # Tesseract OCR
    tess_bin = shutil.which("tesseract")
    result["tesseract_bin"]  = bool(tess_bin)
    result["tesseract_path"] = tess_bin

    # Java
    java_ok = False
    java_ver = None
    try:
        r = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5)
        java_ok  = r.returncode == 0
        java_ver = (r.stderr or r.stdout or "").split("\n")[0]
    except Exception:
        pass
    result["java"] = java_ok
    result["java_version"] = java_ver

    # Conda
    conda_bin = shutil.which("conda")
    result["conda"] = bool(conda_bin)
    result["conda_path"] = conda_bin

    # Ollama (LLM local)
    ollama_ok = False
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        ollama_ok = True
    except Exception:
        pass
    result["ollama"] = ollama_ok

    # Google Chrome
    chrome_paths = [
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium-browser"),
        shutil.which("chromium"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    result["chrome"] = any(p and Path(p).exists() for p in chrome_paths)

    # PDF tools
    result["poppler_pdftoppm"] = bool(shutil.which("pdftoppm"))
    result["ghostscript"]      = bool(shutil.which("gs"))

    result["python_packages"]  = py_ok
    result["timestamp"]        = datetime.now(timezone.utc).isoformat()

    # Resumen
    total_py  = len(py_ok)
    ok_py     = sum(1 for v in py_ok.values() if v)
    criticos  = ["fastapi", "uvicorn", "pypdf", "pytesseract", "PIL"]
    ok_crit   = all(py_ok.get(p) for p in criticos)

    # ── Paquetes adicionales de ciencia de datos ──
    ciencia_pkgs = ["pandas", "numpy", "scipy", "sklearn", "matplotlib",
                    "seaborn", "openpyxl", "pdfplumber", "xlrd"]
    ciencia_ok = {}
    for pkg in ciencia_pkgs:
        try:
            mod = __import__(pkg.replace("sklearn","sklearn"))
            ver = getattr(mod, "__version__", "OK")
            ciencia_ok[pkg] = {"ok": True, "version": ver}
        except ImportError:
            ciencia_ok[pkg] = {"ok": False, "version": None}
    result["ciencia_datos"] = ciencia_ok

    # ── Conda — rutas comunes macOS/Linux ──
    conda_rutas = [
        shutil.which("conda"),
        "/opt/homebrew/bin/conda",
        "/usr/local/bin/conda",
        str(Path.home() / "miniconda3" / "bin" / "conda"),
        str(Path.home() / "anaconda3" / "bin" / "conda"),
        str(Path.home() / "mambaforge" / "bin" / "conda"),
        str(Path.home() / ".conda" / "bin" / "conda"),
    ]
    conda_bin = next((r for r in conda_rutas if r and Path(r).exists()), None)
    conda_envs = []
    if conda_bin:
        try:
            r = subprocess.run([conda_bin, "env", "list", "--json"],
                               capture_output=True, text=True, timeout=10)
            envs_data = json.loads(r.stdout)
            conda_envs = [Path(e).name for e in envs_data.get("envs", [])]
        except Exception:
            pass
    result["conda"] = bool(conda_bin)
    result["conda_path"] = conda_bin
    result["conda_envs"] = conda_envs

    # ── Ollama — detección avanzada ──
    try:
        from maer_backend.maer_ollama import estado_completo as _oll_estado
        oll = _oll_estado()
        result["ollama"] = oll["servidor_activo"]
        result["ollama_instalado"] = oll["instalado"]
        result["ollama_bin"] = oll["bin_path"]
        result["ollama_version"] = oll["version"]
        result["ollama_modelos"] = oll["modelos"]
        result["ollama_modelo_activo"] = oll["modelo_elegido"]
    except Exception:
        result["ollama"] = False
        result["ollama_modelos"] = []

    # ── Resumen actualizado ──
    py_paquetes_extra = {pkg: ciencia_ok[pkg]["ok"] for pkg in ciencia_pkgs}
    py_ok.update(py_paquetes_extra)
    total_py  = len(py_ok)
    ok_py     = sum(1 for v in py_ok.values() if (v if isinstance(v, bool) else v))
    criticos  = ["fastapi", "uvicorn"]
    ok_crit   = all(py_ok.get(p) for p in criticos)

    result["python_packages"] = py_ok
    result["timestamp"]       = datetime.now(timezone.utc).isoformat()

    return make_response(True, "DEPS_OK",
                         f"Dependencias: {ok_py}/{total_py} paquetes OK · "
                         f"{'Sistema completo ✅' if ok_crit else 'Faltan críticos ⚠️'} · "
                         f"Conda: {'✅' if conda_bin else '❌'} · "
                         f"Ollama: {'✅ ' + (result.get('ollama_modelo_activo') or '') if result.get('ollama') else '❌'}",
                         result)


# ─── Ollama: listar modelos ───────────────────────────────────────────────────
@app.get("/api/ollama-modelos")
async def api_ollama_modelos():
    """Lista todos los modelos Ollama instalados con detección automática."""
    try:
        from maer_backend.maer_ollama import estado_completo
        estado = estado_completo()
        total = estado["total_modelos"]
        elegido = estado["modelo_elegido"]
        return make_response(
            True, "OLLAMA_OK" if estado["servidor_activo"] else "OLLAMA_OFFLINE",
            f"{'Servidor activo' if estado['servidor_activo'] else 'Servidor inactivo'} · "
            f"{total} modelo(s) · Usando: {elegido or 'Ninguno'}",
            estado
        )
    except Exception as e:
        return make_response(False, "OLLAMA_ERR", f"Error detectando Ollama: {e}", {})


@app.post("/api/ollama-pull")
async def api_ollama_pull(payload: dict):
    """Descarga un modelo de Ollama. Body: {model: 'llama3.2'}"""
    model = payload.get("model", "").strip()
    if not model:
        return make_response(False, "NO_MODEL", "Se requiere el campo 'model'")
    try:
        from maer_backend.maer_ollama import pull_modelo
        ok, msg = pull_modelo(model)
        return make_response(ok, "PULL_OK" if ok else "PULL_ERR", msg, {"model": model})
    except Exception as e:
        return make_response(False, "PULL_FAIL", str(e))


# ─── Conda: listar entornos ───────────────────────────────────────────────────
@app.get("/api/conda-envs")
async def api_conda_envs():
    """Lista los entornos Conda disponibles con detección en rutas comunes."""
    import shutil, subprocess, json as _json
    rutas = [
        shutil.which("conda"),
        "/opt/homebrew/bin/conda",
        "/usr/local/bin/conda",
        str(Path.home() / "miniconda3" / "bin" / "conda"),
        str(Path.home() / "anaconda3" / "bin" / "conda"),
        str(Path.home() / "mambaforge" / "bin" / "conda"),
    ]
    conda_bin = next((r for r in rutas if r and Path(r).exists()), None)
    if not conda_bin:
        return make_response(False, "CONDA_NA", "Conda no encontrado. Instala desde conda.io", {"envs": []})

    try:
        r = subprocess.run([conda_bin, "env", "list", "--json"],
                           capture_output=True, text=True, timeout=15)
        data = _json.loads(r.stdout)
        envs = data.get("envs", [])
        envs_info = []
        for env_path in envs:
            p = Path(env_path)
            py_bin = p / "bin" / "python"
            py_ver = None
            if py_bin.exists():
                try:
                    rv = subprocess.run([str(py_bin), "--version"],
                                        capture_output=True, text=True, timeout=5)
                    py_ver = (rv.stdout or rv.stderr).strip()
                except Exception:
                    pass
            envs_info.append({
                "name":    p.name,
                "path":    str(env_path),
                "python":  py_ver,
                "activo":  str(env_path) == os.environ.get("CONDA_PREFIX", ""),
            })
        ver_r = subprocess.run([conda_bin, "--version"],
                               capture_output=True, text=True, timeout=5)
        return make_response(True, "CONDA_OK",
                             f"Conda encontrado · {len(envs_info)} entorno(s)",
                             {"conda_version": ver_r.stdout.strip(), "conda_path": conda_bin,
                              "envs": envs_info})
    except Exception as e:
        return make_response(False, "CONDA_ERR", f"Error al listar entornos: {e}", {})


# ─── Pandas: analizar datos CSV/XLSX ─────────────────────────────────────────
@app.post("/api/analizar-datos")
async def api_analizar_datos(payload: dict):
    """
    Análisis de datos con Pandas/NumPy para archivos CSV, XLSX, TSV.
    Body: {"path": "/ruta/archivo.csv", "operacion": "describe|head|correlacion|nulos|tipos|todo"}
    """
    ruta = payload.get("path", "").strip()
    operacion = payload.get("operacion", "todo").lower()
    max_filas = int(payload.get("max_filas", 5000))

    if not ruta:
        return make_response(False, "NO_PATH", "Se requiere 'path' del archivo")

    file_path = Path(ruta)
    if not file_path.exists():
        return make_response(False, "NOT_FOUND", f"Archivo no encontrado: {ruta}")

    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        return make_response(False, "PANDAS_NA",
                             "Pandas no instalado. Ejecuta: pip install pandas openpyxl")

    try:
        ext = file_path.suffix.lower()
        if ext in (".xlsx", ".xls", ".xlsm"):
            df = pd.read_excel(file_path, nrows=max_filas)
        elif ext == ".tsv":
            df = pd.read_csv(file_path, sep="\t", nrows=max_filas, encoding="utf-8-sig")
        elif ext in (".csv", ".txt"):
            # Detectar separador automáticamente
            sample = file_path.read_text(encoding="utf-8-sig", errors="ignore")[:2000]
            sep = "," if sample.count(",") > sample.count(";") else ";"
            df = pd.read_csv(file_path, sep=sep, nrows=max_filas, encoding="utf-8-sig")
        else:
            return make_response(False, "FORMAT_NA",
                                 f"Formato '{ext}' no soportado. Usa: CSV, XLSX, TSV")

        resultado = {
            "archivo": file_path.name,
            "filas":   int(len(df)),
            "columnas": int(len(df.columns)),
            "columnas_nombre": list(df.columns),
        }

        if operacion in ("tipos", "todo"):
            resultado["tipos"] = {c: str(t) for c, t in df.dtypes.items()}

        if operacion in ("head", "todo"):
            resultado["primeras_filas"] = df.head(5).fillna("").to_dict(orient="records")

        if operacion in ("describe", "todo"):
            desc = df.describe(include="all").fillna("").to_dict()
            resultado["estadisticas"] = {
                col: {k: (float(v) if isinstance(v, (int, float, np.integer, np.floating)) else str(v))
                      for k, v in stats.items()}
                for col, stats in desc.items()
            }

        if operacion in ("nulos", "todo"):
            nulos = df.isnull().sum()
            resultado["nulos"] = {
                "por_columna": {c: int(n) for c, n in nulos.items()},
                "total": int(nulos.sum()),
                "porcentaje": round(float(nulos.sum()) / max(len(df) * len(df.columns), 1) * 100, 2),
            }

        if operacion in ("correlacion", "todo"):
            try:
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if len(num_cols) >= 2:
                    corr = df[num_cols].corr().round(3).fillna(0).to_dict()
                    resultado["correlacion"] = {
                        c: {k: float(v) for k, v in vals.items()}
                        for c, vals in corr.items()
                    }
                    # Top correlaciones
                    pares = []
                    corr_df = df[num_cols].corr()
                    for i, c1 in enumerate(num_cols):
                        for c2 in num_cols[i+1:]:
                            val = corr_df.loc[c1, c2]
                            if not np.isnan(val):
                                pares.append({"col1": c1, "col2": c2, "r": round(float(val), 3)})
                    pares.sort(key=lambda x: abs(x["r"]), reverse=True)
                    resultado["top_correlaciones"] = pares[:10]
            except Exception as ec:
                resultado["correlacion_error"] = str(ec)

        if operacion == "todo":
            # Detección de posibles columnas IMSS
            imss_cols = {}
            for col in df.columns:
                col_l = col.lower()
                if any(k in col_l for k in ["curp", "nss", "rfc", "semana", "salario", "sbc"]):
                    sample_vals = df[col].dropna().head(3).tolist()
                    imss_cols[col] = [str(v) for v in sample_vals]
            if imss_cols:
                resultado["columnas_imss_detectadas"] = imss_cols

        return make_response(True, "DATOS_OK",
                             f"Análisis completado: {resultado['filas']} filas × {resultado['columnas']} columnas",
                             resultado)

    except Exception as e:
        import traceback
        return make_response(False, "ANALISIS_ERR", f"Error analizando datos: {e}",
                             {"traceback": traceback.format_exc()[-500:]})


# ─── Test runner rápido ───────────────────────────────────────────────────────
@app.get("/api/test-run")
async def api_test_run(suite: str = "basico"):
    """
    Ejecuta la suite de pruebas de MAER.
    Parámetros: suite=basico|completo|endpoints|ollama|pandas
    """
    try:
        import subprocess as _sp
        tester_path = BASE_DIR / "maer_tester.py"
        if not tester_path.exists():
            return make_response(False, "TESTER_NA",
                                 "maer_tester.py no encontrado. Créalo primero.")
        r = _sp.run(
            [sys.executable, str(tester_path), f"--suite={suite}"],
            capture_output=True, text=True, timeout=120,
            cwd=str(BASE_DIR)
        )
        lineas = (r.stdout + r.stderr).splitlines()
        # Extraer resumen final
        resumen = [l for l in lineas if any(k in l for k in ["✅","❌","⚠️","PASS","FAIL","ERROR","Total"])]
        return make_response(
            r.returncode == 0, "TEST_PASS" if r.returncode == 0 else "TEST_FAIL",
            f"Suite '{suite}' completada",
            {"salida": lineas[-50:], "resumen": resumen, "returncode": r.returncode}
        )
    except Exception as e:
        return make_response(False, "TEST_ERR", str(e))


def main():
    host = os.environ.get("MAER_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("MAER_WEB_PORT", "8765"))
    print(f"🦁 MAER Dashboard iniciando en http://localhost:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
