# Skill 实现规范

## 目录结构

```
OpenClaw-Alpha/
├── skills/                         # SKILL 文档目录（只放 SKILL.md 和 docs）
│   └── {skill_name}/
│       ├── SKILL.md                # 能力说明 + 分析指引（对外）
│       └── docs/                   # 开发文档（对内）
│           ├── spec.md             # 需求文档（业务视角）
│           ├── design.md           # 设计文档（技术视角）
│           └── decisions.md        # 关键决策/调研记录
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
- `skills/{skill_name}/` - 只放文档（SKILL.md + docs/）
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

### 分析步骤

每个步骤包含：
- **输入**：需要什么数据/前置条件
- **动作**：运行什么脚本或做什么操作
- **输出**：产生什么结果，保存到哪里

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
