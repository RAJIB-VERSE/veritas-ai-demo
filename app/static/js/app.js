/**
 * Main Frontend Logic for VeritasAI
 */

// Show a toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    
    container.appendChild(toast);

    // Auto remove after 5s
    setTimeout(() => {
        toast.classList.add('exit');
        setTimeout(() => toast.remove(), 300); // Wait for exit animation
    }, 5000);
}

// Reset the analysis form and results
function resetForm() {
    document.getElementById('articleText').value = '';
    document.getElementById('articleUrl').value = '';
    document.getElementById('articleTitle').value = '';
    
    const resultContainer = document.getElementById('resultContainer');
    if (resultContainer) {
        resultContainer.classList.add('hidden');
    }
    
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.style.display = 'block';
    }
    
    // Smooth scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Analyze the article
async function analyzeArticle() {
    const text = document.getElementById('articleText').value.trim();
    const url = document.getElementById('articleUrl').value.trim();
    const title = document.getElementById('articleTitle').value.trim();
    const btn = document.getElementById('analyzeBtn');

    if (!text && !url) {
        showToast('Please provide either article text or a URL to analyze.', 'warning');
        return;
    }

    // Set loading state
    btn.classList.add('loading');
    btn.textContent = 'Analyzing...';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text, url, title })
        });

        const data = await response.json();

        if (!response.ok) {
            showToast(data.error || 'An error occurred during analysis.', 'error');
            return;
        }

        displayResults(data);
        showToast('Analysis complete!', 'success');

    } catch (error) {
        console.error('Analysis error:', error);
        showToast('Failed to connect to the analysis service.', 'error');
    } finally {
        // Reset button
        btn.classList.remove('loading');
        btn.innerHTML = '🔍 Analyze Article';
    }
}

// Display the results dynamically
function displayResults(data) {
    // Hide form, show results
    document.getElementById('analysisForm').style.display = 'none';
    
    // NEW: Live Web Fact Check
    const liveFactCheckCard = document.getElementById('liveFactCheckCard');
    if (data.fact_check && data.fact_check.status !== 'error') {
        liveFactCheckCard.style.display = 'block';
        const fcStatus = document.getElementById('liveFactCheckStatus');
        fcStatus.textContent = data.fact_check.message;
        
        if (data.fact_check.status === 'debunked') {
            liveFactCheckCard.style.borderColor = 'var(--accent-red)';
            fcStatus.style.color = 'var(--accent-red)';
        } else if (data.fact_check.status === 'verified') {
            liveFactCheckCard.style.borderColor = 'var(--accent-green)';
            fcStatus.style.color = 'var(--accent-green)';
        } else {
            liveFactCheckCard.style.borderColor = 'var(--accent-amber)';
            fcStatus.style.color = 'var(--accent-amber)';
        }
        
        const fcSources = document.getElementById('liveFactCheckSources');
        if (data.fact_check.sources && data.fact_check.sources.length > 0) {
            fcSources.innerHTML = data.fact_check.sources.map(s => 
                `<a href="${s.url}" target="_blank" class="feature-tag" style="background: rgba(255, 255, 255, 0.05); color: var(--text-secondary); text-decoration: none; border-color: rgba(255, 255, 255, 0.1);">
                    ${s.title}
                </a>`
            ).join('');
        } else {
            fcSources.innerHTML = '';
        }
    } else {
        liveFactCheckCard.style.display = 'none';
    }

    const resultContainer = document.getElementById('resultContainer');
    resultContainer.classList.remove('hidden');

    // 1. Verdict & Confidence
    const isReal = data.classification.label === 'REAL';
    const conf = Math.round(data.classification.confidence * 100);
    
    const verdictBadge = document.getElementById('verdictBadge');
    verdictBadge.className = `verdict-badge ${isReal ? 'real' : 'fake'}`;
    
    document.getElementById('verdictIcon').textContent = isReal ? '✅' : '❌';
    document.getElementById('verdictLabel').textContent = isReal ? 'LIKELY TRUE' : 'LIKELY FALSE';
    
    document.getElementById('confidenceValue').textContent = `${conf}%`;
    const confFill = document.getElementById('confidenceFill');
    confFill.style.width = `${conf}%`;
    confFill.className = `confidence-fill ${conf >= 70 ? 'high' : 'low'}`;

    // 2. Sentiment
    const sent = data.sentiment;
    const sentValEl = document.getElementById('sentimentValue');
    sentValEl.textContent = sent.compound.toFixed(2);
    sentValEl.className = `sentiment-value ${sent.compound > 0.05 ? 'positive' : (sent.compound < -0.05 ? 'negative' : 'neutral')}`;
    
    document.getElementById('sentPosBar').style.width = `${(sent.positive * 100).toFixed(0)}%`;
    document.getElementById('sentPosVal').textContent = `${(sent.positive * 100).toFixed(0)}%`;
    
    document.getElementById('sentNegBar').style.width = `${(sent.negative * 100).toFixed(0)}%`;
    document.getElementById('sentNegVal').textContent = `${(sent.negative * 100).toFixed(0)}%`;
    
    document.getElementById('sentNeuBar').style.width = `${(sent.neutral * 100).toFixed(0)}%`;
    document.getElementById('sentNeuVal').textContent = `${(sent.neutral * 100).toFixed(0)}%`;

    // Sensationalism
    const sensationalism = Math.round((sent.sensationalism_score || 0) * 100);
    if (sensationalism > 20) {
        document.getElementById('sensationalismContainer').style.display = 'block';
        document.getElementById('sensationalismValue').textContent = `${sensationalism}%`;
        document.getElementById('sensationalismFill').style.width = `${sensationalism}%`;
    } else {
        document.getElementById('sensationalismContainer').style.display = 'none';
    }

    // 3. Source Credibility
    const src = data.source_analysis;
    const credBadge = document.getElementById('credibilityBadge');
    credBadge.textContent = src.credibility || 'UNKNOWN';
    credBadge.className = `credibility-badge ${(src.credibility || 'unknown').toLowerCase()}`;
    
    // Top Reliability Badge
    const relBadge = document.getElementById('reliabilityBadge');
    const isReliable = (src.credibility === 'HIGH' || src.credibility === 'MEDIUM');
    const isUnreliable = (src.credibility === 'LOW');
    
    if (isReliable) {
        relBadge.className = 'verdict-badge real';
        relBadge.style = '';
        document.getElementById('reliabilityIcon').textContent = '✅';
        document.getElementById('reliabilityLabel').textContent = 'LIKELY REAL';
    } else if (isUnreliable) {
        relBadge.className = 'verdict-badge fake';
        relBadge.style = '';
        document.getElementById('reliabilityIcon').textContent = '❌';
        document.getElementById('reliabilityLabel').textContent = 'LIKELY FALSE';
    } else {
        relBadge.className = 'verdict-badge';
        relBadge.style.background = 'rgba(255, 255, 255, 0.05)';
        relBadge.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        relBadge.style.color = 'var(--text-secondary)';
        document.getElementById('reliabilityIcon').textContent = '❓';
        document.getElementById('reliabilityLabel').textContent = 'UNKNOWN';
    }
    
    if (src.credible_sources && src.credible_sources.length > 0) {
        document.getElementById('credibleSources').style.display = 'block';
        document.getElementById('credibleSourceTags').innerHTML = src.credible_sources.map(s => `<span class="feature-tag" style="background: rgba(0, 255, 136, 0.1); border-color: rgba(0, 255, 136, 0.3); color: var(--accent-green);">${s}</span>`).join('');
    } else {
        document.getElementById('credibleSources').style.display = 'none';
    }
    
    if (src.questionable_sources && src.questionable_sources.length > 0) {
        document.getElementById('questionableSources').style.display = 'block';
        document.getElementById('questionableSourceTags').innerHTML = src.questionable_sources.map(s => `<span class="feature-tag suspicious">${s}</span>`).join('');
    } else {
        document.getElementById('questionableSources').style.display = 'none';
    }
    
    // Suspicious Patterns
    if (src.suspicious_patterns) {
        const patternsList = document.getElementById('patternsList');
        let patternsHtml = '';
        if (src.suspicious_patterns.excessive_caps) patternsHtml += '<div>• Excessive use of ALL CAPS</div>';
        if (src.suspicious_patterns.excessive_punctuation) patternsHtml += '<div>• Excessive punctuation (!!! or ???)</div>';
        if (src.suspicious_patterns.no_sources_cited) patternsHtml += '<div>• No external sources or links cited</div>';
        if (src.suspicious_patterns.very_short) patternsHtml += '<div>• Article is unusually short</div>';
        
        if (patternsHtml) {
            document.getElementById('suspiciousPatterns').style.display = 'block';
            patternsList.innerHTML = patternsHtml;
        } else {
            document.getElementById('suspiciousPatterns').style.display = 'none';
        }
    }

    // 4. ML Features (if any)
    const features = data.classification.top_features;
    if (features && features.length > 0) {
        document.getElementById('featuresSection').style.display = 'block';
        document.getElementById('featureTags').innerHTML = features.map(f => `<span class="feature-tag">${f}</span>`).join('');
    } else {
        document.getElementById('featuresSection').style.display = 'none';
    }
    
    // 5. Clickbait / Suspicious Phrases
    const suspiciousPhrases = src.clickbait_phrases || [];
    if (suspiciousPhrases.length > 0) {
        document.getElementById('suspiciousSection').style.display = 'block';
        document.getElementById('suspiciousTags').innerHTML = suspiciousPhrases.map(p => `<span class="feature-tag suspicious">"${p}"</span>`).join('');
    } else {
        document.getElementById('suspiciousSection').style.display = 'none';
    }

    // Update details link
    if (data.article_id) {
        document.getElementById('viewDetailsLink').href = `/results/${data.article_id}`;
    }

    // Scroll to results
    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
