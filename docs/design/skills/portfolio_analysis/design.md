# 设计文档 - 持仓分析

## 一、技术方案

分为三个独立的分析功能：
- 持仓结构分析（权重、HHI）
- 相关性分析（协方差矩阵）
- 风险贡献分析（风险平价）

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 实时行情 | AKShare | `stock_zh_a_spot_em()` |
| 日线数据 | AKShare | `stock_zh_a_hist()` |
| 行业分类 | Tushare | `index_classify()` |

## 三、模块划分

```
portfolio_analysis/scripts/
├── portfolio_processor/          # 持仓结构分析
│   └── portfolio_processor.py
├── correlation_processor/        # 相关性分析
│   └── correlation_processor.py
└── risk_contribution_processor/  # 风险贡献
    └── risk_contribution_processor.py
```

## 四、输入格式

**字符串格式**：`代码:股数[:成本价]`
```
000001:1000:12.5,600000:500:8.2
```

**JSON 格式**：
```json
{
  "holdings": [
    {"code": "000001", "shares": 1000, "cost": 12.5}
  ]
}
```

## 五、输出设计

`.openclaw_alpha/portfolio-analysis/{date}/portfolio.json`
