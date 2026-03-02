# Phase 1 设计：产业热度追踪子 Skill

> 版本: v1.0
> 创建时间: 2026-02-28
> 更新时间: 2026-03-02
> 状态: 已完成

---

## 一、目标

创建 `industry-trend` 子 skill，为 Echo 提供产业热度追踪能力。

**核心原则**：
- 一个 skill，多个数据脚本
- 脚本只做数据获取，返回结构化 JSON
- Echo 调用脚本，负责分析和回答
- 后续持续扩展数据接口

---

## 二、目录结构

```
OpenClaw-Alpha/
├── src/
│   └── openclaw_alpha/
│       └── commands/
│           ├── board_industry.py   # 行业板块 ✅
│           ├── board_concept.py    # 概念板块 ✅
│           └── ...                 # 后续扩展
├── skills/
│   └── industry-trend/
│       └── SKILL.md                # skill 定义
└── SKILL.md                        # 主 skill 的 SKILL.md
```

---

## 三、已完成的数据脚本

| 脚本 | 功能 | 数据源 | 状态 |
|------|------|--------|------|
| `board_industry.py` | 行业板块行情 | 同花顺 | ✅ |
| `board_concept.py` | 概念板块行情 | 东方财富 | ✅ |

---

## 四、后续扩展计划

| 脚本 | 功能 | 优先级 |
|------|------|--------|
| `stock_hot_rank.py` | 股票热度排名 | P1 |
| `capital_flow.py` | 资金流向 | P1 |
| `board_cons.py` | 板块成分股 | P2 |

---

## 五、验收标准

- [x] 子 skill 目录只有 SKILL.md
- [x] `uv run` 可正常运行脚本
- [x] 返回正确格式的 JSON 数据
- [x] OpenClaw 能加载该子 skill

---

*文档结束*
