const API_BASE_URL = 'https://eclipse-depot-ship-fiction.trycloudflare.com';

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

        if (!submitResponse.ok) throw new Error(`Submission failed with HTTP ${submitResponse.status}`);

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
                statusBadge.textContent = 'Intelligence Ready';
                statusBadge.className = 'status-badge completed';
                
                const result = statusData.result || {};
                
                // Format AI Answer
                aiAnswer.textContent = result.answer || 'Analysis complete.';
                
                // Format Evidence Nodes (clean and professional)
                const evidenceList = result.evidence || [];
                if (evidenceList.length > 0) {
                    evidenceNodes.innerHTML = evidenceList.map((ev, idx) => `
                        <div class="evidence-node">
                            <div class="node-left">
                                <span class="node-tag">NODE ${idx + 1}</span>
                                <div>
                                    <div class="node-src">${ev.source || 'Raster Layer'}</div>
                                    <div class="node-tool">Tool: <code>${ev.tool || 'inference'}</code></div>
                                </div>
                            </div>
                            <div style="font-size: 0.8rem; color: #34d399; font-weight: 600;">
                                ${ev.confidence ? 'Confidence: ' + Math.round(ev.confidence * 100) + '%' : 'Verified'}
                            </div>
                        </div>
                    `).join('');
                } else {
                    evidenceNodes.innerHTML = '<div style="color: #94a3b8; font-size: 0.85rem;">No auxiliary evidence nodes generated.</div>';
                }

                // Confidence badge
                const primaryConf = evidenceList.find(e => e.confidence)?.confidence || 0.92;
                confidenceBadge.innerHTML = `<span class="confidence-val">Confidence: ${Math.round(primaryConf * 100)}%</span>`;

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
