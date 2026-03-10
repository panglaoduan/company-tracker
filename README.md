# 公司追踪系统 - CEO/高管动态与战略分析

## 📋 追踪公司列表

| 公司 | 代码 | 市场 | 创始人/关键人物 |
|------|------|------|----------------|
| **特斯拉** | TSLA | 美股 | Elon Musk (CEO) |
| **SpaceX** | 私有 | - | Elon Musk (CEO/CTO) |
| **AST SpaceMobile** | ASTS | 美股 | Abel Avellan (CEO/Founder) |
| **小米集团** | 1810.HK | 港股 | 雷军 (CEO/Founder) |
| **地平线机器人** | Pre-IPO | - | 余凯 (CEO/Founder) |
| **甘李药业** | 603087.SH | A 股 | 甘忠如 (Founder) |

## 🎯 追踪维度

### 1. 长期经营战略
- 公司战略调整
- 新产品/技术发布
- 市场扩张计划
- 投资/并购动向
- 合作伙伴关系

### 2. 创始人/高管动态
- 公开演讲/访谈
- 社交媒体动态
- 持股变动
- 人事任免
- 个人影响力事件

### 3. 行业竞争格局
- 竞争对手动态
- 行业政策变化
- 技术趋势
- 市场份额变化
- 供应链变化

## 📊 数据来源

- 新闻资讯（Google News、新浪财经、Seeking Alpha）
- 官方渠道（公司官网、财报、公告）
- 社交媒体（Twitter/X、微博）
- 行业报告（券商研报、咨询机构）
- 监管文件（SEC  filings、港交所公告）

## 🌐 网站功能

- **时间线视图** - 按时间顺序展示所有事件
- **公司筛选** - 按公司过滤信息
- **分类筛选** - 按类型（战略/高管/竞争）过滤
- **搜索功能** - 关键词搜索历史事件
- **影响评估** - 正面/负面/中性标签
- **导出功能** - 导出 PDF/Excel 报告

## ⚙️ 自动更新

- 每日定时抓取（上午 9 点、下午 6 点）
- Telegram 推送重要事件
- 每周生成汇总报告

## 📁 项目结构

```
company-tracker/
├── data/                    # 数据存储
│   ├── events.json          # 事件数据库
│   └── cache/               # 缓存目录
├── scripts/                 # 脚本
│   ├── collector.py         # 数据采集
│   ├── analyzer.py          # AI 分析
│   └── updater.py           # 定时更新
├── website/                 # 网站
│   ├── index.html           # 主页
│   ├── timeline.js          # 时间线组件
│   └── style.css            # 样式
└── templates/               # 模板
    └── report.md            # 报告模板
```

## 🚀 快速开始

```bash
# 1. 首次运行数据采集
cd /Users/duanclaw/.easyclaw/workspace/company-tracker
python3.10 scripts/collector.py --companies all

# 2. 查看网站
open website/index.html

# 3. 设置定时更新（cron）
crontab -e
# 添加：0 9,18 * * * cd /path && python3 scripts/updater.py
```

## 💡 使用说明

详见各脚本的 README 文档。
