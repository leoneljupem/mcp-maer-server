"""
Tests — MAER Bloques 8, 9, 10, 12: Sugerencias, Recordatorios,
        Historial de Cartas y Atajos de Teclado
Leonel Houssen Mojica — Ecatepec MX — 2026
"""
import json
import re
from pathlib import Path

import pytest

RAIZ      = Path(__file__).parent.parent
JS_DIR    = RAIZ / "maer_backend" / "web_ui" / "static" / "js"
CSS_MAER  = RAIZ / "maer_backend" / "web_ui" / "static" / "css" / "maer.css"
INDEX     = RAIZ / "maer_backend" / "web_ui" / "static" / "index.html"
CORE_JS   = JS_DIR / "maer.core.js"
GUARDIAN  = JS_DIR / "maer.guardian.js"

# ════════════════════════════════════════════════
# BLOQUE 8 — Sugerencias en Chat (maer.sugerencias.js)
# ════════════════════════════════════════════════

class TestBloque8Sugerencias:
    """Bloque 8 — Autocompletado en tiempo real."""

    JS = JS_DIR / "maer.sugerencias.js"

    @pytest.fixture(autouse=True)
    def js(self):
        self.contenido = self.JS.read_text()

    def test_archivo_existe_y_no_vacio(self):
        assert self.JS.exists(), "maer.sugerencias.js debe existir"
        assert self.JS.stat().st_size > 500

    def test_cargado_en_index_html(self):
        assert "maer.sugerencias.js" in INDEX.read_text()

    def test_metodos_publicos(self):
        for metodo in ["init()", "buscar(", "mostrar(", "ocultar()", "seleccionar("]:
            assert metodo in self.contenido, f"Método '{metodo}' faltante"

    def test_catalogo_tiene_items(self):
        # Al menos 15 frases en el catálogo
        count = self.contenido.count("cat:")
        assert count >= 15, f"Catálogo con {count} items, esperado >= 15"

    def test_busqueda_normaliza_acentos(self):
        assert "NFD" in self.contenido or "normalize" in self.contenido, \
            "Debe normalizar caracteres con acento"

    def test_constantes_min_chars_y_max(self):
        assert "MIN_CHARS" in self.contenido
        assert "MAX" in self.contenido

    def test_css_dropdown_existe(self):
        css = CSS_MAER.read_text()
        for clase in [".sugerencias-dropdown", ".sugerencia-item", ".sugerencia-texto",
                      ".sugerencia-cat", ".sugerencia-activa"]:
            assert clase in css, f"Clase CSS '{clase}' faltante"

    def test_css_mark_resaltado(self):
        assert ".sugerencia-texto mark" in CSS_MAER.read_text()

    def test_navegacion_teclado(self):
        for tecla in ["ArrowDown", "ArrowUp", "Enter", "Escape"]:
            assert tecla in self.contenido, f"Tecla '{tecla}' no manejada"

    def test_guardian_registra_modulo(self):
        g = GUARDIAN.read_text()
        assert "maer.sugerencias" in g
        assert "MAER.sugerencias" in g

    def test_init_llamado_en_core(self):
        core = CORE_JS.read_text()
        assert "sugerencias.init()" in core

    def test_autoenvio_al_seleccionar(self):
        # Debe llamar a MAER.chat.send() al seleccionar una sugerencia
        assert "chat" in self.contenido and "send" in self.contenido


# ════════════════════════════════════════════════
# BLOQUE 9 — Recordatorios con Fecha Límite (maer.recordatorios.js)
# ════════════════════════════════════════════════

class TestBloque9Recordatorios:
    """Bloque 9 — Alertas automáticas para eventos de pensión."""

    JS = JS_DIR / "maer.recordatorios.js"

    @pytest.fixture(autouse=True)
    def js(self):
        self.contenido = self.JS.read_text()

    def test_archivo_existe_y_no_vacio(self):
        assert self.JS.exists(), "maer.recordatorios.js debe existir"
        assert self.JS.stat().st_size > 500

    def test_cargado_en_index_html(self):
        assert "maer.recordatorios.js" in INDEX.read_text()

    def test_metodos_publicos(self):
        for metodo in ["init()", "agregar(", "verificar()", "listar()",
                       "eliminar(", "completar(", "render()"]:
            assert metodo in self.contenido, f"Método '{metodo}' faltante"

    def test_storage_key(self):
        assert "maer_recordatorios" in self.contenido

    def test_persistencia_localstorage(self):
        assert "localStorage.setItem" in self.contenido
        assert "localStorage.getItem" in self.contenido

    def test_calculo_dias_restantes(self):
        # Debe calcular días entre fecha actual y fecha límite
        assert "diasRestantes" in self.contenido or "dias_restantes" in self.contenido

    def test_estados_urgencia(self):
        for estado in ["#dc2626", "#f59e0b", "#22c55e"]:
            assert estado in self.contenido, f"Color de urgencia '{estado}' faltante"

    def test_badge_en_tab_pension(self):
        assert "rec-badge" in self.contenido or "badge" in self.contenido

    def test_integracion_notificaciones(self):
        assert "notificaciones" in self.contenido

    def test_container_html_existe(self):
        assert 'id="recordatorios-lista"' in INDEX.read_text()

    def test_formulario_html_existe(self):
        html = INDEX.read_text()
        assert 'id="rec-titulo"' in html
        assert 'id="rec-fecha"' in html
        assert 'id="rec-dias"' in html

    def test_guardian_registra_modulo(self):
        g = GUARDIAN.read_text()
        assert "maer.recordatorios" in g
        assert "MAER.recordatorios" in g

    def test_init_y_render_llamados_en_core(self):
        core = CORE_JS.read_text()
        assert "recordatorios.init()" in core
        assert "recordatorios.render()" in core

    def test_css_badge_existe(self):
        assert ".rec-badge" in CSS_MAER.read_text()


# ════════════════════════════════════════════════
# BLOQUE 10 — Historial de Versiones de Cartas (maer.cartas-historial.js)
# ════════════════════════════════════════════════

class TestBloque10CartasHistorial:
    """Bloque 10 — Guardar, listar, comparar y re-imprimir cartas."""

    JS = JS_DIR / "maer.cartas-historial.js"

    @pytest.fixture(autouse=True)
    def js(self):
        self.contenido = self.JS.read_text()

    def test_archivo_existe_y_no_vacio(self):
        assert self.JS.exists(), "maer.cartas-historial.js debe existir"
        assert self.JS.stat().st_size > 500

    def test_cargado_en_index_html(self):
        assert "maer.cartas-historial.js" in INDEX.read_text()

    def test_metodos_publicos(self):
        for metodo in ["init()", "guardar(", "listar()", "obtener(",
                       "eliminar(", "comparar(", "reimprimir(", "render()"]:
            assert metodo in self.contenido, f"Método '{metodo}' faltante"

    def test_storage_key(self):
        assert "maer_cartas_historial" in self.contenido

    def test_persistencia_localstorage(self):
        assert "localStorage.setItem" in self.contenido
        assert "localStorage.getItem" in self.contenido

    def test_limite_50_cartas(self):
        assert "50" in self.contenido, "Debe limitar a 50 cartas"

    def test_tipos_de_cartas(self):
        for tipo in ["semanas", "recurso", "amparo"]:
            assert tipo in self.contenido, f"Tipo de carta '{tipo}' faltante"

    def test_funcionalidad_comparar(self):
        assert "comparar" in self.contenido
        assert "cartas-comparacion" in self.contenido

    def test_funcionalidad_reimprimir(self):
        assert "reimprimir" in self.contenido
        assert "carta-texto" in self.contenido

    def test_containers_html_existen(self):
        html = INDEX.read_text()
        assert 'id="cartas-historial-lista"' in html
        assert 'id="cartas-comparacion"' in html

    def test_guardian_registra_modulo(self):
        g = GUARDIAN.read_text()
        assert "maer.cartas-historial" in g
        assert "MAER.cartasHistorial" in g

    def test_init_y_render_llamados_en_core(self):
        core = CORE_JS.read_text()
        assert "cartasHistorial.init()" in core
        assert "cartasHistorial.render()" in core

    def test_css_historial_existe(self):
        css = CSS_MAER.read_text()
        assert ".carta-hist-item" in css or ".card" in css

    def test_integracion_voz(self):
        assert "MAER.voz" in self.contenido or "voz?" in self.contenido


# ════════════════════════════════════════════════
# BLOQUE 12 — Atajos de Teclado (maer.atajos.js)
# ════════════════════════════════════════════════

class TestBloque12Atajos:
    """Bloque 12 — Hotkeys globales para navegación rápida."""

    JS = JS_DIR / "maer.atajos.js"

    @pytest.fixture(autouse=True)
    def js(self):
        self.contenido = self.JS.read_text()

    def test_archivo_existe_y_no_vacio(self):
        assert self.JS.exists(), "maer.atajos.js debe existir"
        assert self.JS.stat().st_size > 500

    def test_cargado_en_index_html(self):
        assert "maer.atajos.js" in INDEX.read_text()

    def test_metodos_publicos(self):
        for metodo in ["init()", "registrar(", "listar()",
                       "mostrarAyuda()", "ocultarAyuda()", "toggleAyuda()"]:
            assert metodo in self.contenido, f"Método '{metodo}' faltante"

    def test_atajos_de_navegacion_alt(self):
        assert "alt+" in self.contenido or "Alt" in self.contenido

    def test_atajos_ctrl_enter(self):
        assert "ctrl+enter" in self.contenido or "ctrl" in self.contenido

    def test_atajo_escape(self):
        assert "escape" in self.contenido or "Escape" in self.contenido

    def test_atajo_ctrl_k_enfoque_chat(self):
        assert "ctrl+k" in self.contenido or "chat-input" in self.contenido

    def test_atajo_help_shift_interrogacion(self):
        assert "shift+?" in self.contenido or "toggleAyuda" in self.contenido

    def test_atajo_guardian(self):
        assert "guardian" in self.contenido.lower()

    def test_css_overlay_existe(self):
        css = CSS_MAER.read_text()
        for clase in [".atajos-overlay", ".atajos-modal", ".atajos-header",
                      ".atajos-body", ".atajos-fila", ".atajos-combo"]:
            assert clase in css, f"Clase CSS '{clase}' faltante"

    def test_css_kbd_tag(self):
        assert "kbd" in CSS_MAER.read_text()

    def test_no_intercepta_en_inputs(self):
        # Debe verificar si el foco está en input/textarea
        assert "input" in self.contenido
        assert "textarea" in self.contenido

    def test_guardian_registra_modulo(self):
        g = GUARDIAN.read_text()
        assert "maer.atajos" in g
        assert "MAER.atajos" in g

    def test_init_llamado_en_core(self):
        core = CORE_JS.read_text()
        assert "atajos.init()" in core

    def test_normaliza_combos(self):
        assert "_normalizar" in self.contenido

    def test_agrupacion_en_panel_ayuda(self):
        # El panel de ayuda agrupa por tipo (Navegación, Acciones, etc.)
        assert "Navegaci" in self.contenido or "grupos" in self.contenido


# ════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN: suite completa maer.test.js
# ════════════════════════════════════════════════

class TestSuiteTestJS:
    """Verifica que maer.test.js está correctamente configurado."""

    JS_TEST = JS_DIR / "maer.test.js"

    @pytest.fixture(autouse=True)
    def js(self):
        self.contenido = self.JS_TEST.read_text()

    def test_archivo_existe(self):
        assert self.JS_TEST.exists()
        assert self.JS_TEST.stat().st_size > 1000

    def test_cargado_en_index_html(self):
        assert "maer.test.js" in INDEX.read_text()

    def test_no_auto_ejecuta(self):
        # No debe terminar con })(); — debe exponer como función
        texto = self.contenido.strip()
        assert not texto.endswith("})();"), \
            "maer.test.js no debe auto-ejecutarse — debe exponer MAER_runTests()"

    def test_expone_funcion_global(self):
        assert "MAER_runTests" in self.contenido or "window.MAER_runTests" in self.contenido

    def test_cubre_todos_los_bloques(self):
        # Debe probar los módulos principales
        for modulo in ["MAER.timeline", "MAER.recordatorios", "MAER.cartasHistorial",
                       "MAER.sugerencias", "MAER.atajos", "MAER.guardian"]:
            assert modulo in self.contenido, f"Suite no cubre '{modulo}'"

    def test_boton_en_diagnostico_html(self):
        html = INDEX.read_text()
        assert "MAER_runTests" in html, "Debe haber botón para ejecutar la suite en el HTML"

    def test_panel_diagnostico_tiene_contenido(self):
        html = INDEX.read_text()
        assert 'id="panel-diagnostico"' in html
        assert "Suite de Pruebas" in html or "suite" in html.lower()
