#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公司追踪数据采集器
搜索新闻、财报、高管动态等信息
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict


# 追踪的公司配置
COMPANIES = {
    'tesla': {
        'name_cn': '特斯拉',
        'name_en': 'Tesla',
        'stock_code': 'TSLA',
        'market': '美股',
        'founders': ['Elon Musk'],
        'keywords': ['特斯拉', 'Tesla', 'Elon Musk', 'TSLA'],
        'color': '#e82127'
    },
    'spacex': {
        'name_cn': 'SpaceX',
        'name_en': 'SpaceX',
        'stock_code': '私有',
        'market': '私有',
        'founders': ['Elon Musk'],
        'keywords': ['SpaceX', 'Elon Musk', 'Starship', 'Falcon'],
        'color': '#000000'
    },
    'ast_spacemobile': {
        'name_cn': 'AST 太空移动',
        'name_en': 'AST SpaceMobile',
        'stock_code': 'ASTS',
        'market': '美股',
        'founders': ['Abel Avellan'],
        'keywords': ['AST SpaceMobile', 'ASTS', 'Abel Avellan', '太空卫星'],
        'color': '#0066cc'
    },
    'xiaomi': {
        'name_cn': '小米集团',
        'name_en': 'Xiaomi',
        'stock_code': '1810.HK',
        'market': '港股',
        'founders': ['雷军'],
        'keywords': ['小米', 'Xiaomi', '雷军', 'Lei Jun', '小米汽车'],
        'color': '#ff6900'
    },
    'horizon_robotics': {
        'name_cn': '地平线机器人',
        'name_en': 'Horizon Robotics',
        'stock_code': 'Pre-IPO',
        'market': '未上市',
        'founders': ['余凯'],
        'keywords': ['地平线', 'Horizon Robotics', '余凯', 'AI 芯片', '自动驾驶芯片'],
        'color': '#00aa00'
    },
    'ganli_pharma': {
        'name_cn': '甘李药业',
        'name_en': 'Gan & Lee Pharmaceuticals',
        'stock_code': '603087.SH',
        'market': 'A 股',
        'founders': ['甘忠如'],
        'keywords': ['甘李药业', '甘忠如', '胰岛素', '生物制药'],
        'color': '#cc00cc'
    }
}


class EventCollector:
    """事件采集器"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.events_file = self.data_dir / 'events.json'
        self.events = self.load_events()
    
    def load_events(self) -> List[Dict]:
        """加载已有事件"""
        if self.events_file.exists():
            with open(self.events_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_events(self):
        """保存事件"""
        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
        print(f"💾 已保存 {len(self.events)} 条事件")
    
    def generate_id(self, content: str) -> str:
        """生成事件 ID"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def add_event(self, company_id: str, title: str, content: str, 
                  source: str, url: str, category: str, 
                  sentiment: str = 'neutral', importance: int = 3):
        """添加事件"""
        event = {
            'id': self.generate_id(title + content),
            'company_id': company_id,
            'company_name': COMPANIES[company_id]['name_cn'],
            'title': title,
            'content': content,
            'source': source,
            'url': url,
            'category': category,  # strategy, executive, competition
            'sentiment': sentiment,  # positive, negative, neutral
            'importance': importance,  # 1-5
            'created_at': datetime.now().isoformat(),
            'collected_at': datetime.now().isoformat()
        }
        
        # 检查是否已存在
        exists = any(e['id'] == event['id'] for e in self.events)
        if not exists:
            self.events.append(event)
            print(f"  ✅ 新增：{title[:50]}...")
            return True
        else:
            print(f"  ⏭️  跳过：{title[:50]}...")
            return False
    
    def search_news(self, query: str) -> List[Dict]:
        """搜索新闻（使用 web_search）"""
        from .utils import web_search_news
        return web_search_news(query)
    
    def collect_company_news(self, company_id: str):
        """采集公司新闻"""
        company = COMPANIES[company_id]
        print(f"\n📰 采集：{company['name_cn']} ({company['name_en']})")
        
        # 搜索关键词
        for keyword in company['keywords'][:3]:  # 前 3 个关键词
            print(f"  搜索：{keyword}")
            
            # 这里调用 web_search
            # 由于工具限制，我们用模拟数据演示
            # 实际使用时替换为真实的 web_search 调用
            
            news_items = self.search_news(f"{keyword} 公司 战略 2024")
            
            for item in news_items[:5]:  # 每个关键词最多 5 条
                self.add_event(
                    company_id=company_id,
                    title=item.get('title', '无标题'),
                    content=item.get('snippet', ''),
                    source=item.get('source', '网络搜索'),
                    url=item.get('url', ''),
                    category='strategy',
                    sentiment='neutral',
                    importance=3
                )
            
            time.sleep(1)  # 避免请求过快
    
    def collect_all(self):
        """采集所有公司"""
        print("=" * 60)
        print("🚀 开始采集公司新闻")
        print("=" * 60)
        
        for company_id in COMPANIES.keys():
            self.collect_company_news(company_id)
        
        self.save_events()
        
        print("\n" + "=" * 60)
        print("✅ 采集完成！")
        print("=" * 60)
        print(f"总事件数：{len(self.events)}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='公司追踪数据采集')
    parser.add_argument('--companies', type=str, default='all', 
                       help='公司列表，all 或逗号分隔')
    parser.add_argument('--output', type=str, default='data/events.json',
                       help='输出文件')
    
    args = parser.parse_args()
    
    collector = EventCollector()
    
    if args.companies == 'all':
        collector.collect_all()
    else:
        company_ids = args.companies.split(',')
        for cid in company_ids:
            if cid.strip() in COMPANIES:
                collector.collect_company_news(cid.strip())
        collector.save_events()


if __name__ == '__main__':
    main()
