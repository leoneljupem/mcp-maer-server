#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════
#  🦁 MAER 4.0 — LANZADOR INTELIGENTE
#  GUI completo con modos Online (ngrok) y Localhost
#  Analizador HTML tipo F12 · Chat integrado · Control total
#  Leonel Houssen Mojica — Ecatepec MX — 2026
# ══════════════════════════════════════════════════════════════════
"""
USO:   python lanzador_maer.py
DEPS:  pip install pyngrok requests pillow
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading, subprocess, sys, os, webbrowser, time, json, re, requests
from pathlib import Path
from datetime import datetime

# ── Configuración ──────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.resolve()
SERVER_DIR  = BASE_DIR / "maer_backend" / "web_ui"
SERVER_SCRIPT = SERVER_DIR / "server.py"
PORT        = int(os.environ.get("MAER_WEB_PORT", "8765"))
LOCAL_URL   = f"http://localhost:{PORT}"
LOG_FILE    = BASE_DIR / ".maer_launch.log"
NGROK_URL_F = BASE_DIR / ".maer_ngrok_url.txt"

# ── Colores MAER ────────────────────────────────────────────────────
C = {
    "bg":        "#0f1117",
    "bg2":       "#1a1d27",
    "bg3":       "#222534",
    "verde":     "#00a65a",
    "verde_dim": "#00703c",
    "azul":      "#3b82f6",
    "dorado":    "#f59e0b",
    "rojo":      "#ef4444",
    "texto":     "#e2e8f0",
    "muted":     "#64748b",
    "border":    "#2d3748",
    "white":     "#ffffff",
}

# ─────────────────────────────────────────────────────────────────────
class MAERLanzador:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🦁 MAER 4.0 — Lanzador")
        self.root.geometry("900x680")
        self.root.configure(bg=C["bg"])
        self.root.resizable(True, True)
        self.root.minsize(750, 550)

        # Estado
        self._server_proc = None
        self._ngrok_tunnel = None
        self._modo_activo  = None
        self._url_activa   = tk.StringVar(value="—")
        self._estado       = tk.StringVar(value="⏳ Servidor detenido")
        self._chat_history = []

        self._build_ui()
        self._check_server_running()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI PRINCIPAL ────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["verde_dim"], height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🦁", font=("Helvetica", 26), bg=C["verde_dim"],
                 fg=C["white"]).pack(side="left", padx=14)
        tk.Label(hdr, text="MAER 4.0", font=("Helvetica", 20, "bold"),
                 bg=C["verde_dim"], fg=C["white"]).pack(side="left")
        tk.Label(hdr, text="Asistente IMSS · Pensiones y Expedientes",
                 font=("Helvetica", 11), bg=C["verde_dim"], fg="#a7f3d0").pack(side="left", padx=12)

        # Estado badge (derecha)
        self._lbl_estado = tk.Label(hdr, textvariable=self._estado,
                                     font=("Helvetica", 10, "bold"),
                                     bg=C["verde_dim"], fg=C["dorado"])
        self._lbl_estado.pack(side="right", padx=16)

        # ── CUERPO PRINCIPAL ──
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=0, pady=0)

        # Panel izquierdo (controles)
        left = tk.Frame(body, bg=C["bg2"], width=280)
        left.pack(side="left", fill="y", padx=0)
        left.pack_propagate(False)
        self._build_left(left)

        # Panel derecho (log + chat)
        right = tk.Frame(body, bg=C["bg"])
        right.pack(side="right", fill="both", expand=True)
        self._build_right(right)

    def _build_left(self, frame):
        # Sección: Modo de inicio
        self._section(frame, "⚡  MODO DE INICIO")

        # Botón Localhost
        self._btn_local = tk.Button(
            frame, text="💻  LOCALHOST\n(sin internet, privado)",
            font=("Helvetica", 12, "bold"),
            bg=C["verde"], fg=C["white"], activebackground=C["verde_dim"],
            relief="flat", cursor="hand2", height=3,
            command=self._iniciar_localhost
        )
        self._btn_local.pack(fill="x", padx=14, pady=(8, 4))

        # Botón Online (ngrok)
        self._btn_online = tk.Button(
            frame, text="🌐  EN LÍNEA (ngrok)\n(acceso celular / Chrome Ext.)",
            font=("Helvetica", 12, "bold"),
            bg=C["azul"], fg=C["white"], activebackground="#2563eb",
            relief="flat", cursor="hand2", height=3,
            command=self._iniciar_online
        )
        self._btn_online.pack(fill="x", padx=14, pady=4)

        # Botón Detener
        self._btn_stop = tk.Button(
            frame, text="🛑  Detener servidor",
            font=("Helvetica", 10),
            bg=C["bg3"], fg=C["rojo"], activebackground=C["border"],
            relief="flat", cursor="hand2",
            command=self._detener
        )
        self._btn_stop.pack(fill="x", padx=14, pady=(4, 0))

        # URL activa
        self._section(frame, "🔗  URL ACTIVA")
        url_fr = tk.Frame(frame, bg=C["bg3"], bd=0)
        url_fr.pack(fill="x", padx=14, pady=4)
        self._lbl_url = tk.Label(url_fr, textvariable=self._url_activa,
                                  font=("Courier", 9), bg=C["bg3"],
                                  fg=C["verde"], wraplength=220, justify="left")
        self._lbl_url.pack(side="left", padx=8, pady=6)

        tk.Button(url_fr, text="🔗", font=("Helvetica", 10),
                  bg=C["bg3"], fg=C["muted"], relief="flat", cursor="hand2",
                  command=self._abrir_browser).pack(side="right", padx=4)

        # Acciones rápidas
        self._section(frame, "🛠️  HERRAMIENTAS")

        herrs = [
            ("🔍 Analizar HTML (F12)",       self._abrir_f12),
            ("📄 Exportar PDF expediente",   self._exportar_pdf),
            ("🔧 Verificar dependencias",    self._verificar_deps),
            ("📂 Analizar carpeta",           self._analizar_carpeta),
            ("🤖 Seleccionar modelo Ollama", self._abrir_selector_ollama),
            ("🩺 Panel diagnóstico",          self._abrir_diagnostico),
            ("📱 Código QR URL pública",     self._mostrar_qr),
        ]
        for txt, cmd in herrs:
            tk.Button(frame, text=txt, font=("Helvetica", 10),
                      bg=C["bg3"], fg=C["texto"], activebackground=C["border"],
                      relief="flat", cursor="hand2", anchor="w", padx=10,
                      command=cmd).pack(fill="x", padx=14, pady=2)

        # Espacio + consola externa
        tk.Frame(frame, bg=C["bg2"], height=8).pack()
        tk.Button(frame, text="🖥️  Abrir Consola IA (maer_consola.py)",
                  font=("Helvetica", 10, "bold"),
                  bg=C["dorado"], fg="#000000", activebackground="#d97706",
                  relief="flat", cursor="hand2",
                  command=self._abrir_consola).pack(fill="x", padx=14, pady=8)

    def _build_right(self, frame):
        # ── LOG del sistema ──
        log_fr = tk.Frame(frame, bg=C["bg"])
        log_fr.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        tk.Label(log_fr, text="📋  LOG DEL SISTEMA", font=("Helvetica", 10, "bold"),
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w")

        self.log_area = scrolledtext.ScrolledText(
            log_fr, font=("Courier", 10), bg=C["bg2"], fg=C["texto"],
            insertbackground=C["verde"], relief="flat",
            wrap="word", height=18
        )
        self.log_area.pack(fill="both", expand=True, pady=4)
        self.log_area.configure(state="disabled")
        # Tags de color
        self.log_area.tag_config("ok",    foreground=C["verde"])
        self.log_area.tag_config("err",   foreground=C["rojo"])
        self.log_area.tag_config("warn",  foreground=C["dorado"])
        self.log_area.tag_config("info",  foreground=C["azul"])
        self.log_area.tag_config("muted", foreground=C["muted"])

        # ── CHAT con MAER ──
        tk.Label(frame, text="💬  CHAT CON MAER (responde en segundos)",
                 font=("Helvetica", 10, "bold"),
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w", padx=8)

        chat_out_fr = tk.Frame(frame, bg=C["bg"])
        chat_out_fr.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.chat_area = scrolledtext.ScrolledText(
            chat_out_fr, font=("Helvetica", 10), bg=C["bg3"], fg=C["texto"],
            relief="flat", wrap="word", height=10
        )
        self.chat_area.pack(fill="both", expand=True)
        self.chat_area.configure(state="disabled")
        self.chat_area.tag_config("user",  foreground=C["azul"],    font=("Helvetica", 10, "bold"))
        self.chat_area.tag_config("maer",  foreground=C["verde"],   font=("Helvetica", 10))
        self.chat_area.tag_config("error", foreground=C["rojo"],    font=("Helvetica", 9))
        self.chat_area.tag_config("ts",    foreground=C["muted"],   font=("Helvetica", 8))

        # Input chat
        inp_fr = tk.Frame(frame, bg=C["bg2"])
        inp_fr.pack(fill="x", padx=8, pady=(0, 8))

        self.chat_input = tk.Entry(inp_fr, font=("Helvetica", 11),
                                    bg=C["bg3"], fg=C["texto"],
                                    insertbackground=C["verde"],
                                    relief="flat")
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=6)
        self.chat_input.bind("<Return>", self._enviar_chat)

        tk.Button(inp_fr, text="Enviar ▶", font=("Helvetica", 10, "bold"),
                  bg=C["verde"], fg=C["white"], relief="flat", cursor="hand2",
                  padx=12, command=self._enviar_chat).pack(side="right", pady=4, padx=4)

    # ── HELPERS UI ──────────────────────────────────────────────────
    def _section(self, frame, text):
        tk.Frame(frame, bg=C["border"], height=1).pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(frame, text=text, font=("Helvetica", 9, "bold"),
                 bg=C["bg2"], fg=C["muted"]).pack(anchor="w", padx=14, pady=4)

    def _log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"[{ts}] ", "muted")
        self.log_area.insert("end", f"{msg}\n", tag)
        self.log_area.see("end")
        self.log_area.configure(state="disabled")
        # También escribir a archivo
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")
        except Exception:
            pass

    def _chat_append(self, quien, msg, tag="maer"):
        ts = datetime.now().strftime("%H:%M")
        self.chat_area.configure(state="normal")
        self.chat_area.insert("end", f"\n[{ts}] ", "ts")
        self.chat_area.insert("end", f"{quien}: ", tag)
        self.chat_area.insert("end", msg.strip() + "\n", "maer" if quien != "Tú" else "user")
        self.chat_area.see("end")
        self.chat_area.configure(state="disabled")

    # ── SERVIDOR ────────────────────────────────────────────────────
    def _iniciar_localhost(self):
        if self._server_proc:
            self._log("Servidor ya en ejecución.", "warn")
            return
        self._modo_activo = "local"
        self._estado.set("⏳ Iniciando servidor...")
        threading.Thread(target=self._run_server, daemon=True).start()

    def _iniciar_online(self):
        self._modo_activo = "online"
        self._estado.set("⏳ Iniciando servidor + ngrok...")
        threading.Thread(target=self._run_server_online, daemon=True).start()

    def _run_server(self):
        self._log(f"Iniciando servidor MAER en {LOCAL_URL} ...", "info")
        try:
            cmd = [sys.executable, str(SERVER_SCRIPT)]
            self._server_proc = subprocess.Popen(
                cmd, cwd=str(SERVER_DIR),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True
            )
            time.sleep(3)
            if self._server_proc.poll() is None:
                self._log(f"✅ Servidor activo: {LOCAL_URL}", "ok")
                self._estado.set("✅ Servidor activo")
                self._url_activa.set(LOCAL_URL)
                self.root.after(500, lambda: webbrowser.open(LOCAL_URL))
                # Leer output en background
                threading.Thread(target=self._leer_output, daemon=True).start()
            else:
                self._log("❌ Servidor falló al iniciar", "err")
                self._estado.set("❌ Error al iniciar")
        except Exception as e:
            self._log(f"❌ Error: {e}", "err")
            self._estado.set("❌ Error")

    def _run_server_online(self):
        self._run_server()
        if not self._server_proc or self._server_proc.poll() is not None:
            return
        self._log("Iniciando túnel ngrok...", "info")
        try:
            from pyngrok import ngrok, conf
            env_file = BASE_DIR / ".env"
            token = ""
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("NGROK_AUTHTOKEN="):
                        token = line.split("=", 1)[1].strip()
            if token:
                conf.get_default().auth_token = token
                self._log("ngrok authtoken configurado ✅", "ok")
            else:
                self._log("⚠ Sin NGROK_AUTHTOKEN — sesión de 60 min. Agrega al .env", "warn")

            tunnel = ngrok.connect(PORT, "http")
            url = tunnel.public_url
            NGROK_URL_F.write_text(url)
            self._url_activa.set(url)
            self._log(f"🌐 URL pública: {url}", "ok")
            self._estado.set("🌐 En línea")
            self.root.after(200, lambda: webbrowser.open(url))
        except ImportError:
            self._log("⚠ pyngrok no instalado: pip install pyngrok", "warn")
            self._log(f"Accesible solo en: {LOCAL_URL}", "info")
        except Exception as e:
            self._log(f"⚠ ngrok error: {e} — usando localhost", "warn")

    def _leer_output(self):
        """Lee stdout del servidor y lo vuelca al log."""
        if not self._server_proc:
            return
        for line in self._server_proc.stdout:
            line = line.rstrip()
            if line:
                tag = "ok" if ("OK" in line or "started" in line.lower()) else \
                      "err" if ("error" in line.lower() or "exception" in line.lower()) else "muted"
                self.root.after(0, lambda l=line, t=tag: self._log(l, t))

    def _detener(self):
        if self._server_proc:
            self._server_proc.terminate()
            self._server_proc = None
            self._log("🛑 Servidor detenido.", "warn")
            self._estado.set("⏳ Servidor detenido")
            self._url_activa.set("—")
        try:
            from pyngrok import ngrok
            ngrok.kill()
            self._log("ngrok detenido.", "warn")
        except Exception:
            pass
        if NGROK_URL_F.exists():
            NGROK_URL_F.unlink()

    def _check_server_running(self):
        """Verifica si el servidor ya está corriendo al iniciar."""
        def _check():
            try:
                r = requests.get(LOCAL_URL, timeout=2)
                if r.status_code == 200:
                    self.root.after(0, lambda: self._log(
                        f"⚡ Servidor ya activo en {LOCAL_URL}", "ok"))
                    self.root.after(0, lambda: self._estado.set("✅ Servidor activo"))
                    self.root.after(0, lambda: self._url_activa.set(LOCAL_URL))
            except Exception:
                self.root.after(0, lambda: self._log(
                    "Servidor no activo. Selecciona modo para iniciar.", "muted"))
        threading.Thread(target=_check, daemon=True).start()

    # ── HERRAMIENTAS ────────────────────────────────────────────────
    def _abrir_browser(self):
        url = self._url_activa.get()
        if url and url != "—":
            webbrowser.open(url)
        else:
            messagebox.showwarning("MAER", "Primero inicia el servidor.")

    def _abrir_f12(self):
        """Abre ventana analizadora de HTML tipo DevTools F12."""
        url = self._url_activa.get()
        if url == "—":
            url = LOCAL_URL
        win = tk.Toplevel(self.root)
        win.title(f"🔍 F12 Analizador HTML — {url}")
        win.geometry("1100x750")
        win.configure(bg=C["bg"])

        # Toolbar
        tb = tk.Frame(win, bg=C["bg3"])
        tb.pack(fill="x")
        url_var = tk.StringVar(value=url)
        tk.Entry(tb, textvariable=url_var, font=("Courier", 11),
                 bg=C["bg2"], fg=C["texto"], insertbackground=C["verde"],
                 relief="flat").pack(side="left", fill="x", expand=True, padx=8, pady=6)

        def _cargar():
            _url = url_var.get()
            threading.Thread(target=lambda: _fetch_html(_url), daemon=True).start()

        tk.Button(tb, text="🔄 Cargar", bg=C["verde"], fg=C["white"], relief="flat",
                  cursor="hand2", command=_cargar).pack(side="right", padx=8, pady=4)

        # Notebook (tabs)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, pady=4)

        # Tab HTML
        tab_html = tk.Frame(nb, bg=C["bg"])
        nb.add(tab_html, text="  📄 HTML Fuente  ")
        html_txt = scrolledtext.ScrolledText(tab_html, font=("Courier", 10),
                                              bg="#1e1e2e", fg="#cdd6f4",
                                              insertbackground=C["verde"], relief="flat")
        html_txt.pack(fill="both", expand=True)
        html_txt.tag_config("tag",   foreground="#89b4fa")
        html_txt.tag_config("attr",  foreground="#a6e3a1")
        html_txt.tag_config("str",   foreground="#f38ba8")
        html_txt.tag_config("cmnt",  foreground="#6c7086")
        html_txt.tag_config("script",foreground="#fab387")

        # Tab Estructura
        tab_tree = tk.Frame(nb, bg=C["bg"])
        nb.add(tab_tree, text="  🌲 Estructura  ")
        tree = ttk.Treeview(tab_tree, show="tree headings")
        tree.heading("#0", text="Elemento HTML")
        tree.pack(fill="both", expand=True)

        # Tab Network (APIs)
        tab_net = tk.Frame(nb, bg=C["bg"])
        nb.add(tab_net, text="  📡 APIs MAER  ")
        net_txt = scrolledtext.ScrolledText(tab_net, font=("Courier", 9),
                                             bg="#1e1e2e", fg="#cdd6f4",
                                             relief="flat")
        net_txt.pack(fill="both", expand=True)

        # Tab Consola JS (comandos a la API)
        tab_js = tk.Frame(nb, bg=C["bg"])
        nb.add(tab_js, text="  > Consola API  ")
        js_out = scrolledtext.ScrolledText(tab_js, font=("Courier", 10),
                                            bg="#1e1e2e", fg="#cdd6f4",
                                            relief="flat", height=20)
        js_out.pack(fill="both", expand=True)
        js_inp_fr = tk.Frame(tab_js, bg=C["bg3"])
        js_inp_fr.pack(fill="x")
        tk.Label(js_inp_fr, text=">", font=("Courier", 12, "bold"),
                 bg=C["bg3"], fg=C["verde"]).pack(side="left", padx=8)
        js_inp = tk.Entry(js_inp_fr, font=("Courier", 11),
                          bg=C["bg2"], fg=C["texto"], insertbackground=C["verde"],
                          relief="flat")
        js_inp.pack(side="left", fill="x", expand=True, pady=6)

        def _exec_api(evt=None):
            cmd = js_inp.get().strip()
            if not cmd:
                return
            js_inp.delete(0, "end")
            js_out.configure(state="normal")
            js_out.insert("end", f"\n> {cmd}\n", "")
            # Ejecutar contra la API MAER
            def _run():
                try:
                    _u = url_var.get().rstrip("/")
                    if cmd.startswith("GET "):
                        r = requests.get(_u + cmd[4:], timeout=8)
                    elif cmd.startswith("POST "):
                        parts = cmd[5:].split(" ", 1)
                        ep = parts[0]
                        body = json.loads(parts[1]) if len(parts) > 1 else {}
                        r = requests.post(_u + ep, json=body, timeout=8)
                    else:
                        r = requests.get(_u + ("" if cmd.startswith("/") else "/api/") + cmd, timeout=8)
                    out = json.dumps(r.json(), ensure_ascii=False, indent=2)[:3000]
                except Exception as e:
                    out = f"Error: {e}"
                js_out.after(0, lambda: [
                    js_out.configure(state="normal"),
                    js_out.insert("end", out + "\n", ""),
                    js_out.see("end"),
                    js_out.configure(state="disabled"),
                ])
            threading.Thread(target=_run, daemon=True).start()

        js_inp.bind("<Return>", _exec_api)
        tk.Button(js_inp_fr, text="Ejecutar", bg=C["verde"], fg=C["white"],
                  relief="flat", cursor="hand2", command=_exec_api).pack(side="right", padx=8)

        # Mostrar endpoints disponibles en tab network
        apis = [
            ("POST", "/api/llm-chat",              "Chat con IA"),
            ("POST", "/api/curp-decodificar",       "Decodificar CURP"),
            ("POST", "/api/sinavid-consulta",        "Consultar SINAVID"),
            ("POST", "/api/exportar-pdf",           "Exportar PDF"),
            ("POST", "/api/imss-consulta",          "Consulta IMSS"),
            ("POST", "/api/analizar-documento",     "Analizar documento"),
            ("GET",  "/api/verificar-dependencias", "Verificar deps"),
            ("GET",  "/api/ngrok-url",              "URL ngrok"),
            ("POST", "/api/imss-selenium",          "Selenium IMSS"),
        ]
        net_txt.configure(state="normal")
        net_txt.insert("end", "📡 ENDPOINTS MAER 4.0\n" + "─"*50 + "\n")
        for meth, ep, desc in apis:
            net_txt.insert("end", f"  [{meth:4}] {ep:<40} {desc}\n")
        net_txt.insert("end", "\n💡 Úsalos en la pestaña '> Consola API'\n")
        net_txt.insert("end", "  Ejemplos:\n")
        net_txt.insert("end", '  POST /api/llm-chat {"prompt":"¿Qué es la Ley 73?"}\n')
        net_txt.insert("end", '  POST /api/curp-decodificar {"curp":"LOOA531113HTCPBN09"}\n')
        net_txt.insert("end", '  GET /api/verificar-dependencias\n')
        net_txt.configure(state="disabled")

        def _fetch_html(_url):
            """Descarga HTML y lo muestra con colores."""
            try:
                r = requests.get(_url, timeout=8)
                html = r.text
            except Exception as e:
                html = f"<!-- Error: {e} -->"

            html_txt.configure(state="normal")
            html_txt.delete("1.0", "end")

            # Colorear HTML con regex básico
            pos = 0
            for m in re.finditer(
                r'(<!--.*?-->)|(</?\w[\w-]*(?:\s+[^>]*)?>)|("(?:[^"\\]|\\.)*")|([^<>"]+)',
                html, re.DOTALL
            ):
                cmnt, tag, string, txt = m.groups()
                if cmnt:
                    html_txt.insert("end", cmnt, "cmnt")
                elif tag:
                    html_txt.insert("end", tag, "tag")
                elif string:
                    html_txt.insert("end", string, "str")
                elif txt:
                    html_txt.insert("end", txt)

            html_txt.configure(state="disabled")

            # Construir árbol de estructura
            def _build_tree(parent, text, depth=0):
                if depth > 4:
                    return
                tags = re.findall(r'<(\w+)(?:\s[^>]*)?>.*?</\1>', text, re.DOTALL)
                for t in tags[:30]:
                    tag_name = re.match(r'<(\w+)', t).group(1)
                    node = tree.insert(parent, "end", text=f"<{tag_name}>")
                    _build_tree(node, t, depth + 1)

            tree.after(0, lambda: [tree.delete(*tree.get_children()),
                                   _build_tree("", html)])

        # Cargar al abrir
        threading.Thread(target=lambda: _fetch_html(url), daemon=True).start()

    def _exportar_pdf(self):
        """Llama al endpoint exportar-pdf y abre el resultado."""
        def _run():
            try:
                r = requests.post(f"{LOCAL_URL}/api/exportar-pdf",
                                  json={"nombre": "Desde Lanzador MAER",
                                        "notas": "Generado desde el lanzador"},
                                  timeout=20)
                d = r.json().get("data", {})
                p = d.get("pdf_path")
                if p:
                    self._log(f"✅ PDF generado: {Path(p).name}", "ok")
                    webbrowser.open(f"file://{p}")
                else:
                    self._log(f"⚠ Error PDF: {r.json().get('message')}", "warn")
            except Exception as e:
                self._log(f"❌ Error exportar PDF: {e}", "err")
        threading.Thread(target=_run, daemon=True).start()

    def _verificar_deps(self):
        def _run():
            try:
                r = requests.get(f"{LOCAL_URL}/api/verificar-dependencias", timeout=12)
                d = r.json().get("data", {})
                pkg = d.get("python_packages", {})
                ok  = sum(1 for v in pkg.values() if v)
                self._log(f"🔧 Dependencias: {ok}/{len(pkg)} paquetes OK | "
                          f"Java:{d.get('java')} Tesseract:{d.get('tesseract_bin')} "
                          f"Ollama:{d.get('ollama')}", "ok" if ok == len(pkg) else "warn")
            except Exception as e:
                self._log(f"❌ Error verificar deps: {e}", "err")
        threading.Thread(target=_run, daemon=True).start()

    def _analizar_carpeta(self):
        path = filedialog.askdirectory(title="Selecciona carpeta para analizar")
        if not path:
            return
        self._log(f"📂 Analizando carpeta: {path}", "info")
        def _run():
            try:
                r = requests.post(f"{LOCAL_URL}/api/expediente-imss",
                                  json={"carpeta": path}, timeout=30)
                d = r.json().get("data", {})
                self._log(f"✅ Expediente {d.get('porcentaje',0)}% completo — "
                          f"{d.get('documentos_encontrados',0)}/{d.get('documentos_requeridos',0)} docs", "ok")
                falt = d.get("criticos_faltantes", [])
                if falt:
                    self._log(f"⚠ Documentos críticos faltantes: "
                              f"{', '.join(f['nombre'] for f in falt)}", "warn")
            except Exception as e:
                self._log(f"❌ Error: {e}", "err")
        threading.Thread(target=_run, daemon=True).start()

    def _abrir_diagnostico(self):
        url = self._url_activa.get()
        if url == "—":
            url = LOCAL_URL
        webbrowser.open(f"{url}?tab=diagnostico")

    def _mostrar_qr(self):
        url = self._url_activa.get()
        if url == "—":
            messagebox.showinfo("QR", "Primero inicia MAER en modo Online (ngrok).")
            return
        try:
            import qrcode
            win = tk.Toplevel(self.root)
            win.title("📱 Código QR — Escanea con tu celular")
            win.configure(bg=C["bg"])
            qr = qrcode.make(url)
            from PIL import ImageTk
            qr_tk = ImageTk.PhotoImage(qr.resize((300, 300)))
            tk.Label(win, image=qr_tk, bg=C["bg"]).pack(padx=20, pady=20)
            tk.Label(win, text=url, font=("Courier", 10), bg=C["bg"],
                     fg=C["verde"]).pack()
            win.qr_img = qr_tk  # evitar GC
        except ImportError:
            messagebox.showinfo("QR", f"Instala: pip install qrcode pillow\nURL: {url}")

    def _abrir_consola(self):
        consola = BASE_DIR / "maer_consola.py"
        if not consola.exists():
            messagebox.showwarning("MAER", f"maer_consola.py no encontrado en:\n{consola}")
            return
        subprocess.Popen([sys.executable, str(consola)])
        self._log("🖥️ Consola IA abierta en nueva ventana.", "ok")

    # ── CHAT ────────────────────────────────────────────────────────
    def _enviar_chat(self, evt=None):
        msg = self.chat_input.get().strip()
        if not msg:
            return
        self.chat_input.delete(0, "end")
        self._chat_append("Tú", msg, "user")
        self._chat_history.append({"role": "user", "content": msg})
        threading.Thread(target=self._llamar_maer, args=(msg,), daemon=True).start()

    def _llamar_maer(self, msg):
        try:
            url = self._url_activa.get()
            if url == "—":
                url = LOCAL_URL
            r = requests.post(f"{url}/api/llm-chat",
                              json={"prompt": msg}, timeout=20)
            d  = r.json()
            resp = d.get("data", {}).get("response") or d.get("message", "Sin respuesta")
            engine = d.get("data", {}).get("engine", "?")
            self.root.after(0, lambda: self._chat_append(
                f"🦁 MAER [{engine}]", resp, "maer"))
        except Exception as e:
            self.root.after(0, lambda: self._chat_append(
                "Error", f"No se pudo contactar a MAER: {e}", "error"))

    # ── CIERRE ──────────────────────────────────────────────────────
    def _on_close(self):
        if self._server_proc and messagebox.askyesno(
                "MAER", "¿Detener el servidor MAER al cerrar el lanzador?"):
            self._detener()
        self.root.destroy()

    def _detectar_ollama(self):
        """Detecta modelos Ollama al arrancar y los muestra en el log."""
        def _run():
            import shutil, urllib.request, json as _json, subprocess as _sp
            self.root.after(0, lambda: self._log("🤖 Detectando Ollama...", "muted"))
            # Buscar binario
            rutas = [
                shutil.which("ollama"),
                "/opt/homebrew/bin/ollama",
                "/usr/local/bin/ollama",
                "/Applications/Ollama.app/Contents/MacOS/ollama",
                str(Path.home() / "miniconda3" / "bin" / "ollama"),
                str(Path.home() / "anaconda3" / "bin" / "ollama"),
                str(Path.home() / ".local" / "bin" / "ollama"),
            ]
            ollama_bin = next((r for r in rutas if r and Path(r).exists()), None)
            if not ollama_bin:
                self.root.after(0, lambda: self._log(
                    "⚠️ Ollama no encontrado. Instala desde ollama.ai", "warn"))
                return

            # Obtener versión
            try:
                rv = _sp.run([ollama_bin, "--version"], capture_output=True,
                             text=True, timeout=5)
                ver = (rv.stdout or rv.stderr).strip()
                self.root.after(0, lambda: self._log(
                    f"✅ Ollama: {ver} ({ollama_bin.split('/')[-3] if '/' in ollama_bin else 'sistema'})", "ok"))
            except Exception:
                pass

            # Verificar servidor
            ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            servidor_ok = False
            try:
                urllib.request.urlopen(f"{ollama_url}/api/tags", timeout=3)
                servidor_ok = True
            except Exception:
                pass

            if not servidor_ok:
                # Intentar arrancar
                try:
                    _sp.Popen([ollama_bin, "serve"],
                              stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
                              start_new_session=True)
                    import time as _t; _t.sleep(3)
                    urllib.request.urlopen(f"{ollama_url}/api/tags", timeout=3)
                    servidor_ok = True
                    self.root.after(0, lambda: self._log(
                        "✅ Servidor Ollama iniciado automáticamente", "ok"))
                except Exception:
                    self.root.after(0, lambda: self._log(
                        "⚠️ Ollama instalado pero servidor inactivo. Ejecuta: ollama serve", "warn"))
                    return

            # Listar modelos
            try:
                with urllib.request.urlopen(f"{ollama_url}/api/tags", timeout=5) as r:
                    data = _json.loads(r.read())
                modelos = data.get("models", [])
                if not modelos:
                    self.root.after(0, lambda: self._log(
                        "⚠️ Ollama activo pero sin modelos. Usa: ollama pull llama3.2", "warn"))
                    return

                # Ordenar por tamaño (mayor = más capaz)
                modelos.sort(key=lambda x: x.get("size", 0), reverse=True)
                self.root.after(0, lambda: self._log(
                    f"🤖 {len(modelos)} modelo(s) Ollama disponibles:", "ok"))

                # Tabla de modelos
                preferencia = ["llama3.3","llama3.2","llama3.1","llama3","mistral-nemo",
                               "mistral","gemma3","gemma2","qwen2.5","phi4","phi3","deepseek-r1"]
                elegido = None
                env_model = os.environ.get("OLLAMA_MODEL", "")
                nombres = [m["name"] for m in modelos]

                if env_model and any(env_model in n for n in nombres):
                    elegido = env_model
                else:
                    for pref in preferencia:
                        for n in nombres:
                            if pref in n.lower():
                                elegido = n; break
                        if elegido: break
                    if not elegido and nombres:
                        elegido = nombres[0]

                for m in modelos:
                    det  = m.get("details", {})
                    tam  = m.get("size", 0)
                    tam_str = f"{tam//1024//1024//1024:.1f}GB" if tam > 1e9 else f"{tam//1024//1024}MB"
                    star = " ⭐ ACTIVO" if m["name"] == elegido else ""
                    params = det.get("parameter_size", "")
                    quant  = det.get("quantization_level", "")
                    tag = "ok" if m["name"] == elegido else "muted"
                    msg_m = m
                    msg_s = star
                    msg_ts = tam_str
                    msg_p = params
                    msg_q = quant
                    self.root.after(0, lambda mm=msg_m, ss=msg_s, ts=msg_ts, pp=msg_p, qq=msg_q, tt=tag:
                        self._log(f"  • {mm['name']} ({ts}{', ' + pp if pp else ''}"
                                  f"{', ' + qq if qq else ''}){ss}", tt))

                if elegido:
                    el = elegido
                    self.root.after(200, lambda e=el:
                        self._log(f"💬 LLM activo: {e}  — El chat usará este modelo", "ok"))
                    # Guardar en .env si no estaba
                    if not env_model:
                        try:
                            env_path = BASE_DIR / ".env"
                            txt = env_path.read_text() if env_path.exists() else ""
                            if "OLLAMA_MODEL=" not in txt:
                                with open(env_path, "a") as f:
                                    f.write(f"\nOLLAMA_MODEL={elegido}\n")
                                self.root.after(300, lambda:
                                    self._log(f"💾 OLLAMA_MODEL={elegido} guardado en .env", "muted"))
                        except Exception:
                            pass
            except Exception as e:
                self.root.after(0, lambda: self._log(f"⚠️ Error listando modelos: {e}", "warn"))

        threading.Thread(target=_run, daemon=True).start()

    def _abrir_selector_ollama(self):
        """Abre una ventana para seleccionar el modelo Ollama por defecto."""
        import shutil, urllib.request, json as _json

        win = tk.Toplevel(self.root)
        win.title("🤖 Seleccionar modelo Ollama")
        win.geometry("680x500")
        win.configure(bg=C["bg"])

        tk.Label(win, text="🤖 Modelos Ollama Instalados",
                 font=("Helvetica", 14, "bold"), bg=C["bg"],
                 fg=C["verde"]).pack(pady=(16, 4))
        tk.Label(win, text="Selecciona el modelo que MAER usará para responder preguntas.",
                 font=("Helvetica", 10), bg=C["bg"],
                 fg=C["muted"]).pack()

        # Tabla de modelos
        frame_tabla = tk.Frame(win, bg=C["bg"])
        frame_tabla.pack(fill="both", expand=True, padx=16, pady=8)

        cols = ("Modelo", "Tamaño", "Familia", "Params", "Cuantización")
        tree = ttk.Treeview(frame_tabla, columns=cols, show="headings", height=12)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width={"Modelo":200,"Tamaño":80,"Familia":100,
                                    "Params":80,"Cuantización":100}.get(col,100))
        scroll = tk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        estado_var = tk.StringVar(value="Cargando modelos...")
        tk.Label(win, textvariable=estado_var, font=("Helvetica", 10),
                 bg=C["bg"], fg=C["muted"]).pack()

        elegido_var = tk.StringVar(value="")
        modelo_actual = os.environ.get("OLLAMA_MODEL", "")

        def _cargar():
            ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            try:
                with urllib.request.urlopen(f"{ollama_url}/api/tags", timeout=5) as r:
                    data = _json.loads(r.read())
                modelos = sorted(data.get("models", []),
                                 key=lambda x: x.get("size", 0), reverse=True)
                if not modelos:
                    win.after(0, lambda: estado_var.set("Sin modelos instalados. Usa: ollama pull llama3.2"))
                    return
                for m in modelos:
                    det = m.get("details", {})
                    tam = m.get("size", 0)
                    tam_str = f"{tam//1024//1024//1024:.1f} GB" if tam > 1e9 else f"{tam//1024//1024} MB"
                    star = " ⭐" if m["name"] == modelo_actual else ""
                    win.after(0, lambda mm=m, ts=tam_str, ss=star, dd=det:
                        tree.insert("", "end", values=(
                            mm["name"] + ss, ts,
                            dd.get("family",""), dd.get("parameter_size",""),
                            dd.get("quantization_level","")
                        ), tags=("activo",) if ss else ()))
                tree.tag_configure("activo", foreground=C["verde"])
                win.after(0, lambda: estado_var.set(
                    f"✅ {len(modelos)} modelo(s) disponibles. Selecciona y presiona 'Usar este modelo'."))
            except Exception as e:
                win.after(0, lambda: estado_var.set(f"❌ Error: {e}"))

        threading.Thread(target=_cargar, daemon=True).start()

        def _seleccionar():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("MAER", "Selecciona un modelo de la tabla.", parent=win)
                return
            nombre = tree.item(sel[0], "values")[0].replace(" ⭐", "").strip()
            elegido_var.set(nombre)
            # Guardar en .env
            try:
                env_path = BASE_DIR / ".env"
                txt = env_path.read_text() if env_path.exists() else ""
                lineas = [l for l in txt.splitlines() if not l.startswith("OLLAMA_MODEL=")]
                lineas.append(f"OLLAMA_MODEL={nombre}")
                env_path.write_text("\n".join(lineas) + "\n")
                os.environ["OLLAMA_MODEL"] = nombre
                estado_var.set(f"✅ Guardado: OLLAMA_MODEL={nombre}")
                self._log(f"🤖 Modelo Ollama cambiado a: {nombre}", "ok")
                messagebox.showinfo("MAER", f"Modelo guardado: {nombre}\n\nMAER usará este modelo para responder.", parent=win)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        btn_fr = tk.Frame(win, bg=C["bg"])
        btn_fr.pack(pady=8)
        tk.Button(btn_fr, text="⭐ Usar este modelo",
                  font=("Helvetica", 11, "bold"), bg=C["verde"], fg=C["white"],
                  relief="flat", cursor="hand2", padx=16, pady=6,
                  command=_seleccionar).pack(side="left", padx=8)
        tk.Button(btn_fr, text="🔄 Recargar",
                  font=("Helvetica", 11), bg=C["bg3"], fg=C["texto"],
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=lambda: [tree.delete(*tree.get_children()),
                                   threading.Thread(target=_cargar, daemon=True).start()]
                  ).pack(side="left", padx=4)
        tk.Button(btn_fr, text="📖 ollama pull llama3.2",
                  font=("Helvetica", 10), bg=C["bg3"], fg=C["azul"],
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=lambda: self._log(
                      "💡 Ejecuta en terminal: ollama pull llama3.2", "info")
                  ).pack(side="left", padx=4)

    def run(self):
        self._log("🦁 MAER Lanzador iniciado. Selecciona modo para comenzar.", "ok")
        self._log(f"📁 Directorio MAER: {BASE_DIR}", "muted")
        self._detectar_ollama()
        self.root.mainloop()


# ── MAIN ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Auto-instalar dependencias básicas
    for pkg in ["requests", "pyngrok"]:
        try:
            __import__(pkg.replace("-", "_").replace("pyngrok", "pyngrok"))
        except ImportError:
            print(f"Instalando {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

    app = MAERLanzador()
    app.run()
