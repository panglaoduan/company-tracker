#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_youtube.py
搜索 YouTube 上长期分析相关股票的达人视频，
筛选高播放 / 高评论视频，用 AI 生成摘要后写入 events.json。

使用方式：
  python3 scripts/fetch_youtube.py
  python3 scripts/fetch_youtube.py --company tesla
  python3 scripts/fetch_youtube.py --days 14   # 搜最近 14 天
"""

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# ─── 路径 ────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
DATA_FILE = ROOT / 'data' / 'events.json'

# ─── 追踪公司配置 ─────────────────────────────────────────────────────────────
COMPANIES = [
    {
        'id':       'tesla',
        'name':     '特斯拉',
        'keywords': ['Tesla stock analysis', 'TSLA long term', 'Tesla investment 2025 2026'],
        'ticker':   'TSLA',
    },
    {
        'id':       'ast_spacemobile',
        'name':     'AST SpaceMobile',
        'keywords': ['AST SpaceMobile analysis', 'ASTS stock long term', 'AST SpaceMobile investment'],
        'ticker':   'ASTS',
    },
    {
        'id':       'xiaomi',
        'name':     '小米集团',
        'keywords': ['小米股票分析', '小米集团长线', 'Xiaomi stock analysis HK'],
        'ticker':   '1810.HK',
    },
    {
        'id':       'ganli_pharma',
        'name':     '甘李药业',
        'keywords': ['甘李药业分析', '甘李药业股票', '胰岛素龙头分析'],
        'ticker':   '603087.SS',
    },
    {
        'id':       'spacex',
        'name':     'SpaceX',
        'keywords': ['SpaceX investment analysis', 'SpaceX future outlook', 'SpaceX Starlink valuation'],
        'ticker':   None,
    },
    {
        'id':       'horizon_robotics',
        'name':     '地平线机器人',
        'keywords': ['地平线机器人分析', '地平线机器人股票', 'Horizon Robotics analysis'],
        'ticker':   None,
    },
]

# ─── 采集参数 ─────────────────────────────────────────────────────────────────
MAX_VIDEOS_PER_QUERY  = 5   # 每个关键词最多取 N 个视频
MIN_VIEW_COUNT        = 5_000  # 最低播放量门槛
LOOKBACK_DAYS         = 30    # 只看最近 N 天内发布的视频

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


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


def parse_view_count(text: str) -> int:
    """'1.2M views' / '23K views' / '8,342 views' → int"""
    text = text.lower().replace(',', '').strip()
    m = re.search(r'([\d.]+)\s*([kmb]?)', text)
    if not m:
        return 0
    num = float(m.group(1))
    suffix = m.group(2)
    return int(num * {'k': 1_000, 'm': 1_000_000, 'b': 1_000_000_000}.get(suffix, 1))


def parse_relative_date(text: str) -> Optional[str]:
    """
    '2 days ago' / '1 week ago' / '3 months ago' → 'YYYY-MM-DD'
    返回 None 表示解析失败。
    """
    text = text.lower()
    now  = datetime.now()
    m = re.search(r'(\d+)\s+(second|minute|hour|day|week|month|year)', text)
    if not m:
        # 也可能是中文，如"3 天前"
        m = re.search(r'(\d+)\s*(秒|分钟|小时|天|周|个月|年)', text)
        if not m:
            return None
        num   = int(m.group(1))
        unit  = m.group(2)
        delta_map = {
            '秒': timedelta(seconds=num), '分钟': timedelta(minutes=num),
            '小时': timedelta(hours=num), '天': timedelta(days=num),
            '周': timedelta(weeks=num),   '个月': timedelta(days=num*30),
            '年': timedelta(days=num*365),
        }
        delta = delta_map.get(unit, timedelta(0))
    else:
        num  = int(m.group(1))
        unit = m.group(2)
        delta_map = {
            'second': timedelta(seconds=num), 'minute': timedelta(minutes=num),
            'hour':   timedelta(hours=num),   'day':    timedelta(days=num),
            'week':   timedelta(weeks=num),   'month':  timedelta(days=num*30),
            'year':   timedelta(days=num*365),
        }
        delta = delta_map.get(unit, timedelta(0))

    return (now - delta).strftime('%Y-%m-%d')


# ─── YouTube 搜索（无 API，解析搜索结果页）─────────────────────────────────────

def search_youtube(query: str, max_results: int = 10, lookback_days: int = 30) -> list[dict]:
    """
    在 YouTube 搜索页面中提取视频信息。
    返回列表，每项：{video_id, title, channel, views, date_str, url}
    """
    # sp 参数：按上传日期排序（最新）
    # EgIIAQ%3D%3D = 本周；EgIIAhAB = 本月；自定义用 CAI%3D 排序
    sp_map = {
        7:  'EgIIAQ%3D%3D',   # 本周
        30: 'EgIIAhAB',       # 本月
        365:'EgIIARAB',       # 今年
    }
    sp = sp_map.get(lookback_days, 'EgIIAhAB')
    url = f'https://www.youtube.com/results?search_query={quote_plus(query)}&sp={sp}'

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f'  ❌ YouTube 搜索失败：{e}')
        return []

    # YouTube 把数据塞在 ytInitialData JSON 里
    m = re.search(r'var ytInitialData\s*=\s*(\{.+?\});\s*</script>', resp.text, re.DOTALL)
    if not m:
        # 尝试另一种格式
        m = re.search(r'ytInitialData\s*=\s*(\{.+?\});\s*(?:var |</script>)', resp.text, re.DOTALL)
    if not m:
        print(f'  ⚠️  未找到 ytInitialData，可能被反爬')
        return []

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        # JSON 很大，尝试宽松解析
        try:
            raw = m.group(1)
            # 截断到合理位置
            data = json.loads(raw[:5_000_000])
        except Exception as e:
            print(f'  ❌ JSON 解析失败：{e}')
            return []

    # 从嵌套结构中提取 videoRenderer
    videos = []
    try:
        sections = (
            data.get('contents', {})
                .get('twoColumnSearchResultsRenderer', {})
                .get('primaryContents', {})
                .get('sectionListRenderer', {})
                .get('contents', [])
        )
        for section in sections:
            items = (
                section.get('itemSectionRenderer', {}).get('contents', [])
            )
            for item in items:
                vr = item.get('videoRenderer', {})
                if not vr:
                    continue

                video_id = vr.get('videoId', '')
                title_runs = vr.get('title', {}).get('runs', [])
                title = ''.join(r.get('text', '') for r in title_runs)
                channel = (
                    vr.get('ownerText', {}).get('runs', [{}])[0].get('text', '') or
                    vr.get('longBylineText', {}).get('runs', [{}])[0].get('text', '')
                )

                # 播放量
                view_text = (
                    vr.get('viewCountText', {}).get('simpleText', '') or
                    ''.join(r.get('text','') for r in vr.get('viewCountText',{}).get('runs',[]))
                )
                views = parse_view_count(view_text)

                # 发布时间
                date_text = (
                    vr.get('publishedTimeText', {}).get('simpleText', '') or ''
                )
                date_str = parse_relative_date(date_text) or datetime.now().strftime('%Y-%m-%d')

                if not video_id or not title:
                    continue

                videos.append({
                    'video_id': video_id,
                    'title':    title,
                    'channel':  channel,
                    'views':    views,
                    'view_text': view_text,
                    'date_str': date_str,
                    'url':      f'https://www.youtube.com/watch?v={video_id}',
                })

                if len(videos) >= max_results:
                    break
            if len(videos) >= max_results:
                break
    except Exception as e:
        print(f'  ⚠️  解析视频列表出错：{e}')

    return videos


# ─── 抓取视频页面，提取描述 / 评论数 ──────────────────────────────────────────

def fetch_video_detail(video_id: str) -> dict:
    """
    返回 {description, comment_count, like_count, duration}
    """
    url = f'https://www.youtube.com/watch?v={video_id}'
    result = {'description': '', 'comment_count': 0, 'like_count': 0, 'duration': ''}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f'    ⚠️  视频页抓取失败：{e}')
        return result

    # 提取 ytInitialData 里的 description
    m = re.search(r'var ytInitialData\s*=\s*(\{.+?\});\s*</script>', resp.text, re.DOTALL)
    if not m:
        m = re.search(r'ytInitialData\s*=\s*(\{.+?\});\s*(?:var |</script>)', resp.text, re.DOTALL)

    if m:
        try:
            data = json.loads(m.group(1)[:5_000_000])
            # 尝试提取 description
            desc_runs = (
                data.get('engagementPanels', [{}])[0]
                    .get('engagementPanelSectionListRenderer', {})
                    .get('content', {})
            )
            # 简化：用正则在原始 HTML 里找 description
        except Exception:
            pass

    # 从 HTML meta 标签拿 description
    soup = BeautifulSoup(resp.text, 'html.parser')
    desc_tag = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
    if desc_tag:
        result['description'] = desc_tag.get('content', '')[:800]

    # 评论数 / 点赞数：从 ytInitialData JSON 里找
    like_m = re.search(r'"likeCount"\s*:\s*"(\d+)"', resp.text)
    if like_m:
        result['like_count'] = int(like_m.group(1))

    comment_m = re.search(r'"commentCount"\s*:\s*\{"simpleText"\s*:\s*"([\d,]+)"', resp.text)
    if comment_m:
        result['comment_count'] = int(comment_m.group(1).replace(',', ''))

    # 时长
    dur_m = re.search(r'"lengthText"\s*:\s*\{"accessibility".*?"simpleText"\s*:\s*"([\d:]+)"', resp.text)
    if dur_m:
        result['duration'] = dur_m.group(1)

    return result


# ─── 生成事件摘要 ─────────────────────────────────────────────────────────────

def build_summary(company: dict, video: dict, detail: dict) -> str:
    """将视频信息拼成一段中文摘要。"""
    parts = []

    channel = video.get('channel', '未知频道')
    views   = video.get('view_text', str(video.get('views', 0)))
    dur     = detail.get('duration', '')
    likes   = detail.get('like_count', 0)
    comments= detail.get('comment_count', 0)

    parts.append(
        f"YouTube 频道「{channel}」发布了一期关于 {company['name']} 的深度分析视频，"
        f"播放量 {views}"
        + (f"，视频时长 {dur}" if dur else '')
        + (f"，获得 {likes:,} 个点赞" if likes else '')
        + (f"，评论 {comments:,} 条" if comments else '')
        + '。'
    )

    desc = detail.get('description', '').strip()
    if desc:
        # 截取前 300 字作为内容摘要
        snippet = desc[:300].replace('\n', ' ')
        if len(desc) > 300:
            snippet += '……'
        parts.append(f'\n\n📝 视频简介：{snippet}')

    parts.append(
        f'\n\n⚠️ 以上为社媒达人观点，仅供参考，请结合基本面独立判断。'
    )
    return ''.join(parts)


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def is_relevant(title: str, company: dict) -> bool:
    """
    粗略相关性过滤：标题里至少包含公司名、ticker 或关键词之一。
    """
    title_lower = title.lower()
    checks = [company['id'].replace('_', ' ')]
    if company.get('ticker'):
        checks.append(company['ticker'].lower().split('.')[0])  # 'TSLA', '1810', 'ASTS'
    # 从 keywords 里提取核心词
    for kw in company['keywords']:
        for word in kw.split():
            if len(word) >= 4:
                checks.append(word.lower())
    return any(c in title_lower for c in checks)


def process_company(company: dict, existing_ids: set, lookback_days: int) -> list:
    new_events = []
    seen_video_ids = set()

    for kw in company['keywords']:
        print(f'  🔍 搜索：{kw}')
        videos = search_youtube(kw, max_results=MAX_VIDEOS_PER_QUERY, lookback_days=lookback_days)
        print(f'    找到 {len(videos)} 个视频')

        for v in videos:
            vid_id = v['video_id']
            if vid_id in seen_video_ids:
                continue
            seen_video_ids.add(vid_id)

            # 相关性过滤
            if not is_relevant(v['title'], company):
                print(f'    🚫 不相关：{v["title"][:50]}')
                continue

            # 播放量过滤
            if v['views'] < MIN_VIEW_COUNT:
                print(f'    ⏩ 跳过（播放量 {v["views"]:,} < {MIN_VIEW_COUNT:,}）：{v["title"][:40]}')
                continue

            event_id = make_id(f'yt_{company["id"]}_{vid_id}')
            if event_id in existing_ids:
                print(f'    ✅ 已存在：{v["title"][:40]}')
                continue

            print(f'    📺 处理：{v["title"][:50]}（{v["view_text"]}）')
            time.sleep(1.5)  # 礼貌延迟
            detail = fetch_video_detail(vid_id)

            summary = build_summary(company, v, detail)
            importance = 4 if v['views'] >= 100_000 else 3

            event = {
                'id':           event_id,
                'company_id':   company['id'],
                'company_name': company['name'],
                'title':        f'📺 {v["channel"]}：{v["title"][:60]}',
                'content':      summary,
                'source':       f'YouTube · {v["channel"]}',
                'url':          v['url'],
                'category':     'social',
                'sentiment':    'neutral',
                'importance':   importance,
                'created_at':   v['date_str'] + 'T12:00:00',
                'social_data': {
                    'platform':      'youtube',
                    'channel':       v['channel'],
                    'video_id':      vid_id,
                    'views':         v['views'],
                    'view_text':     v['view_text'],
                    'like_count':    detail.get('like_count', 0),
                    'comment_count': detail.get('comment_count', 0),
                    'duration':      detail.get('duration', ''),
                    'description':   detail.get('description', ''),
                },
            }
            new_events.append(event)
            existing_ids.add(event_id)
            print(f'    ✅ 已添加')

        time.sleep(2)

    return new_events


def main():
    parser = argparse.ArgumentParser(description='抓取 YouTube 社媒观点')
    parser.add_argument('--company', default='all', help='公司 id 或 all')
    parser.add_argument('--days',    type=int, default=LOOKBACK_DAYS, help='搜索最近几天的视频')
    args = parser.parse_args()

    print('=' * 55)
    print('🎬 开始抓取 YouTube 社媒观点')
    print('=' * 55)

    events       = load_events()
    existing_ids = {e['id'] for e in events}
    new_total    = 0

    companies = COMPANIES if args.company == 'all' else [c for c in COMPANIES if c['id'] == args.company]

    for company in companies:
        print(f'\n🏢 {company["name"]}')
        new_events = process_company(company, existing_ids, args.days)
        events.extend(new_events)
        new_total += len(new_events)
        print(f'  ➕ 新增 {len(new_events)} 条')

    save_events(events)
    print(f'\n✅ 完成！新增 {new_total} 条社媒观点，总计 {len(events)} 条')


if __name__ == '__main__':
    main()
