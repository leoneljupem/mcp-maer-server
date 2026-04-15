// 🦁 MAER Dashboard — Frontend Application
// Leonel Mojica — Ecatepec MX — 2026

const API = '';  // Same origin

// ═══════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════

async function apiCall(endpoint, payload = {}) {
    try {
        const res = await fetch(`${API}/api/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return await res.json();
    } catch (e) {
        return { ok: false, code: 'NETWORK_ERROR', message: e.message, data: {} };
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function setLoading(btn, loading) {
    if (loading) {
        btn.dataset.originalText = btn.textContent;
        btn.innerHTML = '<span class="spinner"></span> Procesando...';
        btn.classList.add('loading');
    } else {
        btn.textContent = btn.dataset.originalText || 'Ejecutar';
        btn.classList.remove('loading');
    }
}

// ═══════════════════════════════════════════════
// Navigation
// ═══════════════════════════════════════════════

const panelTitles = {
    upload: { title: 'Subir Archivo', subtitle: 'Sube documentos, PDFs o imágenes para análisis' },
    ocr: { title: 'OCR Multimodal', subtitle: 'Extrae texto con Tesseract, EasyOCR o PaddleOCR' },
    ids: { title: 'CURP / RFC / INE', subtitle: 'Detecta y valida identificadores oficiales mexicanos' },
    tables: { title: 'Tablas PDF', subtitle: 'Extrae tablas y formularios de documentos PDF' },
    nlp: { title: 'NLP Entidades', subtitle: 'Clasifica personas, organizaciones, fechas y ubicaciones' },
    duplicates: { title: 'Imágenes Duplicadas', subtitle: 'Encuentra imágenes similares usando hash perceptual' },
    faces: { title: 'Reconocimiento Facial', subtitle: 'Detecta y agrupa rostros en imágenes' },
    cluster: { title: 'Clustering', subtitle: 'Agrupa archivos por similitud visual' },
    indexing: { title: 'Indexar Carpeta', subtitle: 'Crea un índice completo con metadatos y snippets' },
    search: { title: 'Buscar en Índice', subtitle: 'Busca en el índice generado por MAER' },
    llm: { title: '🧠 LLM Local Offline', subtitle: 'Chatea, resume o extrae datos de tus documentos usando Llama.cpp' },
    settings: { title: '⚙️ Ajustes Avanzados', subtitle: 'Configura motores, temperaturas y límites globales del sistema' },
};

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const panel = btn.dataset.panel;
        if (!panel) return;

        // Update nav
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Show panel
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        const targetPanel = document.getElementById(`panel-${panel}`);
        if (targetPanel) targetPanel.classList.add('active');

        // Update header
        const info = panelTitles[panel] || { title: panel, subtitle: '' };
        document.getElementById('panel-title').textContent = info.title;
        document.getElementById('panel-subtitle').textContent = info.subtitle;
    });
});

// ═══════════════════════════════════════════════
// Upload
// ═══════════════════════════════════════════════

const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');

document.getElementById('btn-select-file').addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', () => {
    handleFiles(fileInput.files);
});

async function handleFiles(files) {
    const container = document.getElementById('upload-results');

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch(`${API}/api/upload`, {
                method: 'POST',
                body: formData,
            });
            const result = await res.json();

            if (result.ok) {
                showToast(`✅ ${file.name} subido correctamente`, 'success');
                const data = result.data || {};
                container.innerHTML = `
                    <div class="result-card">
                        <div class="result-header">
                            <span class="result-title">📄 ${escapeHtml(file.name)}</span>
                            <span class="result-badge ok">SUBIDO</span>
                        </div>
                        <div class="result-meta">
                            <span>📁 ${escapeHtml(data.path || '')}</span>
                            <span>📏 ${formatBytes(data.size || file.size)}</span>
                        </div>
                    </div>
                ` + container.innerHTML;

                // Auto-fill paths in other panels
                const filePath = data.path || '';
                document.getElementById('ocr-path').value = filePath;
                document.getElementById('ids-path').value = filePath;
                if (file.name.endsWith('.pdf')) {
                    document.getElementById('tables-path').value = filePath;
                }
                document.getElementById('nlp-path').value = filePath;
                document.getElementById('llm-path').value = filePath;
            } else {
                showToast(`❌ Error subiendo ${file.name}`, 'error');
            }
        } catch (e) {
            showToast(`❌ Error de red: ${e.message}`, 'error');
        }
    }
}

// ═══════════════════════════════════════════════
// OCR
// ═══════════════════════════════════════════════

document.getElementById('btn-ocr').addEventListener('click', async () => {
    const btn = document.getElementById('btn-ocr');
    const path = document.getElementById('ocr-path').value.trim();
    const engine = document.getElementById('ocr-engine').value;

    if (!path) return showToast('Ingresa la ruta del archivo', 'error');

    setLoading(btn, true);
    const result = await apiCall('ocr', { path, engine });
    setLoading(btn, false);

    const container = document.getElementById('ocr-results');
    const data = result.data || {};

    if (result.ok) {
        showToast('OCR completado', 'success');
        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">${escapeHtml(data.engine || 'N/A')}</div><div class="stat-label">Motor usado</div></div>
                <div class="stat-card"><div class="stat-value">${data.pages_processed || 0}</div><div class="stat-label">Páginas</div></div>
                <div class="stat-card"><div class="stat-value">${data.cached ? '✅' : '❌'}</div><div class="stat-label">Cache</div></div>
            </div>
            <div class="result-card">
                <div class="result-header">
                    <span class="result-title">Texto extraído</span>
                    <span class="result-badge ok">${(data.text || '').length} chars</span>
                </div>
                <div class="result-text">${escapeHtml(data.text || 'Sin texto')}</div>
            </div>
        `;
    } else {
        container.innerHTML = `<div class="result-card"><div class="result-header"><span class="result-title">Error</span><span class="result-badge error">ERROR</span></div><div class="result-text">${escapeHtml(result.message)}</div></div>`;
    }
});

// ═══════════════════════════════════════════════
// IDs Detection
// ═══════════════════════════════════════════════

document.getElementById('btn-detect-ids').addEventListener('click', async () => {
    const btn = document.getElementById('btn-detect-ids');
    const path = document.getElementById('ids-path').value.trim();
    if (!path) return showToast('Ingresa la ruta del archivo', 'error');

    setLoading(btn, true);
    const result = await apiCall('detect-ids', { mode: 'file', path });
    setLoading(btn, false);

    const container = document.getElementById('ids-results');
    const data = result.data || {};
    const ids = data.ids || {};
    const related = data.related || {};

    if (result.ok) {
        showToast('IDs detectados', 'success');
        let html = '<div class="stats-grid">';
        html += `<div class="stat-card"><div class="stat-value">${(ids.curp_validas || []).length}</div><div class="stat-label">CURP válidas</div></div>`;
        html += `<div class="stat-card"><div class="stat-value">${(ids.curp_invalidas || []).length}</div><div class="stat-label">CURP inválidas</div></div>`;
        html += `<div class="stat-card"><div class="stat-value">${(ids.rfc_validos || []).length}</div><div class="stat-label">RFC válidos</div></div>`;
        html += `<div class="stat-card"><div class="stat-value">${(ids.ine_clave || []).length}</div><div class="stat-label">INE</div></div>`;
        html += '</div>';

        html += '<div class="result-card"><div class="result-header"><span class="result-title">Identificadores encontrados</span></div><div class="tags">';
        (ids.curp_validas || []).forEach(c => html += `<span class="tag tag-curp">✅ ${c}</span>`);
        (ids.curp_invalidas || []).forEach(c => html += `<span class="tag tag-curp" style="opacity:0.5">❌ ${c}</span>`);
        (ids.rfc_validos || []).forEach(r => html += `<span class="tag tag-rfc">📋 ${r}</span>`);
        (ids.ine_clave || []).forEach(i => html += `<span class="tag tag-ine">🪪 ${i}</span>`);
        html += '</div></div>';

        html += '<div class="result-card"><div class="result-header"><span class="result-title">Datos asociados</span></div><div class="tags">';
        (related.emails || []).forEach(e => html += `<span class="tag tag-email">📧 ${escapeHtml(e)}</span>`);
        (related.phones || []).forEach(p => html += `<span class="tag tag-phone">📞 ${escapeHtml(p)}</span>`);
        (related.nss_candidates || []).forEach(n => html += `<span class="tag tag-nss">🏥 ${n}</span>`);
        html += '</div></div>';

        container.innerHTML = html;
    } else {
        container.innerHTML = `<div class="result-card"><div class="result-badge error">ERROR</div><p>${escapeHtml(result.message)}</p></div>`;
    }
});

document.getElementById('btn-validate-curp').addEventListener('click', async () => {
    const curp = document.getElementById('curp-input').value.trim();
    if (!curp) return showToast('Ingresa una CURP', 'error');
    const result = await apiCall('curp-check', { curp });
    const container = document.getElementById('ids-results');
    const data = result.data || {};
    container.innerHTML = `
        <div class="result-card">
            <div class="result-header">
                <span class="result-title">Validación CURP: ${escapeHtml(curp.toUpperCase())}</span>
                <span class="result-badge ${result.ok ? 'ok' : 'error'}">${data.status || (result.ok ? 'VÁLIDA' : 'INVÁLIDA')}</span>
            </div>
            <div class="result-text">${escapeHtml(JSON.stringify(result, null, 2))}</div>
        </div>
    ` + container.innerHTML;
});

// ═══════════════════════════════════════════════
// Tables
// ═══════════════════════════════════════════════

document.getElementById('btn-extract-tables').addEventListener('click', async () => {
    const btn = document.getElementById('btn-extract-tables');
    const path = document.getElementById('tables-path').value.trim();
    if (!path) return showToast('Ingresa la ruta del PDF', 'error');

    setLoading(btn, true);
    const result = await apiCall('tables', { path });
    setLoading(btn, false);

    const container = document.getElementById('tables-results');
    const data = result.data || {};

    if (result.ok) {
        const tables = data.tables || [];
        showToast(`${tables.length} tablas encontradas`, 'success');

        let html = `<div class="stats-grid">
            <div class="stat-card"><div class="stat-value">${tables.length}</div><div class="stat-label">Tablas</div></div>
        </div>`;

        tables.forEach((t, idx) => {
            html += `<div class="result-card">
                <div class="result-header">
                    <span class="result-title">Tabla ${idx + 1} — Página ${t.page}</span>
                    <span class="result-badge ok">${t.row_count} filas × ${t.col_count} cols</span>
                </div>
                <table class="data-table"><thead><tr>`;
            (t.headers || []).forEach(h => html += `<th>${escapeHtml(h)}</th>`);
            html += '</tr></thead><tbody>';
            (t.rows || []).slice(0, 20).forEach(row => {
                html += '<tr>';
                row.forEach(cell => html += `<td>${escapeHtml(cell)}</td>`);
                html += '</tr>';
            });
            html += '</tbody></table></div>';
        });

        container.innerHTML = html;
    } else {
        container.innerHTML = `<div class="result-card"><span class="result-badge error">ERROR</span><p>${escapeHtml(result.message)}</p></div>`;
    }
});

// ═══════════════════════════════════════════════
// NLP
// ═══════════════════════════════════════════════

document.getElementById('btn-nlp').addEventListener('click', async () => {
    const btn = document.getElementById('btn-nlp');
    const path = document.getElementById('nlp-path').value.trim();
    const text = document.getElementById('nlp-text').value.trim();

    if (!path && !text) return showToast('Ingresa ruta o texto', 'error');

    setLoading(btn, true);
    const result = await apiCall('nlp', { path: path || undefined, text: text || undefined });
    setLoading(btn, false);

    const container = document.getElementById('nlp-results');
    const data = result.data || {};
    const entities = (data.entities || {}).entities || {};
    const classification = data.classification || {};

    if (result.ok) {
        showToast('Entidades extraídas', 'success');
        let html = `<div class="stats-grid">
            <div class="stat-card"><div class="stat-value">${classification.type || '?'}</div><div class="stat-label">Tipo documento</div></div>
            <div class="stat-card"><div class="stat-value">${Math.round((classification.confidence || 0) * 100)}%</div><div class="stat-label">Confianza</div></div>
        </div>`;

        html += '<div class="result-card"><div class="result-header"><span class="result-title">Entidades detectadas</span></div><div class="tags">';
        (entities.personas || []).forEach(e => html += `<span class="tag tag-person">👤 ${escapeHtml(e.text)}</span>`);
        (entities.organizaciones || []).forEach(e => html += `<span class="tag tag-org">🏢 ${escapeHtml(e.text)}</span>`);
        (entities.ubicaciones || []).forEach(e => html += `<span class="tag tag-loc">📍 ${escapeHtml(e.text)}</span>`);
        (entities.fechas || []).forEach(e => html += `<span class="tag tag-date">📅 ${escapeHtml(e.text)}</span>`);
        (entities.cantidades || []).forEach(e => html += `<span class="tag tag-nss">💰 ${escapeHtml(e.text)}</span>`);
        html += '</div></div>';

        container.innerHTML = html;
    } else {
        container.innerHTML = `<div class="result-card"><span class="result-badge error">ERROR</span><p>${escapeHtml(result.message)}</p></div>`;
    }
});

// ═══════════════════════════════════════════════
// LLM Local
// ═══════════════════════════════════════════════

const llmModeSelect = document.getElementById('llm-mode');
const llmSchemaGroup = document.getElementById('llm-schema-group');

if (llmModeSelect) {
    llmModeSelect.addEventListener('change', () => {
        if (llmModeSelect.value === 'extract') {
            llmSchemaGroup.style.display = 'block';
        } else {
            llmSchemaGroup.style.display = 'none';
        }
    });
}

const btnLlm = document.getElementById('btn-llm');
if (btnLlm) {
    btnLlm.addEventListener('click', async () => {
        const path = document.getElementById('llm-path').value.trim();
        const text = document.getElementById('llm-text').value.trim();
        const mode = document.getElementById('llm-mode').value;
        const schema = document.getElementById('llm-schema').value.trim() || 'Extrae entidades principales en JSON';

        if (!path && !text && mode !== 'renapo') return showToast('Ingresa ruta o texto', 'error');
        if (mode === 'renapo' && !path) return showToast('Modo Renapo requiere una ruta a un PDF/Imagen', 'error');

        let endpoint = 'llm-summarize';
        let payload = { path: path || undefined, text: text || undefined };

        if (mode === 'extract') {
            endpoint = 'llm-extract';
            payload.schema_description = text ? `${text}\nEsquema: ${schema}` : schema;
        } else if (mode === 'renapo') {
            endpoint = 'renapo-verify';
            payload = { path };
        } else if (mode === 'chat') {
            endpoint = 'llm-chat';
            // En chat, permitimos texto libre (con o sin archivo adjunto)
            payload = { prompt: text, path: path || undefined };
        }

        setLoading(btnLlm, true);
        const result = await apiCall(endpoint, payload);
        setLoading(btnLlm, false);

        const container = document.getElementById('llm-results');
        const data = result.data || {};

        if (result.ok) {
            showToast('Proceso AI completado', 'success');
            let html = '';
            
            if (mode === 'summarize') {
                html += `<div class="result-card">
                    <div class="result-header">
                        <span class="result-title">Resumen Generado</span>
                        <span class="result-badge ok">AI</span>
                    </div>
                    <div class="result-text" style="white-space: pre-wrap;">${escapeHtml(data.text || '')}</div>
                </div>`;
            } else if (mode === 'extract') {
                html += `<div class="result-card">
                    <div class="result-header">
                        <span class="result-title">JSON Extraído</span>
                        <span class="result-badge ok">AI</span>
                    </div>
                    <div class="result-text"><pre>${escapeHtml(JSON.stringify(data.json || data.raw_text, null, 2))}</pre></div>
                </div>`;
            } else if (mode === 'renapo') {
                 html += `<div class="result-card">
                    <div class="result-header">
                        <span class="result-title">Validación Renapo Cruzada (CURP: ${escapeHtml(data.curp_analizada || '')})</span>
                        <span class="result-badge ${data.renapo_status === 'VIGENTE' ? 'ok' : 'error'}">${data.renapo_status}</span>
                    </div>
                    <div class="result-meta">
                        <span>Lógica AI sobre correspondencia de identidad del documento:</span>
                    </div>
                    <div class="result-text"><pre>${escapeHtml(JSON.stringify(data.llm_analysis || {}, null, 2))}</pre></div>
                </div>`;
            } else if (mode === 'chat') {
                html += `<div class="result-card">
                    <div class="result-header">
                        <span class="result-title">Respuesta Libre de la IA</span>
                        <span class="result-badge ok">AI Chat</span>
                    </div>
                    <div class="result-text" style="white-space: pre-wrap;">${escapeHtml(data.response || data.text || '')}</div>
                </div>`;
            }

            container.innerHTML = html;
        } else {
            container.innerHTML = `<div class="result-card"><span class="result-badge error">ERROR</span><p>${escapeHtml(result.message)}</p></div>`;
        }
    });
}

// ═══════════════════════════════════════════════
// Duplicates
// ═══════════════════════════════════════════════

const dupesSlider = document.getElementById('dupes-threshold');
dupesSlider.addEventListener('input', () => {
    document.getElementById('dupes-threshold-val').textContent = dupesSlider.value;
});

document.getElementById('btn-dupes').addEventListener('click', async () => {
    const btn = document.getElementById('btn-dupes');
    const dir = document.getElementById('dupes-dir').value.trim();
    const threshold = parseInt(dupesSlider.value);
    if (!dir) return showToast('Ingresa la carpeta', 'error');

    setLoading(btn, true);
    const result = await apiCall('duplicates', { base_dir: dir, threshold });
    setLoading(btn, false);

    const container = document.getElementById('dupes-results');
    const data = result.data || {};

    if (result.ok) {
        const groups = data.duplicates || [];
        showToast(`${groups.length} grupos de duplicados`, 'success');

        let html = `<div class="stats-grid">
            <div class="stat-card"><div class="stat-value">${data.total_images || 0}</div><div class="stat-label">Imágenes</div></div>
            <div class="stat-card"><div class="stat-value">${groups.length}</div><div class="stat-label">Grupos duplicados</div></div>
        </div>`;

        groups.forEach((g, idx) => {
            html += `<div class="result-card">
                <div class="result-header">
                    <span class="result-title">Grupo ${idx + 1} — ${g.count} imágenes</span>
                    <span class="result-badge ok">dist ≤ ${g.max_distance}</span>
                </div>
                <div class="result-text">${(g.group || []).map(p => escapeHtml(p)).join('\n')}</div>
            </div>`;
        });

        container.innerHTML = html || '<div class="result-card"><p>No se encontraron duplicados</p></div>';
    } else {
        container.innerHTML = `<div class="result-card"><span class="result-badge error">ERROR</span><p>${escapeHtml(result.message)}</p></div>`;
    }
});

// ═══════════════════════════════════════════════
// Faces
// ═══════════════════════════════════════════════

document.getElementById('btn-faces').addEventListener('click', async () => {
    const btn = document.getElementById('btn-faces');
    const dir = document.getElementById('faces-dir').value.trim();
    if (!dir) return showToast('Ingresa la carpeta', 'error');

    setLoading(btn, true);
    const result = await apiCall('faces', { base_dir: dir });
    setLoading(btn, false);

    const container = document.getElementById('faces-results');
    const data = result.data || {};

    if (result.ok) {
        showToast(`${data.total_faces || 0} rostros detectados`, 'success');
        let html = `<div class="stats-grid">
            <div class="stat-card"><div class="stat-value">${data.total_faces || 0}</div><div class="stat-label">Rostros</div></div>
            <div class="stat-card"><div class="stat-value">${data.total_groups || 0}</div><div class="stat-label">Grupos</div></div>
        </div>`;

        (data.groups || []).forEach((g, idx) => {
            html += `<div class="result-card">
                <div class="result-header">
                    <span class="result-title">Grupo ${idx + 1} — ${g.count} rostros</span>
                </div>
                <div class="result-text">${(g.faces || []).map(f => escapeHtml(f.path)).join('\n')}</div>
            </div>`;
        });

        container.innerHTML = html;
    } else {
        container.innerHTML = `<div class="result-card"><span class="result-badge error">ERROR</span><p>${escapeHtml(result.message)}</p></div>`;
    }
});

// ═══════════════════════════════════════════════
// Cluster
// ═══════════════════════════════════════════════

document.getElementById('btn-cluster').addEventListener('click', async () => {
    const btn = document.getElementById('btn-cluster');
    const dir = document.getElementById('cluster-dir').value.trim();
    if (!dir) return showToast('Ingresa la carpeta', 'error');

    setLoading(btn, true);
    const result = await apiCall('cluster', { base_dir: dir, type: 'images' });
    setLoading(btn, false);

    const container = document.getElementById('cluster-results');
    const data = result.data || {};

    if (result.ok) {
        const clusters = data.clusters || [];
        showToast(`${clusters.length} clusters`, 'success');

        let html = `<div class="stats-grid">
            <div class="stat-card"><div class="stat-value">${data.total_images || 0}</div><div class="stat-label">Imágenes</div></div>
            <div class="stat-card"><div class="stat-value">${clusters.length}</div><div class="stat-label">Clusters</div></div>
            <div class="stat-card"><div class="stat-value">${data.noise_images || 0}</div><div class="stat-label">Sin grupo</div></div>
        </div>`;

        clusters.forEach((c, idx) => {
            html += `<div class="result-card">
                <div class="result-header">
                    <span class="result-title">Cluster ${c.cluster_id} — ${c.count} imágenes</span>
                </div>
                <div class="result-text">${(c.images || []).map(p => escapeHtml(p)).join('\n')}</div>
            </div>`;
        });

        container.innerHTML = html || '<div class="result-card"><p>No se encontraron clusters</p></div>';
    } else {
        container.innerHTML = `<div class="result-card"><span class="result-badge error">ERROR</span><p>${escapeHtml(result.message)}</p></div>`;
    }
});

// ═══════════════════════════════════════════════
// Index
// ═══════════════════════════════════════════════

document.getElementById('btn-index').addEventListener('click', async () => {
    const btn = document.getElementById('btn-index');
    const dir = document.getElementById('index-dir').value.trim();
    const maxFiles = parseInt(document.getElementById('index-max').value) || 500;
    if (!dir) return showToast('Ingresa la carpeta a indexar', 'error');

    setLoading(btn, true);
    const result = await apiCall('index', { base_dir: dir, max_files: maxFiles });
    setLoading(btn, false);

    const container = document.getElementById('index-results');
    const data = result.data || {};

    if (result.ok) {
        showToast(`${data.processed || 0} archivos indexados`, 'success');
        
        // Auto-fill en Búsqueda para UX
        const searchDirInput = document.getElementById('search-dir');
        if (searchDirInput && data.base_dir) {
            searchDirInput.value = data.base_dir;
        }
        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">${data.processed || 0}</div><div class="stat-label">Archivos</div></div>
                <div class="stat-card"><div class="stat-value">${data.errors || 0}</div><div class="stat-label">Errores</div></div>
            </div>
            <div class="result-card">
                <div class="result-header"><span class="result-title">Índice creado</span><span class="result-badge ok">OK</span></div>
                <div class="result-meta">
                    <span>📁 ${escapeHtml(data.base_dir || '')}</span>
                    <span>📄 ${escapeHtml(data.out_file || '')}</span>
                </div>
            </div>`;
    } else {
        container.innerHTML = `<div class="result-card"><span class="result-badge error">ERROR</span><p>${escapeHtml(result.message)}</p></div>`;
    }
});

// ═══════════════════════════════════════════════
// Search
// ═══════════════════════════════════════════════

document.getElementById('btn-search').addEventListener('click', async () => {
    const btn = document.getElementById('btn-search');
    const query = document.getElementById('search-query').value.trim();
    const dir = document.getElementById('search-dir').value.trim();
    if (!query) return showToast('Ingresa un término de búsqueda', 'error');

    setLoading(btn, true);
    const result = await apiCall('search-index', { query, base_dir: dir || undefined });
    setLoading(btn, false);

    const container = document.getElementById('search-results');
    const data = result.data || {};
    const results = data.results || [];

    if (result.ok) {
        showToast(`${results.length} resultados`, 'success');
        let html = '';
        results.forEach(r => {
            const rawPath = r.path || '';
            const isImg = rawPath.toLowerCase().match(/\.(jpg|jpeg|png|webp|bmp)$/);
            
            html += `<div class="result-card interactive-card" data-filepath="${escapeHtml(rawPath)}" title="Doble clic para abrir en tu computadora">
                <div class="result-header">
                    <span class="result-title">${escapeHtml(rawPath)}</span>
                    <span class="result-badge ok">${escapeHtml(r.ext || '')}</span>
                </div>
                <div class="result-meta">
                    <span>📏 ${formatBytes(r.size_bytes || 0)}</span>
                </div>
                <div class="result-text">${escapeHtml(r.snippet_preview || '')}</div>
                <div class="quick-actions" style="margin-top: 0.5rem; display: flex; gap: 0.5rem;">
                    <button class="btn btn-secondary btn-sm action-route" data-target="ocr" data-path="${escapeHtml(rawPath)}">🔍 OCR</button>
                    ${isImg ? `<button class="btn btn-secondary btn-sm action-route" data-target="faces" data-path="${escapeHtml(rawPath.substring(0, rawPath.lastIndexOf('/')))}">👤 Buscar Rostros en Carpeta</button>` : ''}
                    <button class="btn btn-secondary btn-sm action-route" data-target="llm" data-path="${escapeHtml(rawPath)}">🧠 Analizar IA</button>
                    <button class="btn btn-primary btn-sm action-open" data-path="${escapeHtml(rawPath)}">📂 Abrir Archivo</button>
                </div>
            </div>`;
        });
        container.innerHTML = html || '<div class="result-card"><p>Sin resultados</p></div>';
    } else {
        container.innerHTML = `<div class="result-card"><span class="result-badge error">ERROR</span><p>${escapeHtml(result.message)}</p></div>`;
    }
});

// Search on Enter
document.getElementById('search-query').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('btn-search').click();
});

// Event Delegation for Search Results (Double click and Action Buttons)
document.getElementById('search-results').addEventListener('dblclick', async (e) => {
    const card = e.target.closest('.interactive-card');
    if (card) {
        const path = card.dataset.filepath;
        await apiCall('open', { path });
    }
});

document.getElementById('search-results').addEventListener('click', async (e) => {
    const btnOpen = e.target.closest('.action-open');
    if (btnOpen) {
        const path = btnOpen.dataset.path;
        await apiCall('open', { path });
        return;
    }

    const btnRoute = e.target.closest('.action-route');
    if (btnRoute) {
        const target = btnRoute.dataset.target;
        const path = btnRoute.dataset.path;
        // Poner path en el input correspondiente
        const inputMap = {
            'ocr': 'ocr-path',
            'llm': 'llm-path',
            'faces': 'faces-dir'
        };
        const inputId = inputMap[target];
        if (inputId) {
            const inputEl = document.getElementById(inputId);
            if (inputEl) inputEl.value = path;
        }
        // Navegar a la pestaña
        document.getElementById(`nav-${target}`).click();
    }
});

// ═══════════════════════════════════════════════
// Settings (Ajustes Avanzados)
// ═══════════════════════════════════════════════

function loadSettings() {
    const defaultSettings = {
        llm_tokens: 2048,
        llm_temp: 0.2,
        ocr_engine: "auto",
        dupe_threshold: 10
    };
    
    let current = {};
    try {
        current = JSON.parse(localStorage.getItem('maer_settings')) || {};
    } catch {
        current = {};
    }
    
    const settings = { ...defaultSettings, ...current };
    
    const eTokens = document.getElementById('cfg-llm-tokens');
    const eTemp = document.getElementById('cfg-llm-temp');
    const eOcr = document.getElementById('cfg-ocr-engine');
    const eDupe = document.getElementById('cfg-dupe-threshold');
    
    if (eTokens) eTokens.value = settings.llm_tokens;
    if (eTemp) eTemp.value = settings.llm_temp;
    if (eOcr) eOcr.value = settings.ocr_engine;
    if (eDupe) eDupe.value = settings.dupe_threshold;
    
    // Auto sync UI sliders if needed
    const dt = document.getElementById('dupes-threshold');
    if (dt) dt.value = settings.dupe_threshold;
    const dtval = document.getElementById('dupes-threshold-val');
    if (dtval) dtval.textContent = settings.dupe_threshold;

    return settings;
}

const btnSaveSettings = document.getElementById('btn-save-settings');
if (btnSaveSettings) {
    btnSaveSettings.addEventListener('click', () => {
        const settings = {
            llm_tokens: parseInt(document.getElementById('cfg-llm-tokens').value) || 2048,
            llm_temp: parseFloat(document.getElementById('cfg-llm-temp').value) || 0.2,
            ocr_engine: document.getElementById('cfg-ocr-engine').value || 'auto',
            dupe_threshold: parseInt(document.getElementById('cfg-dupe-threshold').value) || 10
        };
        localStorage.setItem('maer_settings', JSON.stringify(settings));
        loadSettings(); // update dependencies
        showToast('⚙️ Ajustes guardados correctamente', 'success');
    });
}

loadSettings();

// ═══════════════════════════════════════════════
// Server Status
// ═══════════════════════════════════════════════

async function checkStatus() {
    try {
        const res = await fetch(`${API}/api/status`);
        const result = await res.json();

        const dot = document.querySelector('.status-dot');
        const text = document.querySelector('.status-text');

        if (result.ok) {
            dot.classList.add('online');
            text.textContent = 'MAER Online';

            // Show module badges
            const badges = document.getElementById('modules-badges');
            const modules = (result.data || {}).modules || {};
            badges.innerHTML = Object.entries(modules).map(([name, ok]) =>
                `<span class="badge ${ok ? 'badge-ok' : 'badge-missing'}">${ok ? '✓' : '✗'} ${name}</span>`
            ).join('');
        }
    } catch {
        document.querySelector('.status-text').textContent = 'Sin conexión';
    }
}

// Init
checkStatus();
setInterval(checkStatus, 30000);

// ═══════════════════════════════════════════════
// UI File Pickers (Integración Nativos MacOS)
// ═══════════════════════════════════════════════

document.addEventListener('click', async (e) => {
    const btnFile = e.target.closest('.btn-pick-file');
    if (btnFile) {
        e.preventDefault();
        const targetId = btnFile.dataset.target;
        const result = await fetch('/api/select-file').then(r => r.json());
        if (result && result.ok && result.data) {
            document.getElementById(targetId).value = result.data;
        } else if (result && !result.ok && result.code !== 'CANCEL') {
            showToast('Error abriendo explorador: ' + result.message, 'error');
        }
    }

    const btnDir = e.target.closest('.btn-pick-dir');
    if (btnDir) {
        e.preventDefault();
        const targetId = btnDir.dataset.target;
        const result = await fetch('/api/select-dir').then(r => r.json());
        if (result && result.ok && result.data) {
            document.getElementById(targetId).value = result.data;
        } else if (result && !result.ok && result.code !== 'CANCEL') {
            showToast('Error abriendo explorador: ' + result.message, 'error');
        }
    }
});
