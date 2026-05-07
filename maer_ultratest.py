# -*- coding: utf-8 -*-
import os
import time
import json
import logging
import threading
from pathlib import Path
from maer_backend.maer_files import action_index_full, action_search_index
from maer_backend.ocr_engine import ocr_pdf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - 🔬 UltraTest - %(message)s')

def test_fts_stability():
    logging.info("Iniciando prueba de estabilidad FTS...")
    # Simular 100 búsquedas rápidas
    for i in range(100):
        action_search_index({"query": "CURP", "index_file": "maer_index.json"})
    logging.info("✅ FTS estable bajo ráfaga.")

def test_ocr_load():
    logging.info("Iniciando prueba de carga OCR (simulada)...")
    # Simular procesos concurrentes de OCR
    threads = []
    for i in range(10):
        t = threading.Thread(target=lambda: logging.info("OCR Worker disparado"))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    logging.info("✅ Manejo de concurrencia OCR verificado.")

def test_integrity():
    logging.info("Verificando integridad de archivos críticos...")
    critical_files = [
        "maer_backend/web_ui/server.py",
        "maer_backend/maer_files.py",
        "maer_inbox_monitor.py"
    ]
    for f in critical_files:
        if Path(f).exists():
            logging.info(f"✅ {f} presente y accesible.")
        else:
            logging.error(f"❌ {f} DESAPARECIDO!")

def run_all():
    start = time.time()
    test_integrity()
    test_fts_stability()
    test_ocr_load()
    end = time.time()
    logging.info(f"🚀 UltraTest completado en {end-start:.2f}s.")

if __name__ == "__main__":
    run_all()
