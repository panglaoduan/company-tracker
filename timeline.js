// 公司配置
const COMPANIES = {
    'tesla': { name: '特斯拉', color: '#e82127' },
    'spacex': { name: 'SpaceX', color: '#000000' },
    'ast_spacemobile': { name: 'AST 太空', color: '#0066cc' },
    'xiaomi': { name: '小米', color: '#ff6900' },
    'horizon_robotics': { name: '地平线', color: '#00aa00' },
    'ganli_pharma': { name: '甘李药业', color: '#cc00cc' }
};

const CATEGORIES = {
    'strategy':   { name: '经营战略', icon: '📈' },
    'executive':  { name: '高管动态', icon: '👔' },
    'competition':{ name: '行业竞争', icon: '⚔️' },
    'earnings':   { name: '财报发布', icon: '📋' },
    'volatility': { name: '股价异动', icon: '⚡' },
};

const SENTIMENTS = {
    'positive': { name: '正面', class: 'sentiment-positive' },
    'negative': { name: '负面', class: 'sentiment-negative' },
    'neutral': { name: '中性', class: 'sentiment-neutral' }
};

let allEvents = [];
let filteredEvents = [];

// 加载事件数据
async function loadEvents() {
    try {
        // 尝试加载本地 JSON 文件
        const response = await fetch('./events.json');
        if (!response.ok) {
            throw new Error('数据文件不存在');
        }
        allEvents = await response.json();
        
        // 按时间倒序排序
        allEvents.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        filteredEvents = [...allEvents];
        renderEvents();
        updateStats();
        
    } catch (error) {
        console.error('加载数据失败:', error);
        // 使用示例数据
        loadDemoData();
    }
}

// 加载示例数据（演示用）
function loadDemoData() {
    allEvents = [
        {
            id: '1',
            company_id: 'xiaomi',
            company_name: '小米集团',
            title: '小米汽车 SU7 交付突破 10 万辆，雷军宣布 2024 年目标翻倍',
            content: '雷军在社交媒体上宣布，小米汽车 SU7 交付量突破 10 万辆，创下新能源汽车行业最快交付记录。同时宣布 2024 年交付目标提升至 20 万辆，并计划在欧洲市场推出首款车型。',
            source: '新浪财经',
            url: 'https://example.com',
            category: 'strategy',
            sentiment: 'positive',
            importance: 5,
            created_at: new Date().toISOString()
        },
        {
            id: '2',
            company_id: 'tesla',
            company_name: '特斯拉',
            title: 'Elon Musk 宣布 Tesla Bot  Optimus 将于 2024 年底量产',
            content: '在 Tesla AI Day 上，Elon Musk 展示了 Optimus 人形机器人的最新进展，表示将在 2024 年底开始小批量生产，主要用于特斯拉工厂内部。长期目标年产 100 万台。',
            source: 'TechCrunch',
            url: 'https://example.com',
            category: 'strategy',
            sentiment: 'positive',
            importance: 5,
            created_at: new Date(Date.now() - 86400000).toISOString()
        },
        {
            id: '3',
            company_id: 'spacex',
            company_name: 'SpaceX',
            title: 'SpaceX Starship 第三次试飞成功，Elon Musk 称 2025 年实现载人登月',
            content: 'SpaceX 的 Starship 重型火箭成功完成第三次试飞，进入预定轨道并安全返回。Elon Musk 表示，按照目前进展，2025 年实现载人登月目标可期。',
            source: 'SpaceNews',
            url: 'https://example.com',
            category: 'strategy',
            sentiment: 'positive',
            importance: 5,
            created_at: new Date(Date.now() - 172800000).toISOString()
        },
        {
            id: '4',
            company_id: 'horizon_robotics',
            company_name: '地平线机器人',
            title: '地平线机器人递交港股 IPO 申请，余凯：将加大 AI 芯片研发',
            content: '地平线机器人正式向港交所递交 IPO 申请，拟募资 10 亿美元。创始人余凯表示，上市后将加大高阶自动驾驶芯片和具身智能机器人的研发投入。',
            source: '36 氪',
            url: 'https://example.com',
            category: 'executive',
            sentiment: 'positive',
            importance: 4,
            created_at: new Date(Date.now() - 259200000).toISOString()
        },
        {
            id: '5',
            company_id: 'ganli_pharma',
            company_name: '甘李药业',
            title: '甘李药业新一代胰岛素类似物获批，甘忠如：将大幅降低患者负担',
            content: '甘李药业宣布其新一代超速效胰岛素类似物获得国家药监局批准上市。创始人甘忠如表示，新产品将大幅降低糖尿病患者用药负担，预计年销售额可达 20 亿元。',
            source: '医药魔方',
            url: 'https://example.com',
            category: 'strategy',
            sentiment: 'positive',
            importance: 4,
            created_at: new Date(Date.now() - 345600000).toISOString()
        },
        {
            id: '6',
            company_id: 'ast_spacemobile',
            company_name: 'AST 太空移动',
            title: 'AST SpaceMobile 与 Verizon 达成合作协议，股价大涨 25%',
            content: 'AST SpaceMobile 宣布与美国最大运营商 Verizon 达成独家合作协议，将共同开发卫星直连手机服务。消息公布后股价大涨 25%，CEO Abel Avellan 称这是"历史性时刻"。',
            source: 'Reuters',
            url: 'https://example.com',
            category: 'competition',
            sentiment: 'positive',
            importance: 5,
            created_at: new Date(Date.now() - 432000000).toISOString()
        }
    ];
    
    filteredEvents = [...allEvents];
    renderEvents();
    updateStats();
}

// 渲染事件列表（带年月分隔标记）
function renderEvents() {
    const timeline = document.getElementById('timeline');

    if (filteredEvents.length === 0) {
        timeline.innerHTML = '<div class="no-events"><p>📭 暂无匹配的事件</p></div>';
        return;
    }

    let html = '';
    let lastYearMonth = null;

    filteredEvents.forEach(event => {
        const company  = COMPANIES[event.company_id] || { name: event.company_name, color: '#667eea' };
        const category = CATEGORIES[event.category]  || { name: event.category, icon: '📌' };
        const sentiment= SENTIMENTS[event.sentiment] || { name: event.sentiment, class: 'sentiment-neutral' };

        const date = new Date(event.created_at);
        const year  = date.getFullYear();
        const month = date.getMonth() + 1;
        const yearMonth = `${year}-${String(month).padStart(2, '0')}`;

        // 如果年月发生变化，插入分隔标记
        if (yearMonth !== lastYearMonth) {
            // 年份变化时加一个更显眼的年份标记
            const isNewYear = lastYearMonth && year !== parseInt(lastYearMonth.split('-')[0]);
            if (isNewYear || lastYearMonth === null) {
                html += `
                <div class="timeline-year">
                    <div class="timeline-year-badge">${year}</div>
                </div>`;
            }
            html += `
            <div class="timeline-month">
                <div class="timeline-month-badge">${month} 月</div>
            </div>`;
            lastYearMonth = yearMonth;
        }

        const dateStr = date.toLocaleDateString('zh-CN', {
            month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
        });

        // 把事件数据编码存到 data 属性，供弹窗读取
        const dataAttr = encodeURIComponent(JSON.stringify(event));

        html += `
        <div class="event-card" style="border-left-color: ${company.color}; cursor:pointer;"
             onclick="openModal(this)" data-event="${dataAttr}">
            <div class="event-header">
                <div>
                    <span class="event-company" style="background: ${company.color}">${company.name}</span>
                    <span class="event-category">${category.icon} ${category.name}</span>
                </div>
            </div>
            <h3 class="event-title">${event.title}</h3>
            <p class="event-content" style="display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;">${event.content}</p>
            <div class="event-meta" style="margin-top:12px;">
                <span>📅 ${dateStr}</span>
                <span>📰 ${event.source}</span>
                <span class="${sentiment.class}">● ${sentiment.name}</span>
                <span>📊 ${'⭐'.repeat(event.importance)}</span>
            </div>
            <span style="display:inline-block;margin-top:10px;color:#667eea;font-size:0.9em;">点击查看详情 →</span>
        </div>`;
    });

    timeline.innerHTML = html;
}

// 更新统计信息
function updateStats() {
    document.getElementById('totalEvents').textContent = allEvents.length;
    
    // 今日事件
    const today = new Date().toDateString();
    const todayCount = allEvents.filter(e => new Date(e.created_at).toDateString() === today).length;
    document.getElementById('todayEvents').textContent = todayCount;
    
    // 最后更新
    if (allEvents.length > 0) {
        const lastUpdate = new Date(allEvents[0].created_at);
        document.getElementById('lastUpdate').textContent = lastUpdate.toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit'});
    }
}

// 筛选事件
function filterEvents() {
    const companyFilter = document.getElementById('companyFilter').value;
    const categoryFilter = document.getElementById('categoryFilter').value;
    const searchText = document.getElementById('searchInput').value.toLowerCase();
    
    filteredEvents = allEvents.filter(event => {
        // 公司筛选
        if (companyFilter !== 'all' && event.company_id !== companyFilter) {
            return false;
        }
        
        // 分类筛选
        if (categoryFilter !== 'all' && event.category !== categoryFilter) {
            return false;
        }
        
        // 搜索
        if (searchText) {
            const searchContent = (event.title + event.content).toLowerCase();
            if (!searchContent.includes(searchText)) {
                return false;
            }
        }
        
        return true;
    });
    
    renderEvents();
}

// 当前图表实例（避免重复创建）
let priceChartInst = null;
let volChartInst   = null;

// 打开详情弹窗
function openModal(card) {
    const event = JSON.parse(decodeURIComponent(card.dataset.event));
    const company  = COMPANIES[event.company_id] || { name: event.company_name, color: '#667eea' };
    const category = CATEGORIES[event.category]  || { name: event.category, icon: '📌' };
    const sentiment= SENTIMENTS[event.sentiment] || { name: '中性', class: 'sentiment-neutral' };

    const date = new Date(event.created_at);
    const dateStr = date.toLocaleDateString('zh-CN', {
        year: 'numeric', month: 'long', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });

    // 公司 + 分类标签
    document.getElementById('modalCompanyBar').innerHTML = `
        <span style="background:${company.color};color:white;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600;">${company.name}</span>
        <span style="background:#f0f0f0;color:#555;padding:4px 14px;border-radius:20px;font-size:13px;">${category.icon} ${category.name}</span>
        <span class="${sentiment.class}" style="padding:4px 14px;border-radius:20px;font-size:13px;color:white;">● ${sentiment.name}</span>
    `;

    document.getElementById('modalTitle').textContent = event.title;
    document.getElementById('modalMeta').innerHTML = `
        <span>📅 ${dateStr}</span>
        <span>📰 来源：${event.source}</span>
        <span>📊 重要性：${'⭐'.repeat(event.importance)}</span>
    `;
    document.getElementById('modalContent').textContent = event.content;

    // ── 股价区块 ──
    const sd = event.stock_data;
    let stockHtml = '';
    if (!sd) {
        stockHtml = `<div class="stock-block">
            <h4>📈 新闻发布后一周股价</h4>
            <p class="stock-unlisted">该公司尚未上市，暂无股价数据</p>
        </div>`;
    } else {
        const upDown    = sd.change_pct >= 0;
        const changeClass = upDown ? 'stock-change-up' : 'stock-change-down';
        const changeIcon  = upDown ? '▲' : '▼';
        const fmtVol = v => v >= 1e8 ? (v/1e8).toFixed(1)+'亿'
                         : v >= 1e4  ? (v/1e4).toFixed(1)+'万' : v;
        const avgVol = Math.round(sd.volumes.reduce((a,b)=>a+b,0)/sd.volumes.length);

        stockHtml = `<div class="stock-block">
            <h4>📈 新闻发布后一周股价走势（${sd.ticker}）</h4>
            <div class="stock-summary">
                <div class="stock-stat">
                    <div class="val">${sd.open_price}</div>
                    <div class="lbl">新闻日收盘</div>
                </div>
                <div class="stock-stat">
                    <div class="val">${sd.close_price}</div>
                    <div class="lbl">一周后收盘</div>
                </div>
                <div class="stock-stat">
                    <div class="val ${changeClass}">${changeIcon} ${Math.abs(sd.change_pct)}%</div>
                    <div class="lbl">一周涨跌幅</div>
                </div>
                <div class="stock-stat">
                    <div class="val">${fmtVol(avgVol)}</div>
                    <div class="lbl">日均成交量</div>
                </div>
            </div>
            <div class="stock-summary" style="grid-template-columns:1fr 1fr;margin-bottom:12px;">
                <div class="stock-stat">
                    <div class="val" style="color:#e5483c;">↑ ${sd.week_high}</div>
                    <div class="lbl">周最高</div>
                </div>
                <div class="stock-stat">
                    <div class="val" style="color:#22a06b;">↓ ${sd.week_low}</div>
                    <div class="lbl">周最低</div>
                </div>
            </div>
            <div class="chart-wrap"><canvas id="priceChart"></canvas></div>
            <div class="chart-wrap-vol"><canvas id="volChart"></canvas></div>
        </div>`;
    }

    // 来源链接
    const isRealUrl = event.url && !event.url.includes('example.com');
    const footerHtml = isRealUrl
        ? `<a href="${event.url}" target="_blank" class="modal-source-link">🔗 查看原文报道</a>`
        : `<p style="color:#aaa;font-size:0.9em;">暂无原文链接，数据来源：${event.source}</p>`;

    document.getElementById('modalFooter').innerHTML = stockHtml + footerHtml;

    document.getElementById('modalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';

    // 渲染图表（需要 DOM 已插入）
    if (sd) {
        if (priceChartInst) priceChartInst.destroy();
        if (volChartInst)   volChartInst.destroy();

        const upColor = sd.change_pct >= 0 ? '#22a06b' : '#e5483c';

        priceChartInst = new Chart(document.getElementById('priceChart'), {
            type: 'line',
            data: {
                labels: sd.dates,
                datasets: [{
                    data: sd.closes,
                    borderColor: upColor,
                    backgroundColor: upColor + '18',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: upColor,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 11 } } },
                    y: { grid: { color: '#f0f0f0' }, ticks: { font: { size: 11 } } }
                },
                animation: { duration: 400 }
            }
        });

        volChartInst = new Chart(document.getElementById('volChart'), {
            type: 'bar',
            data: {
                labels: sd.dates,
                datasets: [{
                    data: sd.volumes,
                    backgroundColor: sd.closes.map((c, i) =>
                        i === 0 ? '#aaa' : (c >= sd.closes[i-1] ? '#22a06b88' : '#e5483c88')
                    ),
                    borderRadius: 3
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                    y: { grid: { display: false }, ticks: {
                        font: { size: 10 },
                        callback: v => v >= 1e8 ? (v/1e8).toFixed(0)+'亿'
                                    : v >= 1e4  ? (v/1e4).toFixed(0)+'万' : v
                    }}
                },
                animation: { duration: 400 }
            }
        });
    }
}

// 点击遮罩关闭
function closeModal(e) {
    if (e.target === document.getElementById('modalOverlay')) {
        closeModalDirect();
    }
}

function closeModalDirect() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.body.style.overflow = '';
}

// ESC 键关闭
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModalDirect();
});

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', loadEvents);
