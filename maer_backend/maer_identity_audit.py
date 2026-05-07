# -*- coding: utf-8 -*-
"""
🦁 MAER — Auditor de Identidad y Conflictos
Detecta duplicidad de NSS, CURP, Homónimos e inconsistencias.
Leonel Houssen Mojica — 2026
"""

import re
import json
from pathlib import Path

def audit_identity(index_path="/Users/houssenm/mcp-maer-server/maer_index.json"):
    """Busca conflictos de identidad en todos los documentos indexados."""
    if not Path(index_path).exists():
        return {"ok": False, "msg": "No hay índice."}
    
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    all_nss = {}
    all_curps = {}
    
    nss_pattern = r'\b\d{11}\b'
    curp_pattern = r'\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b'
    
    # Manejar si el índice es una lista (formato FTS5) o dict (legacy)
    items = index if isinstance(index, list) else index.items()
    
    for item in items:
        if isinstance(index, list):
            path = item.get("path", "")
            text = item.get("snippet", "") + " " + item.get("text", "")
        else:
            path, data = item
            text = data.get("text", "")
        # Extraer NSS
        found_nss = re.findall(nss_pattern, text)
        for n in found_nss:
            all_nss[n] = all_nss.get(n, []) + [Path(path).name]
            
        # Extraer CURP
        found_curps = re.findall(curp_pattern, text)
        for c in found_curps:
            all_curps[c] = all_curps.get(c, []) + [Path(path).name]

    conflicts = []
    if len(all_nss) > 1:
        conflicts.append({
            "tipo": "DUPLICIDAD_NSS",
            "desc": f"Se detectaron {len(all_nss)} números de seguro social diferentes en tus documentos.",
            "detalles": all_nss
        })
        
    if len(all_curps) > 1:
        conflicts.append({
            "tipo": "DUPLICIDAD_CURP",
            "desc": f"Se detectaron {len(all_curps)} CURPs diferentes. Esto bloquea cualquier trámite.",
            "detalles": all_curps
        })
            
    # ── VALIDACIÓN DE COHERENCIA BIOMÉTRICA (EL "SORPRESA" ENGINE) ──
    coherence_alerts = []
    for curp, files in all_curps.items():
        # 1. Extraer fecha de la CURP (Posiciones 5-10: YYMMDD)
        curp_date_str = curp[4:10]
        
        # 2. Validar contra NSS (Posiciones 3-4 del NSS: Año de registro)
        for nss, nfiles in all_nss.items():
            reg_year = int(nss[2:4])
            birth_year = int(curp_date_str[0:2])
            
            # Un registro en el IMSS no puede ser más de 14 años antes de nacer (usualmente)
            # Y no debería ser mayor al año actual
            if reg_year < birth_year and (birth_year - reg_year) > 1:
                 coherence_alerts.append({
                    "tipo": "INCONSISTENCIA_NSS_FECHA",
                    "desc": f"El NSS {nss} indica un año de registro ({reg_year}) anterior al nacimiento en CURP ({birth_year}). Posible duplicidad de identidad.",
                    "archivos": list(set(files + nfiles))
                 })

        # 3. Validar RFC (si existe en el índice)
        rfc_pattern = r'\b[A-Z]{4}\d{6}[A-Z0-9]{3}\b'
        for item in items:
            if isinstance(index, list):
                path = item.get("path", "")
                text = item.get("snippet", "") + " " + item.get("text", "")
            else:
                path, data = item
                text = data.get("text", "")
            
            rfcs = re.findall(rfc_pattern, text)
            for r in rfcs:
                if r[:10] != curp[:10]:
                    coherence_alerts.append({
                        "tipo": "CONFLICTO_RFC_CURP",
                        "desc": f"El RFC {r} no coincide con la CURP {curp}. Esto causará rechazo automático en AFORE.",
                        "archivos": [Path(path).name]
                    })

    conflicts.extend(coherence_alerts)
    
    return {
        "ok": True,
        "conflicts": conflicts,
        "resumen": f"Auditoría Forense completada. {len(conflicts)} conflictos detectados.",
        "biometric_check": "PASS" if not coherence_alerts else "FAIL"
    }
