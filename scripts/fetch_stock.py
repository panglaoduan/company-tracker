#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为每条事件抓取新闻发布后一周内的股价数据
使用 Yahoo Finance（免费，无需 API Key）
"""

import json
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

# 公司 → 股票代码映射
STOCK_MAP = {
    'tesla':            'TSLA',
    'spacex':           None,        # 未上市，无股价
    'ast_spacemobile':  'ASTS',
    'xiaomi':           '1810.HK',
    'horizon_robotics': None,        # 未上市
    'ganli_pharma':     '603087.SS', # A 股后缀用 .SS
}

def fetch_week_price(ticker_symbol: str, event_date: str):
    """
    抓取事件日期后一周的日线数据
    返回: { dates, closes, volumes, change_pct, open_price, week_high, week_low }
    """
    start = datetime.fromisoformat(event_date).date()
    end   = start + timedelta(days=10)  # 多取几天，避免节假日不够 5 个交易日

    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(start=start.isoformat(), end=end.isoformat(), interval='1d')

        if df.empty:
            print(f"  ⚠️  {ticker_symbol} 无数据（可能节假日或退市）")
            return None

        df = df.head(7)  # 最多取 7 个交易日

        open_price  = float(df['Close'].iloc[0])
        close_price = float(df['Close'].iloc[-1])
        change_pct  = round((close_price - open_price) / open_price * 100, 2)

        result = {
            'ticker':      ticker_symbol,
            'open_price':  round(open_price, 2),
            'close_price': round(close_price, 2),
            'week_high':   round(float(df['High'].max()), 2),
            'week_low':    round(float(df['Low'].min()), 2),
            'change_pct':  change_pct,
            'dates':       [d.strftime('%m/%d') for d in df.index],
            'closes':      [round(float(v), 2) for v in df['Close']],
            'volumes':     [int(v) for v in df['Volume']],
        }

        trend = '📈' if change_pct >= 0 else '📉'
        print(f"  ✅ {ticker_symbol}: {open_price:.2f} → {close_price:.2f} ({change_pct:+.2f}%) {trend}")
        return result

    except Exception as e:
        print(f"  ❌ {ticker_symbol} 抓取失败：{e}")
        return None


def main():
    data_file = Path(__file__).parent.parent / 'data' / 'events.json'

    with open(data_file, 'r', encoding='utf-8') as f:
        events = json.load(f)

    print("=" * 55)
    print("📈 开始抓取股价数据（Yahoo Finance）")
    print("=" * 55)

    for event in events:
        company_id   = event['company_id']
        ticker_symbol = STOCK_MAP.get(company_id)

        if not ticker_symbol:
            print(f"\n⏭️  {event['company_name']} —— 未上市，跳过")
            event['stock_data'] = None
            continue

        event_date = event['created_at'][:10]  # 取 YYYY-MM-DD
        print(f"\n🏢 {event['company_name']} ({ticker_symbol}) @ {event_date}")

        stock_data = fetch_week_price(ticker_symbol, event_date)
        event['stock_data'] = stock_data

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print("✅ 股价数据写入完成！")
    print("=" * 55)


if __name__ == '__main__':
    main()
