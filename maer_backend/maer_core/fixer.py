#!/usr/bin/env python3
# 🦁 MAER Core — Fixer
# Leonel Mojica — Ecatepec MX — 2026

"""
Corrige archivos de texto: trailing spaces, encoding, etc.
"""

from pathlib import Path

TEXT_EXTS = {
    ".txt",
    ".md",
    ".log",
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".html",
    ".htm",
    ".css",
    ".json",
    ".yml",
    ".yaml",
    ".xml",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".php",
    ".rb",
    ".go",
    ".rs",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".csv",
}


def run_fix(input_dir: Path, report_dir: Path):
    """Corrige problemas comunes en archivos de código."""
    print(f"🔧 Corrigiendo archivos en: {input_dir}")

    if not input_dir.exists():
        print(f"⚠️  Directorio no existe: {input_dir}")
        return

    fixed_count = 0
    skipped_count = 0

    for p in input_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            skipped_count += 1
            continue

        try:
            with open(p, "rb") as f:
                data = f.read(1024 * 1024)  # 1MB max
            text = data.decode("utf-8", errors="ignore")
            original = text

            # Strip trailing whitespace
            lines = [line.rstrip() for line in text.splitlines()]
            fixed = "\n".join(lines)
            if text.endswith("\n"):
                fixed += "\n"

            if fixed != original:
                # Backup
                backup = p.with_suffix(p.suffix + ".maer.bak")
                backup.write_text(original, encoding="utf-8")
                p.write_text(fixed, encoding="utf-8")
                fixed_count += 1
                print(f"  ✏️  Corregido: {p.name}")

        except Exception as e:
            print(f"  ❌ Error en {p.name}: {e}")

    print(
        f"✅ Corrección completa: {fixed_count} archivos corregidos, {skipped_count} omitidos"
    )
