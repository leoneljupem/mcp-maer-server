"""
Tests — MAER Web API (FastAPI)
Leonel Houssen Mojica — Ecatepec MX — 2026
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Tests de API endpoints ─────────────────────────────
class TestWebAPI:
    def test_fastapi_importa(self):
        import fastapi

        assert fastapi is not None

    def test_uvicorn_importa(self):
        import uvicorn

        assert uvicorn is not None

    def test_server_existe(self):
        server = Path(__file__).parent.parent / "maer_backend" / "web_ui" / "server.py"
        assert server.exists(), "server.py debe existir"

    def test_static_dir_existe(self):
        static = Path(__file__).parent.parent / "maer_backend" / "web_ui" / "static"
        assert static.exists(), "Directorio static debe existir"

    def test_css_compact_implementado(self):
        css = (
            Path(__file__).parent.parent
            / "maer_backend"
            / "web_ui"
            / "static"
            / "css"
            / "maer-compact.css"
        )
        assert css.exists()
        contenido = css.read_text()
        assert "TODO" not in contenido, "CSS no debe tener TODOs sin implementar"
        assert len(contenido) > 500, "CSS debe tener contenido real"


# ── Tests de estructura del proyecto ───────────────────
class TestEstructura:
    ARCHIVOS_REQUERIDOS = [
        "index.mjs",
        "package.json",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "maer_backend/maer_files.py",
        "maer_backend/ocr_engine.py",
        "maer_backend/nlp_engine.py",
        "maer_backend/table_extractor.py",
        "maer_backend/web_ui/server.py",
    ]

    def test_archivos_requeridos_existen(self):
        raiz = Path(__file__).parent.parent
        faltantes = []
        for archivo in self.ARCHIVOS_REQUERIDOS:
            if not (raiz / archivo).exists():
                faltantes.append(archivo)
        assert not faltantes, f"Archivos faltantes: {faltantes}"

    def test_no_hay_archivos_gigantes(self):
        raiz = Path(__file__).parent.parent
        limite_mb = 10
        excluir = ["node_modules", ".git", "models", "miniforge", ".gguf"]
        grandes = []
        for f in raiz.rglob("*"):
            if not f.is_file():
                continue
            ruta_str = str(f)
            if any(ex in ruta_str for ex in excluir):
                continue
            if f.stat().st_size > limite_mb * 1024 * 1024:
                grandes.append(f"{f.name} ({f.stat().st_size // 1024 // 1024}MB)")
        assert not grandes, f"Archivos demasiado grandes en el repo: {grandes}"

    def test_no_hay_pdfs_en_raiz(self):
        raiz = Path(__file__).parent.parent
        pdfs_raiz = list(raiz.glob("*.pdf"))
        assert (
            not pdfs_raiz
        ), f"PDFs no deben estar en la raiz: {[p.name for p in pdfs_raiz]}"

    def test_git_inicializado(self):
        git_dir = Path(__file__).parent.parent / ".git"
        assert git_dir.exists(), "El proyecto debe tener Git inicializado"


# ── Tests de nuevos endpoints y módulos JS ─────────────
class TestNuevosEndpoints:
    """Verifica que los nuevos endpoints están declarados en server.py."""

    def _leer_server(self):
        return (
            Path(__file__).parent.parent / "maer_backend" / "web_ui" / "server.py"
        ).read_text()

    def test_endpoint_server_info_existe(self):
        src = self._leer_server()
        assert '"/api/server-info"' in src, "Debe existir /api/server-info"

    def test_endpoint_llm_status_existe(self):
        src = self._leer_server()
        assert '"/api/llm-status"' in src, "Debe existir /api/llm-status"

    def test_endpoint_tasker_receive_existe(self):
        src = self._leer_server()
        assert '"/api/tasker-receive"' in src, "Debe existir /api/tasker-receive"

    def test_server_info_retorna_ip_local(self):
        """server-info debe detectar la IP local."""
        src = self._leer_server()
        assert "ip_local" in src and "socket" in src

    def test_server_info_detecta_ngrok(self):
        src = self._leer_server()
        assert "ngrok" in src and "4040" in src


class TestModulosJSNuevos:
    """Verifica que los módulos JS tienen las funciones nuevas."""

    JS_DIR = Path(__file__).parent.parent / "maer_backend" / "web_ui" / "static" / "js"

    def _leer_js(self, nombre):
        return (self.JS_DIR / nombre).read_text()

    def test_poder_tiene_analizar_con_ia(self):
        src = self._leer_js("maer.poder.js")
        assert "analizarConIA" in src

    def test_poder_tiene_plantilla_ia(self):
        src = self._leer_js("maer.poder.js")
        assert "_plantillaIA" in src

    def test_poder_subtab_ia_en_render(self):
        src = self._leer_js("maer.poder.js")
        assert "poder-sub-ia" in src

    def test_poder_plantillas_cobertura(self):
        src = self._leer_js("maer.poder.js")
        for plantilla in ("semanas", "pension", "documentos", "curp", "expediente"):
            assert plantilla in src, f"Falta plantilla '{plantilla}' en poder.js"

    def test_whatsapp_tiene_filtrar_imss(self):
        src = self._leer_js("maer.whatsapp.js")
        assert "filtrarIMSS" in src

    def test_whatsapp_keywords_imss(self):
        src = self._leer_js("maer.whatsapp.js")
        for kw in ("imss", "pensión", "curp", "semanas", "afore"):
            assert kw in src, f"Falta keyword IMSS '{kw}' en maer.whatsapp.js"

    def test_sistema_tiene_cargar_url_tasker(self):
        src = self._leer_js("maer.sistema.js")
        assert "_cargarUrlTasker" in src

    def test_sistema_llama_api_server_info(self):
        src = self._leer_js("maer.sistema.js")
        assert "server-info" in src
