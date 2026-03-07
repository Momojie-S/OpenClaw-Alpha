# Skill 实现规范

## 目录结构

```
OpenClaw-Alpha/
├── skills/                         # SKILL 目录（文档 + 代码）
│   └── {skill_name}/
│       ├── SKILL.md                # 能力说明 + 分析指引
│       └── scripts/                # Skill 脚本
│           ├── __init__.py
│           ├── {data_type}_fetcher/
│           │   ├── __init__.py
│           │   ├── {data_type}_fetcher.py
│           │   ├── tushare.py
│           │   └── akshare.py
│           └── {scenario}_processor/
│               ├── __init__.py
│               └── {scenario}_processor.py
│
├── src/openclaw_alpha/
│   ├── core/                       # 框架核心
│   └── data_sources/               # 数据源实现
│
├── tests/                          # 测试
│   └── skills/{skill_name}/
│
├── pyproject.toml                  # 包配置
└── .env                            # 环境变量
```

**分离关注点**：
- `skills/` - 每个 Skill 自包含：文档 + 代码
- `src/openclaw_alpha/` - 框架核心，通过包导入

**导入方式**：
- 基类：`from openclaw_alpha.core.fetcher import Fetcher`
- Skill 内部：`from .xxx import xxx`

**运行方式**：
```bash
# 直接执行
uv run --env-file .env python skills/{skill_name}/scripts/{processor}/{processor}.py

# 模块方式
uv run --env-file .env python -m skills.{skill_name}.scripts.{processor}.{processor}
```

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

## 参考资料

- [DataFetcher 实现规范](fetcher-implementation-standard.md)
- [Processor 实现规范](processor-implementation-standard.md)

