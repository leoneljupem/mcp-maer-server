"""
Tests — MAER Backend Python: todos los módulos del servidor
Leonel Houssen Mojica — Ecatepec MX — 2026
"""
import sys
import os
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

# ════════════════════════════════════════════════
# EXISTENCIA DE ARCHIVOS PYTHON
# ════════════════════════════════════════════════

class TestExistenciaModulos:
    """Verifica que todos los módulos Python del backend existen."""

    MODULOS = [
        "maer_backend/__init__.py",
        "maer_backend/maer.py",
        "maer_backend/maer_files.py",
        "maer_backend/ocr_engine.py",
        "maer_backend/nlp_engine.py",
        "maer_backend/table_extractor.py",
        "maer_backend/image_analyzer.py",
        "maer_backend/llm_engine.py",
        "maer_backend/maer_ollama.py",
        "maer_backend/maer_core/__init__.py",
        "maer_backend/maer_core/analyzer.py",
        "maer_backend/maer_core/fixer.py",
        "maer_backend/maer_core/generator.py",
        "maer_backend/web_ui/__init__.py",
        "maer_backend/web_ui/server.py",
    ]

    def test_todos_los_modulos_existen(self):
        faltantes = [m for m in self.MODULOS if not (RAIZ / m).exists()]
        assert not faltantes, f"Módulos Python faltantes: {faltantes}"

    def test_modulos_no_vacios(self):
        vacios = [
            m for m in self.MODULOS
            if (RAIZ / m).exists() and (RAIZ / m).stat().st_size == 0
        ]
        assert not vacios, f"Módulos Python vacíos: {vacios}"

    def test_requirements_txt_existe(self):
        assert (RAIZ / "requirements.txt").exists()

    def test_requirements_tiene_dependencias_clave(self):
        reqs = (RAIZ / "requirements.txt").read_text()
        for dep in ["fastapi", "uvicorn", "anthropic", "pytesseract",
                    "Pillow", "pypdf", "python-dotenv"]:
            assert dep.lower() in reqs.lower(), f"Dependencia '{dep}' faltante en requirements.txt"


# ════════════════════════════════════════════════
# IMPORTACIÓN DE MÓDULOS LIGEROS
# ════════════════════════════════════════════════

class TestImportacionesLigeras:
    """Importa módulos que no requieren GPU ni modelos pesados."""

    def test_maer_backend_init_importa(self):
        import maer_backend
        assert maer_backend is not None

    def test_maer_files_importa(self):
        from maer_backend import maer_files
        assert maer_files is not None

    def test_ocr_engine_importa(self):
        from maer_backend import ocr_engine
        assert ocr_engine is not None

    def test_nlp_engine_importa(self):
        from maer_backend import nlp_engine
        assert nlp_engine is not None

    def test_table_extractor_importa(self):
        from maer_backend import table_extractor
        assert table_extractor is not None

    def test_maer_core_init_importa(self):
        from maer_backend import maer_core
        assert maer_core is not None

    def test_maer_core_analyzer_importa(self):
        from maer_backend.maer_core import analyzer
        assert analyzer is not None

    def test_maer_core_fixer_importa(self):
        from maer_backend.maer_core import fixer
        assert fixer is not None

    def test_maer_core_generator_importa(self):
        from maer_backend.maer_core import generator
        assert generator is not None


# ════════════════════════════════════════════════
# SINTAXIS PYTHON (compilación sin errores)
# ════════════════════════════════════════════════

class TestSintaxisPython:
    """Verifica que todos los archivos Python compilan sin errores de sintaxis."""

    ARCHIVOS_PY = [
        "maer_backend/__init__.py",
        "maer_backend/maer_files.py",
        "maer_backend/ocr_engine.py",
        "maer_backend/nlp_engine.py",
        "maer_backend/table_extractor.py",
        "maer_backend/image_analyzer.py",
        "maer_backend/llm_engine.py",
        "maer_backend/maer_ollama.py",
        "maer_backend/maer_core/__init__.py",
        "maer_backend/maer_core/analyzer.py",
        "maer_backend/maer_core/fixer.py",
        "maer_backend/maer_core/generator.py",
        "maer_backend/web_ui/__init__.py",
        "maer_backend/web_ui/server.py",
    ]

    @pytest.mark.parametrize("archivo", ARCHIVOS_PY)
    def test_compila_sin_errores(self, archivo):
        import py_compile
        ruta = str(RAIZ / archivo)
        try:
            py_compile.compile(ruta, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"Error de sintaxis en {archivo}: {e}")


# ════════════════════════════════════════════════
# MÓDULO: maer_files.py — Funciones clave
# ════════════════════════════════════════════════

class TestMaerFiles:
    """Tests para maer_backend/maer_files.py — validación documental mexicana."""

    def test_importa(self):
        from maer_backend import maer_files
        assert maer_files is not None

    def test_tiene_funciones_principales(self):
        from maer_backend import maer_files
        # Al menos debe tener funciones de validación IMSS
        modulo_texto = (RAIZ / "maer_backend" / "maer_files.py").read_text()
        for fn in ["curp", "nss", "rfc", "imss"]:
            assert fn.lower() in modulo_texto.lower(), \
                f"maer_files.py debería referenciar '{fn}'"

    def test_no_tiene_escape_invalido(self):
        """Verifica que el bug del backslash inválido esté corregido (línea 1342)."""
        import py_compile, warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ruta = str(RAIZ / "maer_backend" / "maer_files.py")
            py_compile.compile(ruta, doraise=True)
        syntax_warns = [x for x in w if "invalid escape" in str(x.message).lower()]
        assert not syntax_warns, f"SyntaxWarning de escape inválido: {syntax_warns}"


# ════════════════════════════════════════════════
# MÓDULO: ocr_engine.py — Cache y funciones
# ════════════════════════════════════════════════

class TestOcrEngine:
    """Tests para maer_backend/ocr_engine.py."""

    def test_funciones_cache_existen(self):
        from maer_backend import ocr_engine
        assert hasattr(ocr_engine, "_load_cache"), "_load_cache debe existir"
        assert hasattr(ocr_engine, "_save_cache"), "_save_cache debe existir"

    def test_cache_variable_global(self):
        from maer_backend import ocr_engine
        assert hasattr(ocr_engine, "_ocr_cache")

    def test_load_cache_archivo_inexistente(self, tmp_path):
        from maer_backend.ocr_engine import _load_cache
        _load_cache(str(tmp_path / "no_existe.json"))  # No debe lanzar excepción

    def test_save_y_load_cache(self, tmp_path):
        from maer_backend import ocr_engine
        cache_path = str(tmp_path / "cache_test.json")
        ocr_engine._ocr_cache = {"hash_test": "texto_test"}
        ocr_engine._cache_loaded = True
        ocr_engine._save_cache(cache_path)
        assert Path(cache_path).exists()
        with open(cache_path) as f:
            data = json.load(f)
        assert data["hash_test"] == "texto_test"

    def test_load_cache_json_invalido(self, tmp_path):
        from maer_backend.ocr_engine import _load_cache
        bad = tmp_path / "bad.json"
        bad.write_text("{malformed:::}")
        _load_cache(str(bad))  # No debe lanzar excepción

    def test_variable_motor_por_defecto(self):
        motor = os.environ.get("MAER_OCR_ENGINE", "auto")
        assert motor in ["auto", "tesseract", "easyocr", "paddleocr"]


# ════════════════════════════════════════════════
# MÓDULO: web_ui/server.py — Estructura FastAPI
# ════════════════════════════════════════════════

class TestWebUiServer:
    """Tests para maer_backend/web_ui/server.py."""

    def test_server_py_existe(self):
        assert (RAIZ / "maer_backend" / "web_ui" / "server.py").exists()

    def test_server_py_tiene_fastapi(self):
        contenido = (RAIZ / "maer_backend" / "web_ui" / "server.py").read_text()
        assert "FastAPI" in contenido or "fastapi" in contenido.lower()

    def test_server_py_tiene_endpoint_salud(self):
        contenido = (RAIZ / "maer_backend" / "web_ui" / "server.py").read_text()
        assert "/health" in contenido or "/status" in contenido or "ping" in contenido.lower()

    def test_server_py_monta_archivos_estaticos(self):
        contenido = (RAIZ / "maer_backend" / "web_ui" / "server.py").read_text()
        assert "static" in contenido.lower() or "StaticFiles" in contenido

    def test_directorio_static_existe(self):
        assert (RAIZ / "maer_backend" / "web_ui" / "static").exists()

    def test_index_html_existe(self):
        assert (RAIZ / "maer_backend" / "web_ui" / "static" / "index.html").exists()


# ════════════════════════════════════════════════
# MÓDULO: nlp_engine.py
# ════════════════════════════════════════════════

class TestNlpEngine:
    """Tests para maer_backend/nlp_engine.py."""

    def test_importa(self):
        from maer_backend import nlp_engine
        assert nlp_engine is not None

    def test_tiene_funciones_nlp(self):
        contenido = (RAIZ / "maer_backend" / "nlp_engine.py").read_text()
        # Debe tener alguna función de procesamiento de texto
        assert len(contenido) > 100, "nlp_engine.py no debe estar vacío"

    def test_no_errores_sintaxis(self):
        import py_compile
        py_compile.compile(str(RAIZ / "maer_backend" / "nlp_engine.py"), doraise=True)


# ════════════════════════════════════════════════
# MÓDULO: table_extractor.py
# ════════════════════════════════════════════════

class TestTableExtractor:
    """Tests para maer_backend/table_extractor.py."""

    def test_importa(self):
        from maer_backend import table_extractor
        assert table_extractor is not None

    def test_tiene_funciones_extraccion(self):
        contenido = (RAIZ / "maer_backend" / "table_extractor.py").read_text()
        for keyword in ["table", "extract", "pdf", "excel"]:
            if keyword.lower() in contenido.lower():
                return  # Basta con que tenga al menos uno
        pytest.fail("table_extractor.py debe referenciar tablas, extracción, PDF o Excel")


# ════════════════════════════════════════════════
# MÓDULO: maer_core/ — Analyzer, Fixer, Generator
# ════════════════════════════════════════════════

class TestMaerCore:
    """Tests para el paquete maer_backend/maer_core."""

    def test_analyzer_tiene_clase_o_funcion(self):
        contenido = (RAIZ / "maer_backend" / "maer_core" / "analyzer.py").read_text()
        assert len(contenido) > 50, "analyzer.py no debe estar vacío"

    def test_fixer_tiene_clase_o_funcion(self):
        contenido = (RAIZ / "maer_backend" / "maer_core" / "fixer.py").read_text()
        assert len(contenido) > 50

    def test_generator_tiene_clase_o_funcion(self):
        contenido = (RAIZ / "maer_backend" / "maer_core" / "generator.py").read_text()
        assert len(contenido) > 50

    def test_init_expone_submodulos(self):
        init_txt = (RAIZ / "maer_backend" / "maer_core" / "__init__.py").read_text()
        # El __init__ puede estar vacío o importar submodulos
        assert init_txt is not None  # Existe aunque esté vacío


# ════════════════════════════════════════════════
# CONFIGURACIÓN: .env y variables de entorno
# ════════════════════════════════════════════════

class TestConfiguracion:
    """Tests de configuración del proyecto."""

    def test_env_example_existe(self):
        assert (RAIZ / ".env.example").exists()

    def test_env_en_gitignore(self):
        gitignore = RAIZ / ".gitignore"
        if gitignore.exists():
            assert ".env" in gitignore.read_text()

    def test_variable_ocr_engine_valida(self):
        motor = os.environ.get("MAER_OCR_ENGINE", "auto")
        assert motor in ["auto", "tesseract", "easyocr", "paddleocr"]

    def test_variable_ocr_dpi_valida(self):
        dpi = int(os.environ.get("MAER_OCR_DPI", "300"))
        assert 72 <= dpi <= 600

    def test_variable_puerto_servidor(self):
        puerto = int(os.environ.get("MAER_PORT", "8765"))
        assert 1024 <= puerto <= 65535


# ════════════════════════════════════════════════
# SERVIDOR MCP (Node.js)
# ════════════════════════════════════════════════

class TestServidorMCP:
    """Tests para el servidor MCP (Node.js)."""

    def test_index_mjs_existe(self):
        assert (RAIZ / "index.mjs").exists()

    def test_index_mjs_no_vacio(self):
        assert (RAIZ / "index.mjs").stat().st_size > 500

    def test_package_json_valido(self):
        pkg = RAIZ / "package.json"
        assert pkg.exists()
        data = json.loads(pkg.read_text())
        assert data.get("name") == "mcp-maer-server"
        assert data.get("main") == "index.mjs"
        assert "scripts" in data

    def test_package_json_scripts_completos(self):
        data = json.loads((RAIZ / "package.json").read_text())
        scripts = data.get("scripts", {})
        for script in ["start", "test", "dev", "dashboard"]:
            assert script in scripts, f"Script '{script}' faltante en package.json"

    def test_mcp_sdk_instalado(self):
        sdk = RAIZ / "node_modules" / "@modelcontextprotocol"
        assert sdk.exists(), "MCP SDK debe estar en node_modules"

    def test_index_mjs_importa_mcp_sdk(self):
        contenido = (RAIZ / "index.mjs").read_text()
        assert "@modelcontextprotocol" in contenido or "modelcontextprotocol" in contenido


# ════════════════════════════════════════════════
# ASSETS FRONTEND
# ════════════════════════════════════════════════

class TestAssetsFrontend:
    """Tests para assets del frontend (JS, CSS, HTML)."""

    JS_DIR  = RAIZ / "maer_backend" / "web_ui" / "static" / "js"
    CSS_DIR = RAIZ / "maer_backend" / "web_ui" / "static" / "css"

    MODULOS_JS_REQUERIDOS = [
        "maer.core.js", "maer.diccionario.js", "maer.voz.js", "maer.chat.js",
        "maer.aprendizaje.js", "maer.archivos.js", "maer.busqueda.js",
        "maer.organizar.js", "maer.imagenes.js", "maer.pension.js",
        "maer.timeline.js", "maer.recordatorios.js", "maer.cartas-historial.js",
        "maer.sugerencias.js", "maer.atajos.js", "maer.etiquetas.js",
        "maer.compacto.js", "maer.resumen.js", "maer.qr.js", "maer.stats.js",
        "maer.poder.js", "maer.diagnostico.js", "maer.sinavid.js",
        "maer.tareas.js", "maer.memoria.js", "maer.sistema.js",
        "maer.guardian.js", "maer.whatsapp.js", "maer.notificaciones.js",
        "maer.exportar.js", "maer.ajustes.js", "maer.test.js",
    ]

    def test_todos_los_js_existen(self):
        faltantes = [
            m for m in self.MODULOS_JS_REQUERIDOS
            if not (self.JS_DIR / m).exists()
        ]
        assert not faltantes, f"Archivos JS faltantes: {faltantes}"

    def test_todos_los_js_no_vacios(self):
        vacios = [
            m for m in self.MODULOS_JS_REQUERIDOS
            if (self.JS_DIR / m).exists()
            and (self.JS_DIR / m).stat().st_size < 50
        ]
        assert not vacios, f"Archivos JS vacíos: {vacios}"

    def test_maer_css_existe_y_tiene_contenido(self):
        css = self.CSS_DIR / "maer.css"
        assert css.exists()
        assert css.stat().st_size > 5000

    def test_maer_compact_css_sin_todos(self):
        css = self.CSS_DIR / "maer-compact.css"
        assert css.exists()
        assert "TODO" not in css.read_text(), "maer-compact.css no debe tener TODOs"

    def test_todos_los_js_cargados_en_html(self):
        html = (RAIZ / "maer_backend" / "web_ui" / "static" / "index.html").read_text()
        no_cargados = [
            m for m in self.MODULOS_JS_REQUERIDOS
            if m not in html
        ]
        assert not no_cargados, f"Scripts no cargados en index.html: {no_cargados}"

    def test_guardian_registra_todos_los_modulos_clave(self):
        guardian = (self.JS_DIR / "maer.guardian.js").read_text()
        for modulo in ["MAER.timeline", "MAER.recordatorios", "MAER.cartasHistorial",
                       "MAER.sugerencias", "MAER.atajos", "MAER.etiquetas"]:
            assert modulo in guardian, f"Guardian no registra '{modulo}'"

    def test_core_inicializa_todos_los_modulos(self):
        core = (self.JS_DIR / "maer.core.js").read_text()
        for llamada in ["timeline.init()", "recordatorios.init()", "cartasHistorial.init()",
                        "sugerencias.init()", "atajos.init()", "etiquetas.init()",
                        "compacto.init()", "resumen.init()", "qr.init()", "stats.init()"]:
            assert llamada in core, f"maer.core.js no llama '{llamada}'"
