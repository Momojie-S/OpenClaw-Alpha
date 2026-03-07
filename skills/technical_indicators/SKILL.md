---
name: openclaw_alpha_technical_indicators
description: "技术指标分析：计算 MACD、RSI、KDJ、布林带、均线等技术指标，判断买卖信号。适用于：(1) 技术面分析，(2) 买卖时机判断，(3) 趋势识别。不适用于：基本面分析、自动交易、复杂技术形态。"
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

本 skill 使用 **TA-Lib** 计算技术指标（性能更高）。如果安装失败，会自动降级使用纯 Python 实现。

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

```bash
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001

# 指定天数
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001 --days 120

# 只分析特定指标
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001 --indicators "macd,rsi"

# 自定义参数
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001 --params '{"macd": {"fast": 10, "slow": 20, "signal": 7}}'
```

### 运行记录

运行记录保存在：
- 完整结果：`.openclaw_alpha/technical_indicators/{date}/indicator_analysis.json`

## 分析步骤

### Step 1: 基本分析

**输入**：股票代码

**动作**：运行脚本计算技术指标
```bash
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001
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

### Step 2: 深度分析

**输入**：指定指标和参数

**动作**：自定义分析
```bash
# 只看 MACD 和 RSI
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001 --indicators "macd,rsi"

# 使用更长历史数据（120 天）
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001 --days 120

# 自定义 MACD 参数
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001 --params '{"macd": {"fast": 10, "slow": 22, "signal": 7}}'
```

**输出**：自定义指标的分析结果

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `symbol` | 股票代码 | 必填 |
| `--days` | 历史天数 | 60 |
| `--indicators` | 指标列表（逗号分隔） | 全部 |
| `--params` | 指标参数（JSON 格式） | 默认参数 |
| `--top-n` | 显示最近 N 天信号 | 5 |

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

## 综合评分

基于各指标信号计算综合评分：

| 总分 | 建议 | 置信度 |
|------|------|--------|
| ≥ 3 | 强烈买入 | 高 |
| 1-2 | 买入 | 中 |
| -1 ~ 0 | 中性 | 低 |
| -2 ~ -1 | 卖出 | 中 |
| ≤ -3 | 强烈卖出 | 高 |

---

## 使用场景

### 场景 1：快速判断买卖时机

```
使用者：000001 现在可以买吗？
Agent：运行技术指标分析，查看综合建议
```

### 场景 2：追踪趋势变化

```
使用者：000001 最近趋势怎么样？
Agent：运行技术指标分析，重点看均线、MACD
```

### 场景 3：判断超买超卖

```
使用者：000001 是不是涨太多了？
Agent：运行技术指标分析，重点看 RSI、KDJ
```

### 场景 4：自定义技术分析

```
使用者：用我的参数分析 000001
Agent：运行技术指标分析 --params '{"macd": {...}}'
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
3. **市场环境**：技术分析在不同市场环境下效果不同
4. **风险提示**：技术指标仅供参考，不构成投资建议
5. **数据要求**：至少需要 30 天历史数据才能计算指标
6. **TA-Lib 依赖**：建议安装 TA-Lib 以获得更好性能，如未安装会自动降级使用纯 Python 实现

---

## 技术实现

**数据源**：AKShare stock_zh_a_hist

**计算库**：TA-Lib（优先）或 pandas

**输出**：
- 控制台：精简结果（指标值 + 信号 + 建议）
- 文件：完整数据（含历史序列）
