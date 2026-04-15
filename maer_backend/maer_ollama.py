#!/usr/bin/env python3
"""
maer_ollama.py — Detección y gestión inteligente de Ollama
═══════════════════════════════════════════════════════════
Detecta Ollama en rutas comunes de macOS/Linux/Windows,
lista los modelos descargados y permite chat directo.

Leonel Houssen Mojica — Ecatepec MX — 2026
"""
import os
import json
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# ─── Rutas donde puede estar Ollama (macOS, Linux, Windows) ───────────────────
OLLAMA_PATHS = [
    # PATH del sistema
    shutil.which("ollama"),
    # macOS Homebrew
    "/opt/homebrew/bin/ollama",
    "/usr/local/bin/ollama",
    # macOS app bundle
    "/Applications/Ollama.app/Contents/MacOS/ollama",
    # Linux estándar
    "/usr/bin/ollama",
    "/usr/local/bin/ollama",
    # WSL / Linux custom
    "/home/linuxbrew/.linuxbrew/bin/ollama",
    # Snap (Ubuntu)
    "/snap/bin/ollama",
    # Conda
    str(Path.home() / "miniconda3" / "bin" / "ollama"),
    str(Path.home() / "anaconda3" / "bin" / "ollama"),
    str(Path.home() / ".local" / "bin" / "ollama"),
]

# Directorio de modelos Ollama
OLLAMA_MODEL_DIRS = [
    Path.home() / ".ollama" / "models",
    Path("/usr/share/ollama/.ollama/models"),
    Path("/var/lib/ollama/models"),
]

# URL del servidor Ollama (puede cambiar si el usuario puso otro puerto)
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


# ─── Detección binario ────────────────────────────────────────────────────────
def encontrar_ollama_bin() -> Optional[str]:
    """Devuelve la ruta al binario de Ollama, o None si no se encuentra."""
    for path in OLLAMA_PATHS:
        if path and Path(path).exists():
            return str(path)
    return None


# ─── Estado del servidor ──────────────────────────────────────────────────────
def servidor_activo(timeout: int = 3) -> bool:
    """Verifica si el servidor Ollama está corriendo en OLLAMA_URL."""
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        return True
    except Exception:
        return False


# ─── Listar modelos via API ───────────────────────────────────────────────────
def listar_modelos_api() -> List[Dict]:
    """
    Obtiene la lista de modelos via API REST de Ollama.
    Devuelve lista de dicts con: name, size_mb, modified, family, params.
    """
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
            data = json.loads(r.read())
        modelos = []
        for m in data.get("models", []):
            details = m.get("details", {})
            modelos.append({
                "name":     m.get("name", ""),
                "size_mb":  round(m.get("size", 0) / 1024 / 1024, 1),
                "modified": m.get("modified_at", "")[:10],
                "family":   details.get("family", ""),
                "params":   details.get("parameter_size", ""),
                "quant":    details.get("quantization_level", ""),
            })
        return sorted(modelos, key=lambda x: x["size_mb"], reverse=True)
    except Exception:
        return []


# ─── Listar modelos por archivos (sin servidor) ───────────────────────────────
def listar_modelos_disco() -> List[str]:
    """
    Escanea el disco en busca de modelos Ollama descargados.
    Útil cuando el servidor no está corriendo.
    """
    encontrados = []
    for base in OLLAMA_MODEL_DIRS:
        manifests = base / "manifests" / "registry.ollama.ai"
        if manifests.exists():
            for familia in manifests.iterdir():
                if familia.is_dir():
                    for modelo in familia.iterdir():
                        if modelo.is_dir():
                            for tag in modelo.iterdir():
                                if tag.is_file():
                                    encontrados.append(f"{familia.name}/{modelo.name}:{tag.name}")
    return sorted(set(encontrados))


# ─── Arrancar Ollama (si el binario existe pero no está corriendo) ─────────────
def arrancar_ollama(bin_path: str) -> Tuple[bool, str]:
    """
    Intenta iniciar el servidor Ollama en background.
    Devuelve (éxito, mensaje).
    """
    try:
        subprocess.Popen(
            [bin_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        import time; time.sleep(3)
        if servidor_activo():
            return True, "Ollama iniciado automáticamente"
        return False, "Ollama arrancó pero no responde"
    except Exception as e:
        return False, f"No se pudo iniciar Ollama: {e}"


# ─── Seleccionar mejor modelo disponible ─────────────────────────────────────
PREFERENCIA_MODELOS = [
    # Más inteligentes primero
    "llama3.3", "llama3.2", "llama3.1", "llama3",
    "mistral", "mistral-nemo", "mixtral",
    "gemma3", "gemma2", "gemma",
    "qwen2.5", "qwen2", "qwen",
    "phi4", "phi3", "phi",
    "deepseek-r1", "deepseek-coder",
    "codellama",
    "orca-mini", "tinyllama",
]

def elegir_modelo(modelos: List[Dict]) -> Optional[str]:
    """
    Elige el mejor modelo disponible según preferencia predefinida.
    Si OLLAMA_MODEL está en .env, lo usa directamente.
    """
    env_model = os.environ.get("OLLAMA_MODEL", "")
    if env_model:
        # Verificar que exista
        nombres = [m["name"] for m in modelos]
        if env_model in nombres or any(env_model in n for n in nombres):
            return env_model

    nombres = [m["name"] for m in modelos]
    for pref in PREFERENCIA_MODELOS:
        for n in nombres:
            if pref in n.lower():
                return n

    # Si no hay preferencia, usar el primero (mayor tamaño = más capaz)
    return nombres[0] if nombres else None


# ─── Chat con Ollama ──────────────────────────────────────────────────────────
def chat(prompt: str, model: str = None, timeout: int = 90,
         system: str = None, stream: bool = False) -> Dict:
    """
    Envía un prompt a Ollama y devuelve la respuesta.

    Args:
        prompt:  Texto del usuario
        model:   Modelo a usar (auto-detectado si None)
        timeout: Segundos máximos de espera
        system:  Prompt de sistema opcional
        stream:  Si True, devuelve respuesta parcial más rápido

    Returns:
        {"ok": bool, "text": str, "engine": str, "tokens": int}
    """
    if not servidor_activo():
        bin_path = encontrar_ollama_bin()
        if bin_path:
            ok, msg = arrancar_ollama(bin_path)
            if not ok:
                raise ConnectionError(f"Ollama no disponible: {msg}")
        else:
            raise ConnectionError("Ollama no instalado. Descarga desde ollama.ai")

    modelos = listar_modelos_api()
    if not modelos:
        raise ValueError("No hay modelos Ollama descargados. Usa: ollama pull llama3.2")

    model = model or elegir_modelo(modelos)
    if not model:
        raise ValueError("No se pudo determinar el modelo a usar")

    body = {"model": model, "prompt": prompt, "stream": stream}
    if system:
        body["system"] = system

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())

    return {
        "ok":     True,
        "text":   resp.get("response", ""),
        "engine": f"ollama/{model}",
        "tokens": resp.get("eval_count", 0),
        "model":  model,
    }


# ─── Pull de un modelo ────────────────────────────────────────────────────────
def pull_modelo(model: str) -> Tuple[bool, str]:
    """
    Descarga un modelo via `ollama pull`.
    Requiere que el binario esté disponible.
    """
    bin_path = encontrar_ollama_bin()
    if not bin_path:
        return False, "Ollama no instalado"
    try:
        result = subprocess.run(
            [bin_path, "pull", model],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            return True, f"Modelo '{model}' descargado exitosamente"
        return False, result.stderr[:200]
    except Exception as e:
        return False, str(e)


# ─── Resumen del estado ───────────────────────────────────────────────────────
def estado_completo() -> Dict:
    """
    Devuelve un dict con toda la información sobre Ollama:
    binario, servidor, modelos disponibles, modelo seleccionado.
    """
    bin_path = encontrar_ollama_bin()
    activo   = servidor_activo()
    modelos  = listar_modelos_api() if activo else []
    disco    = listar_modelos_disco() if not activo else []
    elegido  = elegir_modelo(modelos) if modelos else None

    # Versión
    version = None
    if bin_path:
        try:
            r = subprocess.run([bin_path, "--version"],
                               capture_output=True, text=True, timeout=5)
            version = (r.stdout or r.stderr).strip()
        except Exception:
            pass

    return {
        "instalado":       bool(bin_path),
        "bin_path":        bin_path,
        "version":         version,
        "servidor_activo": activo,
        "url":             OLLAMA_URL,
        "modelos":         modelos,
        "modelos_disco":   disco,
        "total_modelos":   len(modelos) or len(disco),
        "modelo_elegido":  elegido,
        "modelo_env":      os.environ.get("OLLAMA_MODEL", ""),
    }


if __name__ == "__main__":
    # Prueba rápida
    print("🔍 Detectando Ollama...\n")
    estado = estado_completo()
    print(f"  Binario:   {estado['bin_path'] or 'No encontrado'}")
    print(f"  Versión:   {estado['version'] or 'N/A'}")
    print(f"  Servidor:  {'✅ Activo' if estado['servidor_activo'] else '❌ Inactivo'}")
    print(f"  Modelos:   {estado['total_modelos']}")
    for m in estado["modelos"]:
        star = " ⭐" if m["name"] == estado["modelo_elegido"] else ""
        print(f"    - {m['name']} ({m['size_mb']} MB){star}")
    for m in estado["modelos_disco"]:
        print(f"    - {m} (en disco, servidor apagado)")
    print(f"\n  Modelo activo: {estado['modelo_elegido'] or 'Ninguno'}")
