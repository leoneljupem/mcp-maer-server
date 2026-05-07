#!/usr/bin/env python3
"""
Mini app local para auditar y ordenar el entorno de /Users/houssenm.

Diseno:
- No imprime secretos ni tokens.
- No mueve carpetas de clientes, SAT, IDSE, eFirma, certificados, .ssh, .env ni OAuth.
- Solo mueve candidatos tecnicos claramente prescindibles a una carpeta de revision.
- Genera reportes de texto en Desktop y un indice maestro en el home.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
    import uvicorn
except Exception:  # pragma: no cover
    FastAPI = None
    HTMLResponse = None
    JSONResponse = None
    PlainTextResponse = None
    uvicorn = None


HOME = Path("/Users/houssenm")
DESKTOP = HOME / "Desktop"
MAER = HOME / "mcp-maer-server"
NO_VERIFY = HOME / "-noverify"
STAMP = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
REVIEW_DIR = DESKTOP / f"parecido_o_innecesario_REVISION_{STAMP}"

SENSITIVE_DIR_PARTS = {
    "USB NEGRA",
    "IDSE",
    "eFirma_SAT",
    "Certifica",
    ".ssh",
    ".codex",
    ".claude",
    ".gemini",
    ".openclaw",
}

AI_DIRS = [HOME / ".codex", HOME / ".claude", HOME / ".gemini", HOME / ".openclaw"]

IDSE_GUIDE = """IDSE / IMSS - Recuperacion o creacion de accesos
Fecha de consulta: 2026-05-06

Puntos oficiales importantes:
1. Para IDSE se usa Firma Digital compuesta por NPIE, Certificado Digital .PFX, usuario y contrasena.
2. El NPIE es una serie unica asociada al registro patronal y a un certificado digital vigente; no cambia por expedir o cancelar certificados.
3. Para crear certificado digital adicional se requiere el certificado digital IMSS .pfx vigente, usuario y contrasena del patron/representante, mas nombre, CURP y correo del personal designado.
4. La solicitud y activacion de certificados digitales adicionales se realiza por Internet y, segun IMSS, no requiere acudir a Subdelegacion.
5. Si no se cuenta con contrasena/usuario/certificado vigente del patron, el camino conservador es ubicar .pfx + NPIE + contrasena en archivos propios o tramitar/cancelar/renovar certificado segun el caso con IMSS/Subdelegacion.
6. Para solicitud inicial de Certificado Digital IMSS se define usuario y contrasena, se genera una llave privada .key, y se concluye en Subdelegacion dentro de 10 dias habiles. Despues de entregar documentacion completa, IMSS indica que entrega el certificado digital en aproximadamente una hora.
7. Por seguridad no se debe compartir archivo de certificado digital, usuario ni contrasena.

Fuentes oficiales revisadas:
- https://www.imss.gob.mx/patrones/idse
- https://www.imss.gob.mx/patrones/idse/firma-digital
- https://www.imss.gob.mx/tramites/imss02042b
- https://idse.imss.gob.mx/certificacion/jsp/representante/operativos/descripcionOperativos.jsp
- https://idse.imss.gob.mx/certificacion/jsp/representante/popup/npie.jsp
- https://idse.imss.gob.mx/certificacion/jsp/representante/requerimiento/recomendacion.jsp

Checklist practico para tus clientes:
1. Buscar por cliente/registro patronal/RFC en tus carpetas: .pfx, .key, .cer, archivos con "NPIE", "IDSE", "usuario", "contrasena", "password", "acuse".
2. Si existe .pfx vigente y se conoce usuario/contrasena patronal: entrar al portal de certificacion IDSE y crear Certificado Digital Adicional para la persona que operara altas.
3. Si solo existe .key/.cer SAT, eso no necesariamente equivale al .pfx IMSS/NPIE. Separar eFirma SAT de Certificado Digital IMSS.
4. Si no aparece contrasena o .pfx vigente: preparar tramite de recuperacion/renovacion/cancelacion segun estado del certificado; verificar en portal IDSE y, si se bloquea, contactar IMSS 800 623 2323 o Subdelegacion.
5. Para cada cliente crea ficha segura: RFC, registro patronal, NPIE, correo, ubicacion del .pfx, fecha de vigencia, responsable, sin escribir contrasena en texto plano.
"""


def run(cmd: list[str], timeout: int = 30) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (result.stdout + result.stderr).strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_files(path: Path, max_depth: int = 99) -> int:
    base_depth = len(path.parts)
    total = 0
    for root, dirs, files in os.walk(path):
        if len(Path(root).parts) - base_depth >= max_depth:
            dirs[:] = []
        total += len(files)
    return total


def dir_size(path: Path) -> int:
    try:
        result = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, timeout=8)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.split()[0]) * 1024
    except Exception:
        return -1
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def human_size(num: int) -> str:
    if num < 0:
        return "no calculado"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{num} B"


def is_sensitive(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SENSITIVE_DIR_PARTS:
        return True
    lowered = str(path).lower()
    return any(token in lowered for token in ["/idse/", "/efirma", "/certifica", ".env", "oauth", "auth.json", ".key", ".cer", ".pfx"])


def read_json_keys(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, dict):
        return sorted(str(k) for k in data.keys())
    return [type(data).__name__]


def analyze_noverify() -> dict[str, Any]:
    target = NO_VERIFY
    if not target.exists():
        matches = sorted(DESKTOP.glob("parecido_o_innecesario_REVISION_*/-noverify"), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            target = matches[0]
    if not target.exists():
        return {"exists": False}
    strings = run(["strings", "-a", str(target)], timeout=20).splitlines()[:120]
    info = run(["hdiutil", "imageinfo", str(target)], timeout=20)
    return {
        "exists": True,
        "path": str(target),
        "size": human_size(target.stat().st_size),
        "sha256": sha256(target),
        "file": run(["file", str(target)]),
        "hdiutil_summary": "\n".join(info.splitlines()[:80]),
        "string_signals": [s for s in strings if any(x in s.lower() for x in ["nox", "installer", "appplayer", "yaz5p73t33"])][:60],
        "conclusion": "Imagen de disco UDIF/HFSX de Nox App Player / noxinstaller. No es codigo fuente; parece instalador DMG renombrado como '-noverify'.",
    }


def project_index() -> str:
    top_dirs = []
    for child in sorted(HOME.iterdir(), key=lambda p: p.name.lower()):
        if child.is_dir():
            try:
                top_dirs.append((child.name, human_size(dir_size(child)), count_files(child, 1)))
            except Exception:
                top_dirs.append((child.name, "sin acceso", 0))

    sections = [
        "# Indice maestro de /Users/houssenm",
        f"Generado: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Reglas de seguridad",
        "- No mover: clientes, SAT, IDSE, eFirma, Certifica, .ssh, .env, OAuth, auth.json.",
        "- Mover solo a revision, nunca borrar directo.",
        "- No escribir contrasenas ni tokens en texto plano.",
        "",
        "## Proyectos y entornos principales",
        "- ~/mcp-maer-server: proyecto principal MAER, MCP Node + backend Python + dashboard FastAPI + OCR/NLP/IMSS.",
        "- ~/docinteligence: libreria Python reutilizable para clasificacion documental y entidades.",
        "- ~/Documents/SAT_Tools: scripts fiscales SAT/CFDI/certificados/reportes.",
        "- ~/Desktop/carpeta sin titulo: area pendiente; contiene muchas copias/prototipos MAER y documentos. Revisar al final.",
        "- ~/.codex, ~/.claude, ~/.gemini, ~/.openclaw: sesiones, configuracion, plugins y credenciales de asistentes IA.",
        "- ~/.ollama: modelos locales LLM, alto consumo de disco.",
        "",
        "## Carpetas de primer nivel",
        "| Carpeta | Tamano aprox | Archivos aprox maxdepth 2 | Nota |",
        "|---|---:|---:|---|",
    ]
    for name, size, files in top_dirs:
        note = "sensible/no mover" if name in SENSITIVE_DIR_PARTS or name in {"Documents", "Certifica"} else ""
        if name in {".cache", ".npm", ".Trash", "Downloads"}:
            note = "candidata a limpieza controlada"
        if name == "mcp-maer-server":
            note = "proyecto principal mantenible"
        sections.append(f"| `{name}` | {size} | {files} | {note} |")
    return "\n".join(sections) + "\n"


def ai_sensitive_report() -> str:
    lines = [
        "Reporte de carpetas IA/desarrollo sensibles",
        f"Generado: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "Este reporte NO incluye valores de tokens, cookies, contrasenas ni OAuth. Solo rutas, tipos y nivel de riesgo.",
        "",
    ]
    for base in AI_DIRS:
        lines.append(f"## {base}")
        if not base.exists():
            lines.append("- No existe.")
            continue
        lines.append(f"- Tamano aproximado: {human_size(dir_size(base))}")
        lines.append(f"- Archivos aproximados maxdepth 3: {count_files(base, 3)}")
        emitted = 0
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = "~/" + str(path.relative_to(HOME))
            lower = path.name.lower()
            risky = any(x in lower for x in ["auth", "oauth", "token", "cookie", "login data", "credentials", "creds", "state", "session", ".sqlite"])
            if risky or path.suffix in {".json", ".jsonl", ".sqlite", ".toml", ".pb", ".pbtxt"}:
                keys = read_json_keys(path) if path.suffix == ".json" else []
                detail = f" keys={keys}" if keys else ""
                lines.append(f"- {rel} | {human_size(path.stat().st_size)} | {'ALTO' if risky else 'medio'}{detail}")
                emitted += 1
                if emitted >= 350:
                    lines.append("- ... listado truncado a 350 elementos relevantes para mantener el reporte manejable.")
                    break
        lines.append("")
    lines.extend([
        "Recomendaciones:",
        "- Mantener estas carpetas fuera de Git, ZIPs y respaldos compartidos.",
        "- No copiar auth.json, oauth_creds.json, Login Data, Cookies, state sqlite ni session jsonl a proyectos.",
        "- Si alguna credencial fue compartida, revocarla desde el proveedor correspondiente.",
    ])
    return "\n".join(lines) + "\n"


def maer_report(test_summary: str | None = None) -> str:
    pkg = json.loads((MAER / "package.json").read_text(encoding="utf-8"))
    py_files = sorted((MAER / "maer_backend").glob("*.py"))
    lines = [
        "Informe detallado de mcp-maer-server",
        f"Generado: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Cometido",
        "MAER MCP Server combina servidor MCP Node.js, backend Python, dashboard FastAPI, OCR, NLP, busqueda semantica, analisis de imagenes, validacion de entidades mexicanas e integraciones LLM/Ollama/Groq/Anthropic.",
        "",
        "## Ejecucion",
    ]
    for key, value in pkg.get("scripts", {}).items():
        lines.append(f"- npm run {key}: {value}")
    lines.extend([
        "",
        "## Modulos Python principales",
    ])
    for path in py_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        defs = [line.strip() for line in text.splitlines() if line.startswith(("def ", "class "))]
        lines.append(f"- {path.name}: {len(text.splitlines())} lineas; {', '.join(defs[:8])}")
    lines.extend([
        "",
        "## Hallazgos",
        "- Proyecto funcional y testeable; es la base que conviene conservar.",
        "- Worktree Git esta sucio: hay cambios modificados, .bak borrados y carpetas nuevas; revisar antes de commit.",
        "- .env existe dentro del repo: debe mantenerse fuera de Git y respaldos compartidos.",
        "- models/Llama-3.2-1B-Instruct-Q4_K_M.gguf ocupa ~770 MB; correcto si se usa localmente, pero debe estar excluido de Git.",
        "- tessdata_best contiene eng/spa traineddata (~28 MB total); causa el fallo del test de archivos grandes.",
        "- Hay caches __pycache__, .DS_Store, logs y respaldos internos que pueden limpiarse o excluirse.",
        "- maer_backend/web_ui/server.py es muy grande y concentra muchos endpoints; conviene dividir por routers/modulos.",
        "- Hay endpoints de movimiento/copia de archivos; deben tener listas de bloqueo para certificados, IDSE, .env y rutas sensibles.",
        "",
        "## Pruebas",
        test_summary or "No se ejecuto prueba en esta generacion.",
        "",
        "## Mejoras sugeridas",
        "- Crear .gitignore estricto para .env, modelos, tessdata descargable, caches, logs, respaldos zip y documentos cliente.",
        "- Mover tessdata_best a cache externa o excluirlo en test_no_hay_archivos_gigantes.",
        "- Separar server.py en routers: ocr, imss, llm, archivos, semantic, vision, admin.",
        "- Agregar capa de seguridad de rutas antes de mover/copiar/eliminar archivos.",
        "- Crear fixtures pequenos y evitar datos reales en data/expedientes.",
        "- Documentar un flujo IDSE: localizar credenciales, validar certificado, crear adicional, registrar responsable.",
    ])
    return "\n".join(lines) + "\n"


def safe_move_candidates() -> list[dict[str, str]]:
    candidates = [
        (HOME / "ai_studio_code.py", "duplicado exacto de analizador.py"),
        (HOME / "aura_system_report.json", "reporte generado de 80 MB; no es fuente"),
        (HOME / "aura_activity.log", "log generado; no es fuente"),
        (HOME / "BlueStacks10Installer_10.42.168.1001_native_1ac2506e20e679c9b22d93d4a4e5e84c_MDs1LDM7MTUsMTsxNSw0OzE1LDU7MTU=.exe", "instalador suelto en home"),
        (HOME / "BlueStacksInstaller_5.21.755.7538_395c35be590121d78c1712c611a25eab.pkg", "instalador suelto en home"),
        (HOME / "GoogleDrive.dmg", "instalador suelto en home"),
        (HOME / "anydesk.dmg", "instalador suelto en home"),
        (NO_VERIFY, "imagen de disco Nox renombrada; revisar antes de borrar"),
    ]
    out = []
    for path, reason in candidates:
        if path.exists() and not is_sensitive(path):
            out.append({"path": str(path), "name": path.name, "reason": reason, "size": human_size(path.stat().st_size)})
    return out


def move_safe_candidates() -> dict[str, Any]:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    moved = []
    errors = []
    for item in safe_move_candidates():
        src = Path(item["path"])
        dst = REVIEW_DIR / src.name
        try:
            shutil.move(str(src), str(dst))
            moved.append({**item, "new_path": str(dst)})
        except Exception as exc:
            errors.append({"path": str(src), "error": str(exc)})
    manifest = REVIEW_DIR / "POR_QUE_SE_DEBERIAN_BORRAR_O_ARCHIVAR.md"
    manifest.write_text(render_move_manifest(moved, errors), encoding="utf-8")
    return {"review_dir": str(REVIEW_DIR), "moved": moved, "errors": errors, "manifest": str(manifest)}


def render_move_manifest(moved: list[dict[str, str]], errors: list[dict[str, str]]) -> str:
    lines = [
        "# Carpeta de revision: parecido o innecesario",
        f"Generado: {dt.datetime.now().isoformat(timespec='seconds')}",
        "",
        "Nada de esta carpeta fue borrado. Se movio aqui para revisar con calma.",
        "No se movieron documentos de clientes, SAT, IDSE, eFirma, certificados, .env, OAuth ni auth.json.",
        "",
        "## Movidos",
    ]
    for item in moved:
        lines.append(f"- `{item['name']}` ({item['size']}): {item['reason']}. Origen: `{item['path']}`")
    if errors:
        lines.append("")
        lines.append("## Errores")
        for err in errors:
            lines.append(f"- `{err['path']}`: {err['error']}")
    lines.extend([
        "",
        "## Criterio para borrar definitivamente",
        "- Borrar solo si confirmas que no necesitas reinstalar esa app ni conservar el reporte/log.",
        "- Si tienes duda, dejar en esta carpeta o copiar a disco externo.",
        "- `-noverify` parece instalador Nox renombrado; no abrir si no recuerdas su origen.",
    ])
    return "\n".join(lines) + "\n"


def write_reports(test_summary: str | None = None) -> dict[str, str]:
    index_path = HOME / "PROJECTS_INDEX.md"
    ai_path = DESKTOP / f"REPORTE_IA_SENSIBLE_{STAMP}.txt"
    maer_path = DESKTOP / f"INFORME_MAER_COMPLETO_{STAMP}.txt"
    idse_path = DESKTOP / f"GUIA_IDSE_RECUPERAR_ACCESOS_{STAMP}.txt"
    noverify_path = DESKTOP / f"ANALISIS_NO_VERIFY_{STAMP}.txt"

    index_path.write_text(project_index(), encoding="utf-8")
    ai_path.write_text(ai_sensitive_report(), encoding="utf-8")
    maer_path.write_text(maer_report(test_summary), encoding="utf-8")
    idse_path.write_text(IDSE_GUIDE, encoding="utf-8")
    noverify = analyze_noverify()
    noverify_path.write_text(json.dumps(noverify, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "index": str(index_path),
        "ai_sensitive": str(ai_path),
        "maer_report": str(maer_path),
        "idse_guide": str(idse_path),
        "noverify": str(noverify_path),
    }


def scan_desktop_problematic(limit: int = 200) -> dict[str, Any]:
    base = DESKTOP / "carpeta sin título"
    if not base.exists():
        return {"exists": False, "path": str(base)}
    interesting = []
    for path in base.rglob("*"):
        if len(interesting) >= limit:
            break
        if path.is_dir() and any(token.lower() in path.name.lower() for token in ["maer", "mcp", "estado", "sat", "portal"]):
            interesting.append({"path": str(path), "type": "dir"})
        elif path.is_file() and path.suffix.lower() in {".py", ".js", ".html", ".command", ".json", ".md"}:
            interesting.append({"path": str(path), "type": "file", "size": human_size(path.stat().st_size)})
    return {
        "exists": True,
        "path": str(base),
        "size": human_size(dir_size(base)),
        "files": count_files(base),
        "sample": interesting,
        "note": "Pendiente para el final; no se movio nada aqui.",
    }


def build_app() -> FastAPI:
    app = FastAPI(title="MAER Home Audit")

    @app.get("/", response_class=HTMLResponse)
    async def home():
        return HTML

    @app.get("/api/summary")
    async def summary():
        return {
            "maer": str(MAER),
            "review_candidates": safe_move_candidates(),
            "noverify": analyze_noverify(),
            "desktop_problematic": scan_desktop_problematic(80),
            "reports_hint": "POST /api/reports para generar reportes en Desktop.",
        }

    @app.post("/api/reports")
    async def reports():
        return write_reports()

    @app.post("/api/move-safe")
    async def move_safe():
        return move_safe_candidates()

    @app.get("/api/idse", response_class=PlainTextResponse)
    async def idse():
        return IDSE_GUIDE

    return app


HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MAER Auditor</title>
  <style>
    :root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#202124;background:#f7f8fa}
    body{margin:0}
    header{background:#111827;color:white;padding:18px 24px}
    main{max-width:1180px;margin:0 auto;padding:18px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
    section,.item{background:white;border:1px solid #d8dde6;border-radius:8px;padding:14px}
    button{background:#14532d;color:white;border:0;border-radius:6px;padding:9px 12px;cursor:pointer;font-weight:600}
    button.secondary{background:#374151}
    button.warn{background:#9f1239}
    pre{white-space:pre-wrap;word-break:break-word;background:#0f172a;color:#d1fae5;padding:12px;border-radius:6px;max-height:460px;overflow:auto}
    .muted{color:#5f6368}
    .risk{color:#9f1239;font-weight:700}
  </style>
</head>
<body>
  <header><h1>MAER Auditor de Entorno</h1><div>Auditoria local segura para /Users/houssenm</div></header>
  <main>
    <section>
      <button onclick="loadSummary()">Analizar</button>
      <button class="secondary" onclick="writeReports()">Crear reportes e indice</button>
      <button class="warn" onclick="moveSafe()">Mover candidatos seguros a revision</button>
      <p class="muted">No toca clientes, SAT, IDSE, eFirma, certificados, .env, OAuth ni auth.json.</p>
    </section>
    <div class="grid">
      <section><h2>Candidatos</h2><div id="candidates"></div></section>
      <section><h2>-noverify</h2><div id="noverify"></div></section>
      <section><h2>Desktop pendiente</h2><div id="desktop"></div></section>
    </div>
    <section><h2>Salida</h2><pre id="out">Listo.</pre></section>
  </main>
  <script>
    const out = document.getElementById('out');
    function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
    async function loadSummary(){
      const data = await (await fetch('/api/summary')).json();
      document.getElementById('candidates').innerHTML = data.review_candidates.map(x=>`<div class="item"><b>${esc(x.name)}</b><br>${esc(x.size)}<br><span class="muted">${esc(x.reason)}</span></div>`).join('');
      document.getElementById('noverify').innerHTML = `<div class="item"><b>${esc(data.noverify.size||'no existe')}</b><br>${esc(data.noverify.conclusion||'')}</div>`;
      document.getElementById('desktop').innerHTML = `<div class="item"><b>${esc(data.desktop_problematic.size||'')}</b><br>${esc(data.desktop_problematic.files||0)} archivos<br>${esc(data.desktop_problematic.note||'')}</div>`;
      out.textContent = JSON.stringify(data, null, 2);
    }
    async function writeReports(){
      const data = await (await fetch('/api/reports', {method:'POST'})).json();
      out.textContent = JSON.stringify(data, null, 2);
    }
    async function moveSafe(){
      if(!confirm('Mover solo candidatos tecnicos seguros a carpeta de revision en Desktop?')) return;
      const data = await (await fetch('/api/move-safe', {method:'POST'})).json();
      out.textContent = JSON.stringify(data, null, 2);
      await loadSummary();
    }
    loadSummary();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-reports", action="store_true")
    parser.add_argument("--move-safe", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    if args.write_reports:
        print(json.dumps(write_reports(), ensure_ascii=False, indent=2))
    if args.move_safe:
        print(json.dumps(move_safe_candidates(), ensure_ascii=False, indent=2))
    if args.serve:
        if FastAPI is None or uvicorn is None:
            raise SystemExit("FastAPI/uvicorn no disponibles en este entorno.")
        uvicorn.run(build_app(), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
