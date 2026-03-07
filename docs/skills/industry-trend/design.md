# 设计文档：产业热度追踪

## 一、技术选型

### 1.1 数据源

| 数据源 | 板块类型 | 接口 | 积分要求 |
|--------|----------|------|----------|
| Tushare | 申万行业（一级/二级/三级） | `index_classify` + `sw_daily` | 2000 + 5000 |
| AKShare | 概念板块 | `stock_board_concept_name_em` 等 | 无 |

**优先级**：Tushare > AKShare

**当前积分（5000）限制**：
- 申万行业：✅ 可用
- 概念板块：❌ Tushare 需要 6000 积分，只能用 AKShare

### 1.2 为什么这样选择

- **Tushare 申万行业**：官方分类标准，数据质量高，支持三级分类
- **Tushare 概念板块**：同花顺分类，数据质量高，但需要 6000 积分
- **AKShare 概念板块**：免费备选，当 Tushare 积分不足时使用

## 二、架构设计

### 2.1 Fetcher 设计

```
industry_fetcher/         # 行业板块 Fetcher
├── __init__.py
├── industry_fetcher.py   # IndustryFetcher（入口）
├── tushare.py            # IndustryFetcherTushare
└── akshare.py            # IndustryFetcherAkshare（备用）

concept_fetcher/          # 概念板块 Fetcher
├── __init__.py
├── concept_fetcher.py    # ConceptFetcher（入口）
└── akshare.py            # ConceptFetcherAkshare（仅 AKShare）
```

### 2.2 Processor 设计

```
industry_trend_processor/
├── __init__.py
└── industry_trend_processor.py   # 热度计算 + 排名
```

### 2.3 数据流

```
用户 → SKILL.md → Processor
              ↓
         Fetcher.fetch()
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
Tushare             AKShare
    ↓                   ↓
    └─────────┬─────────┘
              ↓
         数据转换
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
控制台 Top N      文件完整数据
```

## 三、接口设计

### 3.1 行业板块 Fetcher

**输入**：
```python
{
    "category": "L1" | "L2" | "L3",  # 行业层级
    "date": "2026-03-06"             # 日期（默认当日）
}
```

**输出**：
```python
[
    {
        "name": "电子",
        "code": "801080.SI",
        "level": "L1",
        "date": "2026-03-06",
        "metrics": {
            "close": 3500.5,
            "pct_change": 3.5,
            "amount": 120000,      # 万元
            "turnover_rate": 8.2,
            "float_mv": 500000     # 万元
        }
    },
    ...
]
```

### 3.2 概念板块 Fetcher

**输入**：
```python
{
    "date": "2026-03-06"  # 日期（默认当日）
}
```

**输出**：
```python
[
    {
        "name": "AI",
        "code": "...",
        "date": "2026-03-06",
        "metrics": {
            "close": ...,
            "pct_change": ...,
            "amount": ...,
            "turnover_rate": ...,
            "float_mv": ...
        }
    },
    ...
]
```

### 3.3 热度计算 Processor

**命令行参数**：
```bash
uv run --env-file .env python skills/industry-trend/scripts/industry_trend_processor/industry_trend_processor.py \
    --category L1 \      # 行业层级（L1/L2/L3/concept）
    --date 2026-03-06 \  # 日期（默认当日）
    --top-n 10           # 返回 Top N（默认 10）
```

**控制台输出**：
```json
[
    {
        "rank": 1,
        "name": "电子",
        "heat_index": 85.2,
        "trend": "加热中",
        "change_pct": 3.5
    },
    ...
]
```

**文件输出**（`.openclaw_alpha/industry-trend/{date}/heat.json`）：
```json
{
    "date": "2026-03-06",
    "category": "L1",
    "weights": {
        "change": 0.30,
        "turnover": 0.25,
        "volume_ratio": 0.25,
        "up_ratio": 0.20
    },
    "boards": [
        {
            "name": "电子",
            "code": "801080.SI",
            "heat_index": 85.2,
            "scores": {
                "change": 28.5,
                "turnover": 22.1,
                "volume_ratio": 20.3,
                "up_ratio": 14.3
            },
            "metrics": {
                "change_pct": 3.5,
                "turnover_rate": 8.2,
                "amount": 120000,
                "float_mv": 500000,
                "volume_ratio": 12.5
            },
            "trend": "加热中",
            "heat_change": 25.3
        },
        ...
    ]
}
```

## 四、算法设计

### 4.1 热度指数计算

**步骤**：
1. 计算各维度原始值
2. 归一化到 0-100 分
3. 加权求和

**归一化方法**（Min-Max）：
```
score = (value - min) / (max - min) * 100
```

**热度指数**：
```
heat_index = change_score * 0.30
           + turnover_score * 0.25
           + volume_ratio_score * 0.25
           + up_ratio_score * 0.20
```

### 4.2 趋势信号判断

```
if heat_change > 20 and change_pct > 0:
    trend = "加热中"
elif heat_change < -20 or change_pct < -3:
    trend = "降温中"
else:
    trend = "稳定"
```

### 4.3 成交额占比计算

```
volume_ratio = board_amount / total_market_amount * 100
```

需要获取全市场总成交额（可能需要额外接口或汇总）。

### 4.4 涨跌家数比

```
up_ratio = up_count / (up_count + down_count) * 100
```

需要获取板块成分股数据（`index_member_all` 接口）。

## 五、数据源接口

### 5.1 Tushare 行业分类

详见 [index_classify.md](../references/tushare/index_classify.md)

**关键信息**：
- 接口：`pro.index_classify(level='L1', src='SW2021')`
- 积分：2000
- 返回：行业代码、名称、层级

### 5.2 Tushare 行业日线

详见 [sw_daily.md](../references/tushare/sw_daily.md)

**关键信息**：
- 接口：`pro.sw_daily(trade_date='20260306')`
- 积分：5000
- 返回：涨跌幅、成交额、换手率、流通市值等

### 5.3 Tushare 行业成分股

详见 [index_member_all.md](../references/tushare/index_member_all.md)（待补充）

**关键信息**：
- 用于计算涨跌家数比
- 积分：待确认

### 5.4 AKShare 概念板块

详见 [stock_board_concept_name_em.md](../references/akshare/stock_board_concept_name_em.md)（待补充）

**关键信息**：
- 接口：`ak.stock_board_concept_name_em()`
- 积分：无
- 返回：概念板块列表

## 六、关键发现

### 6.1 涨跌家数数据

**概念板块（AKShare）**：
- `stock_board_concept_name_em` 直接返回 `上涨家数` 和 `下跌家数`
- 无需额外计算

**申万行业（Tushare）**：
- 需要通过 `index_member_all` 获取成分股列表
- 再逐个查询成分股当日涨跌情况
- 计算量大，可能影响性能

**优化方案**：
- 概念板块：直接使用 AKShare 提供的涨跌家数
- 申万行业：第一版暂不计算涨跌家数，调整权重分配

### 6.2 全市场成交额

需要确认获取方式：
- 方案1：汇总所有板块成交额
- 方案2：通过大盘指数（如上证指数）获取
- 方案3：第一版不计算成交额占比，调整权重分配

## 七、边界处理

### 7.1 数据缺失

- 某个维度数据缺失时，重新分配权重
- 例如：涨跌家数缺失 → 权重分配给其他三个维度

### 7.2 新股/新板块

- 首日无环比数据 → 趋势信号标记为"新"

### 7.3 停牌/数据异常

- 过滤掉无交易数据的板块
- 数据异常时记录日志，不中断流程
