# 财经新闻监控 - 设计文档

## 一、技术方案

### 1.1 数据获取方式

**最终方案**：复用 `news_driven_investment` 的 `news_fetcher`（基于 AKShare）

**原因**：
- AKShare 新闻接口稳定可用，无频率限制
- 已实现关键词和日期筛选功能
- 避免重复开发，减少维护成本

**原方案（browser）**：
- 设计初期考虑使用 browser 工具抓取新闻
- 但 AKShare 方案更简单稳定，优先采用

### 1.2 技术栈

| 组件 | 技术 |
|------|------|
| 数据获取 | AKShare（复用 news_driven_investment） |
| 筛选功能 | Python 字符串匹配 |
| 数据格式 | JSON |

### 1.3 新闻来源

| 来源 | 接口 | 特点 |
|------|------|------|
| 财联社 | `cls_global` | 实时、快速、覆盖广 |
| 财联社重点 | `cls_important` | 重点精选，数量少 |
| 东方财富个股 | `stock` | 按股票代码获取 |

## 二、架构设计

### 2.1 目录结构

```
skills/news_monitor/
├── SKILL.md              # 使用文档
└── scripts/
    └── __init__.py       # 复用 news_driven_investment 的 fetcher
```

**说明**：
- 不需要独立的 processor，直接复用 news_driven_investment 的 news_fetcher
- SKILL.md 提供简化的使用入口

### 2.2 数据流

```
用户请求 → news_monitor SKILL.md
              ↓
         调用 news_driven_investment/news_fetcher
              ↓
         AKShare 获取新闻
              ↓
         筛选（关键词/日期）
              ↓
         返回结果
```

## 三、核心功能

### 3.1 关键词筛选

在标题和内容中进行大小写不敏感匹配：

```python
def _filter_news(news, keyword):
    if not keyword:
        return news
    keyword_lower = keyword.lower()
    return [
        item for item in news
        if keyword_lower in item.title.lower()
        or keyword_lower in item.content.lower()
    ]
```

### 3.2 日期筛选

支持 YYYY-MM-DD 格式匹配：

```python
def _match_date(item_date, target_date):
    date_str = str(item_date)  # 处理 datetime.date 对象
    return date_str == target_date or date_str.startswith(target_date)
```

## 四、与其他 Skill 关系

| Skill | 关系 |
|-------|------|
| news_driven_investment | news_monitor 复用其 news_fetcher |
| market_sentiment | 可用新闻热度作为情绪判断依据 |
| risk_alert | 可用负面新闻作为风险信号 |

## 五、测试策略

由于复用 news_driven_investment 的 fetcher，测试由该 skill 负责覆盖。

## 六、开发记录

- 2026-03-07：扩展 news_fetcher 增加关键词和日期筛选，创建 news_monitor SKILL.md
