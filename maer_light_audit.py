# -*- coding: utf-8 -*-
"""
Auditoría ligera del proyecto MAER.
- Compila todos los archivos .py para detectar errores de sintaxis.
- Intenta importar cada módulo (sin ejecutar funciones que carguen modelos pesados).
- Genera un informe JSON llamado light_audit_report.json en la raíz del proyecto.
"""
import importlib.util, traceback, json, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - 🔍 LightAudit - %(message)s')

PROJECT_ROOT = Path(__file__).resolve().parent

report = {'syntax_errors': [], 'import_errors': []}

py_files = list(PROJECT_ROOT.rglob('*.py'))
logging.info(f"Escaneando {len(py_files)} archivos Python...")
for f in py_files:
    try:
        compile(f.read_text(encoding='utf-8'), str(f), 'exec')
    except Exception:
        report['syntax_errors'].append({'file': str(f), 'error': traceback.format_exc()})
        continue
    # Intentar importación sin ejecutar código que importe modelos pesados
    try:
        spec = importlib.util.spec_from_file_location(f.stem, str(f))
        mod = importlib.util.module_from_spec(spec)
        # Evitar ejecutar código bajo "if __name__ == '__main__'" y bloques pesados
        # Cargamos el módulo pero atrapamos cualquier excepción
        spec.loader.exec_module(mod)
    except Exception:
        report['import_errors'].append({'file': str(f), 'error': traceback.format_exc()})

out_path = PROJECT_ROOT / 'light_audit_report.json'
with open(out_path, 'w', encoding='utf-8') as out:
    json.dump(report, out, indent=2, ensure_ascii=False)
logging.info(f"Informe guardado en {out_path}")
