# 新闻快速分析

从投资视角快速评估新闻价值，识别相关板块和标的。

---

## 产出清单

### 1. summary（必做）

一句话概括新闻核心内容，通过 CLI `update-news --summary` 写入。

如已有 summary 且准确，跳过。

### 2. analysis（必做）

结构化分析结果，通过 CLI `update-news --analysis` 写入。必填字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `related_sectors` | string[] | 受影响板块 |
| `related_companies` | object[] | 每项含 name、listed(bool)、code |
| `worth_deep_analysis` | boolean | 是否值得深度分析 |

如已有 analysis 且准确，跳过。

### 3. report.md（必做）

在 `news_dir` 下写 `report.md`，包含：
- 一句话概括
- 核心影响分析（每个板块/公司的影响逻辑）
- 投资线索（如有）
- 历史对照（如有相似新闻）

---

## 分析要求

- **投资视角**：关注"对投资有什么影响"，不是新闻摘要
- **完整识别**：所有相关公司都应列出，含未上市和海外
- **多维度交叉**：可调用其他 `openclaw_alpha_*` skill 获取板块热度、资金流向等数据验证
- **诚实原则**：无法判断时明确说明，不强行推断

### worth_deep_analysis 判断依据

- 影响强度是否足够大？
- 是否影响多个重要板块？
- 是否涉及重要上市公司？
- 是否有不确定性需要进一步验证？
