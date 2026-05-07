# -*- coding: utf-8 -*-
"""
Full project audit script.
- Compila cada archivo Python para detectar errores de sintaxis.
- Importa cada módulo y verifica que no lance excepciones al cargar.
- Ejecuta funciones clave (audit_identity, ocr_auto, action_search_index, action_analyze_file).
- Genera un reporte JSON con los resultados.
"""
import os
import sys
import json
import importlib.util
import traceback
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - 🧪 FullAudit - %(message)s')

PROJECT_ROOT = Path(__file__).resolve().parent

# Funciones auxiliares
def load_module(path: Path):
    try:
        spec = importlib.util.spec_from_file_location(path.stem, str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, None
    except Exception as e:
        return None, traceback.format_exc()

def run_critical_functions():
    results = {}
    # audit_identity
    try:
        from maer_backend.maer_identity_audit import audit_identity
        audit_identity()
        results['audit_identity'] = 'OK'
    except Exception:
        results['audit_identity'] = traceback.format_exc()
    # OCR dummy image
    try:
        from maer_backend.ocr_engine import ocr_auto
        from PIL import Image
        dummy = Image.new('RGB', (10, 10), color='white')
        ocr_auto(dummy)
        results['ocr_auto'] = 'OK'
    except Exception:
        results['ocr_auto'] = traceback.format_exc()
    # Search index dummy
    try:
        from maer_backend.maer_files import action_search_index
        action_search_index({"query": "PRUEBA", "index_file": "maer_index.json"})
        results['action_search_index'] = 'OK'
    except Exception:
        results['action_search_index'] = traceback.format_exc()
    # Analyzer dummy (use any small PDF if exists)
    try:
        from maer_backend.maer_pdf_analyzer import action_analyze_file
        sample_pdf = None
        for p in PROJECT_ROOT.rglob('*.pdf'):
            sample_pdf = p
            break
        if sample_pdf:
            action_analyze_file({"path": str(sample_pdf), "mode": "file"})
            results['action_analyze_file'] = 'OK'
        else:
            results['action_analyze_file'] = 'SKIPPED (no PDF found)'
    except Exception:
        results['action_analyze_file'] = traceback.format_exc()
    return results


def main():
    report = {
        'syntax_errors': [],
        'import_errors': [],
        'critical_functions': {},
    }
    # Scan all .py files
    py_files = list(PROJECT_ROOT.rglob('*.py'))
    logging.info(f"Scanning {len(py_files)} Python files...")
    for f in py_files:
        # Compile to catch syntax errors
        try:
            compile(f.read_text(encoding='utf-8'), str(f), 'exec')
        except Exception:
            report['syntax_errors'].append({"file": str(f), "error": traceback.format_exc()})
            continue
        # Attempt import
        mod, err = load_module(f)
        if err:
            report['import_errors'].append({"file": str(f), "error": err})
    # Run critical functions
    report['critical_functions'] = run_critical_functions()

    # Save report
    out_path = PROJECT_ROOT / 'full_audit_report.json'
    with open(out_path, 'w', encoding='utf-8') as out:
        json.dump(report, out, indent=2, ensure_ascii=False)
    logging.info(f"Full audit report saved to {out_path}")

if __name__ == '__main__':
    main()
