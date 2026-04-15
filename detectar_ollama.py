#!/usr/bin/env python3
"""
detectar_ollama.py — Detector y selector de modelos Ollama para MAER 4.0
═══════════════════════════════════════════════════════════════════════════
Ejecuta este script en tu Mac para:
  1. Ver todos los modelos Ollama instalados
  2. Elegir el modelo por defecto para MAER
  3. Guardar la configuración en .env automáticamente
  4. Hacer un test de chat con el modelo seleccionado

Uso:
    python detectar_ollama.py           → lista modelos e interfaz
    python detectar_ollama.py --auto    → elige el mejor automáticamente
    python detectar_ollama.py --test    → lista + test de chat
    python detectar_ollama.py --json    → salida JSON para scripts

Leonel Houssen Mojica — Ecatepec MX — 2026
"""
import sys, os, json, time, shutil, subprocess, argparse, urllib.request, urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

# ── Colores ANSI ──────────────────────────────────────────────────────────────
GRN  = "\033[92m"; YLW = "\033[93m"; RED = "\033[91m"
CYN  = "\033[96m"; WHT = "\033[97m"; DIM = "\033[2m"
BOLD = "\033[1m";  NC  = "\033[0m"

def ok(t):   return f"{GRN}✅ {t}{NC}"
def warn(t): return f"{YLW}⚠️  {t}{NC}"
def err(t):  return f"{RED}❌ {t}{NC}"
def info(t): return f"{CYN}ℹ️  {t}{NC}"

# ── Rutas de Ollama (macOS + Linux + Windows) ─────────────────────────────────
OLLAMA_BIN_PATHS = [
    shutil.which("ollama"),
    "/opt/homebrew/bin/ollama",              # macOS Apple Silicon
    "/usr/local/bin/ollama",                 # macOS Intel / Homebrew
    "/Applications/Ollama.app/Contents/MacOS/ollama",  # macOS App
    "/usr/bin/ollama",                       # Linux
    "/home/linuxbrew/.linuxbrew/bin/ollama", # Linux Homebrew
    "/snap/bin/ollama",                      # Ubuntu Snap
    str(Path.home() / ".local" / "bin" / "ollama"),
    str(Path.home() / "bin" / "ollama"),
    # Conda / miniconda
    str(Path.home() / "miniconda3" / "bin" / "ollama"),
    str(Path.home() / "anaconda3" / "bin" / "ollama"),
    str(Path.home() / "mambaforge" / "bin" / "ollama"),
]

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# ── Preferencia de modelos (mejor primero) ────────────────────────────────────
PREFERENCIA = [
    # Grande y capaz
    "llama3.3:70b", "llama3.1:70b", "mixtral:8x22b", "qwen2.5:72b",
    "deepseek-r1:70b", "deepseek-r1:32b",
    # Mediano - buen balance
    "llama3.3", "llama3.2", "llama3.1", "llama3",
    "mistral-nemo", "mistral", "mixtral",
    "gemma3:27b", "gemma3", "gemma2:27b", "gemma2",
    "qwen2.5:32b", "qwen2.5:14b", "qwen2.5", "qwen2", "qwen",
    "phi4", "phi3:14b", "phi3",
    "deepseek-coder-v2", "deepseek-r1", "deepseek-coder",
    "codellama:34b", "codellama",
    # Pequeños / rápidos
    "orca-mini", "llama3.2:1b", "tinyllama",
]

def encontrar_bin():
    for p in OLLAMA_BIN_PATHS:
        if p and Path(p).exists():
            return str(p)
    return None

def servidor_activo(timeout=3):
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        return True
    except Exception:
        return False

def arrancar_servidor(bin_path):
    print(f"{DIM}  Iniciando servidor Ollama...{NC}")
    subprocess.Popen([bin_path, "serve"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)
    for i in range(8):
        time.sleep(1)
        print(f"\r  Esperando... {i+1}s", end="", flush=True)
        if servidor_activo():
            print(f"\r{ok('Servidor Ollama activo')}")
            return True
    print(f"\r{warn('Servidor tardó demasiado')}")
    return False

def listar_modelos():
    """Obtiene modelos via API REST."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
            data = json.loads(r.read())
        modelos = []
        for m in data.get("models", []):
            det = m.get("details", {})
            modelos.append({
                "name":     m["name"],
                "size_mb":  round(m.get("size", 0) / 1024 / 1024, 0),
                "size_gb":  round(m.get("size", 0) / 1024 / 1024 / 1024, 2),
                "family":   det.get("family", ""),
                "params":   det.get("parameter_size", ""),
                "quant":    det.get("quantization_level", ""),
                "modified": m.get("modified_at", "")[:10],
            })
        return sorted(modelos, key=lambda x: x["size_mb"], reverse=True)
    except Exception as e:
        return []

def listar_modelos_disco():
    """Modelos en disco (servidor apagado)."""
    encontrados = []
    dirs = [
        Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai",
        Path("/usr/share/ollama/.ollama/models/manifests/registry.ollama.ai"),
    ]
    for base in dirs:
        if base.exists():
            for familia in base.iterdir():
                for modelo in (familia.iterdir() if familia.is_dir() else []):
                    for tag in (modelo.iterdir() if modelo.is_dir() else []):
                        if tag.is_file():
                            encontrados.append(f"{familia.name}/{modelo.name}:{tag.name}")
    return sorted(set(encontrados))

def elegir_mejor(modelos):
    nombres = [m["name"] for m in modelos]
    for pref in PREFERENCIA:
        for n in nombres:
            # Coincidencia exacta primero
            if n == pref:
                return n
        for n in nombres:
            # Coincidencia parcial
            if pref.split(":")[0] in n.lower():
                return n
    return nombres[0] if nombres else None

def test_chat(model, prompt="Di 'Hola MAER' en exactamente 5 palabras."):
    """Prueba chat con el modelo dado."""
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=body,
                                  headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    elapsed = time.time() - t0
    return resp.get("response", ""), elapsed

def guardar_env(model):
    """Guarda OLLAMA_MODEL en el archivo .env de MAER."""
    env_path = BASE_DIR / ".env"
    contenido = ""
    if env_path.exists():
        lineas = env_path.read_text().splitlines()
        lineas = [l for l in lineas if not l.startswith("OLLAMA_MODEL=")]
        contenido = "\n".join(lineas)
        if contenido and not contenido.endswith("\n"):
            contenido += "\n"
    contenido += f"OLLAMA_MODEL={model}\n"
    env_path.write_text(contenido)
    return env_path

def imprimir_tabla(modelos, seleccionado=None):
    """Imprime tabla de modelos formateada."""
    if not modelos:
        print(warn("No se encontraron modelos"))
        return
    print()
    print(f"  {BOLD}{'#':<4}{'Modelo':<35}{'Tamaño':<12}{'Familia':<12}{'Params':<10}{'Cuant.':<10}{NC}")
    print(f"  {'─'*4}{'─'*35}{'─'*12}{'─'*12}{'─'*10}{'─'*10}")
    for i, m in enumerate(modelos, 1):
        es_sel = m["name"] == seleccionado
        marca  = f"{GRN}►{NC}" if es_sel else " "
        color  = GRN if es_sel else (CYN if m["size_gb"] > 10 else WHT)
        nombre = m["name"][:33]
        tam    = f"{m['size_gb']} GB" if m["size_gb"] >= 1 else f"{int(m['size_mb'])} MB"
        print(f"  {marca} {color}{i:<3}{nombre:<35}{tam:<12}{m['family'][:10]:<12}"
              f"{m['params'][:8]:<10}{m['quant'][:8]:<10}{NC}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="MAER 4.0 — Detector y selector de modelos Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--auto",  action="store_true", help="Elegir mejor modelo automáticamente")
    parser.add_argument("--test",  action="store_true", help="Probar chat con el modelo seleccionado")
    parser.add_argument("--json",  action="store_true", help="Salida en formato JSON")
    parser.add_argument("--model", default="",          help="Especificar modelo a usar")
    args = parser.parse_args()

    print()
    print(f"{BOLD}{'═'*60}{NC}")
    print(f"{BOLD}  🦁 MAER 4.0 — Detector de Modelos Ollama{NC}")
    print(f"{BOLD}{'═'*60}{NC}")
    print()

    # ── 1. Localizar binario ──────────────────────────────────────────────────
    bin_path = encontrar_bin()
    if bin_path:
        try:
            r = subprocess.run([bin_path, "--version"],
                               capture_output=True, text=True, timeout=5)
            ver = (r.stdout or r.stderr).strip()
            print(ok(f"Ollama encontrado: {bin_path}"))
            print(f"   {DIM}Versión: {ver}{NC}")
        except Exception:
            print(ok(f"Ollama encontrado: {bin_path}"))
    else:
        print(err("Ollama no encontrado"))
        print(f"   Descarga desde: {CYN}https://ollama.ai{NC}")
        print(f"   Luego: {DIM}ollama pull llama3.2{NC}")
        sys.exit(1)

    # ── 2. Verificar/arrancar servidor ────────────────────────────────────────
    print()
    if servidor_activo():
        print(ok(f"Servidor activo en {OLLAMA_URL}"))
    else:
        print(warn(f"Servidor no activo en {OLLAMA_URL}"))
        resp = input(f"  ¿Arrancar ahora? [S/n]: ").strip().lower()
        if resp in ("", "s", "si", "sí", "y", "yes"):
            if not arrancar_servidor(bin_path):
                print(err("No se pudo arrancar el servidor"))
                # Intentar listar modelos desde disco
                disco = listar_modelos_disco()
                if disco:
                    print(f"\n{info('Modelos encontrados en disco:')}")
                    for m in disco:
                        print(f"  • {m}")
                sys.exit(1)
        else:
            print(warn("Servidor apagado. Ejecuta: ollama serve"))
            sys.exit(1)

    # ── 3. Listar modelos ─────────────────────────────────────────────────────
    print()
    modelos = listar_modelos()

    if not modelos:
        print(err("No hay modelos instalados"))
        print(f"   Descarga modelos con: {DIM}ollama pull llama3.2{NC}")
        print(f"   Modelos populares:")
        populares = [
            ("llama3.2",     "3B/8B  — Bueno para español, IMSS ⭐"),
            ("llama3.3",     "70B    — Muy inteligente (requiere 40GB RAM)"),
            ("mistral",      "7B     — Rápido y eficiente"),
            ("gemma3",       "4B/12B — Google, buen rendimiento"),
            ("qwen2.5",      "7B     — Excelente en español"),
            ("phi4",         "14B    — Microsoft, muy bueno"),
            ("deepseek-r1",  "8B/32B — Razonamiento avanzado"),
        ]
        for nombre, desc in populares:
            print(f"     {DIM}ollama pull {nombre}{NC}  {desc}")
        sys.exit(1)

    if args.json:
        data = {
            "bin": bin_path,
            "server": OLLAMA_URL,
            "modelos": modelos,
            "mejor": elegir_mejor(modelos),
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # ── 4. Mostrar tabla ──────────────────────────────────────────────────────
    mejor = elegir_mejor(modelos)
    print(f"{BOLD}  Modelos instalados: {len(modelos)}{NC}")
    imprimir_tabla(modelos, seleccionado=mejor)

    # ── 5. Selección ──────────────────────────────────────────────────────────
    modelo_env = os.environ.get("OLLAMA_MODEL", "")
    if modelo_env:
        print(info(f"OLLAMA_MODEL actual en .env: {modelo_env}"))
        print()

    if args.model:
        elegido = args.model
        print(ok(f"Modelo especificado: {elegido}"))
    elif args.auto:
        elegido = mejor
        print(ok(f"Selección automática: {elegido}"))
    elif len(modelos) == 1:
        elegido = modelos[0]["name"]
        print(ok(f"Solo un modelo disponible: {elegido}"))
    else:
        print(f"  {BOLD}Selecciona el modelo por defecto para MAER:{NC}")
        print(f"  {DIM}(Enter = {mejor} recomendado){NC}")
        print()
        try:
            resp = input(f"  Número [1-{len(modelos)}] o nombre del modelo: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{warn('Cancelado')}")
            sys.exit(0)

        if resp == "":
            elegido = mejor
        elif resp.isdigit():
            idx = int(resp) - 1
            if 0 <= idx < len(modelos):
                elegido = modelos[idx]["name"]
            else:
                print(err(f"Número fuera de rango (1-{len(modelos)})"))
                sys.exit(1)
        else:
            # Buscar por nombre parcial
            coincidencias = [m["name"] for m in modelos if resp.lower() in m["name"].lower()]
            if len(coincidencias) == 1:
                elegido = coincidencias[0]
            elif len(coincidencias) > 1:
                print(warn(f"Varias coincidencias: {', '.join(coincidencias)}"))
                elegido = coincidencias[0]
                print(f"  Usando: {elegido}")
            else:
                print(err(f"Modelo '{resp}' no encontrado"))
                sys.exit(1)

    # ── 6. Test de chat (opcional) ────────────────────────────────────────────
    if args.test or (not args.auto and not args.model):
        probar = args.test
        if not probar:
            try:
                r = input(f"\n  ¿Probar chat con '{elegido}'? [S/n]: ").strip().lower()
                probar = r in ("", "s", "si", "sí", "y", "yes")
            except (KeyboardInterrupt, EOFError):
                probar = False

        if probar:
            print()
            print(f"  {DIM}Enviando prompt de prueba a {elegido}...{NC}")
            prompts_imss = [
                "¿Cuántas semanas necesito cotizar para pensionarme con Ley 73 del IMSS?",
                "¿Qué es la Modalidad 40 del IMSS?",
                "Explica brevemente la diferencia entre Ley 73 y Ley 97 del IMSS.",
            ]
            import random
            prompt = random.choice(prompts_imss)
            print(f"  {DIM}Pregunta: {prompt}{NC}")
            print()
            try:
                respuesta, elapsed = test_chat(elegido, prompt)
                print(f"  {BOLD}Respuesta de {elegido} ({elapsed:.1f}s):{NC}")
                print()
                # Mostrar respuesta formateada (máx 400 chars)
                for linea in respuesta[:400].splitlines():
                    print(f"  {linea}")
                if len(respuesta) > 400:
                    print(f"  {DIM}... (respuesta truncada, {len(respuesta)} chars total){NC}")
                print()
                print(ok(f"Chat funcionando correctamente ({elapsed:.1f}s de respuesta)"))
            except Exception as e:
                print(err(f"Error en chat: {e}"))

    # ── 7. Guardar en .env ────────────────────────────────────────────────────
    print()
    print(f"  {BOLD}Modelo seleccionado: {GRN}{elegido}{NC}")

    try:
        guardar = True
        if not args.auto and not args.model:
            r = input(f"\n  ¿Guardar '{elegido}' como modelo por defecto en .env? [S/n]: ").strip().lower()
            guardar = r in ("", "s", "si", "sí", "y", "yes")

        if guardar:
            env_path = guardar_env(elegido)
            print(ok(f"Guardado en: {env_path}"))
            print(f"   {DIM}MAER usará '{elegido}' automáticamente al arrancar{NC}")
    except (KeyboardInterrupt, EOFError):
        print(f"\n{warn('No guardado')}")

    # ── 8. Resumen final ──────────────────────────────────────────────────────
    print()
    print(f"{BOLD}{'═'*60}{NC}")
    print(f"{BOLD}  Configuración MAER + Ollama:{NC}")
    print(f"{'─'*60}")
    print(f"  Binario:   {DIM}{bin_path}{NC}")
    print(f"  Servidor:  {DIM}{OLLAMA_URL}{NC}")
    print(f"  Modelos:   {GRN}{len(modelos)} instalados{NC}")
    print(f"  Activo:    {GRN}{elegido}{NC}")
    print()
    print(f"  Para usar MAER con este modelo:")
    print(f"    {DIM}python lanzador_maer.py{NC}      ← interfaz gráfica")
    print(f"    {DIM}python maer_consola.py{NC}       ← consola IA")
    print(f"    {DIM}python maer_tester.py --suite=ollama{NC}  ← pruebas")
    print(f"{BOLD}{'═'*60}{NC}")
    print()

    # Exportar también para scripts
    if args.json:
        print(json.dumps({"elegido": elegido, "total": len(modelos)}, indent=2))


if __name__ == "__main__":
    main()
