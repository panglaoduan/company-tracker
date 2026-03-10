#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化示例数据
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

# 示例事件数据
DEMO_EVENTS = [
    {
        'id': '1',
        'company_id': 'xiaomi',
        'company_name': '小米集团',
        'title': '小米汽车 SU7 交付突破 10 万辆，雷军宣布 2024 年目标翻倍',
        'content': '雷军在社交媒体上宣布，小米汽车 SU7 交付量突破 10 万辆，创下新能源汽车行业最快交付记录。同时宣布 2024 年交付目标提升至 20 万辆，并计划在欧洲市场推出首款车型。分析师认为，这标志着小米汽车已经站稳脚跟，未来将与特斯拉、比亚迪等展开直接竞争。',
        'source': '新浪财经',
        'url': 'https://finance.sina.com.cn',
        'category': 'strategy',
        'sentiment': 'positive',
        'importance': 5,
        'created_at': datetime.now().isoformat()
    },
    {
        'id': '2',
        'company_id': 'tesla',
        'company_name': '特斯拉',
        'title': 'Elon Musk 宣布 Tesla Bot Optimus 将于 2024 年底量产',
        'content': '在 Tesla AI Day 上，Elon Musk 展示了 Optimus 人形机器人的最新进展，表示将在 2024 年底开始小批量生产，主要用于特斯拉工厂内部。长期目标年产 100 万台。Musk 称这将是"特斯拉历史上最重要的产品"，可能比特斯拉汽车业务更大。',
        'source': 'TechCrunch',
        'url': 'https://techcrunch.com',
        'category': 'strategy',
        'sentiment': 'positive',
        'importance': 5,
        'created_at': (datetime.now() - timedelta(days=1)).isoformat()
    },
    {
        'id': '3',
        'company_id': 'spacex',
        'company_name': 'SpaceX',
        'title': 'SpaceX Starship 第三次试飞成功，Elon Musk 称 2025 年实现载人登月',
        'content': 'SpaceX 的 Starship 重型火箭成功完成第三次试飞，进入预定轨道并安全返回。Elon Musk 表示，按照目前进展，2025 年实现载人登月目标可期。NASA 也对进展表示满意，Artemis 登月计划将依赖 Starship 完成月面着陆任务。',
        'source': 'SpaceNews',
        'url': 'https://spacenews.com',
        'category': 'strategy',
        'sentiment': 'positive',
        'importance': 5,
        'created_at': (datetime.now() - timedelta(days=2)).isoformat()
    },
    {
        'id': '4',
        'company_id': 'horizon_robotics',
        'company_name': '地平线机器人',
        'title': '地平线机器人递交港股 IPO 申请，余凯：将加大 AI 芯片研发',
        'content': '地平线机器人正式向港交所递交 IPO 申请，拟募资 10 亿美元。创始人余凯表示，上市后将加大高阶自动驾驶芯片和具身智能机器人的研发投入。目前地平线已为理想、比亚迪等多家车企供货，2023 年营收预计突破 50 亿元。',
        'source': '36 氪',
        'url': 'https://36kr.com',
        'category': 'executive',
        'sentiment': 'positive',
        'importance': 4,
        'created_at': (datetime.now() - timedelta(days=3)).isoformat()
    },
    {
        'id': '5',
        'company_id': 'ganli_pharma',
        'company_name': '甘李药业',
        'title': '甘李药业新一代胰岛素类似物获批，甘忠如：将大幅降低患者负担',
        'content': '甘李药业宣布其新一代超速效胰岛素类似物获得国家药监局批准上市。创始人甘忠如表示，新产品将大幅降低糖尿病患者用药负担，预计年销售额可达 20 亿元。甘李药业已成为国内胰岛素龙头企业，产品出口欧美市场。',
        'source': '医药魔方',
        'url': 'https://pharmcube.com',
        'category': 'strategy',
        'sentiment': 'positive',
        'importance': 4,
        'created_at': (datetime.now() - timedelta(days=4)).isoformat()
    },
    {
        'id': '6',
        'company_id': 'ast_spacemobile',
        'company_name': 'AST 太空移动',
        'title': 'AST SpaceMobile 与 Verizon 达成合作协议，股价大涨 25%',
        'content': 'AST SpaceMobile 宣布与美国最大运营商 Verizon 达成独家合作协议，将共同开发卫星直连手机服务。消息公布后股价大涨 25%，CEO Abel Avellan 称这是"历史性时刻"。该服务预计 2024 年商用，将覆盖美国农村地区。',
        'source': 'Reuters',
        'url': 'https://reuters.com',
        'category': 'competition',
        'sentiment': 'positive',
        'importance': 5,
        'created_at': (datetime.now() - timedelta(days=5)).isoformat()
    },
    {
        'id': '7',
        'company_id': 'tesla',
        'company_name': '特斯拉',
        'title': '特斯拉中国销量下滑，面临比亚迪激烈竞争',
        'content': '特斯拉中国 11 月销量环比下滑 15%，主要受到比亚迪、理想等本土品牌的激烈竞争。分析师指出，特斯拉 Model 3/Y 已上市多年，产品力相对下降，需要尽快推出新车型。Elon Musk 表示将在 2024 年推出平价车型。',
        'source': '彭博社',
        'url': 'https://bloomberg.com',
        'category': 'competition',
        'sentiment': 'negative',
        'importance': 4,
        'created_at': (datetime.now() - timedelta(days=6)).isoformat()
    },
    {
        'id': '8',
        'company_id': 'xiaomi',
        'company_name': '小米集团',
        'title': '雷军年度演讲：小米将坚持高端化战略，加大研发投入',
        'content': '在小米 14 发布会上，雷军发表年度演讲，强调小米将坚持高端化战略，2024 年研发投入预计超过 200 亿元。小米 14 系列首销成绩亮眼，预计全年高端机占比将超过 20%。雷军还表示，小米汽车是"最后一次创业"。',
        'source': '小米官网',
        'url': 'https://mi.com',
        'category': 'executive',
        'sentiment': 'positive',
        'importance': 4,
        'created_at': (datetime.now() - timedelta(days=7)).isoformat()
    }
]


def main():
    """生成示例数据"""
    print("=" * 60)
    print("📊 生成公司追踪示例数据")
    print("=" * 60)
    
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    
    events_file = data_dir / 'events.json'
    
    with open(events_file, 'w', encoding='utf-8') as f:
        json.dump(DEMO_EVENTS, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已生成 {len(DEMO_EVENTS)} 条示例事件")
    print(f"📁 文件位置：{events_file}")
    print("\n💡 下一步:")
    print("   1. 打开网站：open website/index.html")
    print("   2. 查看时间线展示")
    print("   3. 测试筛选和搜索功能")


if __name__ == '__main__':
    main()
