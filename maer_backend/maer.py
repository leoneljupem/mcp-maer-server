#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦁 MAER PROJECT MANAGER 2026
Leonel Mojica — Mexico City / Ecatepec MX

CLI para análisis documental, corrección de archivos e indexación.

Uso:
    python maer.py scan           → analiza archivos y genera reporte
    python maer.py fix            → corrige archivos de texto/código
    python maer.py full           → scan + fix
    python maer.py index <dir>    → indexa carpeta completa
    python maer.py search <query> → busca en el índice
    python maer.py ocr <file>     → OCR de un archivo
    python maer.py ids <file>     → detecta CURP/RFC/INE en archivo
    python maer.py faces <dir>    → detecta rostros en imágenes
    python maer.py dupes <dir>    → encuentra imágenes duplicadas
"""

import sys
import json
import argparse
from pathlib import Path

# Importar módulos del proyecto
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from maer_core.analyzer import run_scan
from maer_core.fixer import run_fix
from maer_core.generator import ensure_structure


BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "inputs"
REPORT_DIR = DATA_DIR / "reports"


def cmd_scan(args):
    """Escanea archivos y genera reporte."""
    input_dir = Path(args.dir) if args.dir else INPUT_DIR
    ensure_structure(BASE_DIR, DATA_DIR, input_dir, REPORT_DIR)
    run_scan(input_dir, REPORT_DIR)


def cmd_fix(args):
    """Corrige archivos de texto/código."""
    input_dir = Path(args.dir) if args.dir else INPUT_DIR
    ensure_structure(BASE_DIR, DATA_DIR, input_dir, REPORT_DIR)
    run_fix(input_dir, REPORT_DIR)


def cmd_full(args):
    """Scan + Fix combinados."""
    input_dir = Path(args.dir) if args.dir else INPUT_DIR
    ensure_structure(BASE_DIR, DATA_DIR, input_dir, REPORT_DIR)
    run_scan(input_dir, REPORT_DIR)
    run_fix(input_dir, REPORT_DIR)


def cmd_index(args):
    """Indexa una carpeta completa."""
    from maer_files import action_index_full
    result = action_index_full({
        "base_dir": args.dir,
        "max_files": args.max_files,
        "ocr_for_pdf": not args.no_ocr,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_search(args):
    """Busca en el índice."""
    from maer_files import action_search_index
    result = action_search_index({
        "base_dir": args.dir,
        "query": args.query,
        "max_results": args.max_results,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_ocr(args):
    """OCR de un archivo."""
    from maer_files import action_ocr_multimodal
    result = action_ocr_multimodal({
        "path": args.file,
        "engine": args.engine,
    })
    if args.text_only:
        data = result.get("data", {})
        print(data.get("text", ""))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_ids(args):
    """Detecta CURP/RFC/INE en un archivo."""
    from maer_files import action_detect_ids
    result = action_detect_ids({
        "mode": "file",
        "path": args.file,
        "ocr_for_pdf": not args.no_ocr,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_faces(args):
    """Detecta rostros en imágenes."""
    from maer_files import action_face_detect
    result = action_face_detect({
        "base_dir": args.dir,
        "max_files": args.max_files,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_dupes(args):
    """Encuentra imágenes duplicadas."""
    from maer_files import action_image_duplicates
    result = action_image_duplicates({
        "base_dir": args.dir,
        "threshold": args.threshold,
        "max_files": args.max_files,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        prog="maer",
        description="🦁 MAER Project Manager 2026 — Análisis documental multimodal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # scan
    p_scan = subparsers.add_parser("scan", help="Escanea archivos y genera reporte")
    p_scan.add_argument("--dir", type=str, help="Directorio a escanear")
    p_scan.set_defaults(func=cmd_scan)

    # fix
    p_fix = subparsers.add_parser("fix", help="Corrige archivos de texto/código")
    p_fix.add_argument("--dir", type=str, help="Directorio a corregir")
    p_fix.set_defaults(func=cmd_fix)

    # full
    p_full = subparsers.add_parser("full", help="Scan + Fix combinados")
    p_full.add_argument("--dir", type=str, help="Directorio objetivo")
    p_full.set_defaults(func=cmd_full)

    # index
    p_index = subparsers.add_parser("index", help="Indexa una carpeta completa")
    p_index.add_argument("dir", type=str, help="Directorio a indexar")
    p_index.add_argument("--max-files", type=int, default=500, help="Máximo de archivos")
    p_index.add_argument("--no-ocr", action="store_true", help="Desactivar OCR en PDFs")
    p_index.set_defaults(func=cmd_index)

    # search
    p_search = subparsers.add_parser("search", help="Busca en el índice")
    p_search.add_argument("query", type=str, help="Texto a buscar")
    p_search.add_argument("--dir", type=str, default=".", help="Directorio base del índice")
    p_search.add_argument("--max-results", type=int, default=50, help="Máximo de resultados")
    p_search.set_defaults(func=cmd_search)

    # ocr
    p_ocr = subparsers.add_parser("ocr", help="OCR de un archivo")
    p_ocr.add_argument("file", type=str, help="Archivo a procesar")
    p_ocr.add_argument("--engine", type=str, default="auto",
                       choices=["auto", "tesseract", "easyocr", "paddleocr"],
                       help="Motor OCR a usar")
    p_ocr.add_argument("--text-only", action="store_true", help="Solo imprimir texto extraído")
    p_ocr.set_defaults(func=cmd_ocr)

    # ids
    p_ids = subparsers.add_parser("ids", help="Detecta CURP/RFC/INE en un archivo")
    p_ids.add_argument("file", type=str, help="Archivo a analizar")
    p_ids.add_argument("--no-ocr", action="store_true", help="Desactivar OCR")
    p_ids.set_defaults(func=cmd_ids)

    # faces
    p_faces = subparsers.add_parser("faces", help="Detecta rostros en imágenes")
    p_faces.add_argument("dir", type=str, help="Directorio con imágenes")
    p_faces.add_argument("--max-files", type=int, default=200, help="Máximo de archivos")
    p_faces.set_defaults(func=cmd_faces)

    # dupes
    p_dupes = subparsers.add_parser("dupes", help="Encuentra imágenes duplicadas")
    p_dupes.add_argument("dir", type=str, help="Directorio con imágenes")
    p_dupes.add_argument("--threshold", type=int, default=10, help="Umbral de similitud (0-64)")
    p_dupes.add_argument("--max-files", type=int, default=1000, help="Máximo de archivos")
    p_dupes.set_defaults(func=cmd_dupes)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()