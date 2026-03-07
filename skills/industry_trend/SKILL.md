---
name: openclaw_alpha_industry_trend
description: "产业热度追踪，识别市场热点板块和趋势变化。适用于：(1) 查看当前热门行业/概念板块，(2) 发现趋势反转信号，(3) 板块轮动分析。不适用于：个股选择、技术指标分析、长期投资策略。"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["uv"]
---

# 产业热度追踪

追踪市场热点板块，识别趋势变化，辅助投资决策。

## 使用说明

### 脚本运行

所有脚本需在项目根目录下运行，使用 `uv run --env-file .env` 加载环境变量：

```bash
uv run --env-file .env python -m skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor [参数]
```

**如果脚本运行失败**：
1. 检查是否在项目根目录
2. 检查 `.env` 文件是否存在且包含 `TUSHARE_TOKEN`
3. 将错误信息记录到进度文件，不要丢失上下文

### 运行记录

**进度文件位置**：`.openclaw_alpha/industry_trend/{YYYY-MM-DD}/progress.md`

每次运行脚本后，记录：
- 运行时间
- 脚本命令
- 运行结果（成功/失败）
- 关键输出（Top 3 板块）
- 错误信息（如有）

## 分析步骤

### Step 1: 获取一级行业热度

**输入**：日期（默认今天）

**动作**：
```bash
uv run --env-file .env python -m skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor \
    --category L1 \
    --top-n 10
```

**输出**：
- 控制台：Top 10 一级行业热度排名
- 文件：`.openclaw_alpha/industry_trend/{date}/heat.json`（完整数据）

**分析要点**：
- 关注 `trend` 字段：加热中、降温中、稳定
- 查看 `heat_change`：热度环比变化
- 结合 `pct_change`：涨跌幅确认趋势

### Step 2: 获取概念板块热度

**输入**：日期（默认今天）

**动作**：
```bash
uv run --env-file .env python -m skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor \
    --category concept \
    --top-n 10
```

**输出**：
- 控制台：Top 10 概念板块热度排名
- 文件：`.openclaw_alpha/industry_trend/{date}/heat.json`（完整数据）

**分析要点**：
- 概念板块包含涨跌家数，可以判断板块内部分化程度
- 关注 `up_ratio`（涨跌家数比）> 70% 的板块
- 结合 `turnover_rate`（换手率）判断资金活跃度

### Step 3: 深入分析（可选）

**二级行业**：
```bash
uv run --env-file .env python -m skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor \
    --category L2 \
    --top-n 20
```

**三级行业**：
```bash
uv run --env-file .env python -m skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor \
    --category L3 \
    --top-n 30
```

### Step 4: 拥挤度分析（行业轮动关键）

**输入**：日期（默认今天）

**动作**：
```bash
uv run --env-file .env python -m skills.industry_trend.scripts.crowdedness_processor.crowdedness_processor \
    --category L1 \
    --top-n 10
```

**输出**：
- 控制台：Top 10 拥挤度排名
- 文件：`.openclaw_alpha/industry_trend/{date}/crowdedness.json`

**分析要点**：
- **低拥挤 + 高热度** = 黄金组合（最佳入场机会）
- **高拥挤** = 过热风险，谨慎追高
- 关注拥挤度等级：高拥挤（>80）、中等拥挤（50-80）、低拥挤（<50）

### Step 5: 趋势对比（可选）

如果需要对比历史数据：
1. 指定日期参数：`--date 2026-03-05`
2. 运行两次，对比不同日期的热度排名
3. 识别持续升温或降温的板块

## 输出说明

### 控制台输出

```json
{
  "date": "2026-03-06",
  "category": "L1",
  "boards": [
    {
      "rank": 1,
      "name": "电子",
      "heat_index": 85.2,
      "trend": "加热中",
      "change_pct": 3.5,
      "heat_change": 25.3
    },
    ...
  ]
}
```

### 文件输出

位置：`.openclaw_alpha/industry_trend/{date}/heat.json`

包含完整数据：
- 所有板块的热度指数
- 各维度得分明细
- 原始指标数据
- 权重配置

## 热度指数说明

### 申万行业权重（L1/L2/L3）

| 维度 | 权重 | 说明 |
|------|------|------|
| 涨跌幅 | 35% | 价格变动幅度 |
| 换手率 | 30% | 交易活跃程度 |
| 成交额占比 | 35% | 资金关注度 |

### 概念板块权重（concept）

| 维度 | 权重 | 说明 |
|------|------|------|
| 涨跌幅 | 30% | 价格变动幅度 |
| 换手率 | 25% | 交易活跃程度 |
| 成交额占比 | 25% | 资金关注度 |
| 涨跌家数比 | 20% | 板块内股票表现 |

### 趋势信号

| 信号 | 判断规则 |
|------|----------|
| 加热中 | 热度环比 > +20% 且 涨幅 > 0 |
| 降温中 | 热度环比 < -20% 或 涨幅 < -3% |
| 稳定 | 其他情况 |
| 新 | 首日数据（无环比） |

## 拥挤度指标说明

### 计算公式

**拥挤度 = 换手率分位 × 50% + 成交额占比分位 × 50%**

- 换手率分位：当前换手率在所有板块中的相对位置（0-100）
- 成交额占比分位：当前成交额占比在所有板块中的相对位置（0-100）

### 拥挤度等级

| 等级 | 分值 | 含义 | 操作建议 |
|------|------|------|----------|
| 高拥挤 | >80 | 过热风险 | 谨慎追高 |
| 中等拥挤 | 50-80 | 正常活跃 | 可关注 |
| 低拥挤 | <50 | 未过热 | 可入场 |

### 黄金组合（行业轮动）

**理想状态**：高热度（趋势强）+ 低拥挤度（未过热）

| 热度 | 拥挤度 | 判断 |
|------|--------|------|
| 高 | 低 | 黄金组合，最佳入场机会 |
| 高 | 高 | 过热风险，等待回调 |
| 低 | 低 | 底部潜伏，需耐心 |
| 低 | 高 | 资金撤离，避免 |

## 注意事项

1. **数据源限制**：
   - 申万行业：Tushare（5000 积分）
   - 概念板块：AKShare（免费）
   - 如遇数据获取失败，检查积分和网络

2. **第一版限制**：
   - 申万行业不包含涨跌家数（需 6000+ 积分）
   - 概念板块数据可能有缓存延迟

3. **使用建议**：
   - 结合多个层级（L1 + concept）综合判断
   - 不要单凭热度排名做决策
   - 关注趋势信号，而非绝对排名

## 深入分析

获取热度排名后，可以使用其他 skill 进行深入分析：
- **stock-analysis**：分析板块龙头股
- **financial-statement**：分析板块内公司财务
- **technical-indicator**：分析板块指数技术面
