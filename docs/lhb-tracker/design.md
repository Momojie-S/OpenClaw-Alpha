# 龙虎榜追踪 - 设计文档

## 技术选型

**数据源**：AKShare（免费）

**选择理由**：
- AKShare 龙虎榜接口稳定，基于东方财富数据
- 免费，无积分要求
- 接口丰富，覆盖每日龙虎榜、个股详情、营业部追踪

## 核心接口

### 1. 每日龙虎榜

**接口**：`stock_lhb_detail_em(start_date, end_date)`

**用途**：获取指定日期范围内所有上榜股票

**关键字段**：
- 代码、名称
- 上榜原因
- 买入金额、卖出金额
- 净买入金额

### 2. 个股龙虎榜详情

**接口**：`stock_lhb_stock_detail_em(symbol, start_date, end_date)`

**用途**：获取指定股票的上榜历史

**关键字段**：
- 交易日期
- 买入方（机构/营业部）
- 卖出方（机构/营业部）
- 买卖金额

## 架构设计

```
lhb_tracker/
├── scripts/
│   ├── __init__.py
│   ├── lhb_fetcher/           # 龙虎榜数据获取
│   │   ├── __init__.py
│   │   ├── lhb_fetcher.py     # Fetcher 入口
│   │   └── akshare.py         # AKShare 实现
│   └── lhb_processor/         # 龙虎榜分析
│       ├── __init__.py
│       └── lhb_processor.py   # Processor 脚本
└── SKILL.md
```

## Fetcher 设计

### LhbFetcher

**职责**：获取龙虎榜原始数据

**方法**：
- `fetch_daily(date)` - 获取每日龙虎榜
- `fetch_stock_history(symbol, start_date, end_date)` - 获取个股历史

**返回数据**：
```python
# 每日龙虎榜
[
    {
        "code": "000001",
        "name": "平安银行",
        "close": 10.5,
        "change_pct": 9.98,
        "reason": "涨停",
        "buy_amount": 500000000,  # 买入金额（元）
        "sell_amount": 300000000,  # 卖出金额（元）
        "net_buy": 200000000,  # 净买入（元）
    },
    ...
]

# 个股历史
[
    {
        "date": "2026-03-06",
        "reason": "涨停",
        "buyers": [
            {"name": "机构专用", "type": "机构", "amount": 100000000},
            {"name": "华泰证券XX营业部", "type": "游资", "amount": 50000000},
        ],
        "sellers": [
            {"name": "机构专用", "type": "机构", "amount": 30000000},
        ],
        "net_buy": 120000000,
    },
    ...
]
```

## Processor 设计

### LhbProcessor

**功能**：
1. 获取每日龙虎榜数据
2. 按净买入金额排序
3. 识别买卖方类型（机构/游资/北向）
4. 输出精简结果 + 完整数据

**命令行参数**：
- `--action`: 操作类型（daily/stock）
- `--date`: 日期（默认今天）
- `--symbol`: 股票代码（stock 模式必需）
- `--days`: 历史天数（stock 模式，默认 5）
- `--top-n`: 返回数量（默认 10）

**输出示例**：

```json
// 每日龙虎榜
{
  "date": "2026-03-06",
  "total_count": 50,
  "top_inflow": [
    {
      "code": "000001",
      "name": "平安银行",
      "net_buy": 200000000,
      "reason": "涨停",
      "buy_type": "机构+游资"
    },
    ...
  ],
  "top_outflow": [...]
}

// 个股龙虎榜
{
  "symbol": "000001",
  "name": "平安银行",
  "period": "2026-03-01 ~ 2026-03-06",
  "summary": {
    "appearances": 3,
    "total_net_buy": 500000000,
    "org_buy": 300000000,
    "retail_buy": 200000000
  },
  "details": [...]
}
```

## 买卖方类型识别

| 名称模式 | 类型 |
|---------|------|
| 机构专用 | 机构 |
| 深股通/沪股通 | 北向资金 |
| XX证券XX营业部 | 游资 |

## 数据格式约定

- 金额单位：元
- 净买入 = 买入金额 - 卖出金额
- 正值表示净流入，负值表示净流出

## 注意事项

1. **数据延迟**：龙虎榜数据 T+1 发布
2. **非交易日**：返回最近交易日数据
3. **交易时间**：盘中数据可能有延迟
