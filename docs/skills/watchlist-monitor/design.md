# 自选股监控 Skill - 设计文档

## 技术选型

**数据源**：复用 stock_screener 的 StockSpotFetcher
- 已有全市场行情获取能力
- 直接复用，无需重复开发

**存储**：JSON 文件
- 简单、可读、无需数据库
- 路径：`.openclaw_alpha/watchlist-monitor/watchlist.json`

## 架构设计

```
watchlist_monitor/
├── SKILL.md
└── scripts/
    ├── __init__.py
    └── watchlist_processor/
        ├── __init__.py
        └── watchlist_processor.py
```

**复用**：直接导入 `stock_screener` 的 `StockSpotFetcher`

## 数据流

```
命令行参数
     │
     ▼
┌─────────────────────────────────────┐
│     WatchlistProcessor              │
│                                     │
│  add/remove/list/clear/watch/analyze │
│         │                           │
│    ┌────┴────┐                      │
│    ▼         ▼                      │
│ 管理列表   获取行情                   │
│    │         │                      │
│    ▼         ▼                      │
│ JSON文件  StockSpotFetcher          │
└─────────────────────────────────────┘
```

## 接口设计

### 命令行参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `--add` | str | 添加股票，逗号分隔 |
| `--add-file` | str | 从文件添加，每行一个代码 |
| `--remove` | str | 移除股票 |
| `--list` | flag | 列出所有自选股 |
| `--clear` | flag | 清空自选股 |
| `--watch` | flag | 获取实时行情 |
| `--analyze` | flag | 快速分析 |
| `--top-n` | int | 限制显示数量 |

### 行为设计

**add**：
1. 读取现有列表
2. 去重添加新股票
3. 保存列表
4. 输出添加结果

**remove**：
1. 读取现有列表
2. 移除指定股票
3. 保存列表
4. 输出移除结果

**list**：
1. 读取列表
2. 格式化输出

**clear**：
1. 确认提示（需要 --yes 跳过）
2. 清空列表
3. 输出结果

**watch**：
1. 读取列表
2. 调用 StockSpotFetcher 获取行情
3. 筛选出自选股数据
4. 格式化输出

**analyze**：
1. 读取列表
2. 获取行情数据
3. 统计分析（涨跌数量、平均涨幅、异动股票）
4. 输出分析结果

## 数据结构

### 自选股列表文件

```json
{
  "stocks": [
    {
      "code": "000001",
      "added_at": "2026-03-07",
      "note": "银行龙头"
    }
  ],
  "updated_at": "2026-03-07T08:00:00"
}
```

### 行情数据（复用 StockSpotFetcher）

```python
@dataclass
class StockSpot:
    code: str
    name: str
    price: float
    change_pct: float
    change: float
    volume: float
    amount: float
    turnover_rate: float
    market_cap: float
```

### 分析结果

```python
@dataclass
class WatchlistSummary:
    total: int           # 总数
    up_count: int        # 上涨数
    down_count: int      # 下跌数
    flat_count: int      # 平盘数
    avg_change: float    # 平均涨跌幅
    best: StockSpot      # 表现最好
    worst: StockSpot     # 表现最差
    limit_up: list       # 涨停股
    limit_down: list     # 跌停股
```

## 输出格式

### watch 输出

```
自选股行情 (共 5 只)
====================
代码     名称        现价    涨跌幅   成交额(亿)  换手率
000001  平安银行    12.50   +2.35%    15.6      3.2%
600000  浦发银行     8.20   -0.50%     8.2      1.5%
...

统计: 3涨 2跌 平均 +1.2%
```

### analyze 输出

```
自选股分析报告
=============

市场统计:
  总数: 5
  上涨: 3 (60%)
  下跌: 2 (40%)
  平均涨跌幅: +1.2%

表现最好:
  平安银行(000001): +2.35%

表现最差:
  浦发银行(600000): -0.50%

异动提醒:
  无
```

## 异常处理

| 场景 | 处理 |
|------|------|
| 列表为空 | 提示 "自选股列表为空，请先添加" |
| 股票代码无效 | 添加时提示，不保存无效代码 |
| 行情获取失败 | 跳过失败股票，显示已获取的数据 |
| 文件读取失败 | 创建新文件 |

## 测试策略

1. **列表管理测试**：添加、移除、清空操作
2. **去重测试**：重复添加同一股票
3. **行情筛选测试**：从全量数据中筛选自选股
4. **统计分析测试**：验证统计计算正确性
5. **边界情况**：空列表、单个股票、大量股票
