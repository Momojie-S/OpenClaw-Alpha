# ETF 分析 Skill - 设计文档

## 一、技术选型

### 数据源

| 数据源 | 接口 | 用途 | 稳定性 |
|--------|------|------|--------|
| 新浪 | `fund_etf_category_sina` | 实时行情 | ✅ 稳定 |
| 新浪 | `fund_etf_hist_sina` | 历史数据 | ✅ 稳定 |
| 上交所 | `fund_etf_scale_sse` | 规模数据 | ✅ 稳定 |

**决策**：使用新浪数据源作为主要数据源，稳定且无需认证。

### 架构

```
skills/etf_analysis/
├── SKILL.md
└── scripts/
    ├── __init__.py
    └── etf_processor/
        ├── __init__.py
        └── etf_processor.py
```

**决策**：不需要独立的 Fetcher，直接在 Processor 中调用 AKShare 接口。原因：
1. 接口简单，无需多数据源支持
2. 新浪接口稳定可靠
3. 减少代码复杂度

## 二、接口设计

### Processor 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--action` | str | spot | 操作：spot/history |
| `--symbol` | str | - | ETF 代码（history 必填） |
| `--change-min` | float | - | 涨跌幅下限 |
| `--change-max` | float | - | 涨跌幅上限 |
| `--amount-min` | float | - | 成交额下限（亿） |
| `--keyword` | str | - | 名称关键词 |
| `--sort-by` | str | change | 排序字段：change/amount/price |
| `--top-n` | int | 20 | 返回数量 |
| `--days` | int | 30 | 历史天数 |

### 输出格式

**实时行情**：
```json
[
  {
    "code": "sz159915",
    "name": "创业板ETF",
    "price": 2.123,
    "change_pct": 1.52,
    "amount": 5.5,
    "volume": 2500000
  }
]
```

**历史数据**：
```json
{
  "code": "sz159915",
  "name": "创业板ETF",
  "data": [
    {
      "date": "2026-03-06",
      "open": 2.100,
      "high": 2.150,
      "low": 2.090,
      "close": 2.123,
      "volume": 2500000
    }
  ]
}
```

## 三、数据字段映射

### 实时行情

| API 字段 | 输出字段 | 说明 |
|----------|----------|------|
| 代码 | code | ETF 代码 |
| 名称 | name | ETF 名称 |
| 最新价 | price | 最新价 |
| 涨跌幅 | change_pct | 涨跌幅 (%) |
| 涨跌额 | change | 涨跌额 |
| 成交额 | amount | 成交额（转换为亿） |
| 成交量 | volume | 成交量 |

### 历史数据

| API 字段 | 输出字段 | 说明 |
|----------|----------|------|
| date | date | 日期 |
| open | open | 开盘价 |
| high | high | 最高价 |
| low | low | 最低价 |
| close | close | 收盘价 |
| volume | volume | 成交量 |
| amount | amount | 成交额 |

## 四、筛选逻辑

1. **涨跌幅筛选**：`change_min <= 涨跌幅 <= change_max`
2. **成交额筛选**：`amount_min <= 成交额（亿）`
3. **关键词筛选**：名称包含关键词（不区分大小写）
4. **排序**：按指定字段降序

## 五、边界处理

- 非交易日返回空数据
- 筛选条件为空时返回全部
- 历史数据限制最多 365 天
