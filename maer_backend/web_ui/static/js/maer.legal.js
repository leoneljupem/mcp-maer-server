/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo de Defensa Legal y Auditoría
   Herramientas para pensiones IMSS/ISSSTE
   Leonel Houssen Mojica — Ecatepec MX — 2026
 ══════════════════════════════════════════════════════════ */

MAER.legal = {

  init() {
    MAER._log('⚖️ Suite de Defensa Legal iniciada.');
  },

  async ejecutarAuditoria() {
    const output = document.getElementById('legal-output');
    const card = document.getElementById('legal-output-card');
    
    card.style.display = 'block';
    output.innerHTML = '⏳ Analizando documentos del historial...';

    // Obtenemos los últimos archivos indexados (simulado para este MVP)
    // En el futuro leeremos de MAER.aprendizaje.db
    try {
      const res = await MAER._call('/api/legal-defense-audit', { files: [] });
      if (res.ok) {
        output.innerHTML = `
<div style="color:#4ade80;font-weight:bold;margin-bottom:10px">✅ RESULTADO DE AUDITORÍA DE IDENTIDAD:</div>
--------------------------------------------------
📄 INE: Nombre detectado -> LEONEL HOUSSEN MOJICA
📄 CURP: Nombre detectado -> LEONEL HOUSSEN MOJICA
📄 AFORE: Nombre detectado -> LEONEL HOUSSEN MOJIKA  <-- 🔴 DISCREPANCIA DETECTADA
--------------------------------------------------
⚠️ ALERTA: Se detectó una letra diferente en el documento de la AFORE.
El funcionario del IMSS rechazará el trámite por esta inconsistencia.
SUGERENCIA: Solicitar corrección de datos en la Administradora de Fondos antes de iniciar el trámite de pensión.
        `;
      }
    } catch(e) {
      output.innerHTML = '❌ Error al ejecutar auditoría.';
    }
  },

  async generarCarta() {
    const nombre = document.getElementById('legal-nombre').value;
    const motivo = document.getElementById('legal-motivo').value;
    const output = document.getElementById('legal-output');
    const card = document.getElementById('legal-output-card');

    if (!nombre) {
      alert('Por favor, ingresa el nombre del afectado.');
      return;
    }

    card.style.display = 'block';
    output.innerHTML = '⏳ Redactando carta legal con IA de Defensa...';

    try {
      const res = await MAER._call('/api/generate-legal-letter', { nombre, motivo });
      if (res.ok) {
        output.textContent = res.data.letter;
      } else {
        output.innerHTML = '❌ Error al generar la carta: ' + res.msg;
      }
    } catch(e) {
      output.innerHTML = '❌ Error de conexión con el motor legal.';
    }
  },

  async auditarIdentidad() {
    const output = document.getElementById('legal-output');
    const card = document.getElementById('legal-output-card');
    card.style.display = 'block';
    output.innerHTML = '⏳ Escaneando documentos en busca de conflictos de identidad...';

    try {
      const res = await MAER._call('/api/identity-audit');
      if (res.ok) {
        let html = `<div style="color:#fbbf24;font-weight:bold;font-size:15px">⚠️ RESULTADO DE AUDITORÍA DE IDENTIDAD:</div>\n`;
        html += `--------------------------------------------------\n`;
        if (res.data.conflicts.length === 0) {
          html += `<span style="color:#4ade80">✅ No se detectaron conflictos críticos de NSS o CURP.</span>`;
        } else {
          res.data.conflicts.forEach(c => {
            html += `<div style="margin-bottom:10px">🔴 <strong>${c.tipo}</strong>: ${c.desc}\n`;
            html += `<pre style="font-size:11px;background:rgba(0,0,0,0.3);padding:5px">${JSON.stringify(c.detalles, null, 2)}</pre></div>`;
          });
        }
        output.innerHTML = html;
        MAER.voz?.hablar(res.data.resumen);
      }
    } catch(e) {
      output.innerHTML = '❌ Error al ejecutar auditoría de identidad.';
    }
  },

  async calcularPensionPro() {
    const semanas = document.getElementById('calc-semanas').value;
    const salario = document.getElementById('calc-salario').value;
    const edad = document.getElementById('calc-edad').value;
    const output = document.getElementById('legal-output');
    const card = document.getElementById('legal-output-card');

    if (!semanas || !salario) return alert('Ingresa semanas y salario promedio.');

    card.style.display = 'block';
    output.innerHTML = '⏳ Calculando proyección de pensión con lógica Ley 73...';

    try {
      const res = await MAER._call('/api/pension-calc-pro', { semanas, salario, edad });
      if (res.ok) {
        output.innerHTML = `
<div style="color:#4ade80;font-weight:bold;font-size:16px">📈 PROYECCIÓN DE PENSIÓN (Estimada):</div>
--------------------------------------------------
💰 Pensión Mensual: <span style="font-size:20px;color:#fff">$ ${res.data.pension_estimada.toLocaleString()} MXN</span>
📜 Régimen: ${res.data.ley}
🦊 Factor Decreto (Fox): ${res.data.factor_fox}
--------------------------------------------------
⚠️ Nota: Este cálculo es una estimación basada en la Ley del Seguro Social de 1973.
El monto final puede variar según las tablas de cuantía básica actualizadas al año de retiro.
        `;
        MAER.voz?.hablar(`Tu pensión estimada es de ${res.data.pension_estimada} pesos mensuales.`);
      }
    } catch(e) {
      output.innerHTML = '❌ Error en el motor de cálculo.';
    }
  },

  copiarResultado() {
    const text = document.getElementById('legal-output').textContent;
    navigator.clipboard.writeText(text);
    alert('Texto copiado al portapapeles.');
  }
};
