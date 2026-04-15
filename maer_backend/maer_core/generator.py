#!/usr/bin/env python3
# 🦁 MAER Core — Generator (estructura de proyecto)
# Leonel Mojica — Ecatepec MX — 2026

"""
Crea la estructura base de carpetas para MAER.
"""

from pathlib import Path


def ensure_structure(*dirs: Path):
    """Crea directorios si no existen."""
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"  📁 Creado: {d}")
        else:
            pass  # Directorio ya existe
