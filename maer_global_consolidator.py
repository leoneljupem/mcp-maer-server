# -*- coding: utf-8 -*-
import os
import json
import re
import zipfile
from pathlib import Path
from datetime import datetime
from pypdf import PdfWriter, PdfReader
from maer_backend.maer_identity_audit import audit_identity

def run_global_audit():
    print("🦁 Iniciando Consolidación Global MAER...")
    root_dir = Path("/Users/houssenm/mcp-maer-server")
    expedientes_dir = root_dir / "data" / "expedientes"
    output_dir = root_dir / "respaldo_maer" / "PORTAFOLIOS_GLOBALES"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Agrupar archivos por CURP detectada en nombre o contenido
    clients = {} # {CURP: [file_paths]}
    curp_pattern = r'([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d)'
    
    for f in expedientes_dir.rglob("*.pdf"):
        # Buscar en nombre
        m = re.search(curp_pattern, f.name)
        if m:
            curp = m.group(1)
            if curp not in clients: clients[curp] = []
            clients[curp].append(f)
            
    print(f"👥 Clientes detectados: {len(clients)}")
    
    # 2. Procesar cada cliente
    portfolio_reports = []
    
    for curp, files in clients.items():
        print(f"📂 Procesando {curp} ({len(files)} archivos)...")
        
        # Generar Portfolio
        merger = PdfWriter()
        for f in files:
            merger.append(str(f))
            
        p_name = f"PORTAFOLIO_MAER_{curp}_{datetime.now().strftime('%Y%m%d')}.pdf"
        p_path = output_dir / p_name
        with open(p_path, "wb") as f_out:
            merger.write(f_out)
            
        portfolio_reports.append({
            "curp": curp,
            "archivos_originales": [str(f) for f in files],
            "portfolio_generado": str(p_path),
            "original_mapping": {f.name: str(f.parent) for f in files}
        })
        
    # 3. Auditoría de Inconsistencias Global (usando el motor avanzado)
    print("🔍 Buscando inconsistencias en toda la base...")
    audit_results = audit_identity(str(root_dir / "maer_index.json"))
    
    # 4. Crear archivo comprimido final
    zip_path = root_dir / "respaldo_maer" / f"MAER_GLOBAL_AUDIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, 'w') as z:
        # Añadir portafolios
        for p in output_dir.glob("*.pdf"):
            z.write(p, arcname=f"portafolios/{p.name}")
        
        # Añadir reporte
        report = {
            "timestamp": datetime.now().isoformat(),
            "portafolios": portfolio_reports,
            "auditoria_identidad": audit_results
        }
        report_path = root_dir / "respaldo_maer" / "REPORTE_GLOBAL.json"
        with open(report_path, "w", encoding="utf-8") as rf:
            json.dump(report, rf, indent=2, ensure_ascii=False)
        z.write(report_path, arcname="REPORTE_GLOBAL.json")
        
    print(f"✅ Proceso completado. Archivo final: {zip_path}")
    return str(zip_path)

if __name__ == "__main__":
    path = run_global_audit()
    print(f"UBICACION_ZIP: {path}")
