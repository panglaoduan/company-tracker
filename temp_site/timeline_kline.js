// ── K 线图 + 成交量图 ─────────────────────────────────
let chartPrice = null, chartVol = null;

function renderKChart(sd) {
    if (chartPrice) { chartPrice.destroy(); chartPrice = null; }
    if (chartVol)   { chartVol.destroy();   chartVol   = null; }
    if (!sd) return;

    const UP   = '#e5483c';  // 阳线红（涨）
    const DOWN = '#22a06b';  // 阴线绿（跌）

    const candles = sd.dates.map((d, i) => ({
        x: i,
        o: sd.opens[i]  || sd.closes[i],
        h: sd.highs[i]  || sd.closes[i],
        l: sd.lows[i]   || sd.closes[i],
        c: sd.closes[i],
        date: d,
    }));

    const colors = candles.map(d => d.c >= d.o ? UP : DOWN);

    // ── 共用 tooltip ──────────────────────────────
    const sharedTooltip = {
        mode: 'index',
        intersect: false,
        callbacks: {
            title: items => candles[items[0].dataIndex].date,
            label: () => null,
            afterBody: items => {
                const i = items[0].dataIndex;
                const d = candles[i];
                const fv = v => v >= 1e8 ? (v/1e8).toFixed(1)+'亿' : v >= 1e4 ? (v/1e4).toFixed(0)+'万' : v;
                return [
                    `开盘：${d.o}`,
                    `最高：${d.h}`,
                    `最低：${d.l}`,
                    `收盘：${d.c}`,
                    `成交量：${fv(sd.volumes[i])}`,
                ];
            }
        },
        backgroundColor: 'rgba(30,30,50,0.9)',
        titleColor: '#fff',
        bodyColor: '#ddd',
        padding: 10,
        displayColors: false,
        titleFont: { size: 13, weight: 'bold' },
        bodyFont: { size: 12 },
    };

    // ── K 线图 ────────────────────────────────────
    const pCtx = document.getElementById('priceChart').getContext('2d');
    chartPrice = new Chart(pCtx, {
        type: 'candlestick',
        data: {
            labels: candles.map(c => c.date),
            datasets: [{
                label: 'K 线',
                data: candles.map(c => ({ x: c.x, o: c.o, h: c.h, l: c.l, c: c.c })),
                color: {
                    up: UP,
                    down: DOWN,
                    unchanged: '#999',
                },
                borderColor: {
                    up: UP,
                    down: DOWN,
                },
                backgroundColor: {
                    up: '#ffffff',
                    down: DOWN,
                },
                borderWidth: 1.5,
                Wick: {
                    color: UP,
                },
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: sharedTooltip,
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 }, maxRotation: 0 }
                },
                y: {
                    position: 'right',
                    grid: { color: '#f0f0f0' },
                    ticks: { font: { size: 11 } }
                }
            }
        }
    });

    // ── 成交量图 ──────────────────────────────────
    const vCtx = document.getElementById('volChart').getContext('2d');
    chartVol = new Chart(vCtx, {
        type: 'bar',
        data: {
            labels: candles.map(c => c.date),
            datasets: [{
                label: '成交量',
                data: sd.volumes,
                backgroundColor: colors.map(c => c + 'bb'),
                borderRadius: 2,
                barPercentage: 0.7,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: sharedTooltip,
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 0 } },
                y: {
                    position: 'right',
                    grid: { display: false },
                    ticks: {
                        font: { size: 10 },
                        callback: v => v >= 1e8 ? (v/1e8).toFixed(1)+'亿' : v >= 1e4 ? (v/1e4).toFixed(0)+'万' : v
                    }
                }
            }
        }
    });
}
