# 指数分析 Skill - 设计文档

> 版本: v1.0
> 创建时间: 2026-03-07

---

## 一、技术选型

### 1.1 数据源

**优先选择 AKShare**：
- 免费无积分限制
- 接口稳定
- 已有使用经验

**备选 Tushare**：
- 需要 120 积分
- 数据更全面

### 1.2 核心接口

| 接口 | 用途 | 数据源 |
|------|------|--------|
| `stock_zh_index_daily_em` | 指数历史行情 | AKShare |
| `index_dailybasic` | 指数基本面 | Tushare（备选） |

### 1.3 设计决策

1. **单数据源**：第一版只用 AKShare，保持简单
2. **单一 Fetcher**：所有指数行情用一个 IndexFetcher
3. **轻量 Processor**：只做数据加工和趋势判断

---

## 二、架构设计

### 2.1 目录结构

```
skills/index_analysis/
├── SKILL.md                    # 能力说明
└── scripts/
    ├── __init__.py
    ├── index_fetcher/          # 指数行情获取
    │   ├── __init__.py
    │   ├── index_fetcher.py    # 入口类
    │   └── akshare.py          # AKShare 实现
    └── index_processor/        # 指数分析
        ├── __init__.py
        └── index_processor.py  # 分析脚本
```

### 2.2 数据流

```
AKShare API
     │
     ▼
IndexFetcherAkshare
     │ fetch(symbol, start_date, end_date)
     ▼
IndexFetcher（入口）
     │
     ▼
IndexProcessor
     │ - 获取6个指数数据
     │ - 计算均线（MA5, MA20）
     │ - 判断趋势
     │ - 计算市场温度
     │ - 排序强弱
     ▼
输出（控制台 + 文件）
```

---

## 三、模块设计

### 3.1 IndexFetcher

**职责**：获取单个指数的历史行情数据

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| symbol | str | 是 | 指数代码（如 sh000001） |
| start_date | str | 否 | 开始日期（YYYYMMDD） |
| end_date | str | 否 | 结束日期（YYYYMMDD） |

**返回**：
```python
[
    {
        "date": "2026-03-07",
        "open": 3340.5,
        "high": 3358.2,
        "low": 3335.1,
        "close": 3345.67,
        "volume": 320000000,  # 成交量（股）
        "amount": 38500000000  # 成交额（元）
    },
    ...
]
```

### 3.2 IndexProcessor

**职责**：分析多个指数，输出综合报告

**参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| --date | str | 今天 | 分析日期 |
| --top-n | int | 6 | 返回指数数量 |

**处理流程**：

1. **获取数据**：调用 IndexFetcher 获取6个指数的历史数据
2. **计算均线**：MA5 = 最近5个交易日收盘价均值，MA20 同理
3. **判断趋势**：基于价格与均线的关系
4. **计算温度**：基于各指数涨跌幅统计
5. **排序强弱**：按涨跌幅排序
6. **输出结果**：控制台输出精简，文件保存完整

---

## 四、数据模型

### 4.1 指数配置

```python
CORE_INDICES = [
    {"name": "上证指数", "code": "sh000001", "type": "主板"},
    {"name": "深证成指", "code": "sz399001", "type": "主板"},
    {"name": "沪深300", "code": "sh000300", "type": "主板"},
    {"name": "创业板指", "code": "sz399006", "type": "成长"},
    {"name": "科创50", "code": "sh000688", "type": "成长"},
    {"name": "中证500", "code": "sh000905", "type": "中盘"},
]
```

### 4.2 输出结构

```python
{
    "date": "2026-03-07",
    "market_temperature": "正常",  # 过热/温热/正常/偏冷/过冷
    "overall_trend": "震荡",       # 强势上涨/震荡上涨/震荡/震荡下跌/弱势下跌
    "strongest": {"name": "创业板指", "change_pct": 1.5},
    "weakest": {"name": "上证指数", "change_pct": -0.3},
    "indices": [
        {
            "name": "上证指数",
            "code": "sh000001",
            "type": "主板",
            "close": 3345.67,
            "change_pct": -0.3,
            "change_points": -10.05,
            "open": 3340.5,
            "high": 3358.2,
            "low": 3335.1,
            "volume": "3.2亿",
            "amount": "3850亿",
            "ma5": 3352.1,
            "ma20": 3310.5,
            "trend": "震荡"
        },
        ...
    ]
}
```

---

## 五、趋势判断逻辑

### 5.1 单指数趋势

```python
def judge_trend(close, ma5, ma20, change_pct):
    if close > ma5 > ma20 and change_pct > 1:
        return "强势上涨"
    elif ma5 > ma20 and 0 < change_pct <= 1:
        return "震荡上涨"
    elif abs(ma5 - ma20) / ma20 < 0.01 and abs(change_pct) < 1:
        return "震荡"
    elif ma5 < ma20 and -1 <= change_pct < 0:
        return "震荡下跌"
    elif close < ma5 < ma20 and change_pct < -1:
        return "弱势下跌"
    else:
        return "震荡"
```

### 5.2 市场温度

```python
def calc_temperature(indices):
    up_count = sum(1 for i in indices if i["change_pct"] > 2)
    warm_count = sum(1 for i in indices if i["change_pct"] > 1)
    down_count = sum(1 for i in indices if i["change_pct"] < -2)
    cold_count = sum(1 for i in indices if i["change_pct"] < -1)
    
    if up_count >= 3:
        return "过热"
    elif warm_count >= 2:
        return "温热"
    elif down_count >= 3:
        return "过冷"
    elif cold_count >= 2:
        return "偏冷"
    else:
        return "正常"
```

---

## 六、异常处理

| 异常情况 | 处理方式 |
|----------|----------|
| 网络超时 | 重试3次，指数退避 |
| 指数代码无效 | 跳过该指数，继续处理其他 |
| 数据不完整 | 使用默认值或标记为空 |
| 非交易日 | 返回最近交易日数据 |

---

## 七、测试策略

### 7.1 Fetcher 测试

- 转换逻辑测试（3-5个用例）
- 字段映射测试
- 边界情况测试

### 7.2 Processor 测试

- 均线计算测试
- 趋势判断测试（5种趋势各1个）
- 市场温度测试（5种温度各1个）
- 强弱排序测试

---

## 八、与现有 Skills 的关系

| Skill | 关系 |
|-------|------|
| market_sentiment | 指数分析提供市场温度，情绪分析提供涨跌家数、资金流向 |
| industry_trend | 指数是大盘，产业是中观，可联动分析 |
| stock_analysis | 指数提供宏观背景，个股提供微观分析 |
| stock_screener | 筛选时参考指数趋势 |

**联动场景**：
1. 指数下跌 → 查看哪些板块抗跌（industry_trend）
2. 指数上涨 → 筛选强势股（stock_screener）
3. 市场温度过热 → 提醒风险
