# 设计文档 - 预警监控

## 一、技术方案

整合多个 skill 的风险检测能力，通过配置文件管理监控标的和规则。

## 二、模块编排

```
alert_monitor/
├── scripts/
│   ├── alert_processor/     # 主入口
│   │   └── alert_processor.py
│   ├── config_parser/       # 配置解析
│   ├── risk_scanner/        # 持仓风险扫描
│   └── market_scanner/      # 市场异动扫描
```

### 2.1 模块职责

| 模块 | 职责 |
|------|------|
| alert_processor | 主入口，协调扫描流程 |
| config_parser | 解析配置文件 |
| risk_scanner | 扫描持仓风险（复用 risk_alert） |
| market_scanner | 扫描市场异动（复用 northbound_flow, industry_trend） |

### 2.2 依赖的 Skill

| Skill | 复用能力 |
|-------|---------|
| risk_alert | 业绩/价格/资金风险检测 |
| restricted_release | 解禁风险监控 |
| northbound_flow | 北向资金异动 |
| industry_trend | 板块热度追踪 |

## 三、配置文件

**路径**：`~/.openclaw/workspace-alpha/alert_config.yaml`

**结构**：
```yaml
watchlist:
  - symbol: "000001"
    name: "平安银行"
    cost_price: 12.50
    stop_loss: 11.00

rules:
  risk_alert:
    enabled: true
    check_times: ["9:15", "15:05"]
  restricted_release:
    enabled: true
    threshold: 5.0
  northbound_flow:
    enabled: true
    inflow_threshold: 50
    outflow_threshold: 30
  industry_trend:
    enabled: true
    hot_threshold: 30
    cold_threshold: -30
```

## 四、输出

- 控制台：格式化的预警报告
- 文件：`.openclaw_alpha/alert_monitor/{date}/alert_processor.json`
