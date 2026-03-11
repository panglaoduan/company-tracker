#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取：财报发布 + 单日波动 ≥2%
包含 OHLC 数据用于 K 线图
"""

import json, hashlib, yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

COMPANIES = [
    {'id': 'tesla',           'name': '特斯拉',      'ticker': 'TSLA',      'market': 'USD'},
    {'id': 'ast_spacemobile', 'name': 'AST 太空移动', 'ticker': 'ASTS',      'market': 'USD'},
    {'id': 'xiaomi',          'name': '小米集团',     'ticker': '1810.HK',   'market': 'HKD'},
    {'id': 'ganli_pharma',    'name': '甘李药业',     'ticker': '603087.SS', 'market': 'CNY'},
]

VOLATILITY_THRESHOLD = 0.02
LOOKBACK_DAYS        = 180   # 半年
MAX_VOL_PER_STOCK    = 20
DATA_FILE = Path(__file__).parent.parent / 'data' / 'events.json'


def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]

def fmt_vol(v):
    if v >= 1e8: return f"{v/1e8:.1f}亿"
    if v >= 1e4: return f"{v/1e4:.1f}万"
    return str(int(v))

def load_events():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_events(events):
    events.sort(key=lambda e: e['created_at'], reverse=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    meta_file = DATA_FILE.parent / 'meta.json'
    meta = {
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_events": len(events)
    }
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n💾 已保存，共 {len(events)} 条事件，更新时间：{meta['last_updated']}")

def build_stock_data(df, ticker):
    """从 DataFrame 构建含 OHLC 的 stock_data"""
    if df is None or df.empty:
        return None
    df = df.head(7)
    return {
        'ticker':      ticker,
        'open_price':  round(float(df['Close'].iloc[0]), 2),
        'close_price': round(float(df['Close'].iloc[-1]), 2),
        'week_high':   round(float(df['High'].max()), 2),
        'week_low':    round(float(df['Low'].min()), 2),
        'change_pct':  round((float(df['Close'].iloc[-1]) - float(df['Close'].iloc[0]))
                             / float(df['Close'].iloc[0]) * 100, 2),
        'dates':   [d.strftime('%m/%d') for d in df.index],
        'opens':   [round(float(v), 2) for v in df['Open']],
        'highs':   [round(float(v), 2) for v in df['High']],
        'lows':    [round(float(v), 2) for v in df['Low']],
        'closes':  [round(float(v), 2) for v in df['Close']],
        'volumes': [int(v) for v in df['Volume']],
    }


def fetch_earnings(company, df_full, existing_ids):
    """从 yfinance calendar 抓历史 + 未来财报日，并结合已有 df_full 提取 OHLC"""
    new_events = []
    ticker_obj = yf.Ticker(company['ticker'])

    try:
        cal = ticker_obj.calendar
        if not cal or 'Earnings Date' not in cal:
            print(f"  ⚠️  无财报日历")
            return []
        raw_dates = cal['Earnings Date']
        if not isinstance(raw_dates, list):
            raw_dates = [raw_dates]
    except Exception as e:
        print(f"  ❌ 财报日历失败：{e}")
        return []

    # 同时尝试拉历史财报
    try:
        hist_earnings = ticker_obj.earnings_dates  # 返回 DataFrame，index 是日期
        if hist_earnings is not None and not hist_earnings.empty:
            for d in hist_earnings.index:
                raw_dates.append(d.date() if hasattr(d, 'date') else d)
    except:
        pass

    seen = set()
    for raw_d in raw_dates:
        try:
            date_str = str(raw_d)[:10]
            if date_str in seen:
                continue
            seen.add(date_str)

            event_id = make_id(f"earnings_{company['id']}_{date_str}")
            if event_id in existing_ids:
                continue

            # 从 df_full 里切出该日起一周数据
            df_week = df_full[df_full.index.strftime('%Y-%m-%d') >= date_str].head(7) if df_full is not None and not df_full.empty else None
            stock_data = build_stock_data(df_week, company['ticker'])

            is_future = date_str > datetime.today().strftime('%Y-%m-%d')
            chg_str = f"，发布后一周股价 {stock_data['change_pct']:+.2f}%" if stock_data else ""
            content = (f"{company['name']}（{company['ticker']}）于 {date_str} {'预计' if is_future else ''}发布财报{chg_str}。"
                      f"请关注营收、利润及业绩指引等核心数据。")

            event = {
                'id':           event_id,
                'company_id':   company['id'],
                'company_name': company['name'],
                'title':        f"{'📅 预告：' if is_future else '📋 '}{company['name']} 财报发布（{date_str}）",
                'content':      content,
                'source':       'Yahoo Finance 财报日历',
                'url':          f"https://finance.yahoo.com/quote/{company['ticker']}/financials/",
                'category':     'earnings',
                'sentiment':    'neutral' if is_future else ('positive' if (stock_data and stock_data['change_pct'] >= 0) else 'negative'),
                'importance':   5,
                'created_at':   date_str + 'T21:00:00',
                'stock_data':   stock_data,
            }
            new_events.append(event)
            chg_disp = f"{stock_data['change_pct']:+.2f}%" if stock_data else "（未来）"
            print(f"  📋 财报：{date_str} {chg_disp}")

        except Exception as e:
            print(f"  ⚠️  {raw_d} 处理失败：{e}")

    return new_events


def fetch_volatility(company, df_full, existing_ids):
    """从 df_full 找单日波动 ≥2% 的日子"""
    new_events = []
    if df_full is None or df_full.empty:
        return []

    df_full = df_full.copy()
    df_full['pct'] = df_full['Close'].pct_change()
    big = df_full[df_full['pct'].abs() >= VOLATILITY_THRESHOLD].copy()
    big = big.reindex(big['pct'].abs().sort_values(ascending=False).index)
    big = big.head(MAX_VOL_PER_STOCK).sort_index(ascending=False)
    print(f"  ⚡ 找到 {len(big)} 条波动 ≥2%")

    for date, row in big.iterrows():
        date_str = date.strftime('%Y-%m-%d')
        chg      = round(float(row['pct']) * 100, 2)
        event_id = make_id(f"vol_{company['id']}_{date_str}_{chg:.2f}")
        if event_id in existing_ids:
            continue

        close_p = round(float(row['Close']), 2)
        vol     = int(row['Volume'])
        direction = '大涨' if chg > 0 else '大跌'
        icon      = '📈' if chg > 0 else '📉'

        df_week = df_full[df_full.index >= date].head(7)
        stock_data = build_stock_data(df_week, company['ticker'])

        event = {
            'id':           event_id,
            'company_id':   company['id'],
            'company_name': company['name'],
            'title':        f"{icon} {company['name']} 单日{direction} {chg:+.2f}%（{date_str}）",
            'content':      (f"{company['name']}（{company['ticker']}）于 {date_str} 出现单日{direction}，"
                            f"收盘价 {close_p}，涨跌幅 {chg:+.2f}%，当日成交量 {fmt_vol(vol)}。"
                            f"波动幅度超过 2% 预警阈值，请关注当日相关公告或市场消息。"),
            'source':       'Yahoo Finance 行情监控',
            'url':          f"https://finance.yahoo.com/quote/{company['ticker']}/history/",
            'category':     'volatility',
            'sentiment':    'positive' if chg > 0 else 'negative',
            'importance':   5 if abs(chg) >= 5 else 4,
            'created_at':   date_str + 'T16:00:00',
            'stock_data':   stock_data,
        }
        new_events.append(event)

    return new_events


def main():
    print("=" * 55)
    print("🚀 开始抓取财报 + 大波动事件（含 OHLC）")
    print("=" * 55)

    events       = load_events()
    existing_ids = {e['id'] for e in events}
    new_total    = 0
    end_date     = datetime.today()
    start_date   = end_date - timedelta(days=LOOKBACK_DAYS)

    for company in COMPANIES:
        print(f"\n🏢 {company['name']} ({company['ticker']})")

        # 一次性拉全量历史数据
        try:
            ticker_obj = yf.Ticker(company['ticker'])
            df_full = ticker_obj.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1d'
            )
            print(f"  ✅ 历史数据：{len(df_full)} 条")
        except Exception as e:
            print(f"  ❌ 拉取失败：{e}")
            df_full = None

        # 财报
        earned = fetch_earnings(company, df_full, existing_ids)
        events.extend(earned)
        existing_ids.update(e['id'] for e in earned)
        new_total += len(earned)

        # 大波动
        volatile = fetch_volatility(company, df_full, existing_ids)
        events.extend(volatile)
        existing_ids.update(e['id'] for e in volatile)
        new_total += len(volatile)

    save_events(events)
    print(f"\n✅ 新增 {new_total} 条，总计 {len(events)} 条")


if __name__ == '__main__':
    main()
