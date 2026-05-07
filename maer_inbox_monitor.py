# -*- coding: utf-8 -*-
import os
import time
import shutil
import logging
from pathlib import Path
from maer_backend.maer_files import action_analyze_file, action_detect_ids
from maer_backend.maer_identity_audit import audit_identity

# Configuración
DESKTOP = Path.home() / "Desktop"
INBOX = DESKTOP / "MAER_INBOX"
PROCESADOS = INBOX / "PROCESADOS"
ALERTAS = INBOX / "ALERTAS_CRITICAS"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - 🦁 Sentinel - %(message)s')

def setup():
    for d in [INBOX, PROCESADOS, ALERTAS]:
        d.mkdir(parents=True, exist_ok=True)
    logging.info(f"Monitor activado en: {INBOX}")

def process_file(file_path):
    logging.info(f"🔍 Detectado nuevo archivo: {file_path.name}")
    
    try:
        # 1. Análisis de Identidad
        res = action_detect_ids({"path": str(file_path), "mode": "file"})
        ids = res.get("data", {}).get("ids", {})
        
        curps = ids.get("curp_validas", [])
        name_tag = curps[0] if curps else "DESCONOCIDO"
        
        # 2. Renombrado Inteligente
        new_name = f"[{name_tag}]_{int(time.time())}_{file_path.name}"
        
        # 3. Auditoría de Conflictos Críticos
        audit = audit_identity()
        conflicts = audit.get("conflicts", [])
        
        is_critical = False
        for c in conflicts:
            if name_tag in str(c):
                is_critical = True
                break
                
        if is_critical:
            logging.warning(f"⚠️ CONFLICTO CRÍTICO detectado para {name_tag}")
            target_path = ALERTAS / f"ALERTA_{new_name}"
            os.system(f'osascript -e "display notification \"Conflicto Crítico en {file_path.name}\" with title \"🦁 MAER Sentinel\""')
        else:
            target_path = PROCESADOS / new_name

        shutil.move(str(file_path), str(target_path))
        logging.info(f"✅ Archivo procesado y movido a: {target_path.parent.name}")
    except Exception as e:
        logging.error(f"❌ Error procesando {file_path.name}: {e}")
        # Mover a una carpeta de errores para no re-intentar infinitamente
        error_dir = INBOX / "ERRORES"
        error_dir.mkdir(exist_ok=True)
        try:
            shutil.move(str(file_path), str(error_dir / file_path.name))
        except:
            pass

def start_monitor():
    setup()
    while True:
        try:
            for f in INBOX.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    process_file(f)
            time.sleep(5) # Revisar cada 5 segundos
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Error en monitor: {e}")
            time.sleep(10)

if __name__ == "__main__":
    start_monitor()
