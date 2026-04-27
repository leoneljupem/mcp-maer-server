#!/usr/bin/env python3
# 🦁 MAER File Watcher — Auto-indexado en tiempo real
# Leonel Mojica — Ecatepec MX — 2026

"""
Vigila carpetas y re-indexa automáticamente cuando se añaden o modifican archivos.
Usa watchdog (FSEvents en macOS, inotify en Linux).
"""

import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger("maer.watcher")

WATCH_CONFIG = os.environ.get("MAER_WATCH_CONFIG", "data/watched_dirs.json")
_SKIP_EXTS = {
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".exe",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".lock",
    ".pid",
    ".log",
    ".DS_Store",
}

# ── Estado global ──────────────────────────────────────────────────────────────
_observer = None
_watched = {}  # {path_str: {"since": ts, "indexed": n, "errors": n}}
_state_lock = threading.Lock()


# ── Handler de eventos ─────────────────────────────────────────────────────────


class _MAERHandler:
    def __init__(self):
        from watchdog.events import FileSystemEventHandler

        self._base = FileSystemEventHandler

    def dispatch(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in _SKIP_EXTS:
            return
        if path.stat().st_size > 100 * 1024 * 1024 if path.exists() else True:
            return
        _index_in_background(path)


def _make_handler():
    from watchdog.events import FileSystemEventHandler

    class Handler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                _maybe_index(Path(event.src_path))

        def on_modified(self, event):
            if not event.is_directory:
                _maybe_index(Path(event.src_path))

    return Handler()


def _maybe_index(path: Path):
    if not path.exists():
        return
    if path.suffix.lower() in _SKIP_EXTS:
        return
    if path.stat().st_size > 100 * 1024 * 1024:
        return
    _index_in_background(path)


def _index_in_background(path: Path):
    def _run():
        try:
            from maer_backend.maer_search_index import index_file

            result = index_file(path, ocr=False)
            status = result.get("status", "?")
            logger.info(f"Watcher → {path.name}: {status}")
            # Actualizar contador
            with _state_lock:
                for watched_path in list(_watched.keys()):
                    if str(path).startswith(watched_path):
                        if status in ("indexed", "updated"):
                            _watched[watched_path]["indexed"] = (
                                _watched[watched_path].get("indexed", 0) + 1
                            )
                        elif not result.get("ok"):
                            _watched[watched_path]["errors"] = (
                                _watched[watched_path].get("errors", 0) + 1
                            )
                        break
        except Exception as e:
            logger.debug(f"Watcher index error {path}: {e}")

    threading.Thread(target=_run, daemon=True).start()


# ── API pública ────────────────────────────────────────────────────────────────


def start_watching(directory: str) -> dict:
    """Empieza a vigilar un directorio. Crea el observer si no existe."""
    global _observer
    directory = str(Path(directory).expanduser().resolve())

    if not Path(directory).exists():
        return {"ok": False, "error": f"Directorio no existe: {directory}"}

    with _state_lock:
        if directory in _watched:
            return {"ok": True, "status": "already_watching", "path": directory}

    try:
        from watchdog.observers import Observer

        if _observer is None or not _observer.is_alive():
            _observer = Observer()
            _observer.start()

        handler = _make_handler()
        _observer.schedule(handler, directory, recursive=True)

        with _state_lock:
            _watched[directory] = {
                "since": time.time(),
                "indexed": 0,
                "errors": 0,
                "handler": id(handler),
            }

        _save_config()
        logger.info(f"Watcher iniciado: {directory}")
        return {"ok": True, "status": "watching", "path": directory}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def stop_watching(directory: str) -> dict:
    """Deja de vigilar un directorio."""
    global _observer
    directory = str(Path(directory).expanduser().resolve())

    with _state_lock:
        if directory not in _watched:
            return {"ok": False, "error": "No se estaba vigilando ese directorio"}
        del _watched[directory]

    _save_config()

    # Si no quedan carpetas, detener el observer
    with _state_lock:
        if not _watched and _observer and _observer.is_alive():
            _observer.stop()
            _observer = None

    logger.info(f"Watcher detenido: {directory}")
    return {"ok": True, "status": "stopped", "path": directory}


def watcher_status() -> dict:
    """Estado actual del watcher."""
    global _observer
    with _state_lock:
        active = _observer is not None and _observer.is_alive()
        dirs = [
            {
                "path": p,
                "since": info.get("since"),
                "indexed": info.get("indexed", 0),
                "errors": info.get("errors", 0),
            }
            for p, info in _watched.items()
        ]
    return {
        "ok": True,
        "active": active,
        "watching": dirs,
        "count": len(dirs),
    }


def restore_from_config():
    """Al arrancar el servidor, restaura las carpetas vigiladas desde disco."""
    cp = Path(WATCH_CONFIG)
    if not cp.exists():
        return
    try:
        dirs = json.loads(cp.read_text())
        for d in dirs:
            start_watching(d)
        logger.info(f"Watcher restaurado: {len(dirs)} carpeta(s)")
    except Exception as e:
        logger.debug(f"No se pudo restaurar watcher config: {e}")


def _save_config():
    cp = Path(WATCH_CONFIG)
    try:
        cp.parent.mkdir(parents=True, exist_ok=True)
        with _state_lock:
            dirs = list(_watched.keys())
        cp.write_text(json.dumps(dirs, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.debug(f"No se pudo guardar watcher config: {e}")
