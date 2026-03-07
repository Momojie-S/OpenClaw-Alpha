# 设计文档：北向资金追踪

> 版本: v1.0
> 创建时间: 2026-03-07

---

## 一、技术选型

### 1.1 数据源

| 数据 | 数据源 | 接口 | 积分要求 |
|------|--------|------|----------|
| 每日净流入 | AKShare | stock_em_hsgt_north_net_flow_in | 免费 |
| 个股资金流向 | AKShare | stock_hsgt_hold_stock_em | 免费 |
| 历史趋势 | AKShare | stock_em_hsgt_north_net_flow_in | 免费 |

**选择 AKShare 的原因**：
- 免费无积分限制
- 数据源来自东方财富，更新及时
- 接口稳定，使用广泛

### 1.2 架构设计

遵循项目 Fetcher + Processor 架构：
- **FlowFetcher**：获取北向资金净流入数据
- **StockFetcher**：获取个股资金流向数据
- **NorthboundProcessor**：分析资金动向

## 二、数据模型

### 2.1 每日净流入

```python
@dataclass
class DailyFlow:
    """每日净流入"""
    date: str              # 日期 YYYY-MM-DD
    sh_flow: float         # 沪股通净流入（亿元）
    sz_flow: float         # 深股通净流入（亿元）
    total_flow: float      # 合计净流入（亿元）
    status: str            # 状态：大幅流入/流入/平衡/流出/大幅流出
```

### 2.2 个股资金流向

```python
@dataclass
class StockFlow:
    """个股资金流向"""
    code: str              # 股票代码
    name: str              # 股票名称
    hold_change: float     # 持仓变化（万元）
    hold_ratio: float      # 持股比例变化（%）
    direction: str         # 方向：流入/流出
```

### 2.3 资金趋势

```python
@dataclass
class FlowTrend:
    """资金趋势"""
    period: int            # 天数
    total_inflow: float    # 累计净流入（亿元）
    avg_inflow: float      # 日均净流入（亿元）
    inflow_days: int       # 净流入天数
    outflow_days: int      # 净流出天数
    trend: str             # 趋势：持续流入/持续流出/震荡
```

## 三、Processor 设计

### 3.1 命令行参数

```bash
uv run --env-file .env python skills/northbound_flow/scripts/northbound_processor/northbound_processor.py \
    [--action daily|stock|trend] \
    [--date YYYY-MM-DD] \
    [--days 5|10|20] \
    [--top-n 10]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --action | 查询类型 | daily |
| --date | 查询日期 | 今天 |
| --days | 趋势天数 | 5 |
| --top-n | Top N | 10 |

### 3.2 输出格式

**daily（每日净流入）**：
```json
{
  "date": "2026-03-07",
  "sh_flow": 25.3,
  "sz_flow": 18.7,
  "total_flow": 44.0,
  "status": "流入"
}
```

**stock（个股流向）**：
```json
{
  "date": "2026-03-07",
  "top_inflow": [
    {"name": "贵州茅台", "hold_change": 85000, "hold_ratio": 0.05},
    ...
  ],
  "top_outflow": [
    {"name": "宁德时代", "hold_change": -42000, "hold_ratio": -0.03},
    ...
  ]
}
```

**trend（资金趋势）**：
```json
{
  "period": 5,
  "total_inflow": 120.5,
  "avg_inflow": 24.1,
  "inflow_days": 3,
  "outflow_days": 2,
  "trend": "持续流入",
  "daily_data": [...]
}
```

## 四、文件组织

```
skills/northbound_flow/
├── SKILL.md
└── scripts/
    ├── __init__.py
    ├── flow_fetcher/
    │   ├── __init__.py
    │   ├── flow_fetcher.py
    │   └── akshare.py
    └── northbound_processor/
        ├── __init__.py
        └── northbound_processor.py
```

## 五、实现要点

### 5.1 FlowFetcher

只使用 AKShare 实现，接口：
- `stock_em_hsgt_north_net_flow_in()` - 每日净流入
- `stock_hsgt_hold_stock_em()` - 个股持股

### 5.2 数据转换

1. 日期格式：YYYYMMDD → YYYY-MM-DD
2. 净流入单位：亿元
3. 个股持仓变化：万元

### 5.3 状态判断

| 净流入范围 | 状态 |
|------------|------|
| > 50 亿 | 大幅流入 |
| 10 ~ 50 亿 | 流入 |
| -10 ~ 10 亿 | 平衡 |
| -50 ~ -10 亿 | 流出 |
| < -50 亿 | 大幅流出 |

### 5.4 趋势判断

| 条件 | 趋势 |
|------|------|
| 净流入天数 >= 总天数 * 0.7 | 持续流入 |
| 净流出天数 >= 总天数 * 0.7 | 持续流出 |
| 其他 | 震荡 |
