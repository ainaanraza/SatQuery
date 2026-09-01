const API_BASE_URL = 'https://courier-perfume-wishlist-similarly.trycloudflare.com';


document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log("Analyze button was clicked! Form submission started.");

    const query = document.getElementById('queryInput').value;
    const inputsStr = document.getElementById('imageInputs').value;
    const inputs = inputsStr.split(',').map(i => i.trim());

    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('btnSpinner');
    const resultsSection = document.getElementById('resultsSection');
    const statusText = document.getElementById('statusText');
    const jsonOutput = document.getElementById('jsonOutput');

    // UI Loading state
    submitBtn.disabled = true;
    spinner.style.display = 'block';
    resultsSection.style.display = 'block';
    statusText.textContent = 'Submitting...';
    statusText.style.color = '#fbbf24'; // Yellow
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

        if (!submitResponse.ok) throw new Error('Submission failed');

        const data = await submitResponse.json();
        const analysisId = data.analysis_id;

        // Poll for results
        pollJobStatus(analysisId);

    } catch (error) {
        statusText.textContent = 'Error: ' + error.message;
        statusText.style.color = '#ef4444'; // Red
        resetBtn();
    }

    function resetBtn() {
        submitBtn.disabled = false;
        spinner.style.display = 'none';
    }

    async function pollJobStatus(jobId) {
        try {
            statusText.textContent = 'Processing...';

            // In a real app we would poll, but the current backend executes sync in the request
            // so we can just fetch it once. Let's fetch it:
            const statusResponse = await fetch(`${API_BASE_URL}/analyze/${jobId}`);
            if (!statusResponse.ok) throw new Error('Failed to fetch status');

            const statusData = await statusResponse.json();

            if (statusData.status === 'completed') {
                statusText.textContent = 'Completed!';
                statusText.style.color = '#34d399'; // Green
                jsonOutput.textContent = JSON.stringify(statusData.result || statusData, null, 2);
                resetBtn();
            } else if (statusData.status === 'failed') {
                statusText.textContent = 'Failed';
                statusText.style.color = '#ef4444'; // Red
                jsonOutput.textContent = JSON.stringify(statusData, null, 2);
                resetBtn();
            } else {
                // Poll again after a delay
                jsonOutput.textContent = JSON.stringify(statusData, null, 2);
                setTimeout(() => pollJobStatus(jobId), 1000);
            }

        } catch (error) {
            statusText.textContent = 'Error: ' + error.message;
            statusText.style.color = '#ef4444';
            resetBtn();
        }
    }
});
