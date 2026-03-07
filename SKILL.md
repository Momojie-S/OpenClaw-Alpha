---
name: openclaw_alpha
description: "A 股投资分析能力模块。适用于：(1) 市场行情数据获取，(2) 板块热度追踪，(3) 技术指标计算。不适用于：实盘交易、高频策略、美股/港股市场。"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["uv"]
      env: ["TUSHARE_TOKEN"]
    install:
      linux: |
        cd {baseDir}
        cp .env.sample .env
        # 编辑 .env 填入 TUSHARE_TOKEN
        uv sync
---

# OpenClaw-Alpha

A 股投资分析能力模块。

## 安装配置

```bash
cd {baseDir}

# 复制环境变量模板
cp .env.sample .env

# 编辑 .env，填入你的 Tushare Token
# TUSHARE_TOKEN=your_token_here

# 安装依赖
uv sync
```

## 数据源

| 数据源 | 配置要求 | 说明 |
|--------|----------|------|
| AKShare | 无 | 开源免费，无需配置 |
| Tushare | TUSHARE_TOKEN | 需要积分，部分接口有门槛 |

**优先级**：Tushare > AKShare
