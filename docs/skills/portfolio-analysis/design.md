# 持仓分析 Skill - 设计文档

## 技术选型

**数据源**：AKShare（免费、稳定）
- 复用 `stock_screener` 的 `StockSpotFetcher` 获取实时行情
- 新建 `IndustryInfoFetcher` 获取股票行业信息

**理由**：
- 行情数据已在 `stock_screener` 实现，可直接复用
- AKShare 的 `stock_individual_info_em` 接口可获取个股行业信息
- 无需额外积分要求

## 架构设计

```
portfolio_analysis/
├── SKILL.md
└── scripts/
    ├── __init__.py
    ├── industry_fetcher/
    │   ├── __init__.py
    │   ├── industry_fetcher.py
    │   └── akshare.py
    └── portfolio_processor/
        ├── __init__.py
        └── portfolio_processor.py
```

**复用**：直接导入 `stock_screener` 的 `StockSpotFetcher`

```
from skills.stock_screener.scripts.stock_spot_fetcher import fetch as fetch_spot
```

## 数据流

```
用户持仓输入
     │
     ▼
┌─────────────────────────────────────┐
│     PortfolioProcessor              │
│                                     │
│  1. 解析持仓输入                     │
│  2. 获取各股实时行情（复用 Fetcher）  │
│  3. 获取各股行业信息                 │
│  4. 计算持仓权重                     │
│  5. 统计行业分布                     │
│  6. 检查风险规则                     │
│  7. 输出结果                         │
└─────────────────────────────────────┘
```

## 接口设计

### 输入格式

**命令行**：
```bash
# 简单模式（无成本价）
--holdings "000001:1000,600000:500"

# 完整模式（含成本价）
--holdings "000001:1000:12.5,600000:500:8.2"

# 文件模式
--file portfolio.json
```

**JSON 文件**：
```json
{
  "holdings": [
    {"code": "000001", "shares": 1000, "cost": 12.5},
    {"code": "600000", "shares": 500}
  ]
}
```

### IndustryInfoFetcher

**接口**：`stock_individual_info_em`
**参数**：`symbol`（股票代码，6位数字）
**返回字段**：
- `行业`：所属行业

**注意**：此接口是按个股查询，需要批量获取

### PortfolioProcessor

**命令行参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--holdings` | str | - | 持仓字符串 |
| `--file` | str | - | JSON 文件路径 |
| `--date` | str | 今天 | 分析日期 |

**输出**：
- 控制台：精简摘要
- 文件：`.openclaw_alpha/portfolio-analysis/{date}/portfolio.json`

## 计算逻辑

### 持仓权重

```
单股市值 = 当前价格 × 持股数
总市值 = Σ 单股市值
单股权重 = 单股市值 / 总市值 × 100%
```

### 行业权重

```
行业市值 = Σ 该行业内股票市值
行业权重 = 行业市值 / 总市值 × 100%
```

### 集中度指标

**Herfindahl-Hirschman Index (HHI)**：
```
HHI = Σ (权重²)
```
- HHI < 1500：分散
- 1500 ≤ HHI < 2500：中等集中
- HHI ≥ 2500：高度集中

### 盈亏计算

当提供成本价时：
```
盈亏金额 = (当前价 - 成本价) × 持股数
盈亏比例 = (当前价 - 成本价) / 成本价 × 100%
总盈亏 = Σ 盈亏金额
```

## 风险规则

| 规则 | 条件 | 提示 |
|------|------|------|
| 单股集中 | 权重 > 30% | ⚠️ 高风险：单股集中度过高 |
| 行业集中 | 权重 > 50% | ⚠️ 高风险：行业集中度过高 |
| 持仓过少 | 股票数 < 3 | ⚠️ 中风险：持仓过于集中 |
| 持仓过多 | 股票数 > 20 | ℹ️ 低风险：持仓过于分散 |

## 异常处理

| 场景 | 处理 |
|------|------|
| 股票代码无效 | 跳过，记录警告 |
| 无法获取行情 | 跳过，记录警告 |
| 无法获取行业 | 标记为"未知行业" |
| 无有效持仓 | 返回错误提示 |

## 测试策略

1. **输入解析测试**：验证各种输入格式的解析
2. **权重计算测试**：验证市值和权重计算正确性
3. **行业统计测试**：验证行业分布计算
4. **风险检查测试**：验证各风险规则的触发条件
5. **盈亏计算测试**：验证盈亏计算正确性
