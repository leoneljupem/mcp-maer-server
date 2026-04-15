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

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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

# Directorio de archivos estáticos
STATIC_DIR = Path(__file__).parent / "static"
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
    files = payload.get("files", [])
    destination = payload.get("destination", "").strip()
    create_dest = payload.get("create_dest", True)
    moved, errors = [], []
    if not destination:
        return make_response(False, "NO_DEST", "Se requiere carpeta destino.")
    dest_path = Path(destination)
    if create_dest:
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
    return make_response(len(errors) == 0, "MOVE_OK", f"{len(moved)} archivos movidos.", {"moved": moved, "errors": errors})


@app.post("/api/copy-files")
async def api_copy_files(payload: dict):
    """Copia archivos a una carpeta destino (para organización segura)."""
    import shutil
    files = payload.get("files", [])
    destination = payload.get("destination", "").strip()
    copied, errors = [], []
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
            shutil.copy2(str(src), str(dest_path / src.name))
            copied.append(str(dest_path / src.name))
        except Exception as e:
            errors.append(f"{src.name}: {e}")
    return make_response(len(errors) == 0, "COPY_OK", f"{len(copied)} archivos copiados.", {"copied": copied, "errors": errors})


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


@app.post("/api/busqueda-masiva")
async def api_busqueda_masiva(payload: dict):
    """Búsqueda masiva por contenido en directorio, filtrando por tipo."""
    import fnmatch
    base_dir = payload.get("base_dir", ".")
    query = payload.get("query", "").lower()
    tipos = payload.get("tipos", [])  # ["pdf","txt","jpg","docx","xlsx"]
    max_results = payload.get("max_results", 200)
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
            match_name = query in f.name.lower() if query else True
            match_content = False
            if query and not match_name:
                try:
                    if f.suffix.lower() in [".txt",".md",".csv",".json",".js",".py",".html",".css"]:
                        content = f.read_text("utf-8", errors="replace")
                        match_content = query in content.lower()
                    elif f.suffix.lower() == ".pdf":
                        import pdfplumber
                        with pdfplumber.open(str(f)) as pdf:
                            for page in pdf.pages[:5]:
                                t = page.extract_text() or ""
                                if query in t.lower(): match_content = True; break
                except: pass
            if match_name or match_content or not query:
                stat = f.stat()
                results.append({
                    "path": str(f), "name": f.name, "ext": f.suffix.lower(),
                    "size": stat.st_size, "tipo": f.suffix.lstrip(".").upper(),
                    "match": "nombre" if match_name else "contenido",
                })
            if len(results) >= max_results: break
    except Exception as e:
        return make_response(False, "SEARCH_ERR", str(e))
    return make_response(True, "SEARCH_OK", f"{len(results)} resultados encontrados.", {"results": results, "total": len(results)})


@app.post("/api/organizar-sugerir")
async def api_organizar_sugerir(payload: dict):
    """Sugiere cómo organizar archivos en una carpeta."""
    base_dir = payload.get("base_dir", "")
    if not base_dir or not Path(base_dir).exists():
        return make_response(False, "NOT_FOUND", "Directorio no encontrado.")
    files = []
    for f in Path(base_dir).rglob("*"):
        if f.is_file():
            files.append({"name": f.name, "ext": f.suffix.lower(), "size": f.stat().st_size})
    if not files:
        return make_response(False, "EMPTY", "Carpeta vacía.")
    # Group by extension
    from collections import defaultdict
    grupos = defaultdict(list)
    for f in files:
        grupos[f["ext"] or ".sin_ext"].append(f["name"])
    sugerencia = {k: {"cantidad": len(v), "archivos": v[:5], "carpeta_sugerida": _sugerir_carpeta(k)} for k, v in grupos.items()}
    return make_response(True, "ORG_OK", f"Sugerencia para {len(files)} archivos.", {"grupos": sugerencia, "total_archivos": len(files)})

def _sugerir_carpeta(ext):
    m = {".pdf":"Documentos/PDF",".docx":"Documentos/Word",".doc":"Documentos/Word",
         ".xlsx":"Documentos/Excel",".xls":"Documentos/Excel",".jpg":"Imagenes",
         ".jpeg":"Imagenes",".png":"Imagenes",".gif":"Imagenes",".mp4":"Videos",
         ".mp3":"Audio",".zip":"Archivos_Comprimidos",".py":"Codigo/Python",
         ".js":"Codigo/JavaScript",".txt":"Texto",".csv":"Datos",".json":"Datos/JSON"}
    return m.get(ext, f"Otros/{ext.lstrip('.').upper() or 'Sin_Extension'}")


@app.post("/api/tasker-receive")
async def api_tasker_receive(payload: dict):
    """Endpoint para recibir mensajes desde Tasker/AutoRemote en Android."""
    mensaje = payload.get("message", "")
    device = payload.get("device", "unknown")
    timestamp = payload.get("timestamp", "")
    # Store message
    TASKER_LOG_FILE = UPLOAD_DIR.parent / "tasker_messages.json"
    try:
        log = json.loads(TASKER_LOG_FILE.read_text()) if TASKER_LOG_FILE.exists() else []
        log.append({"mensaje": mensaje, "device": device, "timestamp": timestamp, "received": __import__("datetime").datetime.now().isoformat()})
        log = log[-100:]  # keep last 100
        TASKER_LOG_FILE.write_text(json.dumps(log, ensure_ascii=False, indent=2))
    except Exception as e:
        pass
    # Process with LLM if possible
    reply = f"MAER recibido: {mensaje[:50]}"
    try:
        from maer_backend.maer_files import action_llm_chat
        r = action_llm_chat({"prompt": mensaje})
        if r.get("ok"): reply = r["data"]["response"][:500]
    except: pass
    return {"ok": True, "reply": reply}


@app.get("/api/tasker-messages")
async def api_tasker_messages():
    """Obtiene mensajes recibidos de Tasker."""
    TASKER_LOG_FILE = UPLOAD_DIR.parent / "tasker_messages.json"
    try:
        log = json.loads(TASKER_LOG_FILE.read_text()) if TASKER_LOG_FILE.exists() else []
        return make_response(True, "OK", "", {"messages": log[-20:]})
    except Exception as e:
        return make_response(False, "ERR", str(e))


def main():
    host = os.environ.get("MAER_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("MAER_WEB_PORT", "8765"))
    print(f"🦁 MAER Dashboard iniciando en http://localhost:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
