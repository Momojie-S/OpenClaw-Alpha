---
name: openclaw_alpha_restricted_release
description: "限售解禁风险监控。适用于：(1) 查询即将解禁的股票，(2) 查询单只股票的解禁排期，(3) 筛选高解禁风险股票。不适用于：已解禁超过1年的历史数据查询。"
metadata:
  openclaw:
    emoji: "🔓"
    requires:
      bins: ["uv"]
---

# 限售解禁风险监控

限售股解禁是重要的市场风险因素。当大量限售股解禁时，会对股价造成抛压。本 skill 帮助监控解禁风险，提前识别潜在风险股票。

## 核心指标

**占流通市值比例** = 解禁股市值 / 流通市值

这是最重要的风险指标：
- **>= 50%**: 极高风险（解禁量超过现有流通股的一半）
- **>= 30%**: 高风险
- **>= 20%**: 中风险
- **< 20%**: 低风险

## 使用说明

### 脚本运行

```bash
# 查询即将解禁的股票（默认未来7天）
uv run --env-file .env python -m skills.restricted_release.scripts.restricted_release_processor.restricted_release_processor upcoming

# 按占流通市值比例排序（找高风险股票）
uv run --env-file .env python -m skills.restricted_release.scripts.restricted_release_processor.restricted_release_processor upcoming --sort-by ratio --top-n 30

# 查询单只股票的解禁历史和排期
uv run --env-file .env python -m skills.restricted_release.scripts.restricted_release_processor.restricted_release_processor queue 600000

# 筛选高解禁风险股票（占流通市值 >= 20%）
uv run --env-file .env python -m skills.restricted_release.scripts.restricted_release_processor.restricted_release_processor high-risk --min-ratio 0.2
```

### 运行记录

结果自动保存至 `.openclaw_alpha/restricted_release/{date}/` 目录。

## 分析步骤

### Step 1: 查询即将解禁股票

**输入**：查询时间范围（默认7天）

**动作**：
```bash
uv run --env-file .env python -m skills.restricted_release.scripts.restricted_release_processor.restricted_release_processor upcoming --days 7 --sort-by value
```

**输出**：
- 即将解禁的股票列表（代码、名称、解禁日期、解禁市值、占流通市值比例）
- 完整数据保存至 `.openclaw_alpha/restricted_release/{date}/upcoming.json`

### Step 2: 筛选高风险股票

**输入**：最小占流通市值比例（默认10%）

**动作**：
```bash
uv run --env-file .env python -m skills.restricted_release.scripts.restricted_release_processor.restricted_release_processor high-risk --min-ratio 0.2
```

**输出**：
- 高风险股票列表（带风险等级标注）
- 完整数据保存至 `.openclaw_alpha/restricted_release/{date}/high_risk.json`

### Step 3: 查询单只股票解禁排期

**输入**：股票代码

**动作**：
```bash
uv run --env-file .env python -m skills.restricted_release.scripts.restricted_release_processor.restricted_release_processor queue {股票代码}
```

**输出**：
- 该股票的历史和未来解禁记录
- 完整数据保存至 `.openclaw_alpha/restricted_release/{date}/queue_{股票代码}.json`

## 分析思路

### 1. 风险预警

在买入股票前，检查该股票是否有即将解禁：
- 解禁量大 -> 可能面临抛压
- 占流通市值比例高 -> 股价可能大幅波动
- 首发原股东解禁 -> 减持意愿通常较强

### 2. 解禁类型解读

| 类型 | 风险程度 | 说明 |
|------|:--------:|------|
| 首发原股东限售股份 | 高 | 成本低，减持意愿强 |
| 定向增发机构配售股份 | 中 | 机构可能有锁定期约定 |
| 股权激励限售股份 | 低 | 员工持股，通常不会大量减持 |
| 其他类型 | 中 | 需具体分析 |

### 3. 结合其他分析

解禁风险应与其他因素结合：
- 基本面：业绩好的公司解禁影响较小
- 技术面：解禁前已有较大涨幅的股票风险更高
- 资金面：主力资金持续流入可对冲解禁压力

## 注意事项

1. **提前预警**：解禁公告通常提前发布，实际解禁日期可能变化
2. **不等于减持**：解禁只是允许减持，不代表一定会减持
3. **关注高管动向**：高管减持公告是重要参考信号
