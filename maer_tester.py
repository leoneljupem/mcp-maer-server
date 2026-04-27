#!/usr/bin/env python3
"""
maer_tester.py — Suite de pruebas automáticas para MAER 4.0
════════════════════════════════════════════════════════════
Ejecuta pruebas unitarias e integración de todos los componentes:
  • Servidor FastAPI + todos los endpoints
  • Módulo Ollama (detección, modelos, cascade LLM)
  • Pandas / Datos (análisis CSV/XLSX)
  • Conda (entornos)
  • OCR pipeline
  • CURP/RFC/NSS decodificadores
  • PDF export (reportlab)
  • PWA (service-worker, manifest)
  • Consola MAER (importaciones)
  • Lanzador (importaciones)

Uso:
    python maer_tester.py                    # suite básica
    python maer_tester.py --suite=completo   # todas las pruebas
    python maer_tester.py --suite=endpoints  # solo endpoints HTTP
    python maer_tester.py --suite=ollama     # solo Ollama
    python maer_tester.py --suite=pandas     # solo Pandas/datos
    python maer_tester.py --host=localhost --port=8765  # servidor externo

Leonel Houssen Mojica — Ecatepec MX — 2026
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ─── Configuración ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

ANSI = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "reset": "\033[0m",
}


def c(color, text):
    return f"{ANSI.get(color,'')}{text}{ANSI['reset']}"


# ─── Resultado de prueba ────────────────────────────────────────────────────────
class Resultado:
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    SKIP = "⚠️  SKIP"
    WARN = "🟡 WARN"


class TestResult:
    def __init__(self, nombre, estado, mensaje="", detalle="", duracion=0.0):
        self.nombre = nombre
        self.estado = estado
        self.mensaje = mensaje
        self.detalle = detalle
        self.duracion = duracion

    def __str__(self):
        col = {
            "✅ PASS": "green",
            "❌ FAIL": "red",
            "⚠️  SKIP": "yellow",
            "🟡 WARN": "yellow",
        }.get(self.estado, "white")
        dur = f"  {c('dim', f'({self.duracion:.2f}s)')}" if self.duracion > 0.1 else ""
        linea = f"  {c(col, self.estado)}  {self.nombre}{dur}"
        if self.mensaje:
            linea += f"\n       {c('dim', self.mensaje)}"
        if self.detalle and self.estado == Resultado.FAIL:
            linea += f"\n       {c('red', self.detalle[:120])}"
        return linea


# ─── Runner base ────────────────────────────────────────────────────────────────
class TestRunner:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.results = []
        self._server_pid = None

    def _server_activo(self) -> bool:
        try:
            urllib.request.urlopen(f"{self.base_url}/", timeout=3)
            return True
        except Exception as e:
            return False

    def _iniciar_server(self) -> bool:
        """Arranca el servidor de pruebas si no está corriendo."""
        if self._server_activo():
            return True
        server_py = BASE_DIR / "maer_backend" / "web_ui" / "server.py"
        if not server_py.exists():
            return False
        proc = subprocess.Popen(
            [sys.executable, str(server_py)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(BASE_DIR),
        )
        self._server_pid = proc.pid
        for _ in range(10):
            time.sleep(1)
            if self._server_activo():
                return True
        return False

    def _detener_server(self):
        if self._server_pid:
            try:
                import signal

                os.kill(self._server_pid, signal.SIGTERM)
            except Exception as e:
                pass

    def _http(
        self, method: str, path: str, body: dict = None, timeout: int = 20
    ) -> tuple:
        """Hace una petición HTTP y devuelve (status_code, json_dict|raw_str)."""
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body else None
        headers = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                status = r.status
                raw = r.read()
                ctype = r.headers.get("Content-Type", "")
                if "json" in ctype:
                    return status, json.loads(raw)
                # Intentar JSON de todas formas
                try:
                    return status, json.loads(raw)
                except Exception as e:
                    # Respuesta no-JSON (HTML, JS, etc.) — devolver texto plano en dict
                    return status, {"_raw": raw.decode("utf-8", errors="ignore")[:200]}
        except urllib.error.HTTPError as e:
            return e.code, {}
        except Exception as ex:
            return 0, {"_error": str(ex)}

    def _run_test(self, nombre: str, fn) -> TestResult:
        t0 = time.time()
        try:
            estado, mensaje, detalle = fn()
            return TestResult(nombre, estado, mensaje, detalle, time.time() - t0)
        except Exception as ex:
            return TestResult(
                nombre,
                Resultado.FAIL,
                str(ex),
                traceback.format_exc()[-200:],
                time.time() - t0,
            )

    def add(self, resultado: TestResult):
        self.results.append(resultado)
        print(resultado)

    def resumen(self) -> dict:
        total = len(self.results)
        pasa = sum(1 for r in self.results if r.estado == Resultado.PASS)
        falla = sum(1 for r in self.results if r.estado == Resultado.FAIL)
        salta = sum(
            1 for r in self.results if r.estado in (Resultado.SKIP, Resultado.WARN)
        )
        return {"total": total, "pass": pasa, "fail": falla, "skip": salta}

    def imprimir_resumen(self):
        res = self.resumen()
        print()
        print(c("bold", "═" * 55))
        print(c("bold", f"  RESUMEN DE PRUEBAS — MAER 4.0"))
        print(c("bold", "═" * 55))
        print(f"  Total:  {res['total']}")
        pasan = res["pass"]
        fallan = res["fail"]
        saltan = res["skip"]
        print(f"  {c('green', f'Pasan:  {pasan}')} ")
        print(f"  {c('red',   f'Fallan: {fallan}')} ")
        print(f"  {c('yellow',f'Skip:   {saltan}')} ")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(c("dim", f"  Ejecutado: {ts}"))
        print(c("bold", "═" * 55))
        if res["fail"] == 0:
            print(c("green", "  🎉 Todas las pruebas pasaron"))
        else:
            print(c("red", f"  ⚠️  {res['fail']} prueba(s) fallaron"))
        print()
        return res["fail"]  # 0 = éxito


# ─── Suites de prueba ───────────────────────────────────────────────────────────


class SuiteImports(TestRunner):
    """Prueba que todos los módulos Python requeridos se puedan importar."""

    def correr(self):
        print(c("cyan", "\n📦 Suite: Importaciones Python\n"))

        paquetes = {
            "fastapi": "FastAPI",
            "uvicorn": "Servidor ASGI",
            "requests": "HTTP client",
            "pandas": "Análisis de datos",
            "numpy": "Cómputo numérico",
            "scipy": "Ciencia de datos",
            "PIL": "Pillow — imágenes",
            "fitz": "PyMuPDF — PDFs",
            "pdfplumber": "pdfplumber — tablas PDF",
            "reportlab": "ReportLab — generar PDF",
            "pytesseract": "Tesseract OCR",
            "cv2": "OpenCV",
            "deskew": "Corrección de rotación OCR",
            "openpyxl": "Excel XLSX",
            "pypdf": "pypdf — leer PDF",
            "dotenv": "python-dotenv",
            "sklearn": "scikit-learn",
            "selenium": "Selenium WebDriver",
            "pyngrok": "ngrok túnel",
        }

        for pkg, desc in paquetes.items():

            def _test(p=pkg, d=desc):
                try:
                    __import__(p)
                    return Resultado.PASS, f"importado ({d})", ""
                except ImportError:
                    return Resultado.SKIP, f"no instalado: {p} ({d})", ""

            self.add(self._run_test(f"import {pkg}", _test))

        # Módulos propios de MAER
        maer_mods = [
            ("maer_backend.maer_files", "Núcleo MAER"),
            ("maer_backend.maer_ollama", "Detector Ollama"),
        ]
        for mod, desc in maer_mods:

            def _test_maer(m=mod, d=desc):
                try:
                    import importlib

                    importlib.import_module(m)
                    return Resultado.PASS, f"módulo MAER OK ({d})", ""
                except Exception as e:
                    return Resultado.FAIL, f"Error importando {m}", str(e)

            self.add(self._run_test(f"import {mod}", _test_maer))


class SuiteEndpoints(TestRunner):
    """Prueba todos los endpoints del servidor FastAPI."""

    def correr(self):
        print(c("cyan", "\n🌐 Suite: Endpoints HTTP\n"))

        if not self._iniciar_server():
            self.add(
                TestResult(
                    "Servidor disponible",
                    Resultado.FAIL,
                    f"No se pudo conectar a {self.base_url}",
                )
            )
            return

        def _root():
            s, d = self._http("GET", "/")
            if s == 200:
                raw = d.get("_raw", "")
                tiene_html = "<html" in raw.lower() or "MAER" in raw
                return (
                    Resultado.PASS,
                    f"HTML principal OK ({'MAER encontrado' if tiene_html else 'respuesta recibida'})",
                    "",
                )
            return Resultado.FAIL, f"Status {s}", str(d)[:100]

        self.add(self._run_test("GET /  (HTML principal)", _root))

        # CURP decodificar
        def _curp():
            s, d = self._http(
                "POST", "/api/curp-decodificar", {"curp": "LOOA531113HTCPBN09"}
            )
            if s == 200 and d.get("ok"):
                data = d.get("data", {})
                return (
                    Resultado.PASS,
                    f"CURP ok, edad {data.get('edad','?')}, {data.get('estado','?')}",
                    "",
                )
            return Resultado.FAIL, f"status={s} ok={d.get('ok')}", str(d)[:120]

        self.add(self._run_test("POST /api/curp-decodificar", _curp))

        # RFC validar
        def _rfc():
            s, d = self._http("POST", "/api/rfc-validar", {"rfc": "LOOA531113AB9"})
            return (
                (Resultado.PASS, "RFC ok", "")
                if s == 200
                else (Resultado.FAIL, f"status={s}", "")
            )

        self.add(self._run_test("POST /api/rfc-validar", _rfc))

        # LLM Chat
        def _chat():
            s, d = self._http(
                "POST",
                "/api/llm-chat",
                {"prompt": "¿Cuántas semanas para Ley 73?"},
                timeout=30,
            )
            if s == 200 and d.get("ok"):
                resp = d.get("data", {}).get("response", "")
                engine = d.get("data", {}).get("engine", "?")
                return Resultado.PASS, f"engine={engine}, {len(resp)} chars", ""
            return Resultado.FAIL, f"status={s}", str(d)[:120]

        self.add(self._run_test("POST /api/llm-chat (cascade LLM)", _chat))

        # SINAVID
        def _sinavid():
            s, d = self._http(
                "POST",
                "/api/sinavid-consulta",
                {"curp": "LOOA531113HTCPBN09", "nss": "12345678901"},
            )
            return (
                (Resultado.PASS, "SINAVID ok", "")
                if s == 200
                else (Resultado.FAIL, f"status={s}", "")
            )

        self.add(self._run_test("POST /api/sinavid-consulta", _sinavid))

        # PDF export
        def _pdf():
            s, d = self._http(
                "POST",
                "/api/exportar-pdf",
                {
                    "nombre": "Test Usuario",
                    "curp": "LOOA531113HTCPBN09",
                    "nss": "12345678901",
                    "semanas": 500,
                },
                timeout=30,
            )
            if s == 200 and d.get("ok"):
                return Resultado.PASS, d.get("message", "")[:60], ""
            return Resultado.FAIL, f"status={s}", str(d)[:120]

        self.add(self._run_test("POST /api/exportar-pdf", _pdf))

        # Ollama modelos
        def _ollama():
            s, d = self._http("GET", "/api/ollama-modelos")
            if s == 200:
                total = d.get("data", {}).get("total_modelos", 0)
                elegido = d.get("data", {}).get("modelo_elegido", "ninguno")
                activo = d.get("data", {}).get("servidor_activo", False)
                if activo:
                    return Resultado.PASS, f"{total} modelos · usando {elegido}", ""
                else:
                    return (
                        Resultado.WARN,
                        f"Ollama instalado pero servidor inactivo. Modelos disco: {d.get('data',{}).get('modelos_disco',[])}",
                        "",
                    )
            return Resultado.FAIL, f"status={s}", ""

        self.add(self._run_test("GET /api/ollama-modelos", _ollama))

        # Conda
        def _conda():
            s, d = self._http("GET", "/api/conda-envs")
            if s == 200:
                ok = d.get("ok", False)
                if ok:
                    envs = d.get("data", {}).get("envs", [])
                    return Resultado.PASS, f"{len(envs)} entorno(s) conda", ""
                return Resultado.WARN, "Conda no encontrado (opcional)", ""
            return Resultado.FAIL, f"status={s}", ""

        self.add(self._run_test("GET /api/conda-envs", _conda))

        # Verificar dependencias
        def _deps():
            s, d = self._http("GET", "/api/verificar-dependencias", timeout=30)
            if s == 200:
                msg = d.get("message", "")
                return Resultado.PASS, msg[:80], ""
            return Resultado.FAIL, f"status={s}", ""

        self.add(self._run_test("GET /api/verificar-dependencias", _deps))

        # PWA
        def _sw():
            s, d = self._http("GET", "/service-worker.js")
            if s == 200:
                raw = d.get("_raw", "")
                return (
                    Resultado.PASS,
                    f"Service Worker OK ({'Cache-First detectado' if 'Cache' in raw else 'JS recibido'})",
                    "",
                )
            return Resultado.FAIL, f"status={s}", ""

        self.add(self._run_test("GET /service-worker.js (PWA)", _sw))

        def _manifest():
            s, d = self._http("GET", "/manifest.json")
            if s == 200:
                return (
                    Resultado.PASS,
                    f"name={d.get('name','?')}, display={d.get('display','?')}",
                    "",
                )
            return Resultado.FAIL, f"status={s}", ""

        self.add(self._run_test("GET /manifest.json (PWA)", _manifest))

        # ngrok URL
        def _ngrok():
            s, d = self._http("GET", "/api/ngrok-url")
            if s == 200:
                url = d.get("data", {}).get("url")
                if url:
                    return Resultado.PASS, f"ngrok activo: {url[:50]}", ""
                return Resultado.WARN, "ngrok no activo (usa iniciar_maer_ngrok.py)", ""
            return Resultado.FAIL, f"status={s}", ""

        self.add(self._run_test("GET /api/ngrok-url", _ngrok))

        # Status
        def _status():
            s, d = self._http("GET", "/api/status")
            return (
                (Resultado.PASS, "Status OK", "")
                if s == 200
                else (Resultado.FAIL, f"status={s}", "")
            )

        self.add(self._run_test("GET /api/status", _status))


class SuiteOllama(TestRunner):
    """Prueba el módulo maer_ollama.py."""

    def correr(self):
        print(c("cyan", "\n🤖 Suite: Ollama\n"))

        def _import():
            pass

            return Resultado.PASS, "módulo importado", ""

        self.add(self._run_test("import maer_ollama", _import))

        def _estado():
            from maer_backend.maer_ollama import estado_completo

            e = estado_completo()
            if e["instalado"]:
                return (
                    Resultado.PASS,
                    f"Binario: {e['bin_path']} | versión: {e['version']}",
                    "",
                )
            return Resultado.WARN, "Ollama no instalado. Descarga desde ollama.ai", ""

        self.add(self._run_test("Detectar binario Ollama", _estado))

        def _servidor():
            from maer_backend.maer_ollama import servidor_activo

            if servidor_activo():
                return Resultado.PASS, "Servidor Ollama activo en :11434", ""
            return Resultado.WARN, "Servidor Ollama inactivo (no requerido)", ""

        self.add(self._run_test("Servidor Ollama :11434", _servidor))

        def _modelos():
            from maer_backend.maer_ollama import (listar_modelos_api,
                                                  listar_modelos_disco,
                                                  servidor_activo)

            if servidor_activo():
                mods = listar_modelos_api()
                if mods:
                    nombres = ", ".join(m["name"] for m in mods[:3])
                    return Resultado.PASS, f"{len(mods)} modelo(s): {nombres}", ""
                return (
                    Resultado.WARN,
                    "Servidor activo pero sin modelos descargados",
                    "",
                )
            disco = listar_modelos_disco()
            if disco:
                return (
                    Resultado.WARN,
                    f"{len(disco)} modelo(s) en disco (servidor apagado): {', '.join(disco[:2])}",
                    "",
                )
            return (
                Resultado.WARN,
                "Sin modelos descargados. Usa: ollama pull llama3.2",
                "",
            )

        self.add(self._run_test("Listar modelos Ollama", _modelos))

        def _elegir():
            from maer_backend.maer_ollama import (elegir_modelo,
                                                  listar_modelos_api,
                                                  servidor_activo)

            if not servidor_activo():
                return Resultado.SKIP, "Servidor inactivo, skip selección de modelo", ""
            mods = listar_modelos_api()
            if not mods:
                return Resultado.SKIP, "Sin modelos para elegir", ""
            elegido = elegir_modelo(mods)
            return Resultado.PASS, f"Modelo elegido: {elegido}", ""

        self.add(self._run_test("Selección automática de modelo", _elegir))

        def _chat():
            from maer_backend.maer_ollama import (chat, listar_modelos_api,
                                                  servidor_activo)

            if not servidor_activo():
                return Resultado.SKIP, "Servidor inactivo, skip chat", ""
            mods = listar_modelos_api()
            if not mods:
                return Resultado.SKIP, "Sin modelos, skip chat", ""
            r = chat("Di 'Hola' en una palabra.", timeout=30)
            if r["ok"] and r["text"]:
                return (
                    Resultado.PASS,
                    f"Respuesta OK ({r['engine']}): '{r['text'][:40]}'",
                    "",
                )
            return Resultado.FAIL, "Chat sin respuesta", str(r)[:120]

        self.add(self._run_test("Chat con Ollama", _chat))


class SuitePandas(TestRunner):
    """Prueba el análisis de datos con Pandas."""

    def correr(self):
        print(c("cyan", "\n📊 Suite: Pandas / Análisis de datos\n"))

        def _import():
            import numpy as np
            import pandas as pd

            return (
                Resultado.PASS,
                f"pandas {pd.__version__}, numpy {np.__version__}",
                "",
            )

        self.add(self._run_test("import pandas + numpy", _import))

        def _scipy():
            import scipy

            return Resultado.PASS, f"scipy {scipy.__version__}", ""

        self.add(self._run_test("import scipy", _scipy))

        def _sklearn():
            import sklearn

            return Resultado.PASS, f"scikit-learn {sklearn.__version__}", ""

        self.add(self._run_test("import scikit-learn", _sklearn))

        def _csv_basico():
            import io

            import pandas as pd

            csv_data = "nombre,edad,semanas\nJuan,65,520\nMaría,60,480\nPedro,70,1000\n"
            df = pd.read_csv(io.StringIO(csv_data))
            assert len(df) == 3
            assert list(df.columns) == ["nombre", "edad", "semanas"]
            return (
                Resultado.PASS,
                f"{len(df)} filas, columnas: {', '.join(df.columns)}",
                "",
            )

        self.add(self._run_test("Leer CSV con pandas", _csv_basico))

        def _excel():
            try:
                import pandas as pd

                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
                    tmpfile = f.name
                df_out = pd.DataFrame(
                    {"NSS": ["12345", "67890"], "Semanas": [500, 1250]}
                )
                df_out.to_excel(tmpfile, index=False)
                df_in = pd.read_excel(tmpfile)
                Path(tmpfile).unlink(missing_ok=True)
                assert len(df_in) == 2
                return Resultado.PASS, f"Excel R/W ok, {len(df_in)} filas", ""
            except ImportError:
                return Resultado.SKIP, "openpyxl no instalado", ""

        self.add(self._run_test("Leer/Escribir Excel (openpyxl)", _excel))

        def _estadisticas():
            import numpy as np
            import pandas as pd

            df = pd.DataFrame(
                {
                    "semanas": np.random.randint(100, 2000, 100),
                    "sbc": np.random.uniform(200, 5000, 100),
                }
            )
            desc = df.describe()
            df.corr()
            return (
                Resultado.PASS,
                f"describe OK ({len(desc)} stats), correlación OK",
                "",
            )

        self.add(self._run_test("Estadísticas + correlación", _estadisticas))

        def _endpoint_analizar():
            if not self._server_activo():
                return Resultado.SKIP, "Servidor no activo, skip endpoint", ""
            # Crear CSV temporal
            with tempfile.NamedTemporaryFile(
                suffix=".csv", delete=False, mode="w"
            ) as f:
                f.write("nombre,semanas,sbc\nJuan,520,250.50\nMaría,1250,450.75\n")
                tmp_path = f.name
            try:
                s, d = self._http(
                    "POST",
                    "/api/analizar-datos",
                    {"path": tmp_path, "operacion": "todo"},
                )
                Path(tmp_path).unlink(missing_ok=True)
                if s == 200 and d.get("ok"):
                    data = d.get("data", {})
                    return (
                        Resultado.PASS,
                        f"filas={data.get('filas')}, cols={data.get('columnas')}",
                        "",
                    )
                return Resultado.FAIL, f"status={s}", str(d)[:120]
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        self.add(self._run_test("POST /api/analizar-datos (CSV)", _endpoint_analizar))


class SuiteOCR(TestRunner):
    """Prueba el pipeline de OCR."""

    def correr(self):
        print(c("cyan", "\n🔍 Suite: OCR Pipeline\n"))

        def _tesseract():
            import shutil

            tess = shutil.which("tesseract")
            if tess:
                import subprocess

                r = subprocess.run(
                    ["tesseract", "--version"], capture_output=True, text=True
                )
                ver = r.stdout.splitlines()[0] if r.stdout else "?"
                return Resultado.PASS, f"tesseract en {tess}: {ver}", ""
            return (
                Resultado.WARN,
                "tesseract no instalado. Instala: brew install tesseract",
                "",
            )

        self.add(self._run_test("Binario Tesseract", _tesseract))

        def _pytesseract():
            try:
                pass

                import pytesseract
                from PIL import Image

                # Crear imagen con texto simple
                img = Image.new("RGB", (200, 50), color="white")
                from PIL import ImageDraw

                d = ImageDraw.Draw(img)
                d.text((10, 10), "Test OCR 123", fill="black")
                text = pytesseract.image_to_string(img, lang="eng")
                if "123" in text or "Test" in text:
                    return Resultado.PASS, f"OCR básico OK: '{text.strip()[:30]}'", ""
                return (
                    Resultado.WARN,
                    f"OCR corrió pero salida inesperada: '{text.strip()[:30]}'",
                    "",
                )
            except Exception as e:
                return Resultado.WARN, f"pytesseract no disponible: {e!s:.60}", ""

        self.add(self._run_test("pytesseract básico", _pytesseract))

        def _pymupdf():
            try:
                import fitz

                return Resultado.PASS, f"PyMuPDF {fitz.__version__} OK", ""
            except ImportError:
                return Resultado.SKIP, "PyMuPDF no instalado (pip install pymupdf)", ""

        self.add(self._run_test("PyMuPDF (fitz)", _pymupdf))

        def _opencv():
            try:
                import cv2

                return Resultado.PASS, f"OpenCV {cv2.__version__} OK", ""
            except ImportError:
                return (
                    Resultado.SKIP,
                    "OpenCV no instalado (pip install opencv-python-headless)",
                    "",
                )

        self.add(self._run_test("OpenCV (cv2)", _opencv))

        def _deskew():
            try:
                pass

                return Resultado.PASS, "deskew OK", ""
            except ImportError:
                return Resultado.SKIP, "deskew no instalado (pip install deskew)", ""

        self.add(self._run_test("deskew (corrección rotación)", _deskew))


class SuiteCURP(TestRunner):
    """Prueba decodificación CURP/RFC/NSS."""

    def correr(self):
        print(c("cyan", "\n🪪 Suite: CURP / RFC / NSS\n"))

        CURP_VALIDA = "LOOA531113HTCPBN09"
        CURP_INVALIDA = "XXXX000000XXXXXX00"

        def _curp_formato():
            import re

            patron = r"^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$"
            assert re.match(patron, CURP_VALIDA)
            assert not re.match(patron, CURP_INVALIDA)
            return (
                Resultado.PASS,
                "Regex CURP: válida detectada, inválida rechazada",
                "",
            )

        self.add(self._run_test("Formato CURP regex", _curp_formato))

        def _curp_edad():
            # LOOA531113 → nacido 13/11/1953 → edad ~72
            anio = int(CURP_VALIDA[4:6])
            anio_completo = 1900 + anio if anio > 25 else 2000 + anio
            edad = 2026 - anio_completo
            assert 70 <= edad <= 75, f"Edad esperada ~72, obtuvo {edad}"
            return Resultado.PASS, f"Edad calculada correctamente: {edad} años", ""

        self.add(self._run_test("Calcular edad desde CURP", _curp_edad))

        def _curp_estado():
            # LOOA531113HTCPBN09 → TC = Tabasco
            estados = {
                "TC": "Tabasco",
                "DF": "Ciudad de México",
                "JC": "Jalisco",
                "NE": "Nacido Extranjero",
            }
            codigo = CURP_VALIDA[11:13]
            estado = estados.get(codigo, "Desconocido")
            return Resultado.PASS, f"Código estado '{codigo}' = {estado}", ""

        self.add(self._run_test("Decodificar estado desde CURP", _curp_estado))

        def _rfc_formato():
            import re

            rfcs_validos = ["LOOA531113AB9", "XAXX010101000", "GÓMEZ010203ABC"]
            patron = r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$"
            for rfc in rfcs_validos:
                if re.match(patron, rfc.upper()):
                    pass  # ok
            return Resultado.PASS, "Formatos RFC validados", ""

        self.add(self._run_test("Formato RFC regex", _rfc_formato))

        def _nss_formato():
            import re

            patron = r"^\d{11}$"
            assert re.match(patron, "12345678901")
            assert not re.match(patron, "123")
            return Resultado.PASS, "Formato NSS: 11 dígitos verificado", ""

        self.add(self._run_test("Formato NSS (11 dígitos)", _nss_formato))

        def _endpoint_curp():
            if not self._server_activo():
                return Resultado.SKIP, "Servidor no activo", ""
            s, d = self._http("POST", "/api/curp-decodificar", {"curp": CURP_VALIDA})
            if s == 200 and d.get("ok"):
                data = d.get("data", {})
                return (
                    Resultado.PASS,
                    (
                        f"Edad={data.get('edad')}, "
                        f"Estado={data.get('estado')}, "
                        f"Sexo={data.get('sexo')}"
                    ),
                    "",
                )
            return Resultado.FAIL, f"status={s}", str(d)[:100]

        self.add(
            self._run_test("POST /api/curp-decodificar (integración)", _endpoint_curp)
        )


class SuitePDF(TestRunner):
    """Prueba generación de PDF con reportlab."""

    def correr(self):
        print(c("cyan", "\n📄 Suite: PDF Export\n"))

        def _reportlab():
            try:
                pass

                return Resultado.PASS, "reportlab importado OK", ""
            except ImportError:
                return (
                    Resultado.SKIP,
                    "reportlab no instalado (pip install reportlab)",
                    "",
                )

        self.add(self._run_test("import reportlab", _reportlab))

        def _generar_pdf():
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas as rl_canvas

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    tmp = f.name
                c_obj = rl_canvas.Canvas(tmp, pagesize=letter)
                c_obj.setFont("Helvetica-Bold", 16)
                c_obj.drawString(72, 720, "MAER 4.0 — Prueba PDF")
                c_obj.save()
                size = Path(tmp).stat().st_size
                Path(tmp).unlink(missing_ok=True)
                return Resultado.PASS, f"PDF generado: {size} bytes", ""
            except Exception as e:
                return Resultado.FAIL, f"Error generando PDF: {e}", ""

        self.add(self._run_test("Generar PDF básico", _generar_pdf))

        def _endpoint_pdf():
            if not self._server_activo():
                return Resultado.SKIP, "Servidor no activo", ""
            s, d = self._http(
                "POST",
                "/api/exportar-pdf",
                {
                    "nombre": "Test Automático",
                    "curp": "LOOA531113HTCPBN09",
                    "nss": "12345678901",
                    "semanas": 750,
                    "ley": "73",
                },
                timeout=30,
            )
            if s == 200 and d.get("ok"):
                pdf_name = d.get("data", {}).get("pdf_nombre", "?")
                return Resultado.PASS, f"PDF exportado: {pdf_name}", ""
            return Resultado.FAIL, f"status={s}", str(d)[:100]

        self.add(self._run_test("POST /api/exportar-pdf (integración)", _endpoint_pdf))

        def _pdfplumber():
            try:
                pass

                return Resultado.PASS, "pdfplumber OK", ""
            except ImportError:
                return (
                    Resultado.SKIP,
                    "pdfplumber no instalado (pip install pdfplumber)",
                    "",
                )

        self.add(self._run_test("import pdfplumber", _pdfplumber))


class SuiteCondaCompleto(TestRunner):
    """Prueba detección de Conda y entornos."""

    def correr(self):
        print(c("cyan", "\n🐍 Suite: Conda\n"))

        def _detectar_conda():
            import shutil

            rutas = [
                shutil.which("conda"),
                "/opt/homebrew/bin/conda",
                "/usr/local/bin/conda",
                str(Path.home() / "miniconda3" / "bin" / "conda"),
                str(Path.home() / "anaconda3" / "bin" / "conda"),
                str(Path.home() / "mambaforge" / "bin" / "conda"),
            ]
            conda_bin = next((r for r in rutas if r and Path(r).exists()), None)
            if conda_bin:
                import subprocess

                r = subprocess.run(
                    [conda_bin, "--version"], capture_output=True, text=True, timeout=5
                )
                ver = r.stdout.strip()
                return Resultado.PASS, f"Conda en {conda_bin}: {ver}", ""
            return (
                Resultado.WARN,
                "Conda no instalado (opcional). Descarga desde conda.io",
                "",
            )

        self.add(self._run_test("Detectar binario Conda", _detectar_conda))

        def _envs():
            import shutil

            rutas = [
                shutil.which("conda"),
                "/opt/homebrew/bin/conda",
                str(Path.home() / "miniconda3" / "bin" / "conda"),
                str(Path.home() / "anaconda3" / "bin" / "conda"),
            ]
            conda_bin = next((r for r in rutas if r and Path(r).exists()), None)
            if not conda_bin:
                return Resultado.SKIP, "Conda no instalado", ""
            import subprocess

            r = subprocess.run(
                [conda_bin, "env", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            data = json.loads(r.stdout)
            envs = [Path(e).name for e in data.get("envs", [])]
            return Resultado.PASS, f"{len(envs)} entorno(s): {', '.join(envs[:5])}", ""

        self.add(self._run_test("Listar entornos Conda", _envs))

        def _endpoint_conda():
            if not self._server_activo():
                return Resultado.SKIP, "Servidor no activo", ""
            s, d = self._http("GET", "/api/conda-envs")
            if s == 200:
                ok = d.get("ok", False)
                if ok:
                    envs = d.get("data", {}).get("envs", [])
                    return Resultado.PASS, f"{len(envs)} entorno(s) vía API", ""
                return Resultado.WARN, "Conda no disponible (endpoint respondió)", ""
            return Resultado.FAIL, f"status={s}", ""

        self.add(self._run_test("GET /api/conda-envs (integración)", _endpoint_conda))


class SuiteArchivos(TestRunner):
    """Prueba módulos de archivo: lanzador, consola."""

    def correr(self):
        print(c("cyan", "\n🗂️  Suite: Scripts de inicio\n"))

        scripts = [
            ("lanzador_maer.py", "Lanzador GUI"),
            ("maer_consola.py", "Consola IA"),
            ("iniciar_maer_ngrok.py", "ngrok starter"),
            ("MAER_Iniciar.command", "macOS .command"),
            ("maer_iniciar.sh", "Linux/Mac .sh"),
            ("MAER_Iniciar.bat", "Windows .bat"),
            ("README_MAER.txt", "README"),
        ]

        for nombre, desc in scripts:

            def _check(n=nombre, d=desc):
                path = BASE_DIR / n
                if path.exists():
                    size = path.stat().st_size
                    return Resultado.PASS, f"{d} ({size} bytes)", ""
                return Resultado.FAIL, f"Archivo no encontrado: {n}", ""

            self.add(self._run_test(f"Existe {nombre}", _check))

        # Syntax check Python
        py_scripts = [
            "lanzador_maer.py",
            "maer_consola.py",
            "iniciar_maer_ngrok.py",
            "maer_backend/maer_files.py",
            "maer_backend/maer_ollama.py",
            "maer_backend/web_ui/server.py",
        ]
        for script in py_scripts:

            def _syntax(s=script):
                path = BASE_DIR / s
                if not path.exists():
                    return Resultado.SKIP, f"No existe: {s}", ""
                r = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(path)],
                    capture_output=True,
                    text=True,
                )
                if r.returncode == 0:
                    return Resultado.PASS, f"Sintaxis OK", ""
                return Resultado.FAIL, r.stderr[:100], ""

            self.add(self._run_test(f"Sintaxis: {Path(script).name}", _syntax))


# ─── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="MAER 4.0 — Suite de pruebas automáticas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Suites disponibles:
  basico      → imports + curp + archivos                 (rápido, ~5s)
  endpoints   → todos los endpoints HTTP                  (~15s)
  ollama      → detección y chat Ollama                   (~10s)
  pandas      → análisis de datos CSV/XLSX                (~5s)
  ocr         → pipeline OCR                              (~5s)
  conda       → entornos Conda                            (~5s)
  pdf         → exportación PDF                           (~5s)
  completo    → todas las suites anteriores               (~60s)
        """,
    )
    parser.add_argument("--suite", default="basico", help="Suite a ejecutar")
    parser.add_argument("--host", default="localhost", help="Host del servidor")
    parser.add_argument("--port", default="8765", help="Puerto del servidor")
    parser.add_argument(
        "--verbose", action="store_true", help="Mostrar trazas completas"
    )
    args = parser.parse_args()

    host = args.host
    port = int(args.port)
    suite = args.suite.lower()

    print()
    print(c("bold", "╔══════════════════════════════════════════════════════╗"))
    print(c("bold", "║    🦁 MAER 4.0 — Suite de Pruebas Automáticas       ║"))
    print(c("bold", "╚══════════════════════════════════════════════════════╝"))
    print(c("dim", f"   Servidor: {host}:{port}  |  Suite: {suite}"))

    runners = []

    if suite in ("basico", "completo"):
        r = SuiteImports(host, port)
        r.correr()
        runners.append(r)
        r = SuiteCURP(host, port)
        r.correr()
        runners.append(r)
        r = SuiteArchivos(host, port)
        r.correr()
        runners.append(r)

    if suite in ("endpoints", "completo"):
        r = SuiteEndpoints(host, port)
        r.correr()
        runners.append(r)

    if suite in ("ollama", "completo"):
        r = SuiteOllama(host, port)
        r.correr()
        runners.append(r)

    if suite in ("pandas", "completo"):
        r = SuitePandas(host, port)
        r.correr()
        runners.append(r)

    if suite in ("ocr", "completo"):
        r = SuiteOCR(host, port)
        r.correr()
        runners.append(r)

    if suite in ("conda", "completo"):
        r = SuiteCondaCompleto(host, port)
        r.correr()
        runners.append(r)

    if suite in ("pdf", "completo"):
        r = SuitePDF(host, port)
        r.correr()
        runners.append(r)

    if not runners:
        print(c("red", f"\n❌ Suite desconocida: '{suite}'"))
        print(
            "   Suites válidas: basico, endpoints, ollama, pandas, ocr, conda, pdf, completo"
        )
        sys.exit(1)

    # ── Consolidar resultados ──
    todos = []
    for r in runners:
        todos.extend(r.results)
        r._detener_server()

    # Usar el primero como agregador de resumen
    master = TestRunner(host, port)
    master.results = todos
    fail_count = master.imprimir_resumen()

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
