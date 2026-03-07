# 财经新闻监控 - 设计文档

## 一、技术方案

### 1.1 数据获取方式

使用 **OpenClaw browser 工具** 访问财经网站，抓取新闻列表。

**不使用外部 API 的原因**：
- 财经新闻 API 有限流、收费问题
- 浏览器方式更灵活，可覆盖多种来源
- OpenClaw agent 已具备浏览器操作能力

### 1.2 技术栈

| 组件 | 技术 |
|------|------|
| 数据获取 | OpenClaw browser 工具 |
| 页面解析 | browser snapshot + 正则/AI 提取 |
| 数据处理 | Python (标准库) |
| 数据格式 | JSON |

### 1.3 新闻来源

**主来源**：东方财富（数据结构化，热点明确）

**备选来源**：
- 同花顺
- 新浪财经

## 二、架构设计

### 2.1 目录结构

```
skills/news_monitor/
├── SKILL.md
└── scripts/
    ├── __init__.py
    └── news_processor/
        ├── __init__.py
        └── news_processor.py
```

**说明**：
- 浏览器操作通过 OpenClaw 工具完成，不需要单独的 Fetcher
- Processor 负责协调 browser 工具 + 数据处理

### 2.2 数据流

```
用户请求 → news_processor.py
              ↓
         调用 browser 工具
              ↓
         访问东方财富新闻页
              ↓
         获取 snapshot
              ↓
         解析新闻列表
              ↓
         筛选/排序/格式化
              ↓
         输出结果
```

## 三、核心设计

### 3.1 东方财富新闻页面

**目标页面**：https://www.eastmoney.com/

**新闻位置**：
- 首页热点新闻区块
- 或专门的财经新闻频道

**备选页面**：
- 东方财富财经频道：https://finance.eastmoney.com/
- 股票要闻：https://stock.eastmoney.com/

### 3.2 新闻解析策略

**方案 A：直接解析 snapshot**
- 使用 browser snapshot 获取页面结构
- 通过 AI 或正则提取新闻列表

**方案 B：AI 辅助提取**
- 获取 snapshot
- 让 AI 从 snapshot 中提取结构化新闻数据

**选择方案 B**：更灵活，适应页面结构变化

### 3.3 新闻数据结构

```python
@dataclass
class News:
    title: str          # 标题
    source: str         # 来源
    time: str           # 时间
    url: str            # 链接
    summary: str = ""   # 摘要（可选）
```

## 四、Processor 设计

### 4.1 命令行参数

```python
parser.add_argument("--keyword", help="关键词筛选")
parser.add_argument("--stock", help="股票名称或代码")
parser.add_argument("--date", help="日期（YYYY-MM-DD）")
parser.add_argument("--top-n", type=int, default=10, help="返回数量")
parser.add_argument("--source", help="新闻来源")
parser.add_argument("--output", action="store_true", help="保存到文件")
```

### 4.2 处理流程

```python
async def process(keyword, stock, date, top_n):
    # 1. 构建搜索 URL
    url = build_url(keyword or stock, date)
    
    # 2. 使用 browser 访问页面
    snapshot = await browser_snapshot(url)
    
    # 3. 解析新闻列表
    news_list = parse_news(snapshot)
    
    # 4. 筛选/排序
    filtered = filter_news(news_list, keyword, stock)
    sorted_news = sort_by_time(filtered)
    
    # 5. 返回 Top N
    return sorted_news[:top_n]
```

## 五、容错设计

### 5.1 网络重试

- 使用 browser 工具内置的超时机制
- 失败时尝试备选来源

### 5.2 页面结构变化

- 使用 AI 辅助解析，适应结构变化
- 记录解析失败情况，便于优化

### 5.3 部分数据缺失

- 必需字段缺失时跳过该新闻
- 可选字段缺失时使用默认值

## 六、与现有体系联动

| Skill | 联动方式 |
|-------|---------|
| market_sentiment | 新闻热度作为情绪判断依据 |
| risk_alert | 负面新闻作为风险信号 |
| industry_trend | 行业新闻热度作为板块热度参考 |
| stock_analysis | 个股新闻作为分析补充 |

## 七、测试策略

### 7.1 测试范围

**不测试**：
- ❌ browser 工具调用（外部依赖）
- ❌ 网络请求

**需要测试**：
- ✅ 新闻解析逻辑（用 fixture snapshot）
- ✅ 筛选/排序逻辑
- ✅ 格式化输出

### 7.2 测试数据

保存真实的 snapshot 作为 fixture：
- `tests/skills/news_monitor/fixtures/homepage_snapshot.html`
- `tests/skills/news_monitor/fixtures/search_snapshot.html`

## 八、开发计划

1. **调试浏览器** - 访问东方财富，确认 snapshot 结构
2. **实现解析逻辑** - 从 snapshot 提取新闻
3. **实现筛选/排序** - 关键词/时间筛选
4. **编写 SKILL.md** - 使用文档
5. **编写测试** - 解析逻辑测试
6. **验证** - 端到端测试
