"""
Tests — MAER OCR Engine
Leonel Houssen Mojica — Ecatepec MX — 2026
"""

import json
import os
import sys
from pathlib import Path


# Agregar raiz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURES = Path(__file__).parent / "fixtures"


# ── Tests de importacion ────────────────────────────────
class TestImportaciones:
    def test_ocr_engine_importa(self):
        from maer_backend import ocr_engine

        assert ocr_engine is not None

    def test_maer_files_importa(self):
        from maer_backend import maer_files

        assert maer_files is not None

    def test_nlp_engine_importa(self):
        from maer_backend import nlp_engine

        assert nlp_engine is not None

    def test_table_extractor_importa(self):
        from maer_backend import table_extractor

        assert table_extractor is not None


# ── Tests de cache OCR ─────────────────────────────────
class TestCacheOCR:
    def test_cache_carga_sin_error(self, tmp_path):
        from maer_backend.ocr_engine import _load_cache

        cache_path = str(tmp_path / "test_cache.json")
        # Cache inexistente no debe romper
        _load_cache(cache_path)

    def test_cache_guarda_y_carga(self, tmp_path):
        from maer_backend import ocr_engine

        cache_path = str(tmp_path / "test_cache.json")
        # Resetear estado global
        ocr_engine._ocr_cache = {"test_hash": "texto de prueba"}
        ocr_engine._cache_loaded = True
        ocr_engine._save_cache(cache_path)
        # Verificar que se guardo
        assert Path(cache_path).exists()
        with open(cache_path) as f:
            data = json.load(f)
        assert data.get("test_hash") == "texto de prueba"

    def test_cache_json_invalido_no_rompe(self, tmp_path):
        from maer_backend.ocr_engine import _load_cache

        cache_path = tmp_path / "bad_cache.json"
        cache_path.write_text("{ json invalido :::}")
        # No debe lanzar excepcion
        _load_cache(str(cache_path))


# ── Tests de validacion documental mexicana ────────────
class TestValidacionMexicana:
    CURPS_VALIDOS = [
        "LOOA531113HTCPBN09",
        "SAHE800107MDFNRN01",
        "GOMA890312HMCRRR01",
    ]
    CURPS_INVALIDOS = [
        "12345678",
        "CURP_INVALIDA",
        "",
        "AAAA000000XXXXXX00",
    ]

    def test_curp_longitud_valida(self):
        for curp in self.CURPS_VALIDOS:
            assert len(curp) == 18, f"CURP deberia tener 18 chars: {curp}"

    def test_curp_longitud_invalida(self):
        import re

        patron = r"^[A-Z]{4}\d{6}[HM][A-Z]{5}\d{2}$"
        for curp in self.CURPS_INVALIDOS:
            assert not re.match(patron, curp), f"CURP invalida no deberia pasar: {curp}"

    def test_curp_patron_basico(self):
        import re

        patron = r"^[A-Z]{4}\d{6}[HM][A-Z]{5}\d{2}$"
        for curp in self.CURPS_VALIDOS:
            assert re.match(patron, curp), f"CURP no coincide patron: {curp}"


# ── Tests de archivos fixtures ─────────────────────────
class TestFixtures:
    def test_pdf_ejemplo_existe(self):
        pdf = FIXTURES / "sample.pdf"
        assert pdf.exists(), "sample.pdf debe existir en fixtures"

    def test_pdf_no_vacio(self):
        pdf = FIXTURES / "sample.pdf"
        if pdf.exists():
            assert pdf.stat().st_size > 0, "sample.pdf no debe estar vacio"

    def test_directorio_imagenes_existe(self):
        imgs = FIXTURES / "images"
        assert imgs.exists(), "Directorio fixtures/images debe existir"


# ── Tests de configuracion .env ────────────────────────
class TestConfiguracion:
    def test_env_example_existe(self):
        env_example = Path(__file__).parent.parent / ".env.example"
        assert env_example.exists(), ".env.example debe existir"

    def test_env_local_no_en_git(self):
        gitignore = Path(__file__).parent.parent / ".gitignore"
        if gitignore.exists():
            contenido = gitignore.read_text()
            assert ".env" in contenido, ".env debe estar en .gitignore"

    def test_variables_ocr_con_defaults(self):
        # Sin .env, deben usarse valores por defecto
        motor = os.environ.get("MAER_OCR_ENGINE", "auto")
        dpi = int(os.environ.get("MAER_OCR_DPI", "300"))
        assert motor in ["auto", "tesseract", "easyocr", "paddleocr"]
        assert 72 <= dpi <= 600


# ── Tests del servidor MCP (Node) ──────────────────────
class TestServidorMCP:
    def test_index_mjs_existe(self):
        index = Path(__file__).parent.parent / "index.mjs"
        assert index.exists(), "index.mjs debe existir"

    def test_package_json_valido(self):
        pkg = Path(__file__).parent.parent / "package.json"
        assert pkg.exists()
        with open(pkg) as f:
            data = json.load(f)
        assert "name" in data
        assert "main" in data
        assert data["main"] == "index.mjs"

    def test_node_modules_mcp_sdk(self):
        sdk = Path(__file__).parent.parent / "node_modules" / "@modelcontextprotocol"
        assert sdk.exists(), "MCP SDK debe estar instalado en node_modules"
