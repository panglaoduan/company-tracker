/**
 * kline.js
 * K 线图 + 成交量渲染模块（Canvas 手绘）
 * 雪球风格：深色背景、红涨绿跌、十字光标、专业 Tooltip
 */

function renderKChart(sd) {
    if (!sd || !sd.dates || sd.dates.length === 0) return;

    // ── 配色（雪球深色风格） ──
    const THEME = {
        bg:         '#1d1f2b',
        gridLine:   'rgba(255,255,255,0.06)',
        gridText:   '#6b7280',
        axisLine:   'rgba(255,255,255,0.12)',
        upColor:    '#f5475b',    // 阳线红
        upFill:     '#f5475b',
        downColor:  '#2dc08e',    // 阴线绿
        downFill:   '#2dc08e',
        volUp:      'rgba(245,71,91,0.35)',
        volDown:    'rgba(45,192,142,0.35)',
        crosshair:  'rgba(255,255,255,0.25)',
        maLine5:    '#f5c842',    // MA5 黄色
        maLine10:   '#6b8df7',    // MA10 蓝色
        tooltipBg:  'rgba(30,33,48,0.96)',
        tooltipBorder: 'rgba(255,255,255,0.12)',
    };

    const candles = sd.dates.map((d, i) => ({
        label: d,
        o: sd.opens  ? sd.opens[i]  : sd.closes[i],
        h: sd.highs  ? sd.highs[i]  : sd.closes[i],
        l: sd.lows   ? sd.lows[i]   : sd.closes[i],
        c: sd.closes[i],
        v: sd.volumes ? sd.volumes[i] : 0,
    }));

    const n = candles.length;
    if (n === 0) return;

    // 计算 MA
    function calcMA(data, period) {
        return data.map((_, i) => {
            if (i < period - 1) return null;
            let sum = 0;
            for (let j = i - period + 1; j <= i; j++) sum += data[j].c;
            return sum / period;
        });
    }
    const ma5  = n >= 5  ? calcMA(candles, 5)  : [];
    const ma10 = n >= 10 ? calcMA(candles, 10) : [];

    const maxVol = Math.max(...candles.map(d => d.v), 1);

    // ── Canvas 设置 ──
    const canvas = document.getElementById('priceChart');
    if (!canvas) return;

    const dpr    = window.devicePixelRatio || 1;
    const W      = canvas.offsetWidth  || 600;
    const H      = canvas.offsetHeight || 260;
    canvas.width  = W * dpr;
    canvas.height = H * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    // ── 布局参数 ──
    const PAD_L = 56, PAD_R = 14, PAD_T = 20, PAD_B = 24;
    const PRICE_RATIO = 0.65;  // 价格区占比
    const VOL_GAP = 8;         // 价格区与成交量区间距

    const chartW = W - PAD_L - PAD_R;
    const priceH = (H - PAD_T - PAD_B) * PRICE_RATIO;
    const volTop = PAD_T + priceH + VOL_GAP;
    const volH   = H - PAD_B - volTop;
    const slotW  = chartW / n;
    const bodyW  = Math.max(Math.min(slotW * 0.6, 20), 4);
    const wickW  = Math.max(Math.min(slotW * 0.1, 2), 1);

    // Y 轴：价格范围
    const allH = candles.map(d => d.h);
    const allL = candles.map(d => d.l);
    let yMax = Math.max(...allH);
    let yMin = Math.min(...allL);
    const yPad = (yMax - yMin) * 0.08 || yMax * 0.02 || 1;
    yMax += yPad;
    yMin -= yPad;
    const yRange = yMax - yMin || 1;

    const toY = v => PAD_T + priceH - (v - yMin) / yRange * priceH;

    // ── 背景 ──
    ctx.fillStyle = THEME.bg;
    ctx.fillRect(0, 0, W, H);

    // ── 网格线（水平） ──
    ctx.strokeStyle = THEME.gridLine;
    ctx.lineWidth   = 1;
    ctx.setLineDash([]);
    const gridCount = 4;
    for (let t = 0; t <= gridCount; t++) {
        const v = yMin + yRange * (t / gridCount);
        const y = toY(v);
        ctx.beginPath();
        ctx.moveTo(PAD_L, y);
        ctx.lineTo(W - PAD_R, y);
        ctx.stroke();

        // 价格标签
        ctx.fillStyle = THEME.gridText;
        ctx.font      = '11px -apple-system, "Helvetica Neue", sans-serif';
        ctx.textAlign  = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(v.toFixed(2), PAD_L - 6, y);
    }

    // 成交量区分隔线
    ctx.strokeStyle = THEME.axisLine;
    ctx.beginPath();
    ctx.moveTo(PAD_L, volTop - VOL_GAP / 2);
    ctx.lineTo(W - PAD_R, volTop - VOL_GAP / 2);
    ctx.stroke();

    // ── 画每根 K 线 ──
    candles.forEach((d, i) => {
        const cx   = PAD_L + slotW * i + slotW / 2;
        const isUp = d.c >= d.o;
        const color = isUp ? THEME.upColor : THEME.downColor;

        // 影线（上下影线）
        ctx.strokeStyle = color;
        ctx.lineWidth   = wickW;
        ctx.beginPath();
        ctx.moveTo(cx, toY(d.h));
        ctx.lineTo(cx, toY(d.l));
        ctx.stroke();

        // 实体
        const bodyTop = toY(Math.max(d.o, d.c));
        const bodyBot = toY(Math.min(d.o, d.c));
        const bodyHeight = Math.max(bodyBot - bodyTop, 1.5);

        if (isUp) {
            // 阳线：实心红色
            ctx.fillStyle = THEME.upFill;
            ctx.fillRect(cx - bodyW / 2, bodyTop, bodyW, bodyHeight);
        } else {
            // 阴线：实心绿色
            ctx.fillStyle = THEME.downFill;
            ctx.fillRect(cx - bodyW / 2, bodyTop, bodyW, bodyHeight);
        }

        // 成交量柱
        const volRatio = d.v / maxVol;
        const volBarH = volH * volRatio * 0.9;
        ctx.fillStyle = isUp ? THEME.volUp : THEME.volDown;
        ctx.fillRect(cx - bodyW / 2, volTop + volH - volBarH, bodyW, volBarH);
    });

    // ── MA 均线 ──
    function drawMA(maData, color) {
        if (!maData || maData.length === 0) return;
        ctx.strokeStyle = color;
        ctx.lineWidth   = 1.5;
        ctx.setLineDash([]);
        ctx.beginPath();
        let started = false;
        maData.forEach((v, i) => {
            if (v === null) return;
            const x = PAD_L + slotW * i + slotW / 2;
            const y = toY(v);
            if (!started) { ctx.moveTo(x, y); started = true; }
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
    }
    drawMA(ma5, THEME.maLine5);
    drawMA(ma10, THEME.maLine10);

    // ── MA 图例 ──
    ctx.font = '10px -apple-system, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    if (ma5.length > 0) {
        const lastMA5 = ma5.filter(v => v !== null).pop();
        if (lastMA5 !== undefined) {
            ctx.fillStyle = THEME.maLine5;
            ctx.fillText(`MA5: ${lastMA5.toFixed(2)}`, PAD_L + 4, PAD_T + 2);
        }
    }
    if (ma10.length > 0) {
        const lastMA10 = ma10.filter(v => v !== null).pop();
        if (lastMA10 !== undefined) {
            ctx.fillStyle = THEME.maLine10;
            ctx.fillText(`MA10: ${lastMA10.toFixed(2)}`, PAD_L + 100, PAD_T + 2);
        }
    }

    // ── X 轴日期标签 ──
    ctx.fillStyle = THEME.gridText;
    ctx.font      = '10px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    // 智能间隔：根据数据量决定显示哪些日期
    const labelInterval = n <= 5 ? 1 : n <= 10 ? 2 : 3;
    candles.forEach((d, i) => {
        if (i % labelInterval === 0 || i === n - 1) {
            const cx = PAD_L + slotW * i + slotW / 2;
            ctx.fillText(d.label, cx, H - PAD_B + 6);
        }
    });

    // ── 成交量 Y 轴标签 ──
    ctx.fillStyle = THEME.gridText;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.font = '9px -apple-system, sans-serif';
    const fv = v => v >= 1e8 ? (v / 1e8).toFixed(1) + '亿' : v >= 1e4 ? (v / 1e4).toFixed(0) + '万' : v.toString();
    ctx.fillText('量 ' + fv(maxVol), PAD_L + 4, volTop + 2);

    // ── Tooltip + 十字光标 ──
    const tip = document.getElementById('kTooltip');
    if (!tip) return;

    // 创建叠加 canvas 用于十字光标（避免重绘主图）
    let overlayCanvas = canvas.parentElement.querySelector('.kline-overlay');
    if (!overlayCanvas) {
        overlayCanvas = document.createElement('canvas');
        overlayCanvas.className = 'kline-overlay';
        overlayCanvas.style.cssText = 'position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;';
        canvas.parentElement.appendChild(overlayCanvas);
    }
    overlayCanvas.width  = W * dpr;
    overlayCanvas.height = H * dpr;
    const oCtx = overlayCanvas.getContext('2d');
    oCtx.scale(dpr, dpr);

    canvas.onmousemove = e => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = W / rect.width;
        const scaleY = H / rect.height;
        const mx = (e.clientX - rect.left) * scaleX;
        const my = (e.clientY - rect.top) * scaleY;
        const idx = Math.floor((mx - PAD_L) / slotW);

        if (idx < 0 || idx >= n) {
            tip.style.display = 'none';
            oCtx.clearRect(0, 0, W, H);
            return;
        }

        const d = candles[idx];
        const isUp = d.c >= d.o;
        const chg = d.o > 0 ? ((d.c - d.o) / d.o * 100).toFixed(2) : '0.00';
        const chgColor = isUp ? '#f5475b' : '#2dc08e';
        const cx = PAD_L + slotW * idx + slotW / 2;

        // 十字光标
        oCtx.clearRect(0, 0, W, H);
        oCtx.strokeStyle = THEME.crosshair;
        oCtx.lineWidth = 1;
        oCtx.setLineDash([4, 3]);
        // 垂直线
        oCtx.beginPath();
        oCtx.moveTo(cx, PAD_T);
        oCtx.lineTo(cx, H - PAD_B);
        oCtx.stroke();
        // 水平线
        oCtx.beginPath();
        oCtx.moveTo(PAD_L, my);
        oCtx.lineTo(W - PAD_R, my);
        oCtx.stroke();
        oCtx.setLineDash([]);

        // 价格标签（在左侧）
        if (my >= PAD_T && my <= PAD_T + priceH) {
            const priceAtCursor = yMax - (my - PAD_T) / priceH * yRange;
            oCtx.fillStyle = '#3b4054';
            const labelW = 52, labelH = 18;
            oCtx.fillRect(PAD_L - labelW - 4, my - labelH / 2, labelW, labelH);
            oCtx.fillStyle = '#e0e0e0';
            oCtx.font = '10px -apple-system, sans-serif';
            oCtx.textAlign = 'right';
            oCtx.textBaseline = 'middle';
            oCtx.fillText(priceAtCursor.toFixed(2), PAD_L - 8, my);
        }

        // Tooltip
        tip.innerHTML = `
            <div style="margin-bottom:4px;font-weight:600;color:#fff;font-size:13px">${d.label}</div>
            <table style="border-spacing:0;font-size:12px">
                <tr><td style="color:#9ca3af;padding-right:12px">开盘</td><td style="color:#e0e0e0;text-align:right">${d.o.toFixed(2)}</td></tr>
                <tr><td style="color:#9ca3af;padding-right:12px">最高</td><td style="color:#f5475b;text-align:right">${d.h.toFixed(2)}</td></tr>
                <tr><td style="color:#9ca3af;padding-right:12px">最低</td><td style="color:#2dc08e;text-align:right">${d.l.toFixed(2)}</td></tr>
                <tr><td style="color:#9ca3af;padding-right:12px">收盘</td><td style="color:${chgColor};text-align:right;font-weight:600">${d.c.toFixed(2)}</td></tr>
                <tr><td style="color:#9ca3af;padding-right:12px">涨跌</td><td style="color:${chgColor};text-align:right;font-weight:600">${isUp ? '+' : ''}${chg}%</td></tr>
                <tr><td style="color:#9ca3af;padding-right:12px">成交量</td><td style="color:#e0e0e0;text-align:right">${fv(d.v)}</td></tr>
            </table>`;
        tip.style.display = 'block';

        // Tooltip 位置：避免超出容器
        const tipW = 160;
        let tipX = e.clientX - rect.left + 16;
        if (tipX + tipW > rect.width) tipX = e.clientX - rect.left - tipW - 16;
        tip.style.left = Math.max(0, tipX) + 'px';
        tip.style.top  = Math.max(10, e.clientY - rect.top - 60) + 'px';
    };

    canvas.onmouseleave = () => {
        tip.style.display = 'none';
        oCtx.clearRect(0, 0, W, H);
    };
}
