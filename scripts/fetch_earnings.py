#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取季度财报数据摘要
包含：营收、净利润、EPS、毛利率、同比增长
"""

import json, hashlib, yfinance as yf
import pandas as pd
from datetime import datetime
from pathlib import Path

COMPANIES = [
    {'id': 'tesla',           'name': '特斯拉',      'ticker': 'TSLA',      'currency': 'USD', 'unit': '亿美元', 'divisor': 1e8},
    {'id': 'ast_spacemobile', 'name': 'AST 太空移动', 'ticker': 'ASTS',      'currency': 'USD', 'unit': '亿美元', 'divisor': 1e8},
    {'id': 'xiaomi',          'name': '小米集团',     'ticker': '1810.HK',   'currency': 'HKD', 'unit': '亿港元', 'divisor': 1e8},
    {'id': 'ganli_pharma',    'name': '甘李药业',     'ticker': '603087.SS', 'currency': 'CNY', 'unit': '亿元',   'divisor': 1e8},
]

DATA_FILE = Path(__file__).parent.parent / 'data' / 'events.json'


def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]

def fmt(v, divisor):
    """把原始数字转成亿为单位，保留2位小数"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 'N/A'
    return f"{v / divisor:.2f}"

def pct(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 'N/A'
    return f"{v:.1f}%"

def load_events():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_events(events):
    events.sort(key=lambda e: e['created_at'], reverse=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    # 更新 meta.json（记录真实抓取时间）
    meta_file = DATA_FILE.parent / 'meta.json'
    meta = {
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_events": len(events)
    }
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n💾 已保存，共 {len(events)} 条事件，更新时间：{meta['last_updated']}")


def fetch_quarterly_earnings(company, existing_ids):
    """抓取季度财报摘要"""
    new_events = []
    t = yf.Ticker(company['ticker'])
    div = company['divisor']
    unit = company['unit']

    # 1. 季度财务数据
    try:
        qs = t.quarterly_income_stmt
        qb = t.quarterly_balance_sheet
    except Exception as e:
        print(f"  ❌ 财务数据获取失败：{e}")
        return []

    # 2. 历史 earnings_dates（含 EPS 预期 vs 实际）
    try:
        ed = t.earnings_dates
        # 只取过去的（有实际 EPS 的）
        ed_hist = ed[ed['Reported EPS'].notna()].copy()
    except Exception as e:
        print(f"  ⚠️  earnings_dates 获取失败：{e}")
        ed_hist = pd.DataFrame()

    # 3. 逐季度构建事件
    quarters = qs.columns.tolist()  # 最新在前

    for i, q_date in enumerate(quarters):
        date_str = str(q_date)[:10]
        # 跳过未来日期（不抓预告）
        if date_str > datetime.now().strftime('%Y-%m-%d'):
            print(f"  ⏭️  {date_str} 为未来财报，跳过")
            continue

        event_id = make_id(f"earnings_q_{company['id']}_{date_str}")
        if event_id in existing_ids:
            print(f"  ⏭️  {date_str} 已存在")
            continue

        # 提取财务指标
        def get(row):
            try:
                v = qs.loc[row, q_date]
                return None if pd.isna(v) else float(v)
            except: return None

        revenue  = get('Total Revenue')
        net_inc  = get('Net Income')
        gross_p  = get('Gross Profit')
        op_inc   = get('Operating Income')
        eps      = get('Basic EPS')
        ebitda   = get('EBITDA')

        # 同比增长（和4个季度前比较）
        def yoy(row):
            try:
                if i + 4 >= len(quarters): return None
                prev = qs.loc[row, quarters[i+4]]
                curr = qs.loc[row, q_date]
                if pd.isna(prev) or pd.isna(curr) or prev == 0: return None
                return (float(curr) - float(prev)) / abs(float(prev)) * 100
            except: return None

        rev_yoy = yoy('Total Revenue')
        ni_yoy  = yoy('Net Income')

        # 毛利率
        gross_margin = (gross_p / revenue * 100) if revenue and gross_p else None

        # EPS 预期 vs 实际（从 earnings_dates 匹配）
        eps_estimate  = None
        eps_reported  = None
        eps_surprise  = None

        if not ed_hist.empty:
            # 匹配同年同季（日期差在30天内）
            q_dt = pd.Timestamp(date_str)
            for ed_dt, ed_row in ed_hist.iterrows():
                ed_dt_norm = pd.Timestamp(ed_dt).tz_localize(None) if ed_dt.tzinfo else pd.Timestamp(ed_dt)
                if abs((ed_dt_norm - q_dt).days) <= 45:
                    eps_estimate = ed_row.get('EPS Estimate')
                    eps_reported = ed_row.get('Reported EPS')
                    eps_surprise = ed_row.get('Surprise(%)')
                    break

        # 判断季度名称
        q_month = pd.Timestamp(date_str).month
        q_label = {3:'Q1', 6:'Q2', 9:'Q3', 12:'Q4'}.get(q_month, 'Q?')
        q_year  = pd.Timestamp(date_str).year
        title_quarter = f"{q_year} {q_label}"

        # 简短摘要（弹窗表格会展示详情，这里只一句话）
        rev_str = f"{fmt(revenue, div)}{unit}" if revenue else 'N/A'
        ni_str  = f"{fmt(net_inc, div)}{unit}" if net_inc else 'N/A'
        yoy_str = f"，营收同比 {pct(rev_yoy)}" if rev_yoy is not None else ""
        content = f"{company['name']} {title_quarter} 季报：营收 {rev_str}，净利润 {ni_str}{yoy_str}。详情见下方财务表格。"

        # 判断情绪
        if rev_yoy is not None and rev_yoy > 5:
            sentiment = 'positive'
        elif rev_yoy is not None and rev_yoy < -5:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # 当季股价数据（用财报发布后一周）
        stock_data = None
        try:
            ticker_obj = yf.Ticker(company['ticker'])
            df = ticker_obj.history(start=date_str,
                                    end=(pd.Timestamp(date_str) + pd.Timedelta(days=10)).strftime('%Y-%m-%d'),
                                    interval='1d').head(7)
            if not df.empty:
                stock_data = {
                    'ticker':      company['ticker'],
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
        except: pass

        event = {
            'id':           event_id,
            'company_id':   company['id'],
            'company_name': company['name'],
            'title':        f"📋 {company['name']} {title_quarter} 财报｜营收 {fmt(revenue, div)}{unit}" +
                           (f"（{'+' if rev_yoy and rev_yoy>0 else ''}{pct(rev_yoy)} YoY）" if rev_yoy is not None else ""),
            'content':      content,
            'source':       'Yahoo Finance 季报',
            'url':          f"https://finance.yahoo.com/quote/{company['ticker']}/financials/",
            'category':     'earnings',
            'sentiment':    sentiment,
            'importance':   5,
            'created_at':   date_str + 'T21:00:00',
            'stock_data':   stock_data,
            # 额外财务字段（供前端展示）
            'financials': {
                'quarter':       title_quarter,
                'revenue':       revenue,
                'net_income':    net_inc,
                'gross_profit':  gross_p,
                'op_income':     op_inc,
                'ebitda':        ebitda,
                'gross_margin':  gross_margin,
                'eps':           eps,
                'eps_estimate':  float(eps_estimate) if eps_estimate and not pd.isna(eps_estimate) else None,
                'eps_reported':  float(eps_reported) if eps_reported and not pd.isna(eps_reported) else None,
                'eps_surprise':  float(eps_surprise) if eps_surprise and not pd.isna(eps_surprise) else None,
                'rev_yoy':       rev_yoy,
                'ni_yoy':        ni_yoy,
                'unit':          unit,
                'currency':      company['currency'],
                'divisor':       div,
            }
        }

        new_events.append(event)
        beat_str = ""
        if eps_surprise is not None and not pd.isna(eps_surprise):
            beat_str = f" EPS {'超' if eps_surprise > 0 else '不及'}预期 {eps_surprise:+.1f}%"
        print(f"  ✅ {title_quarter}：营收 {fmt(revenue,div)}{unit}，净利 {fmt(net_inc,div)}{unit}{beat_str}")

    return new_events


def main():
    print("=" * 60)
    print("📋 开始抓取季度财报数据")
    print("=" * 60)

    events       = load_events()
    existing_ids = {e['id'] for e in events}
    new_total    = 0

    for company in COMPANIES:
        print(f"\n🏢 {company['name']} ({company['ticker']})")
        earned = fetch_quarterly_earnings(company, existing_ids)
        events.extend(earned)
        existing_ids.update(e['id'] for e in earned)
        new_total += len(earned)

    save_events(events)
    print(f"\n✅ 新增 {new_total} 条财报事件，总计 {len(events)} 条")


if __name__ == '__main__':
    main()
