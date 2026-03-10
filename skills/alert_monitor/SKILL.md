---
name: openclaw_alpha_alert_monitor
description: "预警推送系统。适用于：(1) 持仓风险扫描和预警，(2) 市场异动监控，(3) 定时风险报告，(4) 自选股风险追踪。不适用于：实时交易信号、量化风险模型、高频监控。"
metadata:
  openclaw:
    emoji: "🔔"
    requires:
      bins: ["uv"]
---

# 预警监控 Skill

自动监控持仓风险和市场异动，生成预警报告。支持配置化推送和定时扫描。

## 使用说明

### 脚本运行

```bash
# 综合扫描（持仓风险 + 市场异动）
uv run --env-file .env python -m openclaw_alpha.skills.alert_monitor.alert_processor

# 仅扫描持仓风险
uv run --env-file .env python -m openclaw_alpha.skills.alert_monitor.alert_processor --type risk

# 仅扫描市场异动
uv run --env-file .env python -m openclaw_alpha.skills.alert_monitor.alert_processor --type market

# 简报模式（只显示高风险）
uv run --env-file .env python -m openclaw_alpha.skills.alert_monitor.alert_processor --brief

# 保存报告
uv run --env-file .env python -m openclaw_alpha.skills.alert_monitor.alert_processor --output

# 输出 JSON 格式
uv run --env-file .env python -m openclaw_alpha.skills.alert_monitor.alert_processor --json
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | 扫描类型（full/risk/market） | full |
| `--date` | 扫描日期 | 今天 |
| `--days` | 检查近 N 天 | 5 |
| `--brief` | 简报模式 | False |
| `--output` | 保存报告到文件 | False |
| `--json` | 输出 JSON 格式 | False |

### 配置文件

在 `~/.openclaw/workspace-alpha/alert_config.yaml` 中配置监控标的和规则：

```yaml
# 自选股/持仓列表
watchlist:
  - symbol: "000001"
    name: "平安银行"
    cost_price: 12.50  # 成本价（可选）
    stop_loss: 11.00   # 止损价（可选）
  - symbol: "600000"
    name: "浦发银行"

# 预警规则
rules:
  # 风险预警
  risk_alert:
    enabled: true
    check_times: ["9:15", "15:05"]

  # 解禁风险
  restricted_release:
    enabled: true
    threshold: 5.0  # 占流通市值比例

  # 北向资金
  northbound_flow:
    enabled: true
    inflow_threshold: 50  # 亿
    outflow_threshold: 30  # 亿

  # 板块热度
  industry_trend:
    enabled: true
    hot_threshold: 30  # 热度环比变化阈值
    cold_threshold: -30
```

### 运行记录

运行记录保存在 `.openclaw_alpha/alert_monitor/YYYY-MM-DD/` 目录下：
- `alert_processor.json` - 综合预警报告

## 分析步骤

### Step 1: 配置监控标的

**输入**：自选股/持仓信息

**动作**：编辑配置文件

```bash
vim ~/.openclaw/workspace-alpha/alert_config.yaml
```

**输出**：配置完成

### Step 2: 运行综合扫描

**输入**：配置文件

**动作**：运行预警扫描

```bash
uv run --env-file .env python -m openclaw_alpha.skills.alert_monitor.alert_processor --brief
```

**输出**：预警报告

```
📊 【预警扫描报告】2026-03-08

【持仓风险】
  扫描: 10 只
  高风险: 1 只 | 中风险: 2 只

【高风险详情】
  ⚠️ 002364 中恒电气: 业绩首亏，预计变动 -336.7%

【市场异动】
  🟡 北向大幅流入: 今日净流入 52.3 亿
  🟡 板块热度急升: 电子: 热度环比 +35.2%

【建议】
  ⚠️ 存在高风险持仓，请及时处理
  📈 市场出现异动，请关注
```

### Step 3: 查看完整报告

**输入**：Step 2 的结果

**动作**：如需详细信息，运行完整报告

```bash
uv run --env-file .env python -m openclaw_alpha.skills.alert_monitor.alert_processor
```

**输出**：包含所有风险等级的完整报告

### Step 4: 定时扫描（可选）

**输入**：cron 配置

**动作**：配置定时任务

```yaml
# OpenClaw cron 配置
jobs:
  - name: 早盘风险扫描
    schedule: "0 9:15 * * 1-5"
    command: "扫描持仓风险并推送"

  - name: 收盘风险扫描
    schedule: "0 15:05 * * 1-5"
    command: "综合预警扫描"
```

**输出**：定时推送预警消息

## 预警类型

### 持仓风险预警

| 预警类型 | 触发条件 | 优先级 |
|---------|---------|:------:|
| 业绩暴雷 | 业绩首亏/预减/增亏 | 高 |
| 连续下跌 | 连续 ≥3 天且累计跌幅 ≥10% | 中 |
| 资金流出 | 连续 ≥3 天净流出且累计 ≥1 亿 | 中 |
| 解禁压力 | 解禁占流通市值 ≥5% | 中 |
| 跌破止损 | 跌破用户设定止损线 | 高 |

### 市场异动预警

| 预警类型 | 触发条件 | 优先级 |
|---------|---------|:------:|
| 北向大幅流入 | 单日净流入 ≥50 亿 | 中 |
| 北向大幅流出 | 单日净流出 ≥30 亿 | 高 |
| 板块热度急升 | 热度环比 > +30% | 中 |
| 板块热度骤降 | 热度环比 < -30% | 中 |

## 关联 Skill

- **risk_alert**: 业绩/价格/资金风险检测
- **restricted_release**: 解禁风险监控
- **northbound_flow**: 北向资金流向
- **industry_trend**: 板块热度追踪

本 skill 整合以上能力，提供统一的预警接口。

## 注意事项

1. **配置文件**: 需要先配置 `alert_config.yaml` 才能扫描持仓
2. **网络依赖**: 需要访问 AKShare API 获取数据
3. **推送频率**: 避免频繁扫描，建议每日 2-4 次
4. **非交易时间**: 周末和节假日数据可能为空
5. **仅供参考**: 预警仅供参考，不构成投资建议

## 已实现功能

- ✅ 持仓风险扫描（复用 risk_alert）
- ✅ 市场异动监控（北向资金、板块热度）
- ✅ 配置化监控标的和规则
- ✅ 简报/完整两种报告模式
- ✅ 报告保存

## 待实现功能

- 预警去重（同一风险不重复推送）
- 静默时段（夜间不推送）
- 多渠道推送（企业微信、Discord）
