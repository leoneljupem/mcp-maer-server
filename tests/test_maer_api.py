"""
Tests — MAER Web API (FastAPI)
Leonel Houssen Mojica — Ecatepec MX — 2026
"""
import sys
import pytest
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
        css = Path(__file__).parent.parent / "maer_backend" / "web_ui" / "static" / "css" / "maer-compact.css"
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
        assert not pdfs_raiz, f"PDFs no deben estar en la raiz: {[p.name for p in pdfs_raiz]}"

    def test_git_inicializado(self):
        git_dir = Path(__file__).parent.parent / ".git"
        assert git_dir.exists(), "El proyecto debe tener Git inicializado"
