══════════════════════════════════════════════════════════════════════
  🦁 MAER 4.0 — Sistema de Asistencia para Expedientes de Retiro IMSS
  Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════════════════

INICIO RÁPIDO
─────────────
1. Abrir terminal en esta carpeta
2. Ejecutar el LANZADOR visual:        python lanzador_maer.py
   O la CONSOLA IA avanzada:           python maer_consola.py
   O solo el servidor backend:         python maer_backend/web_ui/server.py


ARCHIVOS PRINCIPALES
─────────────────────
  lanzador_maer.py    GUI visual con opciones Online/Localhost + F12 + Chat
  maer_consola.py     Consola IA con voz, OCR, aprendizaje, vigilancia
  iniciar_maer_ngrok.py  Inicia servidor + túnel ngrok (acceso celular)
  README_MAER.txt     Esta guía


══════════════════════════════════════════════════════════════════════
  LANZADOR GRÁFICO  (lanzador_maer.py)
══════════════════════════════════════════════════════════════════════

REQUISITOS:
  pip install requests pyngrok pillow qrcode

CÓMO USAR:
  python lanzador_maer.py

FUNCIONES DEL LANZADOR:
  ┌─ PANEL IZQUIERDO ─────────────────────────────────────────────┐
  │ 💻 LOCALHOST     Inicia servidor local + abre Chrome          │
  │ 🌐 EN LÍNEA      Crea túnel ngrok + URL pública (celular)    │
  │ 🛑 Detener       Apaga el servidor                            │
  │                                                               │
  │ 🔍 F12 HTML      Ventana analizadora tipo DevTools:           │
  │                  → Tab "HTML Fuente" con colores (tags, attrs)│
  │                  → Tab "Estructura" árbol DOM                 │
  │                  → Tab "APIs MAER" listado de endpoints       │
  │                  → Tab "> Consola API" — escribe comandos:    │
  │                    GET /api/verificar-dependencias            │
  │                    POST /api/llm-chat {"prompt":"..."}        │
  │                    POST /api/curp-decodificar {"curp":"..."}  │
  │                                                               │
  │ 📄 Exportar PDF  Genera expediente IMSS en PDF                │
  │ 🔧 Verificar deps Revisa Java, Tesseract, Ollama, Chrome...  │
  │ 📂 Analizar carpeta  Selecciona carpeta → analiza docs IMSS   │
  │ 📱 Código QR     QR de la URL pública para tu celular         │
  │ 🖥 Consola IA    Lanza maer_consola.py en nueva ventana       │
  └───────────────────────────────────────────────────────────────┘
  ┌─ PANEL DERECHO ───────────────────────────────────────────────┐
  │ LOG en tiempo real (verde=OK, rojo=error, amarillo=aviso)     │
  │ CHAT integrado — escribe y presiona Enter, responde la IA     │
  └───────────────────────────────────────────────────────────────┘


══════════════════════════════════════════════════════════════════════
  CONSOLA IA AVANZADA  (maer_consola.py)
══════════════════════════════════════════════════════════════════════

REQUISITOS:
  pip install requests pypdf pillow pytesseract opencv-python deskew pymupdf
  Tesseract OCR: https://github.com/tesseract-ocr/tesseract
  (Para voz): pip install SpeechRecognition pyaudio

CÓMO USAR:
  python maer_consola.py

ATAJOS DE TECLADO:
  Tab    → Autocompletar comando o ruta de archivo
  ↑ / ↓  → Historial de comandos anteriores
  Ctrl+C → Menú para salir o interrumpir operación actual

COMANDOS DISPONIBLES:
─────────────────────────────────────────────────────────────────────

  CHAT CON IA
  ──────────
  chat <mensaje>
    Habla directamente con MAER. También puedes escribir cualquier
    pregunta sin el prefijo "chat" y MAER responde automáticamente.
    Ejemplos:
      ¿Cuántas semanas necesito para pensionarme con Ley 73?
      chat ¿Qué es el NSS y cómo se obtiene?
      ¿Cuál es la diferencia entre AFORE e IMSS?

  voz
    Activa el reconocimiento de voz continuo. MAER escucha
    cualquier palabra y responde. Di "salir voz" para terminar.
    Requiere: pip install SpeechRecognition pyaudio
    Voz de salida: automática (usa "say" en macOS, espeak en Linux)

─────────────────────────────────────────────────────────────────────

  ANÁLISIS DE ARCHIVOS (OCR AVANZADO)
  ────────────────────────────────────
  analizar <ruta>
    OCR profesional de un archivo individual. Soporta:
      PDF (digital y escaneado), Word (.docx), Excel (.xlsx/.xls),
      Imágenes (PNG, JPG, TIFF, BMP), CSV, TXT, Markdown, JSON, HTML
    El OCR aplica automáticamente:
      • Corrección de inclinación del escáner (deskew)
      • Eliminación de ruido (denoising OpenCV)
      • Umbralización adaptativa (mejor lectura de fondos irregulares)
      • Escalado a 300 DPI para Tesseract
    Extrae y muestra: CURP, RFC, NSS, semanas cotizadas
    Guarda resultado en la base de conocimiento
    Ejemplos:
      analizar ~/Documents/constancia_imss.pdf
      analizar /Users/leo/Desktop/semanas_cotizadas.png
      ocr ~/nss_documento.jpg

  carpeta <ruta>
    Analiza TODOS los archivos de una carpeta y TODAS sus subcarpetas.
    Muestra barra de progreso en tiempo real.
    Al terminar: top archivos, CURPs únicas, RFCs únicos encontrados.
    Ejemplos:
      carpeta ~/Documents/Pensión IMSS
      carpeta ~/Downloads

  tablas <ruta>
    Extrae tablas estructuradas de PDFs, Excel y CSV.
    Ideal para: constancias IMSS, estados de cuenta AFORE,
    nóminas, tablas de semanas cotizadas.
    Muestra las tablas formateadas en consola y exporta a CSV.
    Ejemplo:
      tablas ~/constancia_semanas.pdf
      tablas ~/estado_cuenta_afore.xlsx

─────────────────────────────────────────────────────────────────────

  APRENDIZAJE Y MEMORIA
  ──────────────────────
  aprender <ruta>
    Aprendizaje profundo: indexa TODO el contenido de una carpeta
    (incluyendo subcarpetas y todos los formatos soportados).
    El contenido queda disponible para búsqueda con "buscar".
    MAER recuerda todo entre sesiones (guarda en .maer_conocimiento.json)
    Soporta carpetas de hasta 10,000+ archivos.
    Ejemplos:
      aprender ~/Documents
      aprender /Volumes/Disco_Externo/Expedientes

  vigilar <ruta>
    ⚡ Vigila una carpeta EN TIEMPO REAL.
    Cada vez que agregas o modificas un archivo, MAER:
      1. Lo detecta automáticamente (cada 2 segundos)
      2. Aplica OCR avanzado
      3. Extrae entidades (CURP, RFC, NSS, semanas)
      4. Lo memoriza en la base de conocimiento
      5. Te notifica con voz si hay datos importantes
    Presiona Ctrl+C para dejar de vigilar.
    Ejemplo:
      vigilar ~/Desktop/Documentos IMSS nuevos

  buscar <término>
    Busca un término en todos los archivos aprendidos.
    Muestra el nombre del archivo y el contexto donde aparece.
    Ejemplos:
      buscar LOOA531113HTCPBN09
      buscar semanas cotizadas
      buscar constancia IMSS

─────────────────────────────────────────────────────────────────────

  REPORTES E INFORMES
  ────────────────────
  reporte
    Genera dos tipos de informe automáticamente:
    1. HTML (se abre en el navegador) — visual con gráficas y tablas:
       • Resumen estadístico (archivos, CURPs, RFCs, semanas)
       • Barra de progreso de semanas (Ley 73: 500, cesantía: 1250)
       • Listado de todas las CURPs detectadas
       • Tabla con todos los archivos procesados
    2. PDF (via servidor MAER) — documento formal descargable

  reporte html   → Solo genera el HTML y lo abre en el navegador
  reporte pdf    → Solo genera el PDF (requiere servidor activo)

─────────────────────────────────────────────────────────────────────

  SISTEMA
  ────────
  deps              Verifica todas las dependencias:
                    Python packages, Java, Conda, Tesseract,
                    Ollama (LLM local), Chrome, Poppler

  estado            Muestra estado del servidor, voz, y conocimiento acumulado

  historial         Últimas 20 conversaciones con MAER

  limpiar           Limpia la pantalla y muestra el banner

  ayuda             Muestra esta ayuda

  salir             Sale de la consola (el conocimiento se guarda automáticamente)


══════════════════════════════════════════════════════════════════════
  ACCESO DESDE CELULAR  (PWA)
══════════════════════════════════════════════════════════════════════

OPCIÓN A — Acceso en red local (WiFi):
  1. Abre cmd/terminal y escribe: ipconfig (Windows) / ifconfig (Mac)
  2. Anota tu IP local (ej: 192.168.1.100)
  3. En tu celular abre Chrome: http://192.168.1.100:8765
  4. Menú de Chrome → "Añadir a pantalla de inicio" → MAER instalado

OPCIÓN B — Acceso desde cualquier lugar (internet):
  1. Ejecuta: python iniciar_maer_ngrok.py
  2. Copia la URL pública que aparece (ej: https://abc123.ngrok.io)
  3. Abre esa URL en tu celular
  4. Menú de Chrome → "Añadir a pantalla de inicio"

  Para ngrok gratuito sin límite de tiempo:
  1. Regístrate en https://ngrok.com (gratis)
  2. Copia tu authtoken del dashboard
  3. Agrégalo al archivo .env:  NGROK_AUTHTOKEN=tu_token_aqui


══════════════════════════════════════════════════════════════════════
  CONFIGURAR IA (LLM)
══════════════════════════════════════════════════════════════════════

Por defecto MAER usa un diccionario local de Ley 73/IMSS.
Para respuestas más inteligentes, configura una de estas opciones:

OPCIÓN 1 — Groq (gratis, rápido, en la nube):
  1. Regístrate en https://console.groq.com (gratis)
  2. Crea una API key
  3. Abre el archivo .env y agrega:
       GROQ_API_KEY=gsk_tu_key_aqui
  4. Reinicia el servidor

OPCIÓN 2 — Ollama (gratis, local, privado):
  1. Descarga desde https://ollama.ai
  2. Instala y ejecuta: ollama pull llama3.2
  3. Ollama se detecta automáticamente (localhost:11434)

OPCIÓN 3 — OpenAI u otro compatible:
  OPENAI_API_KEY=sk-tu_key_aqui en el archivo .env


══════════════════════════════════════════════════════════════════════
  APIS DISPONIBLES (para desarrolladores)
══════════════════════════════════════════════════════════════════════

Servidor en http://localhost:8765

  POST /api/llm-chat              Chat con la IA
  POST /api/curp-decodificar      Decodificar CURP localmente
  POST /api/imss-consulta         Consulta IMSS (CURP+NSS)
  POST /api/sinavid-consulta      Vigencia de derechos SINAVID
  POST /api/exportar-pdf          Generar expediente PDF
  POST /api/analizar-documento    OCR + análisis de documento
  POST /api/extract-text          Extraer texto de archivo
  POST /api/expediente-imss       Revisar carpeta de documentos
  POST /api/imss-selenium         Automatización web IMSS
  GET  /api/verificar-dependencias Verificar sistema
  GET  /api/ngrok-url             URL pública activa
  GET  /service-worker.js         Service Worker (PWA)
  GET  /manifest.json             Manifest (PWA)

Ejemplo con curl:
  curl -X POST http://localhost:8765/api/llm-chat \
       -H "Content-Type: application/json" \
       -d '{"prompt":"¿Qué es la Ley 73?"}'

Ejemplo desde Python:
  import requests
  r = requests.post("http://localhost:8765/api/curp-decodificar",
                    json={"curp": "LOOA531113HTCPBN09"})
  print(r.json())


══════════════════════════════════════════════════════════════════════
  ESTRUCTURA DE ARCHIVOS
══════════════════════════════════════════════════════════════════════

  maer_backend/
    web_ui/
      server.py             Servidor FastAPI (30+ endpoints)
      static/
        index.html          Interfaz web principal
        js/
          maer.core.js      Núcleo de la aplicación
          maer.chat.js      Chat con IA
          maer.archivos.js  Análisis de documentos
          maer.poder.js     CURP, RFC, NSS, tarjetas visuales
          maer.sinavid.js   SINAVID, PDF export, Selenium
          maer.diagnostico.js  Diagnóstico del sistema
          ... (30 módulos total)
        css/
          maer.css          Estilos (tema oscuro IMSS)
        manifest.json       PWA manifest
        service-worker.js   PWA offline cache
        icons/              Íconos para instalación móvil
    maer_files.py           Motor OCR + análisis + LLM cascade

  lanzador_maer.py          GUI lanzador (tkinter)
  maer_consola.py           Consola IA avanzada
  iniciar_maer_ngrok.py     Iniciador con túnel ngrok
  .env                      Variables de entorno (API keys)
  .maer_conocimiento.json   Base de conocimiento acumulada
  .maer_consola_hist        Historial de comandos (readline)


══════════════════════════════════════════════════════════════════════
  SOLUCIÓN DE PROBLEMAS
══════════════════════════════════════════════════════════════════════

❌ "ModuleNotFoundError: No module named 'tkinter'"
   → macOS: brew install python-tk
   → Linux: sudo apt install python3-tk

❌ "tesseract is not installed or it's not in your PATH"
   → macOS:  brew install tesseract tesseract-lang
   → Linux:  sudo apt install tesseract-ocr tesseract-ocr-spa
   → Windows: https://github.com/UB-Mannheim/tesseract/wiki

❌ LLM responde "local_diccionario" (no es IA real)
   → Agrega GROQ_API_KEY al archivo .env (gratis en console.groq.com)
   → O instala Ollama: https://ollama.ai

❌ Chrome Extension no accede a localhost
   → Usa el lanzador en modo "EN LÍNEA" (ngrok)
   → O ejecuta: python iniciar_maer_ngrok.py

❌ PDF no se genera
   → Verifica: pip install reportlab
   → El servidor debe estar activo

❌ Voz no funciona
   → macOS: ya tiene "say" integrado (TTS funciona sin instalar nada)
   → Para reconocimiento: pip install SpeechRecognition pyaudio
   → Linux: sudo apt install espeak python3-pyaudio


══════════════════════════════════════════════════════════════════════
  MAER 4.0 — Uso informativo · No tiene validez oficial ante el IMSS
  Para información oficial: www.imss.gob.mx · serviciosdigitales.imss.gob.mx
══════════════════════════════════════════════════════════════════════
