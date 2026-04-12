# 决策记录 - 预警监控

## 调研

### 预警类型分析

| 类型 | 数据源 | 可复用 Skill |
|------|--------|-------------|
| 业绩暴雷 | AKShare | risk_alert |
| 连续下跌 | AKShare | risk_alert |
| 资金流出 | AKShare | risk_alert |
| 解禁风险 | AKShare | restricted_release |
| 北向资金 | AKShare | northbound_flow |
| 板块热度 | AKShare | industry_trend |

## 决策

### 为什么采用编排模式

- 复用已有 skill 的能力，避免重复开发
- 职责分离，各 skill 专注单一功能
- 便于维护和扩展

### 配置文件设计

- YAML 格式，易读易编辑
- 支持持仓信息（成本价、止损线）
- 支持规则开关和阈值调整

### 报告模式

- 简报模式：只显示高风险项
- 完整报告：显示所有风险等级

## 踩坑

（待记录）
