#!/usr/bin/env python3
# 🦁 MAER Core — Analizador
# Leonel Mojica — Ecatepec MX — 2026

"""
Escanea archivos en una carpeta y genera un reporte de análisis.
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def run_scan(input_dir: Path, report_dir: Path):
    """Analiza archivos en input_dir y genera un reporte JSON en report_dir."""
    print(f"🔍 Escaneando archivos en: {input_dir}")

    results = []
    file_count = 0
    total_size = 0

    if not input_dir.exists():
        print(f"⚠️  Directorio no existe: {input_dir}")
        return

    for p in input_dir.rglob("*"):
        if p.is_file():
            file_count += 1
            size = p.stat().st_size
            total_size += size
            results.append({
                "path": str(p),
                "name": p.name,
                "ext": p.suffix.lower(),
                "size_bytes": size,
            })

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir),
        "total_files": file_count,
        "total_size_bytes": total_size,
        "files": results,
    }

    report_file = report_dir / "scan_report.json"
    report_dir.mkdir(parents=True, exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ Escaneo completo: {file_count} archivos ({total_size:,} bytes)")
    print(f"📄 Reporte guardado en: {report_file}")
