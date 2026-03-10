// ── 配置 ──────────────────────────────────────────────
const COMPANIES = {
    tesla:           { name: '特斯拉',      color: '#e82127' },
    spacex:          { name: 'SpaceX',      color: '#1a1a2e' },
    ast_spacemobile: { name: 'AST 太空',    color: '#0066cc' },
    xiaomi:          { name: '小米',        color: '#ff6900' },
    horizon_robotics:{ name: '地平线',      color: '#00aa44' },
    ganli_pharma:    { name: '甘李药业',    color: '#9b27af' },
};

// 分类配置：icon + 独立颜色
const CATEGORIES = {
    strategy:   { name: '经营战略', icon: '📈', color: '#2196f3', bg: '#e3f2fd' },
    executive:  { name: '高管动态', icon: '👔', color: '#9c27b0', bg: '#f3e5f5' },
    competition:{ name: '行业竞争', icon: '⚔️', color: '#ff5722', bg: '#fbe9e7' },
    earnings:   { name: '财报发布', icon: '📋', color: '#4caf50', bg: '#e8f5e9' },
    volatility: { name: '股价异动', icon: '⚡', color: '#ff9800', bg: '#fff3e0' },
};

const SENTIMENTS = {
    positive: { name: '正面', color: '#22a06b' },
    negative: { name: '负面', color: '#e5483c' },
    neutral:  { name: '中性', color: '#888'    },
};

let allEvents      = [];
let filteredEvents = [];
let activeCategories = new Set(['all']);  // 多选状态

// ── 数据加载 ──────────────────────────────────────────
async function loadEvents() {
    try {
        const ts = Date.now();
        // 并行加载 events + meta
        const [evRes, metaRes] = await Promise.all([
            fetch('./events.json?' + ts),
            fetch('./meta.json?'   + ts)
        ]);
        if (!evRes.ok) throw new Error('no data');

        allEvents = await evRes.json();
        allEvents.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        filteredEvents = [...allEvents];
        renderEvents();

        // 从 meta.json 读取真实更新时间
        if (metaRes.ok) {
            const meta = await metaRes.json();
            updateStats(meta.last_updated);
        } else {
            updateStats(null);
        }
    } catch (e) {
        console.error('加载失败', e);
        document.getElementById('timeline').innerHTML =
            '<div class="no-events"><p>📭 数据加载失败，请刷新重试</p></div>';
    }
}

// ── 多选分类筛选 ──────────────────────────────────────
function toggleCategory(cat) {
    if (cat === 'all') {
        activeCategories = new Set(['all']);
    } else {
        activeCategories.delete('all');
        if (activeCategories.has(cat)) {
            activeCategories.delete(cat);
            if (activeCategories.size === 0) activeCategories.add('all');
        } else {
            activeCategories.add(cat);
        }
    }
    // 更新按钮样式
    document.querySelectorAll('.cat-btn').forEach(btn => {
        const c = btn.dataset.cat;
        const active = activeCategories.has(c);
        btn.classList.toggle('active', active);
    });
    applyFilter();
}

function applyFilter() {
    const companyVal = document.getElementById('companyFilter').value;
    const searchText = document.getElementById('searchInput').value.toLowerCase();
    const allCat     = activeCategories.has('all');

    filteredEvents = allEvents.filter(e => {
        if (companyVal !== 'all' && e.company_id !== companyVal) return false;
        if (!allCat && !activeCategories.has(e.category)) return false;
        if (searchText && !(e.title + e.content).toLowerCase().includes(searchText)) return false;
        return true;
    });
    renderEvents();
}

// ── 渲染时间线 ────────────────────────────────────────
function renderEvents() {
    const timeline = document.getElementById('timeline');
    if (!filteredEvents.length) {
        timeline.innerHTML = '<div class="no-events"><p>📭 暂无匹配事件</p></div>';
        return;
    }

    let html = '', lastYM = null;

    filteredEvents.forEach(ev => {
        const co  = COMPANIES[ev.company_id] || { name: ev.company_name, color: '#667eea' };
        const cat = CATEGORIES[ev.category]  || { name: ev.category, icon: '📌', color: '#888', bg: '#f5f5f5' };
        const sen = SENTIMENTS[ev.sentiment] || SENTIMENTS.neutral;

        const d     = new Date(ev.created_at);
        const year  = d.getFullYear();
        const month = d.getMonth() + 1;
        const ym    = `${year}-${String(month).padStart(2,'0')}`;

        if (ym !== lastYM) {
            if (!lastYM || year !== parseInt(lastYM)) {
                html += `<div class="timeline-year"><div class="timeline-year-badge">${year}</div></div>`;
            }
            html += `<div class="timeline-month"><div class="timeline-month-badge">${month} 月</div></div>`;
            lastYM = ym;
        }

        const dateStr = d.toLocaleDateString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' });
        const enc     = encodeURIComponent(JSON.stringify(ev));

        // 股价变动徽章（卡片上显示）
        let priceBadge = '';
        if (ev.stock_data) {
            const chg = ev.stock_data.change_pct;
            const up  = chg >= 0;
            priceBadge = `<span class="price-badge" style="background:${up?'#e8f5e9':'#fce4ec'};color:${up?'#22a06b':'#e5483c'}">
                ${up?'▲':'▼'} ${Math.abs(chg).toFixed(2)}%
            </span>`;
        }

        html += `
        <div class="event-card" style="border-left-color:${co.color};cursor:pointer"
             onclick="openModal(this)" data-event="${enc}">
            <div class="event-header">
                <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">
                    <span class="tag-company" style="background:${co.color}">${co.name}</span>
                    <span class="tag-category" style="background:${cat.bg};color:${cat.color};border:1px solid ${cat.color}40">
                        ${cat.icon} ${cat.name}
                    </span>
                    <span class="tag-sentiment" style="background:${sen.color}22;color:${sen.color}">● ${sen.name}</span>
                    ${priceBadge}
                </div>
            </div>
            <h3 class="event-title">${ev.title}</h3>
            <p class="event-content">${ev.content}</p>
            <div class="event-meta">
                <span>📅 ${dateStr}</span>
                <span>📰 ${ev.source}</span>
                <span>📊 ${'⭐'.repeat(ev.importance)}</span>
            </div>
            <span class="detail-hint">点击查看详情 →</span>
        </div>`;
    });

    timeline.innerHTML = html;
}

// ── 统计栏 ────────────────────────────────────────────
function updateStats(lastUpdated) {
    document.getElementById('totalEvents').textContent = allEvents.length;
    const today = new Date().toDateString();
    document.getElementById('todayEvents').textContent =
        allEvents.filter(e => new Date(e.created_at).toDateString() === today).length;

    // 显示真实数据更新时间
    const el = document.getElementById('lastUpdate');
    if (lastUpdated) {
        // lastUpdated 格式：'2026-03-10 23:40:06'
        const d = new Date(lastUpdated.replace(' ', 'T'));
        el.textContent = d.toLocaleString('zh-CN', {
            month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
        });
        el.title = '数据抓取时间：' + lastUpdated;
    } else {
        el.textContent = '—';
    }
}

// ── K 线图 + 成交量图 ─────────────────────────────────
let chartPrice = null, chartVol = null;

function renderKChart(sd) {
    if (chartPrice) { chartPrice.destroy(); chartPrice = null; }
    if (chartVol)   { chartVol.destroy();   chartVol   = null; }
    if (!sd) return;

    const UP   = '#e5483c';  // 阳线红（涨）
    const DOWN = '#22a06b';  // 阴线绿（跌）

    const candles = sd.dates.map((d, i) => ({
        x: d,
        o: sd.opens  ? sd.opens[i]  : sd.closes[i],
        h: sd.highs  ? sd.highs[i]  : sd.closes[i],
        l: sd.lows   ? sd.lows[i]   : sd.closes[i],
        c: sd.closes[i],
    }));

    const colors = candles.map(d => d.c >= d.o ? UP : DOWN);

    // ── 共用 tooltip ──────────────────────────────
    const sharedTooltip = {
        mode: 'index',
        intersect: false,
        callbacks: {
            title: items => candles[items[0].dataIndex].x,
            label: () => null,      // 去掉默认 label
            afterBody: items => {
                const i = items[0].dataIndex;
                const d = candles[i];
                const fv = v => v >= 1e8 ? (v/1e8).toFixed(1)+'亿'
                              : v >= 1e4 ? (v/1e4).toFixed(0)+'万' : v;
                return [
                    `开盘: ${d.o}`,
                    `最高: ${d.h}`,
                    `最低: ${d.l}`,
                    `收盘: ${d.c}`,
                    `成交量: ${fv(sd.volumes[i])}`,
                ];
            }
        },
        backgroundColor: 'rgba(30,30,50,0.85)',
        titleColor: '#fff',
        bodyColor:  '#ddd',
        padding: 10,
        displayColors: false,
    };

    // ── K 线图：影线 + 实体两个 dataset ──────────
    const pCtx = document.getElementById('priceChart').getContext('2d');
    chartPrice = new Chart(pCtx, {
        type: 'bar',
        data: {
            labels: sd.dates,
            datasets: [
                {   // 影线（高低），极细
                    label: '影线',
                    data: candles.map(d => [d.l, d.h]),
                    backgroundColor: colors,
                    barPercentage: 0.08,
                    categoryPercentage: 1.0,
                    order: 2,
                },
                {   // 实体（开收），宽柱
                    label: 'K线',
                    data: candles.map(d => [
                        Math.min(d.o, d.c),
                        Math.max(d.o, d.c) || Math.min(d.o, d.c) + 0.01  // 防止开收相同导致不显示
                    ]),
                    backgroundColor: colors,
                    barPercentage: 0.55,
                    categoryPercentage: 1.0,
                    order: 1,
                }
            ]
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
                x: { grid: { display: false }, ticks: { font: { size: 11 } } },
                y: {
                    grid: { color: '#f0f0f0' },
                    ticks: { font: { size: 11 } },
                    // 留出上下边距让影线不被截断
                    afterDataLimits: scale => {
                        const range = scale.max - scale.min;
                        scale.min -= range * 0.05;
                        scale.max += range * 0.05;
                    }
                }
            }
        }
    });

    // ── 成交量图 ──────────────────────────────────
    const vCtx = document.getElementById('volChart').getContext('2d');
    chartVol = new Chart(vCtx, {
        type: 'bar',
        data: {
            labels: sd.dates,
            datasets: [{
                data: sd.volumes,
                backgroundColor: colors.map(c => c + 'bb'),
                borderRadius: 2,
                barPercentage: 0.6,
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
                x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                y: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 10 },
                        callback: v => v >= 1e8 ? (v/1e8).toFixed(1)+'亿'
                                    : v >= 1e4  ? (v/1e4).toFixed(0)+'万' : v
                    }
                }
            }
        }
    });
}

// ── 弹窗 ─────────────────────────────────────────────
function openModal(card) {
    const ev  = JSON.parse(decodeURIComponent(card.dataset.event));
    const co  = COMPANIES[ev.company_id] || { name: ev.company_name, color: '#667eea' };
    const cat = CATEGORIES[ev.category]  || { name: ev.category, icon: '📌', color: '#888', bg: '#f5f5f5' };
    const sen = SENTIMENTS[ev.sentiment] || SENTIMENTS.neutral;

    const dateStr = new Date(ev.created_at).toLocaleDateString('zh-CN',
        { year:'numeric', month:'long', day:'numeric', hour:'2-digit', minute:'2-digit' });

    document.getElementById('modalCompanyBar').innerHTML = `
        <span style="background:${co.color};color:#fff;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600">${co.name}</span>
        <span style="background:${cat.bg};color:${cat.color};border:1px solid ${cat.color}60;padding:4px 14px;border-radius:20px;font-size:13px">${cat.icon} ${cat.name}</span>
        <span style="background:${sen.color}22;color:${sen.color};padding:4px 14px;border-radius:20px;font-size:13px">● ${sen.name}</span>`;

    document.getElementById('modalTitle').textContent   = ev.title;
    document.getElementById('modalContent').textContent = ev.content;
    document.getElementById('modalMeta').innerHTML = `
        <span>📅 ${dateStr}</span>
        <span>📰 ${ev.source}</span>
        <span>📊 重要性：${'⭐'.repeat(ev.importance)}</span>`;

    // 财报财务数据区块（只留表格）
    let financialHtml = '';
    if (ev.financials) {
        const f   = ev.financials;
        const div = f.divisor || 1e8;
        const fmt = v => (v == null) ? 'N/A' : (v / div).toFixed(2);
        const pct = v => (v == null) ? '—' : (v > 0 ? '+' : '') + v.toFixed(1) + '%';
        const upC = v => v == null ? '' : (v >= 0 ? 'color:#e5483c' : 'color:#22a06b');

        let epsRow = '';
        if (f.eps_estimate != null && f.eps_reported != null) {
            const beat    = f.eps_reported >= f.eps_estimate;
            const surpStr = f.eps_surprise != null
                ? `${f.eps_surprise > 0 ? '+' : ''}${f.eps_surprise.toFixed(1)}%` : '';
            epsRow = `
            <tr>
                <td>EPS 预期 / 实际</td>
                <td>${f.eps_estimate.toFixed(2)} / <b>${f.eps_reported.toFixed(2)}</b> ${f.currency}</td>
                <td>${beat
                    ? `<span style="color:#22a06b;font-weight:700">✅ 超预期 ${surpStr}</span>`
                    : `<span style="color:#e5483c;font-weight:700">❌ 不及预期 ${surpStr}</span>`}
                </td>
            </tr>`;
        }

        financialHtml = `
        <div class="stock-block" style="margin-bottom:16px">
            <h4>📋 ${f.quarter} 季报财务摘要（${f.unit}）</h4>
            <table class="fin-table">
                <thead><tr><th>指标</th><th>金额</th><th>同比 YoY</th></tr></thead>
                <tbody>
                    <tr><td>营收</td><td><b>${fmt(f.revenue)}</b></td><td style="${upC(f.rev_yoy)}">${pct(f.rev_yoy)}</td></tr>
                    <tr><td>净利润</td><td><b>${fmt(f.net_income)}</b></td><td style="${upC(f.ni_yoy)}">${pct(f.ni_yoy)}</td></tr>
                    <tr><td>毛利润</td><td>${fmt(f.gross_profit)}</td><td>${f.gross_margin != null ? f.gross_margin.toFixed(1)+'% 毛利率' : '—'}</td></tr>
                    <tr><td>经营利润</td><td>${fmt(f.op_income)}</td><td>—</td></tr>
                    <tr><td>EBITDA</td><td>${fmt(f.ebitda)}</td><td>—</td></tr>
                    <tr><td>EPS（基本）</td><td>${f.eps != null ? f.eps.toFixed(2)+' '+f.currency : 'N/A'}</td><td>—</td></tr>
                    ${epsRow}
                </tbody>
            </table>
        </div>`;
    }

    // 股价区块
    const sd = ev.stock_data;
    let stockHtml = '';
    if (!sd) {
        stockHtml = `<div class="stock-block">
            <h4>📈 发布后一周股价</h4>
            <p class="stock-unlisted">暂无股价数据（公司未上市或未来财报）</p>
        </div>`;
    } else {
        const up  = sd.change_pct >= 0;
        const cc  = up ? '#e5483c' : '#22a06b';
        const fv  = v => v>=1e8?(v/1e8).toFixed(1)+'亿':v>=1e4?(v/1e4).toFixed(1)+'万':v;
        const avg = Math.round(sd.volumes.reduce((a,b)=>a+b,0)/sd.volumes.length);
        stockHtml = `<div class="stock-block">
            <h4>📊 发布后一周 K 线（${sd.ticker}）</h4>
            <div class="stock-summary">
                <div class="stock-stat"><div class="val">${sd.open_price}</div><div class="lbl">起始收盘</div></div>
                <div class="stock-stat"><div class="val">${sd.close_price}</div><div class="lbl">一周收盘</div></div>
                <div class="stock-stat"><div class="val" style="color:${cc}">${up?'▲':'▼'} ${Math.abs(sd.change_pct)}%</div><div class="lbl">一周涨跌</div></div>
                <div class="stock-stat"><div class="val">${fv(avg)}</div><div class="lbl">日均成交量</div></div>
            </div>
            <div class="stock-summary" style="grid-template-columns:1fr 1fr;margin-bottom:10px">
                <div class="stock-stat"><div class="val" style="color:#e5483c">↑ ${sd.week_high}</div><div class="lbl">周最高</div></div>
                <div class="stock-stat"><div class="val" style="color:#22a06b">↓ ${sd.week_low}</div><div class="lbl">周最低</div></div>
            </div>
            <p style="font-size:11px;color:#aaa;margin-bottom:4px">▌红涨绿跌（A股/港股惯例）</p>
            <div class="chart-wrap"><canvas id="priceChart"></canvas></div>
            <p style="font-size:11px;color:#aaa;margin:6px 0 4px">成交量</p>
            <div class="chart-wrap-vol"><canvas id="volChart"></canvas></div>
        </div>`;
    }

    const isReal = ev.url && !ev.url.includes('example.com');
    document.getElementById('modalFooter').innerHTML = financialHtml + stockHtml +
        (isReal ? `<a href="${ev.url}" target="_blank" class="modal-source-link">🔗 查看原文报道</a>`
                : `<p style="color:#aaa;font-size:.9em">暂无原文链接 · 来源：${ev.source}</p>`);

    document.getElementById('modalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';

    if (sd) renderKChart(sd);
}

function closeModal(e) {
    if (e.target === document.getElementById('modalOverlay')) closeModalDirect();
}
function closeModalDirect() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModalDirect(); });

// ── 初始化 ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadEvents);
