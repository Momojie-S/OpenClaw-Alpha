# Iteration Loop - 项目自我迭代系统

## 概述

Iteration Loop 是 OpenClaw-Alpha 的核心迭代引擎，负责驱动项目持续自我改进。

**核心理念**：项目不是被动等待指令，而是主动发现问题、处理反馈、推进开发。

---

## 架构定位

```
┌─────────────────────────────────────────────┐
│              Iteration Loop                 │
│            (统一迭代入口)                     │
├─────────────────┬───────────────────────────┤
│  开发任务        │  用户反馈                  │
│  dev_tasks      │  feedback                 │
│  (待实现)        │  (已完成)                  │
└─────────────────┴───────────────────────────┘
```

Iteration Loop 由 Backend 定时触发，检查两类待办事项：

1. **开发任务** (`dev_tasks`) - 项目 TODO、功能开发、bug 修复等
2. **用户反馈** (`feedback`) - 用户提出的问题和建议

两者共享同一个 Agent 执行器，但使用不同的工作流程文档。

---

## 子模块

| 模块 | 路径 | 状态 | 说明 |
|------|------|------|------|
| **feedback** | [./feedback/](./feedback/) | ✅ 已实现 | 用户反馈处理 |
| **dev_tasks** | 待创建 | 🚧 规划中 | 开发任务驱动 |

---

## 处理流程

```
Iteration Loop 触发（定时 / 手动）
    │
    ├── 检查 dev_tasks/
    │   └── 有待执行任务？ → 触发 Agent（dev-task-workflow）
    │
    └── 检查 feedback/new/
        └── 有 pending 反馈？ → 触发 Agent（feedback-workflow）
```

---

## 目录结构

```
workspace/
└── iteration-loop/                  # 迭代工作目录（规划中）
    ├── dev_tasks/                   # 开发任务
    │   ├── pending/                 # 待处理
    │   ├── active/                  # 执行中
    │   └── done/                    # 已完成
    └── feedback/                    # 用户反馈（现有）
        ├── new/                     # 待处理
        └── done/                    # 已完成
```

---

## 相关文档

- [用户反馈处理](./feedback/overview.md) - 反馈处理系统设计
- [反馈 Skill 设计](./feedback/skill-design.md) - Feedback Skill 设计
