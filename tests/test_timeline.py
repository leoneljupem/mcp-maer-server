"""
Tests — MAER Bloque 7: Timeline Visual del Proceso de Pensión IMSS
Leonel Houssen Mojica — Ecatepec MX — 2026
"""

from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
JS_TIMELINE = RAIZ / "maer_backend" / "web_ui" / "static" / "js" / "maer.timeline.js"
CSS_MAER = RAIZ / "maer_backend" / "web_ui" / "static" / "css" / "maer.css"
INDEX_HTML = RAIZ / "maer_backend" / "web_ui" / "static" / "index.html"


class TestTimelineArchivos:
    """Bloque 7 — T1: Los archivos del módulo existen y no están vacíos."""

    def test_maer_timeline_js_existe(self):
        assert JS_TIMELINE.exists(), "maer.timeline.js debe existir"
        assert JS_TIMELINE.stat().st_size > 500, "maer.timeline.js no debe estar vacío"

    def test_timeline_cargado_en_index_html(self):
        contenido = INDEX_HTML.read_text()
        assert (
            "maer.timeline.js" in contenido
        ), "maer.timeline.js debe estar en index.html"

    def test_timeline_panel_div_en_html(self):
        contenido = INDEX_HTML.read_text()
        assert (
            'id="timeline-panel"' in contenido
        ), "#timeline-panel debe existir en index.html"


class TestTimelineCSS:
    """Bloque 7 — T2: Las clases CSS del timeline están definidas."""

    CLASES_REQUERIDAS = [
        ".timeline-track",
        ".timeline-etapa",
        ".timeline-completada",
        ".timeline-actual",
        ".timeline-pendiente",
        ".timeline-icon",
        ".timeline-info",
        ".timeline-label",
        ".timeline-fecha",
        ".timeline-dias",
        ".timeline-line",
    ]

    def test_clases_css_existen(self):
        css = CSS_MAER.read_text()
        faltantes = [c for c in self.CLASES_REQUERIDAS if c not in css]
        assert not faltantes, f"Clases CSS faltantes en maer.css: {faltantes}"

    def test_animacion_timeline_pulse_existe(self):
        css = CSS_MAER.read_text()
        assert "timeline-pulse" in css, "Animación timeline-pulse debe estar definida"


class TestTimelineJS:
    """Bloque 7 — T3: La lógica JavaScript del timeline es correcta."""

    @pytest.fixture(autouse=True)
    def contenido(self):
        self.js = JS_TIMELINE.read_text()

    def test_ocho_etapas_definidas(self):
        # Verificar que las 8 etapas del proceso estén declaradas
        etapas = [
            "documentos",
            "pre-revision",
            "solicitud",
            "revision",
            "resolucion",
            "recurso",
            "amparo",
            "otorgada",
        ]
        for etapa in etapas:
            assert (
                f"'{etapa}'" in self.js or f'"{etapa}"' in self.js
            ), f"Etapa '{etapa}' debe estar definida en maer.timeline.js"

    def test_storage_key_definido(self):
        assert (
            "maer_timeline" in self.js
        ), "STORAGE_KEY 'maer_timeline' debe estar en maer.timeline.js"

    def test_metodos_publicos_existen(self):
        for metodo in ["init()", "marcar(", "obtenerActual()", "render()"]:
            assert (
                metodo in self.js
            ), f"Método '{metodo}' debe estar en maer.timeline.js"

    def test_persistencia_localstorage(self):
        assert "localStorage.setItem" in self.js, "Debe guardar en localStorage"
        assert "localStorage.getItem" in self.js, "Debe leer de localStorage"

    def test_guardian_registra_timeline(self):
        guardian_js = (
            RAIZ / "maer_backend" / "web_ui" / "static" / "js" / "maer.guardian.js"
        )
        assert guardian_js.exists(), "maer.guardian.js debe existir"
        contenido = guardian_js.read_text()
        assert (
            "maer.timeline" in contenido
        ), "maer.guardian.js debe registrar el módulo timeline"
        assert (
            "MAER.timeline" in contenido
        ), "maer.guardian.js debe verificar MAER.timeline"
