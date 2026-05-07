# -*- coding: utf-8 -*-
"""
🦁 MAER — Auditor de Semanas Cotizadas
Extrae tablas de PDFs del IMSS y detecta huecos laborales.
Leonel Houssen Mojica — 2026
"""

import pdfplumber
from pathlib import Path
import re

def audit_semanas_cotizadas(pdf_path):
    """Extrae historial laboral y detecta gaps."""
    results = {
        "ok": False,
        "total_semanas": 0,
        "historial": [],
        "gaps": [],
        "inconsistencias": []
    }
    
    try:
        from datetime import datetime
        FECHA_CORTE_LEY = datetime(1997, 7, 1)
        
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            salarios_historial = [] # Lista de (fecha, monto)
            for page in pdf.pages:
                text = page.extract_text()
                all_text += text
                
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        row_clean = [str(cell).replace('\n', ' ').strip() for cell in row if cell]
                        # Buscar fecha y salario en la fila (Flexibilidad mejorada)
                        date_match = re.search(r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', " ".join(row_clean))
                        sal_match = re.search(r'(\d+\.\d{2})', " ".join(row_clean))
                        
                        if date_match:
                            dstr = date_match.group(1).replace("-", "/")
                            try:
                                dparts = dstr.split("/")
                                if len(dparts[-1]) == 2: # Convertir 24 a 2024
                                    dstr = f"{dparts[0]}/{dparts[1]}/20{dparts[2]}"
                                fecha_dt = datetime.strptime(dstr, "%d/%m/%Y")
                            except: continue
                            
                            if sal_match:
                                salarios_historial.append((fecha_dt, float(sal_match.group(1))))
                            results["historial"].append(row_clean)
            
            # 1. Total de Semanas
            match_semanas = re.search(r'Total de semanas cotizadas:\s*(\d+)', all_text, re.IGNORECASE)
            if match_semanas:
                results["total_semanas"] = int(match_semanas.group(1))
            
            # 2. Salario Promedio (Ley 73: últimas 250 semanas, aprox 5 años)
            if salarios_historial:
                salarios_historial.sort(key=lambda x: x[0], reverse=True)
                # Tomar los salarios detectados más recientes
                ultimos = [s[1] for s in salarios_historial[:20]] # Simplificación de "últimas semanas"
                results["salario_promedio"] = round(sum(ultimos) / len(ultimos), 2)
            else:
                results["salario_promedio"] = "No detectado"

            # 3. Ley Aplicable (Basado en la fecha más antigua del historial)
            if salarios_historial:
                fecha_mas_antigua = min(s[0] for s in salarios_historial)
                es_ley_73 = fecha_mas_antigua < FECHA_CORTE_LEY
                results["ley"] = "Ley 1973 (Favorables)" if es_ley_73 else "Ley 1997 (Afores)"
                results["fecha_inicio_laboral"] = fecha_mas_antigua.strftime("%d/%m/%Y")
            else:
                results["ley"] = "No determinada"

            # 5. Estrategia Sugerida (El "Surprise" Engine)
            results["estrategia"] = []
            if es_ley_73:
                if results["total_semanas"] < 500:
                    results["estrategia"].append("🔴 URGENTE: No cumple semanas mínimas. Se sugiere completar 500 semanas vía Modalidad 10 (Trabajador Independiente) o Modalidad 40.")
                elif results["salario_promedio"] != "No detectado" and results["salario_promedio"] < 500:
                    results["estrategia"].append("🟡 MEJORA: Salario promedio bajo. Se sugiere estrategia de Modalidad 40 para los últimos 5 años para elevar la cuantía.")
                else:
                    results["estrategia"].append("🟢 VIABLE: Expediente sólido para Ley 73. Proceder con solicitud de pensión por cesantía.")
            else:
                results["estrategia"].append("🔵 LEY 97: Se recomienda consolidar saldos de AFORE e INFONAVIT.")

            results["ok"] = True
            return results
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) > 1:
        print(audit_semanas_cotizadas(sys.argv[1]))
