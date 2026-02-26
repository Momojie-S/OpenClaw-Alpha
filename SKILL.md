---
name: openclaw-alpha
description: 股票金融分析 skill。支持 A 股行情查询、技术指标计算、策略回测。当用户询问股票价格、K 线、均线、MACD、策略分析、回测时触发。
metadata:
  {
    "openclaw": {
      "emoji": "📈",
      "requires": { "bins": ["uv"], "env": ["TUSHARE_TOKEN"] },
      "primaryEnv": "TUSHARE_TOKEN"
    }
  }
---

# OpenClaw Alpha - 股票金融分析

A 股市场行情查询与策略分析工具。

## 功能

- 实时行情查询
- K 线数据获取
- 技术指标计算（MA、MACD、RSI 等）
- 策略回测

## 环境配置

```bash
cd ~/.openclaw/workspace/skills/OpenClaw-Alpha
uv sync
```

## 使用

```bash
# 获取行情
uv run {baseDir}/scripts/get_quote.py --symbol 000001

# 运行策略
uv run {baseDir}/scripts/backtest.py --strategy sma --symbol 000001
```

## API Token

需要 [Tushare](https://tushare.pro) Token：

```bash
export TUSHARE_TOKEN=your_token_here
```

或在 `~/.openclaw/openclaw.json` 中配置：

```json
{
  "skills": {
    "openclaw-alpha": {
      "env": {
        "TUSHARE_TOKEN": "your_token_here"
      }
    }
  }
}
```
