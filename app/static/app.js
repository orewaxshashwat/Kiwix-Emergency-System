function quickSearch(queryText) {
    document.getElementById('queryInput').value = queryText;
    submitQuery();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        submitQuery();
    }
}

async function submitQuery() {
    const inputField = document.getElementById('queryInput');
    const query = inputField.value.trim();
    if (!query) return;

    const loadingEl = document.getElementById('loading');
    const responseCard = document.getElementById('responseCard');
    
    loadingEl.classList.remove('hidden');
    responseCard.classList.add('hidden');

    try {
        // Adjust '/api/query' if your server teammate uses a different endpoint route
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: query })
        });

        if (!response.ok) {
            throw new Error('Server returned an error');
        }

        const data = await response.json();
        renderResult(data);
    } catch (error) {
        alert('Failed to connect to local emergency backend node. Make sure the server is running.');
        console.error(error);
    } finally {
        loadingEl.classList.add('hidden');
    }
}

function renderResult(data) {
    const responseCard = document.getElementById('responseCard');
    const answerText = document.getElementById('answerText');
    const sourcesList = document.getElementById('sourcesList');

    // Populate answer text
    answerText.textContent = data.answer || "No response provided by backend.";

    // Clear and populate sources
    sourcesList.innerHTML = '';
    if (data.sources && data.sources.length > 0) {
        data.sources.forEach(source => {
            const li = document.createElement('li');
            li.textContent = source.title || source;
            sourcesList.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = "No direct source references attached.";
        sourcesList.appendChild(li);
    }

    responseCard.classList.remove('hidden');
}