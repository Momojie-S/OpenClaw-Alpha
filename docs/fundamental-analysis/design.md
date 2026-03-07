# 基本面分析 - 设计文档

> 创建日期：2026-03-07

---

## 一、技术选型

### 1.1 数据源选择

| 数据源 | 用途 | 原因 |
|--------|------|------|
| **AKShare** | 主数据源 | 免费、稳定、覆盖广 |
| Tushare | 备用 | 需积分、速度慢 |

### 1.2 核心接口

#### 财务分析指标（`stock_financial_analysis_indicator_em`）

**功能**：获取财务分析主要指标（ROE、EPS、资产负债率等）

**参数**：
- `symbol`: 股票代码（带后缀，如 `000001.SZ`）
- `indicator`: 查询方式（`"按报告期"` 或 `"按单季度"`）

**关键字段**：
| 字段 | 说明 | 单位 |
|------|------|------|
| `SECUCODE` | 股票代码 | - |
| `SECURITY_NAME_ABBR` | 股票名称 | - |
| `REPORT_DATE` | 报告日期 | - |
| `ROEJQ` | ROE(加权) | % |
| `EPSJB` | 每股收益 | 元 |
| `BPS` | 每股净资产 | 元 |
| `ZCFZL` | 资产负债率 | % |
| `LD` | 流动比率 | - |
| `SD` | 速动比率 | - |
| `MGJYXJJE` | 每股经营现金流 | 元 |
| `XSJLL` | 销售净利率 | % |
| `XSMLL` | 销售毛利率 | % |
| `YYZSRGDHBZC` | 营收同比增长 | % |
| `NETPROFITRPHBZC` | 净利润同比增长 | % |

#### 估值数据（`stock_zh_valuation_baidu`）

**功能**：获取 PE、PB、市值等估值指标的历史数据

**参数**：
- `symbol`: 股票代码（6 位数字，如 `000001`）
- `indicator`: 指标类型
  - `"总市值"`
  - `"市盈率(TTM)"`
  - `"市盈率(静)"`
  - `"市净率"`
  - `"市现率"`
- `period`: 时间范围（`"近一年"`、`"近三年"` 等）

**关键字段**：
| 字段 | 说明 |
|------|------|
| `date` | 日期 |
| `value` | 指标值 |

---

## 二、架构设计

### 2.1 模块结构

```
skills/fundamental_analysis/
├── SKILL.md                      # 能力说明
└── scripts/
    ├── __init__.py
    ├── financial_fetcher/        # 财务指标 Fetcher
    │   ├── __init__.py
    │   ├── financial_fetcher.py  # 入口类
    │   └── akshare.py            # AKShare 实现
    ├── valuation_fetcher/        # 估值数据 Fetcher
    │   ├── __init__.py
    │   ├── valuation_fetcher.py  # 入口类
    │   └── akshare.py            # AKShare 实现
    └── fundamental_processor/    # 基本面分析 Processor
        ├── __init__.py
        └── fundamental_processor.py
```

### 2.2 职责分离

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **FinancialFetcher** | 获取财务指标 | 股票代码 | 财务指标 DataFrame |
| **ValuationFetcher** | 获取估值数据 | 股票代码 + 指标类型 | 估值时间序列 DataFrame |
| **FundamentalProcessor** | 综合分析 | 股票代码 | 基本面分析报告 |

---

## 三、接口设计

### 3.1 FinancialFetcher

**入口函数**：`fetch_financial(code: str) -> pd.DataFrame`

**参数**：
- `code`: 股票代码（如 `"000001"`）

**返回**：财务指标 DataFrame（最新一期）

**字段映射**：
```python
{
    "code": "SECUCODE",
    "name": "SECURITY_NAME_ABBR",
    "report_date": "REPORT_DATE",
    "roe": "ROEJQ",
    "eps": "EPSJB",
    "bps": "BPS",
    "debt_ratio": "ZCFZL",
    "current_ratio": "LD",
    "quick_ratio": "SD",
    "cash_per_share": "MGJYXJJE",
    "net_profit_margin": "XSJLL",
    "gross_profit_margin": "XSMLL",
    "revenue_growth": "YYZSRGDHBZC",
    "profit_growth": "NETPROFITRPHBZC",
}
```

### 3.2 ValuationFetcher

**入口函数**：`fetch_valuation(code: str, indicator: str, period: str = "近一年") -> pd.DataFrame`

**参数**：
- `code`: 股票代码（如 `"000001"`）
- `indicator`: 指标类型（`"pe_ttm"`, `"pb"`, `"market_cap"`）
- `period`: 时间范围（默认 `"近一年"`）

**返回**：估值时间序列 DataFrame

**字段**：`["date", "value"]`

### 3.3 FundamentalProcessor

**入口函数**：`analyze(code: str, include_history: bool = False) -> dict`

**参数**：
- `code`: 股票代码
- `include_history`: 是否包含估值历史数据

**返回**：
```python
{
    "code": "000001",
    "name": "平安银行",
    "report_date": "2025-09-30",
    "valuation": {
        "pe_ttm": 4.87,
        "pe_rating": "低估",  # < 15
        "pb": 0.47,
        "pb_rating": "低估",  # < 1.5
    },
    "profitability": {
        "roe": 8.28,
        "roe_rating": "一般",  # 5-10
        "eps": 1.87,
        "net_margin": None,  # 银行业不适用
    },
    "growth": {
        "revenue_growth": -9.78,
        "profit_growth": -3.50,
        "growth_rating": "下滑",
    },
    "financial_health": {
        "debt_ratio": 91.01,
        "debt_rating": "风险",  # > 70%（银行业特殊）
        "current_ratio": None,  # 银行业不适用
    },
    "history": {  # 可选
        "pe": [{"date": "2026-03-07", "value": 4.87}, ...],
        "pb": [{"date": "2026-03-07", "value": 0.47}, ...],
    },
    "summary": "估值偏低，但 ROE 一般，营收下滑需关注",
}
```

---

## 四、评级逻辑

### 4.1 估值评级

| 指标 | 条件 | 评级 |
|------|------|------|
| PE | < 15 | 低估 |
| PE | 15-25 | 合理 |
| PE | > 25 | 高估 |
| PB | < 1.5 | 低估 |
| PB | 1.5-3 | 合理 |
| PB | > 3 | 高估 |

### 4.2 ROE 评级

| 条件 | 评级 |
|------|------|
| > 15% | 优秀 |
| 10-15% | 良好 |
| 5-10% | 一般 |
| < 5% | 较差 |

### 4.3 成长性评级

| 条件 | 评级 |
|------|------|
| 营收增长 > 20% 且 利润增长 > 20% | 高增长 |
| 营收增长 > 0 且 利润增长 > 0 | 稳定增长 |
| 营收增长 < 0 或 利润增长 < 0 | 下滑 |
| 营收增长 < -10% 或 利润增长 < -10% | 大幅下滑 |

### 4.4 资产负债率评级

| 条件 | 评级 |
|------|------|
| < 40% | 健康 |
| 40-60% | 正常 |
| 60-70% | 关注 |
| > 70% | 风险 |

**注**：金融行业（银行、保险）特殊处理，资产负债率 > 90% 为正常。

---

## 五、异常处理

### 5.1 无效股票代码

- 检查格式（6 位数字）
- API 返回空数据时，提示"无效股票代码"

### 5.2 无数据

- 新股可能缺少财务数据
- 返回 `None` 并在 summary 中说明

### 5.3 网络错误

- 重试 3 次（指数退避）
- 最终失败返回错误信息

---

## 六、性能考虑

- 单只股票查询 < 3 秒
- 批量查询建议并发（后续扩展）
- 使用缓存减少重复查询（后续优化）

---

## 七、测试策略

### 7.1 单元测试

- FinancialFetcher 转换逻辑
- ValuationFetcher 转换逻辑
- FundamentalProcessor 评级逻辑
- 边界情况（空数据、异常值）

### 7.2 集成测试

- 真实股票代码测试（000001、600000 等）
- 多种行业股票测试
