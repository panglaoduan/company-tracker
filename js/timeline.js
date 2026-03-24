/**
 * timeline.js
 * 页面主交互逻辑：数据加载、筛选、渲染、弹窗
 * 依赖 config.js 和 kline.js
 */

let allEvents      = [];
let filteredEvents  = [];
let activeCategories = new Set(['all']);

// ── 数据加载 ──────────────────────────────────────────
async function loadEvents() {
    try {
        const ts = Date.now();
        const [evRes, metaRes] = await Promise.all([
            fetch('./events.json?' + ts),
            fetch('./meta.json?'   + ts)
        ]);
        if (!evRes.ok) throw new Error('数据文件加载失败');

        allEvents = await evRes.json();
        allEvents.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        filteredEvents = [...allEvents];
        renderEvents();

        if (metaRes.ok) {
            const meta = await metaRes.json();
            updateStats(meta.last_updated);
        } else {
            updateStats(null);
        }
    } catch (e) {
        console.error('加载失败', e);
        document.getElementById('timeline').innerHTML =
            '<div class="no-events"><p>数据加载失败，请刷新重试</p></div>';
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
    document.querySelectorAll('.cat-btn').forEach(btn => {
        const c = btn.dataset.cat;
        btn.classList.toggle('active', activeCategories.has(c));
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
        timeline.innerHTML = '<div class="no-events"><p>暂无匹配事件</p></div>';
        return;
    }

    let html = '';
    let lastYear = null;
    let lastMonth = null;
    let lastDateLabel = null;

    filteredEvents.forEach(ev => {
        const co  = COMPANIES[ev.company_id] || { name: ev.company_name, color: '#4e6ef2' };
        const cat = CATEGORIES[ev.category]  || { name: ev.category, icon: '', color: '#888', bg: '#f5f5f5' };
        const sen = SENTIMENTS[ev.sentiment] || SENTIMENTS.neutral;

        const d     = new Date(ev.created_at);
        const year  = d.getFullYear();
        const month = d.getMonth() + 1;
        const day   = d.getDate();
        const dateKey = `${year}-${month}-${day}`;

        // 年份标注
        if (year !== lastYear) {
            html += `<div class="timeline-year"><div class="timeline-year-badge">${year}</div></div>`;
            lastYear = year;
            lastMonth = null; // 强制重新输出月份
            lastDateLabel = null; // 年份切换后重置日期
        }

        // 月份标注
        let monthJustRendered = false;
        if (month !== lastMonth) {
            html += `<div class="timeline-month"><div class="timeline-month-badge">${month} 月</div></div>`;
            lastMonth = month;
            monthJustRendered = true;
        }

        // 日期标签：每个事件的圆点旁都显示日期（同一天的只在第一个事件显示）
        const showDateLabel = (dateKey !== lastDateLabel);
        lastDateLabel = dateKey;

        const dateLabelM = String(month).padStart(2, '0');
        const dateLabelD = String(day).padStart(2, '0');
        const enc        = encodeURIComponent(JSON.stringify(ev));

        // 股价变动徽章
        let priceBadge = '';
        if (ev.stock_data) {
            const chg = ev.stock_data.change_pct;
            const up  = chg >= 0;
            priceBadge = `<span class="price-badge ${up ? 'up' : 'down'}">${up ? '▲' : '▼'} ${Math.abs(chg).toFixed(2)}%</span>`;
        }

        // 社媒数据徽章
        let socialBadge = '';
        if (ev.category === 'social' && ev.social_data) {
            const sd = ev.social_data;
            const viewText = sd.view_text || (sd.views ? sd.views.toLocaleString() : '');
            socialBadge = `<span class="social-badge">👁 ${viewText}${sd.comment_count ? ' · 💬 ' + sd.comment_count.toLocaleString() : ''}</span>`;
        }

        // 事件内容预览
        let contentPreview = ev.content;
        if (ev.category === 'social') {
            const parts = ev.content.split('\n\n');
            const summary = parts.length >= 2 ? parts[1] : parts[0];
            contentPreview = summary.slice(0, 120) + (summary.length > 120 ? '...' : '');
        } else {
            contentPreview = ev.content.slice(0, 150) + (ev.content.length > 150 ? '...' : '');
        }

        const dateLabelHtml = showDateLabel
            ? `<div class="timeline-date-label">${dateLabelM}/${dateLabelD}</div>`
            : `<div class="timeline-date-label repeat">${dateLabelM}/${dateLabelD}</div>`;

        html += `
        <div class="event-card" style="border-left-color:${co.color};cursor:pointer"
             onclick="openModal(this)" data-event="${enc}">
            ${dateLabelHtml}
            <div class="event-header">
                <div class="event-tags">
                    <span class="tag-company" style="background:${co.color}">${co.name}</span>
                    <span class="tag-category" style="background:${cat.bg};color:${cat.color};border:1px solid ${cat.color}40">${cat.icon} ${cat.name}</span>
                    <span class="tag-sentiment" style="background:${sen.color}22;color:${sen.color}">● ${sen.name}</span>
                    ${priceBadge}${socialBadge}
                </div>
            </div>
            <h3 class="event-title">${ev.title}</h3>
            <p class="event-content">${contentPreview}</p>
            <div class="event-meta">
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

    // 统计追踪公司数
    const companySet = new Set(allEvents.map(e => e.company_id));
    document.getElementById('companyCount').textContent = companySet.size;

    // 统计今日更新
    const today = new Date().toDateString();
    document.getElementById('todayEvents').textContent =
        allEvents.filter(e => new Date(e.created_at).toDateString() === today).length;

    // 显示最后更新时间（北京时间）
    const el = document.getElementById('lastUpdate');
    if (lastUpdated) {
        const d = new Date(lastUpdated);
        el.textContent = d.toLocaleString('zh-CN', {
            month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
        });
        el.title = '数据抓取时间（北京时间）：' + lastUpdated;
    } else {
        el.textContent = '—';
    }
}

// ── 弹窗 ─────────────────────────────────────────────
function openModal(card) {
    const ev  = JSON.parse(decodeURIComponent(card.dataset.event));
    const co  = COMPANIES[ev.company_id] || { name: ev.company_name, color: '#4e6ef2' };
    const cat = CATEGORIES[ev.category]  || { name: ev.category, icon: '', color: '#888', bg: '#f5f5f5' };
    const sen = SENTIMENTS[ev.sentiment] || SENTIMENTS.neutral;

    const dateStr = new Date(ev.created_at).toLocaleDateString('zh-CN',
        { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });

    document.getElementById('modalCompanyBar').innerHTML = `
        <span style="background:${co.color};color:#fff;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600">${co.name}</span>
        <span style="background:${cat.bg};color:${cat.color};border:1px solid ${cat.color}60;padding:4px 14px;border-radius:20px;font-size:13px">${cat.icon} ${cat.name}</span>
        <span style="background:${sen.color}22;color:${sen.color};padding:4px 14px;border-radius:20px;font-size:13px">● ${sen.name}</span>`;

    document.getElementById('modalTitle').textContent = ev.title;

    const modalContentEl = document.getElementById('modalContent');
    if (ev.category === 'social') {
        modalContentEl.textContent = '';
        modalContentEl.style.display = 'none';
    } else {
        modalContentEl.textContent = ev.content;
        modalContentEl.style.display = '';
    }

    document.getElementById('modalMeta').innerHTML = `
        <span>📅 ${dateStr}</span>
        <span>📰 ${ev.source}</span>
        <span>📊 重要性：${'⭐'.repeat(ev.importance)}</span>`;

    // 财报财务数据区块
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
                    ? `<span style="color:#22a06b;font-weight:700">超预期 ${surpStr}</span>`
                    : `<span style="color:#e5483c;font-weight:700">不及预期 ${surpStr}</span>`}
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
                    <tr><td>毛利润</td><td>${fmt(f.gross_profit)}</td><td>${f.gross_margin != null ? f.gross_margin.toFixed(1) + '% 毛利率' : '—'}</td></tr>
                    <tr><td>经营利润</td><td>${fmt(f.op_income)}</td><td>—</td></tr>
                    <tr><td>EBITDA</td><td>${fmt(f.ebitda)}</td><td>—</td></tr>
                    <tr><td>EPS（基本）</td><td>${f.eps != null ? f.eps.toFixed(2) + ' ' + f.currency : 'N/A'}</td><td>—</td></tr>
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
            <h4>📈 事件后股价走势</h4>
            <p class="stock-unlisted">暂无股价数据（公司未上市或未来财报）</p>
        </div>`;
    } else {
        const up  = sd.change_pct >= 0;
        const cc  = up ? '#e5483c' : '#22a06b';
        const fv  = v => v >= 1e8 ? (v / 1e8).toFixed(1) + '亿' : v >= 1e4 ? (v / 1e4).toFixed(1) + '万' : v;
        const avg = Math.round(sd.volumes.reduce((a, b) => a + b, 0) / sd.volumes.length);
        const dayCount = sd.dates ? sd.dates.length : 0;
        stockHtml = `<div class="stock-block">
            <h4>📊 事件后 ${dayCount} 个交易日 K 线（${sd.ticker}）</h4>
            <div class="stock-summary">
                <div class="stock-stat"><div class="val">${sd.open_price}</div><div class="lbl">起始收盘</div></div>
                <div class="stock-stat"><div class="val">${sd.close_price}</div><div class="lbl">最新收盘</div></div>
                <div class="stock-stat"><div class="val" style="color:${cc}">${up ? '▲' : '▼'} ${Math.abs(sd.change_pct)}%</div><div class="lbl">区间涨跌</div></div>
                <div class="stock-stat"><div class="val">${fv(avg)}</div><div class="lbl">日均成交量</div></div>
            </div>
            <div class="stock-summary two-col">
                <div class="stock-stat"><div class="val" style="color:#e5483c">↑ ${sd.week_high}</div><div class="lbl">区间最高</div></div>
                <div class="stock-stat"><div class="val" style="color:#22a06b">↓ ${sd.week_low}</div><div class="lbl">区间最低</div></div>
            </div>
            <p class="chart-hint">▌红涨绿跌 · 下方柱为成交量 · 悬停查看详情</p>
            <div class="chart-wrap">
                <canvas id="priceChart"></canvas>
                <div id="kTooltip"></div>
            </div>
        </div>`;
    }

    // 社媒视频区块
    let socialHtml = '';
    if (ev.category === 'social' && ev.social_data) {
        const sd2 = ev.social_data;
        const viewText = sd2.view_text || (sd2.views ? sd2.views.toLocaleString() : '—');
        const dur   = sd2.duration ? `<span>⏱ 时长：${sd2.duration}</span>` : '';
        const likes = sd2.like_count ? `<span>👍 点赞：${sd2.like_count.toLocaleString()}</span>` : '';
        const cmts  = sd2.comment_count ? `<span>💬 评论：${sd2.comment_count.toLocaleString()}</span>` : '';

        const cnSummary = ev.content.split('\n\n')[1] || '';
        const aiSummary = ev.description || '';
        const summaryContent = aiSummary || cnSummary;
        const desc = summaryContent ? `
            <div class="social-summary-box">
                <b style="color:#e91e8c">${aiSummary ? '🤖 AI 投资观点总结' : '📝 内容总结'}</b><br>${summaryContent.replace(/\n/g, '<br>')}
            </div>` : '';

        socialHtml = `
        <div class="stock-block social-block">
            <h4 style="color:#e91e8c">📺 YouTube 视频数据</h4>
            <div class="social-stats">
                <span>📺 频道：<b>${sd2.channel || '—'}</b></span>
                <span>👁 播放：<b style="color:#e91e8c">${viewText}</b></span>
                ${likes}${cmts}${dur}
            </div>
            ${desc}
        </div>`;
    }

    const isReal = ev.url && !ev.url.includes('example.com');
    const linkHtml = isReal
        ? `<a href="${ev.url}" target="_blank" class="modal-source-link ${ev.category === 'social' ? 'social-link' : ''}">
              ${ev.category === 'social' ? '▶ 前往 YouTube 观看' : '🔗 查看原文报道'}
           </a>`
        : `<p class="no-link-hint">暂无原文链接 · 来源：${ev.source}</p>`;

    document.getElementById('modalFooter').innerHTML = financialHtml + socialHtml + stockHtml + linkHtml;

    document.getElementById('modalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';

    if (sd) {
        // 等待 DOM 渲染完成后再绘制 K 线
        requestAnimationFrame(() => renderKChart(sd));
    }
}

function closeModal(e) {
    if (e.target === document.getElementById('modalOverlay')) closeModalDirect();
}

function closeModalDirect() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.body.style.overflow = '';
}

// 键盘 ESC 关闭弹窗
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModalDirect();
});

// 初始化
document.addEventListener('DOMContentLoaded', loadEvents);
