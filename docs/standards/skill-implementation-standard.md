# Skill 实现规范

## 目录结构

```
OpenClaw-Alpha/
├── skills/                         # SKILL 文档目录（只放 SKILL.md 和 tasks）
│   └── {skill_name}/
│       ├── SKILL.md                # 能力说明 + 分析指引（对外）
│       └── tasks/                  # 任务模板（Agent session prompt）
│
├── docs/design/skills/             # Skill 设计文档（集中管理）
│   └── {skill_name}/
│       ├── spec.md                 # 需求文档（业务视角）
│       ├── design.md               # 设计文档（技术视角）
│       └── decisions.md            # 关键决策/调研记录
│
├── src/openclaw_alpha/
│   ├── core/                       # 框架核心
│   ├── data_sources/               # 数据源实现
│   └── skills/                     # Skill 代码目录
│       └── {skill_name}/
│           ├── __init__.py
│           ├── {data_type}_fetcher/
│           │   ├── __init__.py
│           │   ├── {data_type}_fetcher.py
│           │   ├── tushare.py
│           │   └── akshare.py
│           └── {scenario}_processor/
│               ├── __init__.py
│               ├── {scenario}_processor.py
│               └── __main__.py     # 入口文件，调用主模块的 main() 函数
│
├── tests/
│   └── skills/{skill_name}/
│
├── pyproject.toml
└── .env
```

**分离关注点**：
- `skills/{skill_name}/` - 只放文档（SKILL.md + tasks/）
- `docs/design/skills/{skill_name}/` - 放设计文档（spec + design + decisions）
- `src/openclaw_alpha/skills/{skill_name}/` - 放代码（fetcher + processor）
- `src/openclaw_alpha/` - 通过 pyproject.toml 注册为包，所有代码统一导入

---

## 命名规范

| 项目 | 规范 | 示例 |
|------|------|------|
| 目录名 | `{skill_name}` | `industry_trend` |
| skill name | `openclaw_alpha_{skill_name}` | `openclaw_alpha_industry_trend` |
| Fetcher 目录 | `{data_type}_fetcher/` | `concept_fetcher/` |
| Processor 目录 | `{scenario}_processor/` | `industry_trend_processor/` |

> **注意**：目录名必须使用下划线 `_`，不能使用连字符 `-`，否则会导致 Python 模块导入失败。

---

## Frontmatter

每个 `SKILL.md` 必须以 YAML frontmatter 开头：

```yaml
---
name: openclaw_alpha_<功能名>
description: "[功能概述]。适用于：(1) 场景A，(2) 场景B。不适用于：场景X。"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["uv"]
---
```

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | ✅ | 唯一标识符，使用 `openclaw_alpha_` 前缀 |
| `description` | ✅ | 功能描述，包含适用和不适用场景 |
| `emoji` | 建议 | UI 图标 |
| `requires.bins` | ✅ | 有 Python 脚本则 `["uv"]`，无脚本则 `[]` |

---

## SKILL.md 编写规范

### 核心原则：Agent 是唯一读者

SKILL.md 的读者是 agent，不是人类用户。编写时应遵循以下原则：

#### 1. Agent 友好视角

- 描述 agent 需要知道的信息，不解释给人类看的概念
- 直接说明参数作用、返回值格式、数据结构
- 不需要教学式的讲解，agent 能理解专业术语

| ❌ 不应该 | ✅ 应该 |
|----------|--------|
| "获取新闻列表：这个命令会从财联社等新闻源拉取..." | "fetch-news：拉取新闻并落盘，支持多数据源" |
| "analysis：结构化的分析结果，包含板块和公司信息..." | "analysis：包含 related_sectors、related_companies、prediction 等字段" |

#### 2. 能力复用，不列 Skill ID

Agent 默认掌握所有 `openclaw_alpha_*` skill。SKILL.md 中引用其他 skill 时：

- **只说能力名称**，不列 skill ID 或完整名称
- **不提供完整调用方式**，agent 知道如何使用

| ❌ 不应该 | ✅ 应该 |
|----------|--------|
| "使用 `openclaw_alpha_industry_trend` skill 获取板块热度" | "获取板块热度数据" |
| "调用 `uv run python -m openclaw_alpha.skills.stock_analysis...`" | "查看个股行情" |
| "参考 `openclaw_alpha_fund_flow_analysis` skill 的输出格式" | "获取资金流向信息" |

#### 3. 指引不约束，保留 Agent 判断空间

- **不写死流程**：只说明目标和可选路径，不规定必须按某个顺序执行
- **提供做法**：说明有哪些做法，agent 根据场景自行选择
- **信任 agent**：agent 会根据实际情况判断哪个命令/参数更合适

| ❌ 不应该（写死） | ✅ 应该（指引） |
|------------------|--------------|
| "1. 先 fetch-news，然后 update-news，最后 search-similar" | "根据需要拉取新闻，搜索历史，更新分析" |
| "必须先用 --summary 生成 embedding 才能用 search-similar" | "search-similar 依赖已有的 summary" |
| "分析时必须先写 analysis，再写 prediction" | "analysis 可包含 prediction 字段" |

### 信息密度优先

| 必须说明 | 可以简化 |
|----------|----------|
| 参数含义、类型、默认值 | 参数调用的实际示例 |
| 返回值结构、字段说明 | 完整的 JSON 示例 |
| 数据文件路径、格式 | 文件编辑的具体步骤 |
| 适用场景、分析原则 | 完整的端到端流程 |

---

## 设计原则

**默认全自动 + 可定制**

| 用户类型 | 期望 | 设计要求 |
|---------|------|---------|
| 懒人/小白 | 不传参数，自动获取 | 默认行为要"够用" |
| 有经验者 | 指定参数，精准筛选 | 支持可选参数定制 |

**实现方式**：
- 所有参数都应有合理默认值
- 不传参数时，自动获取最全面/最热门的数据
- 传参数时，按指定条件精准筛选

**能力复用**

Agent 默认掌握全部 `openclaw_alpha_*` skill。引用时只说能力，不列 skill ID 或完整名称。

---

## SKILL.md 正文结构

```
Frontmatter
    ↓
# 功能名称
    ↓
## 使用说明
    ├── 脚本运行
    └── 运行记录
    ↓
## 分析步骤
    ├── Step 1: 输入 → 动作 → 输出
    ├── Step 2: ...
    └── （可选）引用其他 skill
```

### 使用指引

- **目标**：说明要达到什么目的
- **做法**：列出可选的操作方式，agent 根据场景选择
- **注意**：说明关键约束、依赖关系

---

## CLI 工具（如有）

只说明命令的功能和参数，不写完整调用示例：

| 命令 | 参数 | 功能 |
|------|------|------|
| `fetch-news` | `--source`, `--limit`, `--keyword` | 拉取新闻并落盘 |

Agent 会根据参数说明自行拼凑命令。

---

## 运行方式

```bash
# 运行 processor
uv run --env-file .env python -m openclaw_alpha.skills.{skill_name}.{processor}

# 示例
uv run --env-file .env python -m openclaw_alpha.skills.industry_trend.industry_trend_processor
```

**注意**：每个 Processor 目录下需创建 `__main__.py` 作为入口，避免模块名与包名冲突的 RuntimeWarning。

---

## 参考资料

- [DataFetcher 实现规范](fetcher-implementation-standard.md)
- [Processor 实现规范](processor-implementation-standard.md)
