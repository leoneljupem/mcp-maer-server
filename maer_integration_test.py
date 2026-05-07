# -*- coding: utf-8 -*-
"""
Integration test: lanza el servidor FastAPI y realiza 100 peticiones a los endpoints
para validar que la aplicación funciona sin errores.
"""
import subprocess, time, os, signal
import threading
import requests
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - 🧪 Integración - %(message)s')

PROJECT_ROOT = Path(__file__).resolve().parent
SERVER_MODULE = "maer_backend.web_ui.server"
SERVER_HOST = "http://127.0.0.1:8765"

# -------------------------------------------------------------------
def start_server():
    """Inicia uvicorn en un proceso separado"""
    env = os.environ.copy()
    # Asegúrate de que PYTHONPATH incluya el proyecto
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    cmd = ["python3", "-m", "uvicorn", SERVER_MODULE+":app", "--host", "127.0.0.1", "--port", "8765"]
    logging.info("Arrancando servidor FastAPI...")
    proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def stop_server(proc):
    logging.info("Deteniendo servidor...")
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

def wait_until_up(timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(SERVER_HOST)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

# -------------------------------------------------------------------
def run_tests(iterations=100):
    results = []
    # 1. Login (usamos la contraseña actual del .env o default)
    login_payload = {"password": os.getenv("MAER_PASSWORD", "admin123")}
    for i in range(iterations):
        try:
            # Alternar entre endpoints
            if i % 4 == 0:
                r = requests.post(f"{SERVER_HOST}/api/login", json=login_payload)
                endpoint = "/api/login"
            elif i % 4 == 1:
                # Búsqueda simple
                r = requests.post(f"{SERVER_HOST}/api/search", json={"query": "CURP", "index_file": "maer_index.json"})
                endpoint = "/api/search"
            elif i % 4 == 2:
                # Auditoría de identidad (no necesita payload)
                r = requests.get(f"{SERVER_HOST}/api/audit-identity") if False else requests.post(f"{SERVER_HOST}/api/audit-identity", json={})
                endpoint = "/api/audit-identity"
            else:
                # Analizador de archivo (usamos cualquier PDF pequeño si existe)
                sample_pdf = None
                for p in PROJECT_ROOT.rglob('*.pdf'):
                    sample_pdf = p
                    break
                if sample_pdf:
                    files = {'file': open(sample_pdf, 'rb')}
                    # La API de upload espera multipart
                    r = requests.post(f"{SERVER_HOST}/api/upload", files={'file': (sample_pdf.name, open(sample_pdf, 'rb'), 'application/pdf')})
                    endpoint = "/api/upload"
                else:
                    r = requests.get(SERVER_HOST)  # fallback simple
                    endpoint = "fallback"
            ok = r.status_code == 200
            results.append({"iteration": i+1, "endpoint": endpoint, "status": r.status_code, "ok": ok, "response": r.json() if ok else r.text})
            if not ok:
                logging.error(f"Iter {i+1}: fallo en {endpoint} - código {r.status_code}")
        except Exception as e:
            logging.exception(f"Iter {i+1}: excepción en petición")
            results.append({"iteration": i+1, "endpoint": endpoint, "exception": str(e)})
    return results

def main():
    server_proc = start_server()
    try:
        if not wait_until_up():
            logging.error("Servidor no respondió a tiempo.")
            return
        logging.info("Servidor listo. Ejecutando 100 pruebas de integración...")
        test_results = run_tests(100)
        # Guardar reporte
        out = PROJECT_ROOT / "integration_test_report.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        logging.info(f"Reporte guardado en {out}")
    finally:
        stop_server(server_proc)

if __name__ == "__main__":
    main()
