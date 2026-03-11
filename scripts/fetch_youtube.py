#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_youtube.py
使用 YouTube Data API v3 搜索高播放/高评论的股票分析视频，写入 events.json。

使用方式：
  python3 scripts/fetch_youtube.py
  python3 scripts/fetch_youtube.py --company tesla
  python3 scripts/fetch_youtube.py --days 14
"""

import argparse
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yfinance as yf

# ─── API Key ──────────────────────────────────────────────────────────────────
YOUTUBE_API_KEY = 'AIzaSyDQuLaiqODzwdmMuwxUH9e07OnDoOhrXfc'
YT_API_BASE     = 'https://www.googleapis.com/youtube/v3'

# ─── 路径 ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
DATA_FILE = ROOT / 'data' / 'events.json'

# ─── 追踪公司配置 ─────────────────────────────────────────────────────────────
COMPANIES = [
    {
        'id':       'tesla',
        'name':     '特斯拉',
        'keywords': ['Tesla TSLA stock analysis long term', 'TSLA investment 2026', 'Tesla stock outlook'],
        'ticker':   'TSLA',
    },
    {
        'id':       'ast_spacemobile',
        'name':     'AST SpaceMobile',
        'keywords': ['AST SpaceMobile ASTS stock analysis', 'ASTS long term investment'],
        'ticker':   'ASTS',
    },
    {
        'id':       'xiaomi',
        'name':     '小米集团',
        'keywords': ['小米集团 1810 股票分析', 'Xiaomi stock analysis 1810 HK', '小米股票长线投资'],
        'ticker':   '1810.HK',
    },
    {
        'id':       'ganli_pharma',
        'name':     '甘李药业',
        'keywords': ['甘李药业 603087 股票分析', '甘李药业投资分析'],
        'ticker':   '603087.SS',
    },
    {
        'id':       'spacex',
        'name':     'SpaceX',
        'keywords': ['SpaceX valuation investment analysis', 'SpaceX Starlink stock outlook'],
        'ticker':   None,
    },
    {
        'id':       'horizon_robotics',
        'name':     '地平线机器人',
        'keywords': ['地平线机器人 股票分析', 'Horizon Robotics stock analysis'],
        'ticker':   None,
    },
]

# ─── 采集参数 ─────────────────────────────────────────────────────────────────
MAX_RESULTS_PER_QUERY = 10   # 每个关键词最多取 N 个结果
MIN_VIEW_COUNT        = 5_000
LOOKBACK_DAYS         = 30


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def make_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


def load_events() -> list:
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_events(events: list):
    events.sort(key=lambda e: e['created_at'], reverse=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    meta_file = DATA_FILE.parent / 'meta.json'
    meta = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_events': len(events),
    }
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f'\n💾 已保存，共 {len(events)} 条事件')


def fmt_views(n: int) -> str:
    if n >= 1_000_000:
        return f'{n/1_000_000:.1f}M'
    if n >= 1_000:
        return f'{n/1_000:.1f}K'
    return str(n)


def fetch_stock_after_date(ticker: str, date_str: str, days: int = 5) -> dict:
    """
    拉 date_str 之后 days 个交易日的 OHLCV 数据。
    返回与 fetch_events.py 相同格式的 stock_data dict，供前端 K 线复用。
    """
    if not ticker:
        return None
    try:
        start = datetime.strptime(date_str, '%Y-%m-%d')
        # 多取一些日历日，保证能拿到足够交易日
        end   = start + timedelta(days=days * 3)
        # 不能超过今天
        today = datetime.now()
        if end > today:
            end = today
        if start >= today:
            return None  # 未来日期，无数据

        tk = yf.Ticker(ticker)
        df = tk.history(
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
            interval='1d'
        )
        if df is None or df.empty:
            return None

        df = df.head(days)  # 只取前 N 个交易日
        if len(df) < 1:
            return None

        return {
            'ticker':      ticker,
            'open_price':  round(float(df['Close'].iloc[0]), 3),
            'close_price': round(float(df['Close'].iloc[-1]), 3),
            'week_high':   round(float(df['High'].max()), 3),
            'week_low':    round(float(df['Low'].min()), 3),
            'change_pct':  round(
                (float(df['Close'].iloc[-1]) - float(df['Close'].iloc[0]))
                / float(df['Close'].iloc[0]) * 100, 2
            ),
            'dates':   [d.strftime('%m/%d') for d in df.index],
            'opens':   [round(float(v), 3) for v in df['Open']],
            'highs':   [round(float(v), 3) for v in df['High']],
            'lows':    [round(float(v), 3) for v in df['Low']],
            'closes':  [round(float(v), 3) for v in df['Close']],
            'volumes': [int(v) for v in df['Volume']],
        }
    except Exception as e:
        print(f'    ⚠️  股价数据失败（{ticker} {date_str}）：{e}')
        return None


# ─── YouTube API 调用 ─────────────────────────────────────────────────────────

def yt_search(query: str, published_after: str, max_results: int = 10) -> list:
    """
    调用 search.list，返回 video item 列表。
    published_after: ISO 8601 格式，如 '2026-02-09T00:00:00Z'
    消耗配额：100 点/次
    """
    params = {
        'part':           'snippet',
        'q':              query,
        'type':           'video',
        'order':          'viewCount',       # 按播放量排序，质量更高
        'publishedAfter': published_after,
        'maxResults':     max_results,
        'relevanceLanguage': 'zh' if any(ord(c) > 127 for c in query) else 'en',
        'key':            YOUTUBE_API_KEY,
    }
    try:
        resp = requests.get(f'{YT_API_BASE}/search', params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get('items', [])
    except Exception as e:
        print(f'  ❌ search 失败：{e}')
        return []


def yt_video_detail(video_ids: list) -> dict:
    """
    批量查询 videos.list，返回 {video_id: stats_dict}。
    消耗配额：1 点/次（批量）
    """
    if not video_ids:
        return {}
    params = {
        'part':  'statistics,contentDetails,snippet',
        'id':    ','.join(video_ids),
        'key':   YOUTUBE_API_KEY,
    }
    try:
        resp = requests.get(f'{YT_API_BASE}/videos', params=params, timeout=15)
        resp.raise_for_status()
        result = {}
        for item in resp.json().get('items', []):
            vid_id = item['id']
            stats  = item.get('statistics', {})
            detail = item.get('contentDetails', {})
            snip   = item.get('snippet', {})
            result[vid_id] = {
                'view_count':    int(stats.get('viewCount', 0)),
                'like_count':    int(stats.get('likeCount', 0)),
                'comment_count': int(stats.get('commentCount', 0)),
                'duration':      parse_duration(detail.get('duration', '')),
                'description':   snip.get('description', '')[:500],
                'channel':       snip.get('channelTitle', ''),
                'published_at':  snip.get('publishedAt', ''),
            }
        return result
    except Exception as e:
        print(f'  ❌ videos.list 失败：{e}')
        return {}


def parse_duration(iso: str) -> str:
    """'PT1H23M45S' → '1:23:45'"""
    import re
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso)
    if not m:
        return ''
    h, mn, s = m.group(1), m.group(2), m.group(3)
    h  = int(h)  if h  else 0
    mn = int(mn) if mn else 0
    s  = int(s)  if s  else 0
    if h:
        return f'{h}:{mn:02d}:{s:02d}'
    return f'{mn}:{s:02d}'


# ─── 每家公司处理 ─────────────────────────────────────────────────────────────

def process_company(company: dict, existing_ids: set, lookback_days: int) -> list:
    new_events  = []
    seen_vids   = set()

    # publishedAfter = 今天 - lookback_days
    after_dt = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    published_after = after_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    for kw in company['keywords']:
        print(f'  🔍 {kw}')
        items = yt_search(kw, published_after, MAX_RESULTS_PER_QUERY)
        print(f'    API 返回 {len(items)} 条')

        # 收集 video_id，批量查详情
        batch_ids = []
        for item in items:
            vid_id = item.get('id', {}).get('videoId', '')
            if vid_id and vid_id not in seen_vids:
                batch_ids.append(vid_id)
                seen_vids.add(vid_id)

        if not batch_ids:
            continue

        time.sleep(0.5)
        details = yt_video_detail(batch_ids)

        for item in items:
            vid_id = item.get('id', {}).get('videoId', '')
            if not vid_id or vid_id not in details:
                continue

            d       = details[vid_id]
            views   = d['view_count']
            channel = d['channel'] or item['snippet'].get('channelTitle', '未知频道')
            title   = item['snippet'].get('title', '')
            pub_at  = d['published_at'] or item['snippet'].get('publishedAt', '')
            date_str = pub_at[:10] if pub_at else datetime.now().strftime('%Y-%m-%d')

            # 播放量过滤
            if views < MIN_VIEW_COUNT:
                print(f'    ⏩ 跳过（{fmt_views(views)} 播放）：{title[:45]}')
                continue

            event_id = make_id(f'yt_{company["id"]}_{vid_id}')
            if event_id in existing_ids:
                print(f'    ✅ 已存在：{title[:45]}')
                continue

            # 构建摘要
            meta_parts = [f'播放 {fmt_views(views)}']
            if d['like_count']:    meta_parts.append(f'点赞 {fmt_views(d["like_count"])}')
            if d['comment_count']: meta_parts.append(f'评论 {d["comment_count"]:,}')
            if d['duration']:      meta_parts.append(f'时长 {d["duration"]}')

            desc_snippet = d['description'].strip().replace('\n', ' ')
            if len(desc_snippet) > 300:
                desc_snippet = desc_snippet[:300] + '……'

            content = (
                f'YouTube 频道「{channel}」发布了一期关于 {company["name"]} 的分析视频，'
                f'{" · ".join(meta_parts)}。'
                + (f'\n\n📝 视频简介：{desc_snippet}' if desc_snippet else '')
                + '\n\n⚠️ 以上为社媒达人观点，仅供参考，请结合基本面独立判断。'
            )

            importance = 5 if views >= 500_000 else 4 if views >= 100_000 else 3

            # 拉发布日后5个交易日股价
            ticker = company.get('ticker')
            stock_data = None
            if ticker:
                print(f'    📊 拉取 {ticker} 发布后5日行情…')
                stock_data = fetch_stock_after_date(ticker, date_str, days=5)
                if stock_data:
                    print(f'    📈 股价 {stock_data["change_pct"]:+.2f}%（{date_str} 起5日）')

            event = {
                'id':           event_id,
                'company_id':   company['id'],
                'company_name': company['name'],
                'title':        f'📺 {channel}：{title[:65]}',
                'content':      content,
                'source':       f'YouTube · {channel}',
                'url':          f'https://www.youtube.com/watch?v={vid_id}',
                'category':     'social',
                'sentiment':    'neutral',
                'importance':   importance,
                'created_at':   date_str + 'T12:00:00',
                'stock_data':   stock_data,
                'social_data': {
                    'platform':      'youtube',
                    'channel':       channel,
                    'video_id':      vid_id,
                    'views':         views,
                    'view_text':     fmt_views(views),
                    'like_count':    d['like_count'],
                    'comment_count': d['comment_count'],
                    'duration':      d['duration'],
                    'description':   d['description'],
                },
            }
            new_events.append(event)
            existing_ids.add(event_id)
            print(f'    ✅ +1 [{fmt_views(views)} 播放 · {d["comment_count"]:,} 评论] {title[:45]}')

        time.sleep(1)

    return new_events


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--company', default='all')
    parser.add_argument('--days',    type=int, default=LOOKBACK_DAYS)
    parser.add_argument('--clean',   action='store_true', help='清除旧的社媒数据重新抓')
    args = parser.parse_args()

    print('=' * 55)
    print('🎬 YouTube Data API v3 — 社媒观点抓取')
    print('=' * 55)

    events       = load_events()
    existing_ids = {e['id'] for e in events}

    # 清除旧社媒数据（重新全量抓时用）
    if args.clean:
        before = len(events)
        events = [e for e in events if e.get('category') != 'social']
        existing_ids = {e['id'] for e in events}
        print(f'🗑  清除旧社媒数据 {before - len(events)} 条')

    companies = COMPANIES if args.company == 'all' else [c for c in COMPANIES if c['id'] == args.company]
    new_total = 0

    for company in companies:
        print(f'\n🏢 {company["name"]}')
        new_events = process_company(company, existing_ids, args.days)
        events.extend(new_events)
        new_total += len(new_events)
        print(f'  ➕ 新增 {len(new_events)} 条')

    save_events(events)
    print(f'\n✅ 完成！新增 {new_total} 条，总计 {len(events)} 条')


if __name__ == '__main__':
    main()
