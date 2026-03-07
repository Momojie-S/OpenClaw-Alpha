# 风险监控 Skill 设计文档

> 版本: v1.0
> 创建时间: 2026-03-07

---

## 一、技术选型

### 1.1 数据源选择

| 数据类型 | 推荐数据源 | 备选数据源 | 原因 |
|---------|-----------|-----------|------|
| 业绩预告 | AKShare | Tushare (500积分) | 免费，无积分要求 |
| 日线行情 | AKShare | Tushare (120积分) | 免费，接口稳定 |
| 资金流向 | AKShare | Tushare (2000积分) | 免费，数据实时 |
| 大股东减持 | Tushare (2000积分) | - | Phase 2，需要高积分 |
| 股权质押 | AKShare | Tushare (2000积分) | Phase 2，数据有限 |

**决策**：Phase 1 使用 AKShare 作为唯一数据源，确保无积分门槛。

### 1.2 AKShare 接口

| 数据 | 接口 | 说明 |
|------|------|------|
| 业绩预告 | `stock_em_yjyg` | 东方财富业绩预告 |
| 日线行情 | `stock_zh_a_hist` | 东方财富历史行情 |
| 资金流向 | `stock_individual_fund_flow` | 东方财富个股资金流 |

---

## 二、架构设计

### 2.1 模块关系

```
┌─────────────────────────────────────────────────┐
│              RiskAlertProcessor                  │
│  (风险分析、评级、输出)                           │
└─────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│ForecastFetcher│ │  StockFetcher │ │  FlowFetcher  │
│  (业绩预告)  │ │  (日线行情)  │ │  (资金流向)   │
└────────────┘ └────────────┘ └────────────┘
        │           │           │
        └───────────┼───────────┘
                    ▼
         ┌─────────────────────┐
         │   AkshareDataSource │
         └─────────────────────┘
```

### 2.2 目录结构

```
skills/risk_alert/
├── SKILL.md
└── scripts/
    ├── __init__.py
    ├── forecast_fetcher/        # 业绩预告
    │   ├── __init__.py
    │   ├── forecast_fetcher.py
    │   └── akshare.py
    ├── stock_fetcher/           # 日线行情（复用 stock_analysis）
    │   └── ... (复用或新建)
    ├── flow_fetcher/            # 资金流向（复用 market_sentiment）
    │   └── ... (复用或新建)
    └── risk_processor/          # 风险分析
        ├── __init__.py
        └── risk_processor.py
```

---

## 三、数据流程

### 3.1 全市场扫描流程

```
1. 获取业绩预告 → 筛选预亏/预降 → 业绩风险列表
2. 获取全市场行情 → 筛选连续下跌 → 价格风险列表
3. 获取资金流向 → 筛选持续流出 → 资金风险列表
4. 合并风险列表 → 计算综合评级 → 输出风险报告
```

### 3.2 个股检查流程

```
1. 查询业绩预告 → 判断业绩风险
2. 查询近 N 日行情 → 判断价格风险
3. 查询近 N 日资金流 → 判断资金风险
4. 综合评级 → 输出风险报告
```

---

## 四、接口定义

### 4.1 ForecastFetcher

**输入**：
```python
{
  "date": "2026-03-07",  # 可选，默认最新
  "type": "预亏" | "预降"  # 可选，筛选类型
}
```

**输出**：
```python
[
  {
    "code": "000001",
    "name": "平安银行",
    "type": "预降",
    "change_pct": -30.5,  # 预计变动幅度
    "report_date": "2026-03-31",  # 报告期
    "announce_date": "2026-01-15"  # 公告日期
  },
  ...
]
```

### 4.2 StockFetcher（复用）

复用 `stock_analysis` 的 StockFetcher，增加风险分析所需字段。

### 4.3 FlowFetcher（复用）

复用 `market_sentiment` 的 FlowFetcher，增加个股查询能力。

### 4.4 RiskProcessor

**命令行参数**：
```bash
# 全市场扫描
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --mode scan

# 个股检查
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --mode check --symbol 000001

# 指定日期
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --mode scan --date 2026-03-06
```

**输出格式**：

**全市场扫描**：
```json
{
  "date": "2026-03-07",
  "scan_mode": "market",
  "summary": {
    "high_risk_count": 3,
    "medium_risk_count": 5,
    "low_risk_count": 8,
    "normal_count": 3000
  },
  "high_risk": [
    {
      "code": "000001",
      "name": "平安银行",
      "rating": "高",
      "risks": ["业绩预降", "连续下跌5天"]
    },
    ...
  ],
  "medium_risk": [...],
  "low_risk": [...]
}
```

**个股检查**：
```json
{
  "code": "000001",
  "name": "平安银行",
  "date": "2026-03-07",
  "rating": "高",
  "risks": [
    {
      "type": "业绩风险",
      "level": "高",
      "detail": "业绩预降，预计净利润下降 30%"
    },
    {
      "type": "价格风险",
      "level": "高",
      "detail": "连续下跌 5 天，累计跌幅 12%"
    },
    {
      "type": "资金风险",
      "level": "中",
      "detail": "近 3 天资金净流出 3.5 亿"
    }
  ],
  "suggestions": [
    "关注业绩公告详情",
    "评估持仓比例",
    "考虑风险控制措施"
  ]
}
```

---

## 五、核心算法

### 5.1 业绩风险判断

```
输入: 业绩预告类型
规则:
  IF type IN ["预亏", "预降"] THEN
    RETURN 高风险
  ELSE IF type == "不确定" THEN
    RETURN 中风险
  ELSE
    RETURN 无风险
```

### 5.2 价格风险判断

```
输入: 近 N 日日线数据
计算:
  连续下跌天数 = 连续 close < previous_close 的天数
  累计跌幅 = (start_price - end_price) / start_price * 100
  
规则:
  IF 单日跌幅 >= 9% THEN
    RETURN 高风险
  ELSE IF 连续下跌天数 >= 3 AND 累计跌幅 >= 10% THEN
    RETURN 中风险
  ELSE
    RETURN 无风险
```

### 5.3 资金风险判断

```
输入: 近 N 日资金流向数据
计算:
  连续流出天数 = 连续 net_amount < 0 的天数
  累计流出金额 = SUM(net_amount WHERE net_amount < 0)
  
规则:
  IF 单日净流出 >= 5亿 THEN
    RETURN 高风险
  ELSE IF 连续流出天数 >= 3 AND 累计流出 >= 1亿 THEN
    RETURN 中风险
  ELSE
    RETURN 无风险
```

### 5.4 综合评级

```
输入: 所有风险信号
规则:
  IF EXISTS 高风险信号 THEN
    RETURN "高风险"
  ELSE IF EXISTS 中风险信号 THEN
    RETURN "中风险"
  ELSE IF EXISTS 低风险信号 THEN
    RETURN "低风险"
  ELSE
    RETURN "正常"
```

---

## 六、边界处理

### 6.1 数据缺失

- 业绩预告缺失：跳过业绩风险判断
- 行情数据不足：跳过价格风险判断
- 资金数据缺失：跳过资金风险判断

### 6.2 数据异常

- 停牌股票：标记为"停牌"，不进行风险判断
- ST 股票：自动标记为高风险
- 次新股（上市<60天）：在输出中标注

### 6.3 性能考虑

- 全市场扫描数据量大，考虑分批处理
- 使用缓存减少重复查询
- 输出时限制数量（Top N）

---

## 七、复用策略

### 7.1 复用 stock_analysis

- StockFetcher 可直接复用
- 数据结构兼容
- 增加风险分析所需字段（如连续下跌天数）

### 7.2 复用 market_sentiment

- FlowFetcher 需要扩展（支持个股查询）
- 现有接口是全市场资金流，需要增加单股查询

### 7.3 决策

Phase 1 采用**新建简化版本**：
- ForecastFetcher: 新建
- StockFetcher: 简化版（只获取风险分析所需数据）
- FlowFetcher: 简化版（只获取个股资金流）

后续可以考虑重构为统一的数据服务。

---

## 八、测试策略

### 8.1 单元测试

- 业绩风险判断逻辑
- 价格风险判断逻辑
- 资金风险判断逻辑
- 综合评级逻辑

### 8.2 集成测试

- 全市场扫描流程
- 个股检查流程
- 数据缺失处理

### 8.3 边界测试

- 停牌股票
- ST 股票
- 次新股
- 数据缺失场景
