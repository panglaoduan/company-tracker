# 公司追踪系统 - 使用指南

## 🎉 系统已就绪！

网站已生成示例数据，你现在可以查看了！

---

## 📱 查看网站

### 方法 1：直接打开
```bash
open /Users/duanclaw/.easyclaw/workspace/company-tracker/website/index.html
```

### 方法 2：在浏览器中打开
复制这个路径到浏览器：
```
file:///Users/duanclaw/.easyclaw/workspace/company-tracker/website/index.html
```

---

## 🌐 网站功能

### 1. 时间线视图
- 所有事件按时间倒序排列
- 最新的事件显示在最前面
- 每个事件显示公司、分类、时间、来源

### 2. 筛选功能
- **按公司筛选** - 只看特定公司的信息
- **按分类筛选** - 只看战略/高管/竞争
- **关键词搜索** - 搜索历史事件

### 3. 统计面板
- 总事件数
- 今日更新数
- 追踪公司数
- 最后更新时间

---

## 🔄 更新数据

### 手动更新
```bash
cd /Users/duanclaw/.easyclaw/workspace/company-tracker
python3.10 scripts/collector.py
```

### 自动更新（推荐）

设置定时任务，每天自动更新：

```bash
crontab -e
```

添加以下行（每天上午 9 点和下午 6 点更新）：
```
0 9,18 * * * cd /Users/duanclaw/.easyclaw/workspace/company-tracker && /usr/local/bin/python3.10 scripts/updater.py >> /tmp/company_tracker.log 2>&1
```

---

## 📊 当前追踪的公司

| 公司 | 市场 | 创始人/关键人物 |
|------|------|----------------|
| 特斯拉 (Tesla) | 美股 TSLA | Elon Musk |
| SpaceX | 私有 | Elon Musk |
| AST SpaceMobile | 美股 ASTS | Abel Avellan |
| 小米集团 | 港股 1810.HK | 雷军 |
| 地平线机器人 | Pre-IPO | 余凯 |
| 甘李药业 | A 股 603087.SH | 甘忠如 |

---

## 🔧 自定义配置

### 添加新公司

编辑 `scripts/collector.py` 中的 `COMPANIES` 字典：

```python
'new_company': {
    'name_cn': '公司名称',
    'name_en': 'Company Name',
    'stock_code': '股票代码',
    'market': '市场',
    'founders': ['创始人'],
    'keywords': ['关键词 1', '关键词 2'],
    'color': '#颜色代码'
}
```

### 修改追踪维度

编辑 `scripts/utils.py` 中的分类函数：

```python
def categorize_event(title, content):
    # 添加新的分类关键词
    custom_keywords = ['你的关键词']
    # ...
```

---

## 📈 下一步优化

### 1. 集成真实数据源（需要 API）
- Google News API
- 新浪财经 API
- Twitter/X API（创始人动态）
- SEC filings（美股公告）

### 2. AI 深度分析
- 使用大模型分析事件影响
- 自动生成投资评级
- 竞争格局分析

### 3. Telegram 推送
- 重要事件实时通知
- 每日/每周简报

### 4. 数据可视化
- 股价走势图
- 情感分析趋势
- 词云展示

---

## 💡 使用技巧

### 快速查看特定公司
1. 在"公司"下拉框选择公司
2. 只看该公司的所有动态

### 回顾历史事件
1. 使用搜索功能输入关键词
2. 按时间线查看所有相关事件

### 导出报告
1. 筛选出想看的内容
2. 截图或打印网页
3. 或导出 JSON 数据自行处理

---

## 📞 有问题？

随时告诉我，我可以：
- 添加新功能
- 修复问题
- 优化体验
- 集成更多数据源

---

**祝你使用愉快！** 🚀
