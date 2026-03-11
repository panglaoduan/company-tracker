#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复所有事件的 stock_data：
1. 补全缺少 opens/highs/lows 的数据
2. 严格只取 5 个交易日
"""

import json, yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / 'data' / 'events.json'

# 公司 → ticker 映射
TICKER_MAP = {
    'tesla':           'TSLA',
    'ast_spacemobile': 'ASTS',
    'xiaomi':          '1810.HK',
    'ganli_pharma':    '603087.SS',
    'spacex':          None,
    'horizon_robotics':None,
}


def fetch_5day_ohlcv(ticker_symbol: str, start_date: str):
    """拉取从 start_date 起 5 个交易日的 OHLCV 数据"""
    end = (datetime.fromisoformat(start_date) + timedelta(days=14)).strftime('%Y-%m-%d')
    try:
        df = yf.Ticker(ticker_symbol).history(start=start_date, end=end, interval='1d')
        if df.empty:
            return None
        df = df.head(5)  # 严格取 5 个交易日
        return {
            'ticker':      ticker_symbol,
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
    except Exception as e:
        print(f"    ❌ {ticker_symbol} @ {start_date} 失败：{e}")
        return None


def main():
    events = json.loads(DATA_FILE.read_text())

    print(f"总事件：{len(events)} 条")

    fixed = 0
    for ev in events:
        company_id = ev.get('company_id')
        ticker = TICKER_MAP.get(company_id)

        if not ticker:
            ev['stock_data'] = None
            continue

        sd = ev.get('stock_data')
        needs_fix = (
            sd is None or
            sd.get('opens') is None or
            len(sd.get('dates', [])) < 5
        )

        if not needs_fix:
            continue

        date_str = ev['created_at'][:10]
        print(f"  修复 {ev['company_name']} @ {date_str} ...", end=' ')

        new_sd = fetch_5day_ohlcv(ticker, date_str)
        if new_sd:
            ev['stock_data'] = new_sd
            print(f"✅ {len(new_sd['dates'])} 天  {new_sd['change_pct']:+.2f}%")
            fixed += 1
        else:
            print("⚠️  无数据")

    # 保存
    DATA_FILE.write_text(json.dumps(events, ensure_ascii=False, indent=2))

    # 更新 meta
    meta_file = DATA_FILE.parent / 'meta.json'
    import json as _j
    meta = {
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_events": len(events)
    }
    meta_file.write_text(_j.dumps(meta, ensure_ascii=False, indent=2))

    print(f"\n✅ 修复了 {fixed} 条，共 {len(events)} 条")


if __name__ == '__main__':
    main()
