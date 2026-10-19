// API location, in priority order: ?api=<url> (remembered for later visits), the page's own
// origin when the dashboard is served by the API at /ui, a remembered URL, then a local server.
function resolveApiBase() {
    const fromQuery = new URLSearchParams(window.location.search).get('api');
    if (fromQuery) {
        try { localStorage.setItem('satqueryApiBase', fromQuery); } catch (e) {}
        return fromQuery.replace(/\/+$/, '');
    }
    if (window.location.protocol.startsWith('http')) return window.location.origin;
    try {
        const saved = localStorage.getItem('satqueryApiBase');
        if (saved) return saved.replace(/\/+$/, '');
    } catch (e) {}
    return 'http://127.0.0.1:8000';
}
const API_BASE_URL = resolveApiBase();

// Helper to set preset image inputs
function setImage(imgName) {
    document.getElementById('imageInputs').value = imgName;
}

// Attach preset prompt chip click handlers
document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        const query = chip.getAttribute('data-query');
        const img = chip.getAttribute('data-image');
        if (query) document.getElementById('queryInput').value = query;
        if (img) document.getElementById('imageInputs').value = img;
    });
});

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]
    ));
}

function fileName(path) {
    return String(path || '').split(/[\/]/).pop();
}

function nodeLabel(node) {
    if (!node) return '';
    if (node.type === 'input') return fileName(node.data.path);
    if (node.type === 'tool') return node.data.tool;
    return 'answer';
}

// Key facts worth showing per tool, picked from its first evidence record's metadata.
const STEP_FACTS = {
    temporal_alignment: m => [`order: ${m.temporal_order}`],
    spatial_alignment: m => [`same CRS: ${m.same_crs}`, `overlap: ${m.overlap}`],
    change_detection: m => [`${m.change_percentage}% changed`, `${m.changed_pixel_count} / ${m.valid_pixel_count} px`],
    change_localization: m => m.changed_area_sqm != null ? [`${Math.round(m.changed_area_sqm).toLocaleString()} m²`, `${m.region_count} region(s)`] : [],
    optical_sar_fusion: m => m.statistics ? [`SAR water ${m.statistics.sar_water_percentage}%`]
        .concat(m.statistics.agreement_percentage != null ? [`agreement ${m.statistics.agreement_percentage}%`] : []) : [],
};

function renderEvidenceGraph(graph) {
    if (!graph || !graph.nodes || !graph.nodes.length) {
        return '<div style="color: #94a3b8; font-size: 0.85rem;">No evidence was produced.</div>';
    }
    const byId = Object.fromEntries(graph.nodes.map(n => [n.id, n]));
    const parentsOf = id => graph.edges.filter(e => e.target === id).map(e => nodeLabel(byId[e.source]));

    return graph.nodes.map(node => {
        const parents = parentsOf(node.id);
        const from = parents.length ? `<div class="node-tool">derived from: ${parents.map(p => `<code>${escapeHtml(p)}</code>`).join(', ')}</div>` : '';
        let tag, title, details = [], status = '';

        if (node.type === 'input') {
            const d = node.data;
            tag = 'INPUT';
            title = fileName(d.path);
            details = [d.modality, d.crs, `${d.width}×${d.height}`, `${d.band_count} band(s)`, d.acquisition_time ? `acquired ${d.acquisition_time}` : 'acquisition date unknown'];
        } else if (node.type === 'tool') {
            const d = node.data;
            const meta = (d.evidence && d.evidence[0] && d.evidence[0].metadata) || {};
            tag = 'STEP';
            title = d.tool;
            details = (STEP_FACTS[d.tool] || (() => []))(meta).concat(d.errors || []);
            status = d.success ? '<span class="node-status ok">passed</span>' : '<span class="node-status fail">failed</span>';
        } else {
            tag = 'ANSWER';
            title = node.data.source_tool ? `answered from ${node.data.source_tool}` : 'no answer produced';
        }

        return `
            <div class="evidence-node">
                <div class="node-left">
                    <span class="node-tag">${tag}</span>
                    <div>
                        <div class="node-src">${escapeHtml(title)}</div>
                        ${from}
                        ${details.filter(Boolean).length ? `<div class="node-tool">${details.filter(Boolean).map(escapeHtml).join(' · ')}</div>` : ''}
                    </div>
                </div>
                ${status}
            </div>`;
    }).join('');
}

// Raster upload: files are stored by the API and their server paths fill the inputs field,
// in selection order, so the user can check and reorder T1/T2 or optical/SAR before running.
const fileUpload = document.getElementById('fileUpload');
const uploadStatus = document.getElementById('uploadStatus');

async function uploadFile(file) {
    const form = new FormData();
    form.append('file', file);
    const response = await fetch(`${API_BASE_URL}/uploads`, {
        method: 'POST',
        headers: { 'Bypass-Tunnel-Reminder': 'true' },
        body: form
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
    return body;
}

if (fileUpload) {
    fileUpload.addEventListener('change', async () => {
        const files = Array.from(fileUpload.files || []);
        if (!files.length) return;
        const uploaded = [];
        const failures = [];
        for (const [i, file] of files.entries()) {
            uploadStatus.textContent = `Uploading ${i + 1}/${files.length}: ${file.name}...`;
            try {
                uploaded.push(await uploadFile(file));
            } catch (error) {
                failures.push(`${file.name}: ${error.message}`);
            }
        }
        if (uploaded.length) {
            document.getElementById('imageInputs').value = uploaded.map(u => u.path).join(', ');
        }
        const described = uploaded.map((u, i) =>
            `${i + 1}. ${u.filename} (${u.band_count} band(s), ${u.modality}${u.acquisition_time ? ', ' + u.acquisition_time.slice(0, 10) : ''})`);
        uploadStatus.textContent = [
            uploaded.length ? `Uploaded in this order: ${described.join('  ')}` : '',
            failures.length ? `Failed: ${failures.join('; ')}` : ''
        ].filter(Boolean).join('  |  ');
        uploadStatus.className = 'upload-status' + (failures.length ? ' has-error' : '');
        fileUpload.value = '';
    });
}

// Header badge reflects the provider the API is actually configured with.
async function refreshBackendStatus() {
    const badge = document.getElementById('backendStatus');
    if (!badge) return;
    try {
        const response = await fetch(`${API_BASE_URL}/health`, { headers: { 'Bypass-Tunnel-Reminder': 'true' } });
        const health = await response.json();
        badge.textContent = health.model_provider === 'mock'
            ? 'API online · mock model (no VLM loaded)'
            : `API online · ${health.model_provider} ${health.model_loaded ? '(loaded)' : '(loads on first query)'}`;
    } catch (error) {
        badge.textContent = `API unreachable at ${API_BASE_URL}`;
    }
}
refreshBackendStatus();

const ANSWER_SOURCE_LABELS = {
    'vision.answer': 'Vision-Language Model Answer',
    'change_summary': 'Change Measurement',
    'optical_sar_fusion': 'Optical-SAR Water Fusion',
    'raster.metadata': 'Raster Metadata',
};

// Raw JSON view toggle
const toggleJsonBtn = document.getElementById('toggleJsonBtn');
const jsonViewerWrapper = document.getElementById('jsonViewerWrapper');
const toggleJsonText = document.getElementById('toggleJsonText');

if (toggleJsonBtn) {
    toggleJsonBtn.addEventListener('click', () => {
        const isHidden = jsonViewerWrapper.style.display === 'none';
        jsonViewerWrapper.style.display = isHidden ? 'block' : 'none';
        toggleJsonText.textContent = isHidden ? 'Hide Raw Verification JSON' : 'View Full Verification JSON';
    });
}

document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const query = document.getElementById('queryInput').value.trim();
    const inputsStr = document.getElementById('imageInputs').value.trim();
    const inputs = inputsStr.split(',').map(i => i.trim()).filter(Boolean);

    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('btnSpinner');
    const btnText = submitBtn.querySelector('.btn-text');
    const resultsSection = document.getElementById('resultsSection');
    const pipelineTracker = document.getElementById('pipelineTracker');
    const statusBadge = document.getElementById('statusBadge');
    const aiAnswer = document.getElementById('aiAnswer');
    const confidenceBadge = document.getElementById('confidenceBadge');
    const evidenceNodes = document.getElementById('evidenceNodes');
    const jsonOutput = document.getElementById('jsonOutput');

    // UI Loading state
    submitBtn.disabled = true;
    spinner.style.display = 'inline-block';
    if (btnText) btnText.textContent = 'Analyzing Satellite Data...';
    
    pipelineTracker.style.display = 'block';
    resultsSection.style.display = 'flex';
    
    statusBadge.textContent = 'Processing...';
    statusBadge.className = 'status-badge';
    aiAnswer.innerHTML = '<em>Agent is orchestrating remote sensing tools and querying RS-LLaVA VLM...</em>';
    evidenceNodes.innerHTML = '<div style="color: #64748b; font-size: 0.85rem;">Resolving geospatial evidence...</div>';
    jsonOutput.textContent = '';

    try {
        // Submit Job
        const submitResponse = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Bypass-Tunnel-Reminder': 'true'
            },
            body: JSON.stringify({ query, inputs })
        });

        if (!submitResponse.ok) {
            const detail = (await submitResponse.json().catch(() => ({}))).detail;
            throw new Error(typeof detail === 'string' ? detail : `Submission failed with HTTP ${submitResponse.status}`);
        }

        const data = await submitResponse.json();
        const analysisId = data.analysis_id;

        // Poll for results
        await pollJobStatus(analysisId);

    } catch (error) {
        statusBadge.textContent = 'Failed';
        statusBadge.className = 'status-badge failed';
        aiAnswer.textContent = 'Error: ' + error.message;
        resetBtn();
    }

    function resetBtn() {
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        if (btnText) btnText.textContent = 'Execute Geospatial Intelligence';
    }

    async function pollJobStatus(jobId) {
        try {
            const statusResponse = await fetch(`${API_BASE_URL}/analyze/${jobId}`, {
                headers: { 'Bypass-Tunnel-Reminder': 'true' }
            });
            if (!statusResponse.ok) throw new Error('Failed to fetch job status');

            const statusData = await statusResponse.json();

            if (statusData.status === 'completed') {
                const result = statusData.result || {};
                const succeeded = result.success !== false;

                statusBadge.textContent = succeeded ? 'Intelligence Ready' : 'Analysis Refused';
                statusBadge.className = 'status-badge ' + (succeeded ? 'completed' : 'failed');

                aiAnswer.textContent = result.answer || 'Analysis complete.';
                document.getElementById('answerSourceTag').textContent =
                    ANSWER_SOURCE_LABELS[result.answer_source] || (succeeded ? 'Analysis Result' : 'Analysis Refused');
                if (result.limitations && result.limitations.length) {
                    const list = document.createElement('ul');
                    list.className = 'limitations-list';
                    result.limitations.forEach(text => {
                        const item = document.createElement('li');
                        item.textContent = text;
                        list.appendChild(item);
                    });
                    aiAnswer.appendChild(list);
                }

                evidenceNodes.innerHTML = renderEvidenceGraph(result.evidence_graph);

                // Confidence only exists when a probabilistic model contributed.
                confidenceBadge.innerHTML = typeof result.confidence === 'number'
                    ? `<span class="confidence-val">Model confidence: ${Math.round(result.confidence * 100)}%</span>`
                    : `<span class="confidence-val">${succeeded ? 'Deterministic measurement' : 'No result'}</span>`;

                // Raw JSON
                jsonOutput.textContent = JSON.stringify(statusData, null, 2);
                resetBtn();

            } else if (statusData.status === 'failed') {
                statusBadge.textContent = 'Pipeline Failed';
                statusBadge.className = 'status-badge failed';
                aiAnswer.textContent = statusData.error || 'Execution failed on server.';
                jsonOutput.textContent = JSON.stringify(statusData, null, 2);
                resetBtn();
            } else {
                statusBadge.textContent = statusData.status === 'running' ? 'Running Analysis...' : 'Queued...';
                // Poll again after 1 second
                setTimeout(() => pollJobStatus(jobId), 1000);
            }

        } catch (error) {
            statusBadge.textContent = 'Error';
            statusBadge.className = 'status-badge failed';
            aiAnswer.textContent = 'Polling Error: ' + error.message;
            resetBtn();
        }
    }
});
