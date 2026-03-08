# 文档编写规范

## 核心原则

- **简洁优先** - 每句话都要有价值，避免冗余
- **设计导向** - 说明"是什么"和"为什么"，避免实现细节
- **无代码示例** - 代码在仓库里，不粘贴到文档
- **无版本号时间戳** - 通过 git 查看变更历史
- **概念清晰** - 用自然语言描述，避免让读者猜测

---

## 内容规范

| 应该写 | 不应该写 |
|--------|----------|
| 设计目标和核心思路 | 具体实现代码 |
| 架构概览和模块关系 | 代码示例 |
| 关键决策的背景原因 | 配置文件内容 |
| 接口定义和数据流 | IDE 使用教程 |
| 开发流程和规范要点 | 第三方库基础教程 |

---

## 文档组织

### 目录职责

| 目录 | 内容 | 规范 |
|------|------|------|
| `specs/` | 需求文档 | [spec-standard.md](spec-standard.md) |
| `design/` | 设计文档 | [design-standard.md](design-standard.md) |
| `references/` | API 文档 | [api-doc-standard.md](api-doc-standard.md) |
| `architecture/` | 架构设计 | - |
| `standards/` | 开发规范 | - |

### Skill 文档结构

**Skill 文档自包含在 skills 目录**：
```
skills/{skill_name}/
  SKILL.md             # 能力说明 + 分析指引（必需）
  scripts/             # 脚本代码
```

**开发过程文档（可选）**：
```
docs/skills/{skill_name}/
  spec.md              # 需求文档
  design.md            # 设计文档
```

**迭代流程**：
1. 开发前：在 `docs/skills/{skill_name}/` 编写 spec/design
2. 开发后：合并核心内容到 `skills/{skill_name}/SKILL.md`
3. 合并后：可删除 `docs/skills/{skill_name}/` 目录

### 命名规范

- 使用 kebab-case（如 `industry-trend.md`）
- 文件名应清晰反映内容
- 避免缩写和模糊名称

---

## 文档维护

- 保持文档与代码同步
- 定期审查过时内容
- 移除不再适用的文档
