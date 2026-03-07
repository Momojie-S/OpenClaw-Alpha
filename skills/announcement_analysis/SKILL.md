---
name: openclaw_alpha_announcement_analysis
description: "公告解读能力。适用于：(1) 获取当日或指定日期的上市公司公告；(2) 按类型筛选公告（重大事项、财务报告、风险提示等）；(3) 按股票代码或关键词搜索公告。不适用于：公告正文解析、历史公告存档。"
metadata:
  openclaw:
    emoji: "📢"
    requires:
      bins: ["uv"]
---

# 公告解读

获取和分析上市公司公告，包括重大事项、财务报告、风险提示等。

## 使用说明

### 脚本运行

```bash
# 获取今日全部公告
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor

# 获取指定日期公告
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --date 2026-03-07

# 按类型筛选
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --type 重大事项

# 按股票代码搜索
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --code 000001

# 按关键词搜索
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --keyword "重组"

# 组合使用
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --type 风险提示 --top-n 10
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 日期（YYYY-MM-DD） | 今日 |
| `--type` | 公告类型 | 全部 |
| `--code` | 股票代码 | - |
| `--keyword` | 关键词 | - |
| `--top-n` | 返回数量 | 20 |

### 公告类型

| 类型 | 说明 |
|------|------|
| 全部 | 所有公告 |
| 重大事项 | 重大投资、收购、合作等 |
| 财务报告 | 季报、半年报、年报 |
| 风险提示 | 退市风险、业绩预警等 |
| 资产重组 | 重组、并购、剥离等 |
| 融资公告 | 增发、配股、发债等 |
| 持股变动 | 大股东增减持 |
| 信息变更 | 公司更名、变更经营范围等 |

## 分析步骤

### Step 1: 查看当日重要公告

**输入**：当日日期
**动作**：
```bash
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --top-n 30
```
**输出**：当日公告列表，按重要性排序

### Step 2: 筛选风险提示

**输入**：需要关注的公告类型
**动作**：
```bash
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --type 风险提示
```
**输出**：风险提示公告列表

### Step 3: 搜索特定股票公告

**输入**：股票代码
**动作**：
```bash
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --code 000001
```
**输出**：该股票的公告列表

### Step 4: 关键词搜索

**输入**：关注的关键词（如"重组"、"并购"）
**动作**：
```bash
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --keyword "重组"
```
**输出**：包含关键词的公告列表

## 典型场景

### 场景 1: 持仓股票公告监控

检查持仓股票是否有重要公告：
```bash
# 检查单只股票
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --code 000001

# 检查多只股票（需要分别运行或查看全部后筛选）
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --type 重大事项 --keyword "000001"
```

### 场景 2: 全市场风险扫描

筛选所有风险提示公告：
```bash
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --type 风险提示
```

### 场景 3: 寻找并购重组机会

搜索重组相关公告：
```bash
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --type 资产重组 --top-n 30
```

## 注意事项

- 数据来源：东方财富网
- 网络不稳定时可能需要重试
- 公告重要性仅作参考，请阅读原文了解详情
