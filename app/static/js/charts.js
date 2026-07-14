/**
 * Dashboard Charts and Analytics Logic
 */

// Common Chart.js options for dark mode
const darkThemeOptions = {
    color: '#a0a0c0', // text-secondary
    plugins: {
        legend: {
            labels: { color: '#a0a0c0' }
        },
        tooltip: {
            backgroundColor: 'rgba(20, 20, 45, 0.9)',
            titleColor: '#f0f0f8',
            bodyColor: '#a0a0c0',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
        }
    },
    scales: {
        x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#606080' } // text-muted
        },
        y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#606080' }
        }
    },
    maintainAspectRatio: false,
    responsive: true
};

// Global chart instances
let charts = {
    distribution: null,
    trend: null,
    credibility: null,
    sentiment: null
};

// Load dashboard data
async function loadDashboard() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error('Failed to fetch stats');
        const data = await response.json();
        
        updateStatCards(data);
        renderCharts(data);
        loadHistory(1); // Load first page of history
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        if (typeof showToast === 'function') {
            showToast('Failed to load dashboard data', 'error');
        }
    }
}

// Update summary statistic cards
function updateStatCards(data) {
    document.getElementById('totalAnalyzed').textContent = data.total_analyzed.toLocaleString();
    document.getElementById('fakeCount').textContent = data.fake_count.toLocaleString();
    document.getElementById('realCount').textContent = data.real_count.toLocaleString();
    
    const confPercent = Math.round(data.avg_confidence * 100);
    document.getElementById('avgConfidence').textContent = `${confPercent}%`;
}

// Render all charts
function renderCharts(data) {
    // 1. Distribution Chart (Doughnut)
    const distCtx = document.getElementById('distributionChart').getContext('2d');
    if (charts.distribution) charts.distribution.destroy();
    
    charts.distribution = new Chart(distCtx, {
        type: 'doughnut',
        data: {
            labels: ['Fake', 'Real'],
            datasets: [{
                data: [data.fake_count, data.real_count],
                backgroundColor: [
                    'rgba(255, 0, 110, 0.8)',  // accent-magenta
                    'rgba(0, 255, 136, 0.8)'   // accent-green
                ],
                borderColor: 'rgba(6, 6, 15, 1)',
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            ...darkThemeOptions,
            scales: { x: { display: false }, y: { display: false } },
            cutout: '70%',
            plugins: {
                legend: { position: 'bottom', labels: { color: '#a0a0c0', padding: 20 } }
            }
        }
    });

    // 2. Trend Chart (Line)
    const trendCtx = document.getElementById('trendChart').getContext('2d');
    if (charts.trend) charts.trend.destroy();
    
    const labels = data.daily_trend.map(d => d.date);
    const fakeData = data.daily_trend.map(d => d.fake);
    const realData = data.daily_trend.map(d => d.real);
    
    charts.trend = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Real',
                    data: realData,
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Fake',
                    data: fakeData,
                    borderColor: '#ff006e',
                    backgroundColor: 'rgba(255, 0, 110, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            ...darkThemeOptions,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', align: 'end' }
            }
        }
    });

    // 3. Credibility Chart (Bar)
    const credCtx = document.getElementById('credibilityChart').getContext('2d');
    if (charts.credibility) charts.credibility.destroy();
    
    const credLabels = ['High', 'Medium', 'Low', 'Unknown'];
    const credData = [
        data.credibility_distribution['HIGH'] || 0,
        data.credibility_distribution['MEDIUM'] || 0,
        data.credibility_distribution['LOW'] || 0,
        data.credibility_distribution['UNKNOWN'] || 0
    ];
    
    charts.credibility = new Chart(credCtx, {
        type: 'bar',
        data: {
            labels: credLabels,
            datasets: [{
                label: 'Sources',
                data: credData,
                backgroundColor: [
                    'rgba(0, 255, 136, 0.6)',  // High - Green
                    'rgba(255, 184, 0, 0.6)',  // Med - Amber
                    'rgba(255, 0, 110, 0.6)',  // Low - Magenta
                    'rgba(255, 255, 255, 0.2)' // Unknown - Gray
                ],
                borderRadius: 4
            }]
        },
        options: {
            ...darkThemeOptions,
            plugins: { legend: { display: false } },
            scales: {
                x: { ...darkThemeOptions.scales.x, grid: { display: false } },
                y: { ...darkThemeOptions.scales.y, beginAtZero: true }
            }
        }
    });

    // 4. Sentiment Chart (Gauge/Polar)
    const sentCtx = document.getElementById('sentimentChart').getContext('2d');
    if (charts.sentiment) charts.sentiment.destroy();
    
    // Convert compound avg (-1 to 1) to a gauge value (0 to 100)
    const gaugeValue = ((data.avg_sentiment + 1) / 2) * 100;
    
    charts.sentiment = new Chart(sentCtx, {
        type: 'doughnut',
        data: {
            labels: ['Average Sentiment', ''],
            datasets: [{
                data: [gaugeValue, 100 - gaugeValue],
                backgroundColor: [
                    data.avg_sentiment > 0.05 ? '#00ff88' : (data.avg_sentiment < -0.05 ? '#ff006e' : '#a0a0c0'),
                    'rgba(255, 255, 255, 0.05)'
                ],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            ...darkThemeOptions,
            scales: { x: { display: false }, y: { display: false } },
            cutout: '80%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataIndex === 0) {
                                return `Avg Compound: ${data.avg_sentiment.toFixed(3)}`;
                            }
                            return '';
                        }
                    }
                }
            }
        },
        plugins: [{
            id: 'gaugeText',
            beforeDraw: function(chart) {
                var width = chart.width,
                    height = chart.height,
                    ctx = chart.ctx;
        
                ctx.restore();
                var fontSize = (height / 120).toFixed(2);
                ctx.font = "bold " + fontSize + "em sans-serif";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#f0f0f8";
        
                var text = data.avg_sentiment.toFixed(2),
                    textX = Math.round((width - ctx.measureText(text).width) / 2),
                    textY = height / 1.5;
        
                ctx.fillText(text, textX, textY);
                
                // Add label
                ctx.font = "normal " + (fontSize * 0.4) + "em sans-serif";
                ctx.fillStyle = "#a0a0c0";
                var label = data.avg_sentiment > 0.05 ? "Positive" : (data.avg_sentiment < -0.05 ? "Negative" : "Neutral");
                var labelX = Math.round((width - ctx.measureText(label).width) / 2);
                ctx.fillText(label, labelX, textY + 25);
                ctx.save();
            }
        }]
    });
}

// Load analysis history with pagination
async function loadHistory(page = 1) {
    try {
        const response = await fetch(`/api/history?page=${page}&per_page=10`);
        if (!response.ok) throw new Error('Failed to fetch history');
        
        const data = await response.json();
        const tbody = document.getElementById('historyBody');
        const emptyState = document.getElementById('emptyHistory');
        const table = document.getElementById('historyTable');
        
        if (data.articles.length === 0) {
            table.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }
        
        table.classList.remove('hidden');
        emptyState.classList.add('hidden');
        
        // Populate table
        tbody.innerHTML = data.articles.map(article => {
            const analysis = article.analyses[0] || {};
            const isReal = analysis.prediction === 'REAL';
            const conf = Math.round((analysis.confidence || 0) * 100);
            
            return `
                <tr style="cursor: pointer" onclick="window.location.href='/results/${article.id}'">
                    <td class="title-cell">
                        <strong>${article.title || 'Untitled'}</strong><br>
                        <span style="font-size: 0.8rem; color: var(--text-muted)">
                            ${article.text ? article.text.substring(0, 60) + '...' : ''}
                        </span>
                    </td>
                    <td>
                        <span class="verdict-badge ${isReal ? 'real' : 'fake'}" style="padding: 2px 8px; font-size: 0.75rem;">
                            ${isReal ? '✅ REAL' : '❌ FAKE'}
                        </span>
                    </td>
                    <td>${conf}%</td>
                    <td>
                        <span style="color: ${analysis.sentiment?.compound > 0.05 ? 'var(--accent-green)' : (analysis.sentiment?.compound < -0.05 ? 'var(--accent-magenta)' : 'var(--text-muted)')}">
                            ${(analysis.sentiment?.compound || 0).toFixed(2)}
                        </span>
                    </td>
                    <td>${analysis.source_credibility || 'UNKNOWN'}</td>
                    <td>${article.created_at ? new Date(article.created_at).toLocaleDateString() : '-'}</td>
                </tr>
            `;
        }).join('');
        
        // Render pagination
        renderPagination(data.page, data.pages);
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function renderPagination(currentPage, totalPages) {
    const container = document.getElementById('pagination');
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Prev
    if (currentPage > 1) {
        html += `<button class="page-btn" onclick="loadHistory(${currentPage - 1})">← Prev</button>`;
    }
    
    // Pages (simplified)
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="loadHistory(${i})">${i}</button>`;
    }
    
    // Next
    if (currentPage < totalPages) {
        html += `<button class="page-btn" onclick="loadHistory(${currentPage + 1})">Next →</button>`;
    }
    
    container.innerHTML = html;
}
