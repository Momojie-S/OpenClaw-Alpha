---
name: openclaw_alpha_lhb_tracker
description: "龙虎榜追踪，监控游资和机构动向。适用于：(1) 查看每日龙虎榜净买入排名，(2) 分析个股上榜历史，(3) 了解机构和游资操作风格。不适用于：内资整体流向、行业资金分布。"
metadata:
  openclaw:
    emoji: "🐉"
    requires:
      bins: ["uv"]
---

# 龙虎榜追踪

追踪交易所披露的龙虎榜数据，了解游资、机构和北向资金的大额交易动向。

## 使用说明

### 脚本运行

所有脚本需在项目根目录下运行，使用 `uv run --env-file .env` 加载环境变量：

```bash
uv run --env-file .env python -m openclaw_alpha.skills.lhb_tracker.lhb_processor.lhb_processor [参数]
```

**如果脚本运行失败**：
1. 检查是否在项目根目录
2. 检查网络连接（需要访问东方财富接口）
3. 将错误信息记录到进度文件，不要丢失上下文

### 运行记录

**进度文件位置**：`.openclaw_alpha/lhb-tracker/{YYYY-MM-DD}/progress.md`

每次运行脚本后，记录：
- 运行时间
- 脚本命令
- 运行结果（成功/失败）
- 关键输出（Top 3 股票、净买入金额）
- 错误信息（如有）

## 分析步骤

### Step 1: 查看每日龙虎榜

**输入**：日期（默认最近交易日）、Top N（默认 10）

**动作**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.lhb_tracker.lhb_processor.lhb_processor \
    --action daily \
    --top-n 10
```

**输出**：
- 控制台：当日龙虎榜摘要 + Top N 净买入/卖出股票
- 文件：`.openclaw_alpha/lhb-tracker/{date}/lhb_daily.json`（完整数据）

**分析要点**：
- 关注 `total_net`：龙虎榜整体净买入情况
- 查看 `top_inflow`：机构/游资在买什么
- 查看 `top_outflow`：机构/游资在卖什么
- 注意 `buy_type`：判断是机构主导还是游资主导

### Step 2: 查看个股龙虎榜历史

**输入**：股票代码、天数（默认 5）、Top N（默认 10）

**动作**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.lhb_tracker.lhb_processor.lhb_processor \
    --action stock \
    --symbol 000001 \
    --days 10
```

**输出**：
- 控制台：个股龙虎榜历史摘要
- 文件：`.openclaw_alpha/lhb-tracker/{date}/lhb_stock_000001.json`

**分析要点**：
- 关注 `appearances`：近期上榜次数
- 查看 `org_buy` vs `retail_buy`：机构 vs 游资参与度
- 注意 `main_buyer`：主要买家类型

## 输出说明

### 每日龙虎榜（daily）

```json
{
  "date": "2026-03-07",
  "total_count": 50,
  "total_buy": 120.5,
  "total_sell": 85.3,
  "total_net": 35.2,
  "top_inflow": [
    {
      "code": "000001",
      "name": "平安银行",
      "net_buy": 5.2,
      "change_pct": 9.98,
      "reason": "涨停",
      "buy_type": "机构+游资"
    },
    ///.py
  ],
  "top_outflow": [///.py]
}
```

### 个股龙虎榜（stock）

```json
{
  "symbol": "000001",
  "name": "平安银行",
  "period": "2026-02-25 ~ 2026-03-07",
  "summary": {
    "appearances": 3,
    "total_net_buy": 12.5,
    "org_buy": 8.2,
    "retail_buy": 3.1,
    "north_buy": 1.2,
    "main_buyer": "机构"
  },
  "details": [///.py]
}
```

## 买卖方类型

| 类型 | 识别规则 | 特点 |
|------|----------|------|
| 机构 | 营业部名称包含"机构专用" | 中长线，偏好价值股 |
| 北向 | 营业部名称包含"沪股通/深股通" | 外资 |
| 游资 | 证券营业部 | 短线，偏好题材股 |

## 上榜原因

| 原因 | 说明 | 信号 |
|------|------|------|
| 涨停 | 日涨幅偏离值达 7% | 看多 |
| 跌停 | 日跌幅偏离值达 7% | 看空 |
| 换手率 | 日换手率达 20% | 活跃 |
| 振幅 | 日振幅达 15% | 波动大 |

## 注意事项

1. **数据延迟**：龙虎榜数据 T+1 发布
2. **非交易日**：返回最近交易日的数据
3. **单位说明**：
   - 净买入：亿元
   - 个股持仓变化：万元

## 使用建议

1. **结合北向资金**：龙虎榜（内资）+ 北向资金（外资）= 完整资金流向
2. **关注机构动向**：机构买入的股票通常有更好的持续性
3. **不要盲目跟风**：游资操作灵活，也可能快速撤退

## 深入分析

获取龙虎榜数据后，可以使用其他 skill 进行深入分析：
- **stock_analysis**：分析龙虎榜买入个股的行情
- **industry_trend**：查看龙虎榜股票所在板块的热度
- **northbound_flow**：对比外资动向
