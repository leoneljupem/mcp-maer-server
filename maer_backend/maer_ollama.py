#!/usr/bin/env python3
"""
maer_ollama.py — Detección y gestión inteligente de Ollama
═══════════════════════════════════════════════════════════
Detecta Ollama en rutas comunes de macOS/Linux/Windows,
lista los modelos descargados y permite chat directo.

Leonel Houssen Mojica — Ecatepec MX — 2026
"""

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


# URL del servidor Ollama — leída dinámicamente para respetar cambios en os.environ
def _ollama_url() -> str:
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434")


# Alias de compatibilidad (módulos que importan OLLAMA_URL directamente)
OLLAMA_URL = _ollama_url()


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
        urllib.request.urlopen(f"{_ollama_url()}/api/tags", timeout=timeout)
        return True
    except Exception as e:
        return False


# ─── Listar modelos via API ───────────────────────────────────────────────────
def listar_modelos_api() -> List[Dict]:
    """
    Obtiene la lista de modelos via API REST de Ollama.
    Devuelve lista de dicts con: name, size_mb, modified, family, params.
    """
    try:
        with urllib.request.urlopen(f"{_ollama_url()}/api/tags", timeout=5) as r:
            data = json.loads(r.read())
        modelos = []
        for m in data.get("models", []):
            details = m.get("details", {})
            modelos.append(
                {
                    "name": m.get("name", ""),
                    "size_mb": round(m.get("size", 0) / 1024 / 1024, 1),
                    "modified": m.get("modified_at", "")[:10],
                    "family": details.get("family", ""),
                    "params": details.get("parameter_size", ""),
                    "quant": details.get("quantization_level", ""),
                }
            )
        return sorted(modelos, key=lambda x: x["size_mb"], reverse=True)
    except Exception as e:
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
                                    encontrados.append(
                                        f"{familia.name}/{modelo.name}:{tag.name}"
                                    )
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
        import time

        time.sleep(3)
        if servidor_activo():
            return True, "Ollama iniciado automáticamente"
        return False, "Ollama arrancó pero no responde"
    except Exception as e:
        return False, f"No se pudo iniciar Ollama: {e}"


# ─── Seleccionar mejor modelo disponible ─────────────────────────────────────
# Thinking models (qwen3.x, deepseek-r1, openthinker) van al final:
# son muy lentos y producen <think>...</think> que puede vaciar la respuesta.
PREFERENCIA_MODELOS = [
    # Modelos conversacionales rápidos (prioridad alta)
    "gemma3",
    "gemma2",
    "gemma",
    "llama3.3",
    "llama3.2",
    "llama3.1",
    "llama3",
    "mistral",
    "mistral-nemo",
    "mixtral",
    "qwen2.5",
    "qwen2",
    "phi4",
    "phi3",
    "phi",
    "granite",
    # Modelos de código (útiles para análisis)
    "deepseek-ocr",
    "glm-ocr",
    "codellama",
    # Modelos pequeños de fallback
    "smollm",
    "tinyllama",
    "orca-mini",
    # Thinking models al final (lentos, requieren strip de <think>)
    "qwen3.5",
    "qwen3",
    "deepseek-r1",
    "openthinker",
]

# Modelos que usan <think>...</think> — la respuesta útil viene DESPUÉS del cierre
_THINKING_MODELS = {"qwen3", "qwen3.5", "deepseek-r1", "openthinker", "r1"}


def _modelo_apto_chat(modelo: Dict) -> bool:
    """Descarta modelos que no pueden responder chat de texto en esta máquina."""
    nombre = str(modelo.get("name") or "").lower()
    detalles = modelo.get("details") or {}
    family = str(detalles.get("family") or "").lower()
    caps = detalles.get("capabilities") or modelo.get("capabilities") or []
    if isinstance(caps, str):
        caps = [caps]
    caps = [str(c).lower() for c in caps]

    # Modelos cloud: requieren cuenta/red y responden 403.
    if modelo.get("remote_host") or modelo.get("remote_model"):
        return False
    if ":cloud" in nombre or "cloud" in nombre:
        return False
    # Modelos de embedding: no generan texto.
    if "embed" in family or "embed" in nombre or "bert" in family:
        return False
    # Modelos de visión (mllama/llava): arquitectura no soportada por el runtime local.
    if "mllama" in family or "llava" in family or "vision" in nombre or "vision" in caps:
        return False
    return True


def elegir_modelo(modelos: List[Dict]) -> Optional[str]:
    """
    Elige el mejor modelo local de texto según preferencia predefinida.
    OLLAMA_MODEL se respeta solo si existe y es apto para chat de texto.
    """
    if not modelos:
        return None

    aptos = [m for m in modelos if _modelo_apto_chat(m)]
    if not aptos:
        return None

    nombres = [m["name"] for m in modelos]
    env_model = os.environ.get("OLLAMA_MODEL", "")
    if env_model and (env_model in nombres or any(env_model in n for n in nombres)):
        for m in aptos:
            if env_model == m["name"] or env_model in m["name"]:
                return m["name"]

    # Dentro de la misma preferencia, el modelo más ligero responde más rápido.
    aptos.sort(key=lambda m: (m.get("size_mb", 0), m["name"]))
    for pref in PREFERENCIA_MODELOS:
        for m in aptos:
            if pref in m["name"].lower():
                return m["name"]

    return aptos[0]["name"]


# ─── Chat con Ollama ──────────────────────────────────────────────────────────
def chat(
    prompt: str,
    model: str = None,
    timeout: int = 90,
    system: str = None,
    stream: bool = False,
) -> Dict:
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

    modelo_auto = elegir_modelo(modelos)
    model = model or modelo_auto
    if not model:
        raise ValueError("No se pudo determinar el modelo a usar")

    # Si el modelo elegido falla (instalado roto, arquitectura no soportada, etc.),
    # probar los siguientes modelos locales aptos antes de rendirse.
    candidatos = [model]
    if model == modelo_auto:
        for m in sorted(
            (x for x in modelos if _modelo_apto_chat(x)),
            key=lambda x: (x.get("size_mb", 0), x["name"]),
        ):
            if m["name"] not in candidatos:
                candidatos.append(m["name"])
    candidatos = candidatos[:4]

    ultimo_error = None
    for candidato in candidatos:
        body = {"model": candidato, "prompt": prompt, "stream": stream}
        if system:
            body["system"] = system

        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{_ollama_url()}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
        except Exception as e:
            ultimo_error = e
            continue

        raw_text = resp.get("response", "")

        # Eliminar bloques <think>...</think> de modelos de razonamiento
        is_thinking = any(t in candidato.lower() for t in _THINKING_MODELS)
        if is_thinking or "<think>" in raw_text:
            import re as _re

            clean = _re.sub(r"<think>.*?</think>", "", raw_text, flags=_re.DOTALL).strip()
            raw_text = clean if clean else raw_text  # fallback si todo era thinking

        return {
            "ok": True,
            "text": raw_text,
            "engine": f"ollama/{candidato}",
            "tokens": resp.get("eval_count", 0),
            "model": candidato,
        }

    raise ConnectionError(
        f"Ollama respondió con error en todos los modelos probados: {ultimo_error}"
    )


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
            [bin_path, "pull", model], capture_output=True, text=True, timeout=300
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
    activo = servidor_activo()
    modelos = listar_modelos_api() if activo else []
    disco = listar_modelos_disco() if not activo else []
    elegido = elegir_modelo(modelos) if modelos else None

    # Versión
    version = None
    if bin_path:
        try:
            r = subprocess.run(
                [bin_path, "--version"], capture_output=True, text=True, timeout=5
            )
            version = (r.stdout or r.stderr).strip()
        except Exception as e:
            pass

    return {
        "instalado": bool(bin_path),
        "bin_path": bin_path,
        "version": version,
        "servidor_activo": activo,
        "url": _ollama_url(),
        "modelos": modelos,
        "modelos_disco": disco,
        "total_modelos": len(modelos) or len(disco),
        "modelo_elegido": elegido,
        "modelo_env": os.environ.get("OLLAMA_MODEL", ""),
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
