---
name: openclaw_alpha_technical_indicators
description: "技术指标分析：计算 MACD、RSI、KDJ、布林带、均线等技术指标，判断买卖信号。适用于：(1) 技术面分析，(2) 买卖时机判断，(3) 趋势识别，(4) 量价关系分析。不适用于：基本面分析、自动交易、复杂技术形态。"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["uv"]
---

# 技术指标分析

计算常用技术指标，判断买卖信号，帮助用户从技术面分析股票走势。

## 使用说明

### 安装依赖

本 skill 使用 **TA-Lib** 计算技术指标（性能高、算法标准）。

**安装 TA-Lib**：

```bash
# Linux
sudo apt-get install -y build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib

# macOS
brew install ta-lib
pip install TA-Lib

# Windows
# 下载预编译 wheel: https://github.com/cgohlke/talib-build/releases
pip install TA_Lib‑0.4.28‑cp312‑cp312‑win_amd64.whl
```

### 脚本运行

**技术指标分析**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.technical_indicators.indicator_processor.indicator_processor 000001

# 指定天数
uv run --env-file .env python -m openclaw_alpha.skills.technical_indicators.indicator_processor.indicator_processor 000001 --days 120

# 只分析特定指标
uv run --env-file .env python -m openclaw_alpha.skills.technical_indicators.indicator_processor.indicator_processor 000001 --indicators "macd,rsi"
```

**量价关系分析**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.technical_indicators.volume_price_processor.volume_price_processor 000001

# 指定天数
uv run --env-file .env python -m openclaw_alpha.skills.technical_indicators.volume_price_processor.volume_price_processor 000001 --days 60
```

### 运行记录

运行记录保存在：
- 技术指标：`.openclaw_alpha/technical_indicators/{date}/indicator_analysis.json`
- 量价关系：`.openclaw_alpha/technical_indicators/{date}/volume_price_analysis.json`

## 分析步骤

### Step 1: 技术指标分析

**输入**：股票代码

**动作**：运行脚本计算技术指标
```bash
uv run --env-file .env python -m openclaw_alpha.skills.technical_indicators.indicator_processor.indicator_processor 000001
```

**输出**：
```
技术指标分析 - 000001
==================================================
分析日期: 2026-03-07
数据范围: 2026-01-07 ~ 2026-03-07 (60天)

【指标值】
MACD: DIF=0.25, DEA=0.18, MACD=0.14
RSI(14): 65.32
KDJ: K=72.5, D=68.3, J=80.9
布林带: 上轨=13.2, 中轨=12.5, 下轨=11.8
均线: MA5=12.3, MA10=12.1, MA20=11.9, MA60=11.5

【信号判断】
MACD: 金叉 (+1)
KDJ: 超买 (-1)
均线: 多头排列 (+1)

【综合建议】
总评分: +1
建议: 买入 (中置信度)
```

---

### Step 2: 量价关系分析

**输入**：股票代码

**动作**：运行脚本分析量价关系
```bash
uv run --env-file .env python -m openclaw_alpha.skills.technical_indicators.volume_price_processor.volume_price_processor 000001
```

**输出**：
```
量价关系分析 - 000001
============================================================
分析日期: 2026-03-08
数据范围: 2026-01-08 ~ 2026-03-08 (60天)

【OBV 能量潮】
  当前值: 15000000
  趋势: 上升 (连续 5 天)

【量价相关系数】
  0.650 - 强正相关（量价齐升）

【成交量状态】
  当前: 2500000
  MA5: 2000000 | MA10: 1800000 | MA20: 1600000
  状态: 放量

【量比】
  1.25 - 温和放量

【量价关系判断】
  模式: OBV上升+价涨 | 量价正关联 | 放量上涨
  5日涨跌: +5.00%
  5日成交量变化: +25.00%

  信号: 看涨 (评分: 3)
  分析: 量价配合良好，趋势健康，可继续持有或逢低买入
```

---

### Step 3: 综合判断

结合技术指标和量价关系，形成综合判断：
- 技术指标判断趋势方向
- 量价关系验证趋势可靠性
- 两者共振时信号更可靠

---

## 参数说明

### 技术指标参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `symbol` | 股票代码 | 必填 |
| `--days` | 历史天数 | 60 |
| `--indicators` | 指标列表（逗号分隔） | 全部 |
| `--params` | 指标参数（JSON 格式） | 默认参数 |

### 量价关系参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `symbol` | 股票代码 | 必填 |
| `--days` | 历史天数 | 60 |

---

## 支持的指标

### MACD（趋势指标）

**默认参数**：12, 26, 9

**信号判断**：
- 金叉：DIF 上穿 DEA，买入信号 (+1)
- 死叉：DIF 下穿 DEA，卖出信号 (-1)

---

### RSI（动量指标）

**默认参数**：14

**信号判断**：
- 超买：RSI > 80，卖出信号 (-2)
- 偏强：RSI 70-80，卖出信号 (-1)
- 中性：RSI 30-70，中性 (0)
- 偏弱：RSI 20-30，买入信号 (+1)
- 超卖：RSI < 20，买入信号 (+2)

---

### KDJ（动量指标）

**默认参数**：9, 3, 3

**信号判断**：
- 超买：K > 80，卖出信号 (-1)
- 超卖：K < 20，买入信号 (+1)
- 金叉：K 上穿 D，买入信号 (+1)
- 死叉：K 下穿 D，卖出信号 (-1)

---

### 布林带（波动指标）

**默认参数**：20, 2

**信号判断**：
- 突破上轨：价格 > 上轨，卖出信号 (-1)
- 突破下轨：价格 < 下轨，买入信号 (+1)
- 中轨上方：价格 > 中轨，中性 (0)
- 中轨下方：价格 < 中轨，中性 (0)

---

### 均线（趋势指标）

**默认参数**：5, 10, 20, 60

**信号判断**：
- 多头排列：短期 > 中期 > 长期，买入信号 (+1)
- 空头排列：短期 < 中期 < 长期，卖出信号 (-1)
- 震荡：其他情况，中性 (0)

---

## 量价关系指标

### OBV（能量潮）

累计成交量变化，判断资金流向：
- OBV 上升 + 价涨 → 健康上涨
- OBV 下降 + 价跌 → 健康下跌
- OBV 上升 + 价跌 → 底部背离（可能见底）
- OBV 下降 + 价涨 → 顶部背离（可能见顶）

---

### 量价相关系数

价格变化率与成交量变化率的相关性：
- > 0.5：强正相关（量价齐升）
- 0.2 ~ 0.5：弱正相关
- -0.2 ~ 0.2：无明显关联
- -0.5 ~ -0.2：弱负相关（量价背离）
- < -0.5：强负相关（严重背离）

---

### 成交量状态

基于成交量均线判断：
- 放量：当前 > MA5 > MA10 > MA20
- 缩量：当前 < MA5 < MA10 < MA20
- 巨量：当前 > MA5 × 2
- 地量：当前 < MA5 × 0.5

---

### 量比

今日成交量与过去 5 日平均成交量的比值：
- > 3.0：异常放量
- 2.0 ~ 3.0：明显放量
- 1.5 ~ 2.0：温和放量
- 0.7 ~ 1.5：正常
- 0.5 ~ 0.7：明显缩量
- < 0.5：严重缩量

---

## 综合评分

### 技术指标评分

| 总分 | 建议 | 置信度 |
|------|------|--------|
| ≥ 3 | 强烈买入 | 高 |
| 1-2 | 买入 | 中 |
| -1 ~ 0 | 中性 | 低 |
| -2 ~ -1 | 卖出 | 中 |
| ≤ -3 | 强烈卖出 | 高 |

### 量价关系评分

| 评分 | 信号 | 含义 |
|------|------|------|
| ≥ 2 | 看涨 | 量价配合良好，趋势健康 |
| 1 | 偏多 | 量价关系正常 |
| 0 | 中性 | 量价关系不明确 |
| -1 | 偏空 | 量价关系偏弱 |
| ≤ -2 | 看跌 | 量价关系不佳，趋势可能反转 |

---

## 使用场景

### 场景 1：快速判断买卖时机

```
使用者：000001 现在可以买吗？
Agent：运行技术指标分析 + 量价关系分析，查看综合建议
```

### 场景 2：追踪趋势变化

```
使用者：000001 最近趋势怎么样？
Agent：运行技术指标分析，重点看均线、MACD，用量价关系验证
```

### 场景 3：判断超买超卖

```
使用者：000001 是不是涨太多了？
Agent：运行技术指标分析，重点看 RSI、KDJ，用量价关系判断趋势可靠性
```

### 场景 4：判断趋势可靠性

```
使用者：000001 这波上涨是真突破还是假突破？
Agent：运行量价关系分析，看 OBV 趋势和量价配合情况
```

---

## 相关 Skill

| Skill | 联动方式 |
|-------|---------|
| stock_analysis | 个股行情分析，与技术指标结合 |
| stock_screener | 选股筛选，可按技术信号筛选 |
| watchlist_monitor | 自选股监控，批量技术分析 |
| risk_alert | 风险监控，技术面破位作为风险信号 |

---

## 注意事项

1. **指标滞后性**：技术指标基于历史数据，存在滞后性
2. **综合判断**：不要依赖单一指标，应综合多个指标
3. **量价验证**：量价关系验证趋势的可靠性
4. **市场环境**：技术分析在不同市场环境下效果不同
5. **风险提示**：技术指标仅供参考，不构成投资建议
6. **数据要求**：至少需要 30 天历史数据才能计算指标
7. **TA-Lib 依赖**：需要安装 TA-Lib 库

---

## 技术实现

**数据源**：AKShare stock_zh_a_hist

**计算库**：TA-Lib

**输出**：
- 控制台：精简结果（指标值 + 信号 + 建议）
- 文件：完整数据（含历史序列）
