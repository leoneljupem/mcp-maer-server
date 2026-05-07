# -*- coding: utf-8 -*-
"""
Stress test script: 10,000 random operations on MAER.
It runs without external I/O, using internal functions.
"""
import logging
import random
import time
from pathlib import Path

# Import core functions (they are part of the package)
from maer_backend.maer_files import action_index_full, action_search_index
from maer_backend.maer_identity_audit import audit_identity
from maer_backend.ocr_engine import ocr_auto
from maer_backend.maer_pdf_analyzer import action_analyze_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - 📊 StressTest - %(message)s')

# Sample data for OCR (we need a dummy image). We'll create a small white PNG in memory.
from PIL import Image

def create_dummy_image():
    img = Image.new('RGB', (100, 100), color='white')
    return img

DUMMY_IMAGE = create_dummy_image()

def run_one_iteration(i: int):
    try:
        test_type = random.choice(['fts', 'ocr', 'audit', 'analyze'])
        if test_type == 'fts':
            # Simulate a search query (random letters)
            query = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5))
            action_search_index({"query": query, "index_file": "maer_index.json"})
            logging.info(f"Iter {i}: Búsqueda FTS '{query}' ok")
        elif test_type == 'ocr':
            # Run OCR on dummy image
            ocr_auto(DUMMY_IMAGE)
            logging.info(f"Iter {i}: OCR dummy image ok")
        elif test_type == 'audit':
            # Run identity audit (fast, no args needed)
            audit_identity()
            logging.info(f"Iter {i}: Auditoría de identidad ok")
        elif test_type == 'analyze':
            # Analyze a dummy PDF path (we use a placeholder existing file if any)
            # Find any small pdf in the repo for test, fallback to first PDF found.
            sample_pdf = None
            for p in Path('.').rglob('*.pdf'):
                sample_pdf = p
                break
            if sample_pdf:
                action_analyze_file({"path": str(sample_pdf), "mode": "file"})
                logging.info(f"Iter {i}: Análisis PDF {sample_pdf.name} ok")
            else:
                logging.warning(f"Iter {i}: No PDF found for analysis; skipped")
    except Exception as e:
        logging.error(f"Iter {i}: Error en {test_type}: {e}")

def run_stress_test(total_iters: int = 10000):
    logging.info(f"🚀 Iniciando Stress Test con {total_iters} iteraciones")
    start = time.time()
    for i in range(1, total_iters + 1):
        run_one_iteration(i)
        # Light pause every 1000 iterations to avoid CPU lock-up
        if i % 1000 == 0:
            time.sleep(0.1)
    end = time.time()
    logging.info(f"✅ Stress Test completado en {end - start:.2f}s ({total_iters} iteraciones)")

if __name__ == "__main__":
    run_stress_test()
